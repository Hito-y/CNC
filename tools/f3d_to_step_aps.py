"""Fusion を使わずに .f3d を STEP に変換する (Autodesk Platform Services の Model Derivative API)。

.f3d の中身は Autodesk 独自形式 (ShapeManager) なので、ローカルでは解析できない。
このスクリプトは Autodesk のクラウド変換サービスに .f3d をアップロードして STEP を受け取る。

準備:
  1. https://aps.autodesk.com でアカウントを作り、アプリを作成して Client ID / Client Secret を取得
     (API に Data Management と Model Derivative を有効化)
  2. 環境変数に設定
       export APS_CLIENT_ID=...
       export APS_CLIENT_SECRET=...

使い方:
  python tools/f3d_to_step_aps.py PrintNC_V4.f3d                  # -> PrintNC_V4.step
  python tools/f3d_to_step_aps.py PrintNC_V4.f3d --format iges
  python tools/f3d_to_step_aps.py --list-formats                  # f3d から変換できる形式を確認

アップロードしたファイルは transient バケット (24時間で自動削除) に置く。
"""
import argparse
import base64
import os
import sys
import time
import uuid
from pathlib import Path

import requests

API = "https://developer.api.autodesk.com"
SCOPES = "data:read data:write data:create bucket:create bucket:read"


def get_token():
    cid, secret = os.environ.get("APS_CLIENT_ID"), os.environ.get("APS_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit("環境変数 APS_CLIENT_ID / APS_CLIENT_SECRET を設定してください")
    r = requests.post(f"{API}/authentication/v2/token", auth=(cid, secret),
                      data={"grant_type": "client_credentials", "scope": SCOPES})
    _check(r, "認証")
    return r.json()["access_token"]


def supported_formats(token):
    r = requests.get(f"{API}/modelderivative/v2/designdata/formats", headers=_h(token))
    _check(r, "形式一覧の取得")
    formats = r.json()["formats"]
    return sorted(out for out, sources in formats.items() if "f3d" in sources)


def upload(token, path):
    bucket = f"f3d-to-step-{uuid.uuid4().hex[:12]}"
    r = requests.post(f"{API}/oss/v2/buckets", headers=_h(token),
                      json={"bucketKey": bucket, "policyKey": "transient"})
    _check(r, "バケット作成")
    key = path.name
    base = f"{API}/oss/v2/buckets/{bucket}/objects/{requests.utils.quote(key)}/signeds3upload"
    r = requests.get(base, headers=_h(token))
    _check(r, "アップロード URL の取得")
    info = r.json()
    with open(path, "rb") as f:
        _check(requests.put(info["urls"][0], data=f), "アップロード")
    r = requests.post(base, headers=_h(token), json={"uploadKey": info["uploadKey"]})
    _check(r, "アップロード完了処理")
    object_id = r.json()["objectId"]
    return base64.urlsafe_b64encode(object_id.encode()).decode().rstrip("=")


def translate(token, urn, fmt):
    r = requests.post(f"{API}/modelderivative/v2/designdata/job",
                      headers={**_h(token), "x-ads-force": "true"},
                      json={"input": {"urn": urn}, "output": {"formats": [{"type": fmt}]}})
    _check(r, "変換ジョブの登録")


def wait_manifest(token, urn, timeout=1800):
    t0 = time.time()
    while True:
        r = requests.get(f"{API}/modelderivative/v2/designdata/{urn}/manifest", headers=_h(token))
        _check(r, "変換状況の取得")
        m = r.json()
        print(f"\r  変換中... {m.get('progress', '')} ({m.get('status')})", end="", flush=True)
        if m.get("status") in ("success", "failed", "timeout"):
            print()
            return m
        if time.time() - t0 > timeout:
            sys.exit("\nタイムアウトしました")
        time.sleep(10)


def find_derivative_urns(manifest, fmt):
    urns = []

    def walk(node):
        if node.get("role") == fmt or node.get("outputType") == fmt:
            if node.get("urn"):
                urns.append(node["urn"])
        for child in node.get("children", []) + node.get("derivatives", []):
            walk(child)

    walk(manifest)
    return urns


def download(token, urn, derivative_urn, out_path):
    r = requests.get(f"{API}/modelderivative/v2/designdata/{urn}/manifest/{requests.utils.quote(derivative_urn)}/signedcookies",
                     headers=_h(token))
    _check(r, "ダウンロード URL の取得")
    r2 = requests.get(r.json()["url"], cookies=r.cookies)
    _check(r2, "ダウンロード")
    out_path.write_bytes(r2.content)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("f3d", nargs="?", type=Path)
    ap.add_argument("--format", default="step", choices=["step", "iges", "stl", "obj"])
    ap.add_argument("--out", type=Path, help="出力先 (既定: 入力と同じ場所・同じ名前)")
    ap.add_argument("--list-formats", action="store_true")
    a = ap.parse_args()

    token = get_token()
    formats = supported_formats(token)
    if a.list_formats or not a.f3d:
        print("f3d から変換できる形式:", ", ".join(formats))
        return
    if a.format not in formats:
        sys.exit(f"f3d → {a.format} は APS が対応していません。対応形式: {', '.join(formats)}")

    print(f"アップロード: {a.f3d}")
    urn = upload(token, a.f3d)
    translate(token, urn, a.format)
    manifest = wait_manifest(token, urn)
    if manifest.get("status") != "success":
        sys.exit(f"変換に失敗しました: {manifest}")
    ders = find_derivative_urns(manifest, a.format)
    if not ders:
        sys.exit(f"出力が見つかりません: {manifest}")
    ext = {"step": ".step", "iges": ".iges", "stl": ".stl", "obj": ".obj"}[a.format]
    for i, d in enumerate(ders):
        out = a.out or a.f3d.with_suffix(ext)
        if len(ders) > 1:
            out = out.with_name(f"{out.stem}_{i + 1}{ext}")
        download(token, urn, d, out)
        print(f"保存: {out} ({out.stat().st_size / 1e6:.1f} MB)")


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _check(r, what):
    if not r.ok:
        sys.exit(f"{what}に失敗 (HTTP {r.status_code}): {r.text[:500]}")


if __name__ == "__main__":
    main()
