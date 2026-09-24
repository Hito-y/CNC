"""出力: STEP / STL / 切断リスト / 穴位置表 / 1:1 型紙 SVG / プレビュー PNG / 概要 Markdown"""
import csv
import math
from collections import OrderedDict
from pathlib import Path

import cadquery as cq

from .geometry import AXES

FACE_JA = {("x", 1): "+X面(右)", ("x", -1): "-X面(左)", ("y", 1): "+Y面(奥)", ("y", -1): "-Y面(手前)",
           ("z", 1): "+Z面(上)", ("z", -1): "-Z面(下)"}
TEMPLATE_MAX = 380.0
SVG_FONT = "Noto Sans CJK JP, IPAGothic, Hiragino Sans, Yu Gothic, Meiryo, sans-serif"   # これ以下の面は 1:1 型紙として出力


def _fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _unique_names(parts):
    seen = {}
    out = []
    for q in parts:
        n = seen.get(q.name, 0)
        seen[q.name] = n + 1
        out.append(q.name if n == 0 else f"{q.name} #{n + 1}")
    return out


def export_step(parts, path):
    assy = cq.Assembly(name="printnc_simple")
    for name, q in zip(_unique_names(parts), parts):
        assy.add(q.shape, name=name.replace(" ", "_").replace("#", "n"), color=cq.Color(*q.color))
    assy.export(str(path))


def export_stl(parts, path, tol=0.4):
    cq.exporters.export(cq.Compound.makeCompound([q.shape for q in parts]), str(path),
                        tolerance=tol, angularTolerance=0.3)


# ----------------------------------------------------------------- lists
def _dims_str(q):
    d = sorted((round(v, 1) for v in q.dims), reverse=True)
    return " x ".join(_fmt(v) for v in d)


def cut_list(parts):
    """(fabricated, purchased) それぞれ OrderedDict[key] -> dict"""
    groups = {"fabricated": OrderedDict(), "purchased": OrderedDict()}
    for q in parts:
        if q.category not in groups:
            continue
        if q.category == "fabricated":
            key = (q.bom, q.stock, _dims_str(q))
            size = _fmt(q.length) if q.axis else ""
        else:
            key = (q.bom, q.stock, "")
            size = ""
        g = groups[q.category].setdefault(key, {"bom": q.bom, "stock": q.stock, "dims": key[2],
                                                 "length": size, "qty": 0, "names": [], "note": q.note})
        g["qty"] += 1
        g["names"].append(q.name)
    return groups["fabricated"], groups["purchased"]


def write_cut_list_csv(parts, path):
    fab, pur = cut_list(parts)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["区分", "部品", "素材/型番", "切断長(mm)", "外形(mm)", "数量", "個別名", "備考"])
        for label, grp in (("加工品", fab), ("購入品", pur)):
            for g in grp.values():
                w.writerow([label, g["bom"], g["stock"], g["length"], g["dims"], g["qty"],
                            " / ".join(OrderedDict.fromkeys(g["names"])), g["note"]])


def _face_axes(q, axis, side):
    """穴の面内の2軸。長手方向を先にし、その面の外側から見て鏡像にならない順にする。"""
    others = [a for a in AXES if a != axis]
    if q.axis in others:
        others.remove(q.axis)
        others.insert(0, q.axis)
    u, v = others
    # e_u x e_v が外向き法線 (side * e_axis) と同じ向きなら鏡像にならない
    iu, iv, ia = AXES.index(u), AXES.index(v), AXES.index(axis)
    cyc = 1 if (iv - iu) % 3 == 1 else -1          # e_u x e_v = cyc * e_(third)
    if cyc * side < 0:
        u, v = v, u
    return u, v


def hole_rows(q):
    """穴位置表。貫通穴は軸ごとに 1 面にまとめる (最初の穴の面から見た図)。"""
    view_side = {}
    for h in q.holes:
        if h.through:
            view_side.setdefault(h.axis, h.side)
    rows = []
    for h in q.holes:
        side = view_side[h.axis] if h.through else h.side
        key = (h.axis, side, h.through)
        u, v = _face_axes(q, h.axis, side)
        iu, iv = AXES.index(u), AXES.index(v)
        pu = h.p[iu] - q.bbox[2 * iu]
        pv = h.p[iv] - q.bbox[2 * iv]
        face = FACE_JA[(h.axis, side)] + ("から貫通" if h.through else "")
        rows.append({"face": face, "u": u, "v": v, "pu": pu, "pv": pv, "dia": h.dia,
                     "through": h.through, "note": h.note, "key": key, "cbore": h.cbore})
    rows.sort(key=lambda r: (r["face"], round(r["pv"], 1), round(r["pu"], 1)))
    return rows


def write_drill_csv(parts, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["部品", "面", "基準軸1", "位置1(端から mm)", "基準軸2", "位置2(端から mm)", "穴径", "加工", "用途"])
        for q in parts:
            if q.category != "fabricated":
                continue
            for r in hole_rows(q):
                w.writerow([q.name, r["face"], r["u"].upper(), _fmt(r["pu"]), r["v"].upper(), _fmt(r["pv"]),
                            f"Φ{_fmt(r['dia'])}", "貫通" if r["through"] else "片側の壁のみ", r["note"]])


# ----------------------------------------------------------------- SVG
def write_svgs(parts, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("*.svg"):
        old.unlink()
    done = set()
    written = []
    for q in parts:
        if q.category != "fabricated" or not q.holes or q.name in done:
            continue
        done.add(q.name)
        rows = hole_rows(q)
        faces = OrderedDict()
        for r in rows:
            faces.setdefault(r["key"], []).append(r)
        for (axis, side, through), hs in faces.items():
            u, v = hs[0]["u"], hs[0]["v"]
            iu, iv = AXES.index(u), AXES.index(v)
            W = q.bbox[2 * iu + 1] - q.bbox[2 * iu]
            H = q.bbox[2 * iv + 1] - q.bbox[2 * iv]
            scale = 1 if max(W, H) <= TEMPLATE_MAX else math.ceil(max(W, H) / TEMPLATE_MAX)
            fname = f"{q.name.replace(' ', '_')}_{axis}{'p' if side > 0 else 'm'}{'' if through else '_wall'}.svg"
            written.append(fname)
            (outdir / fname).write_text(_svg(q, hs[0]["face"] + "側から見た図", u, v, W, H, hs, scale),
                                        encoding="utf-8")
    return written


def _svg(q, face, u, v, W, H, hs, scale):
    m = 25.0                      # 余白 (mm, 印刷上)
    w, h = W / scale, H / scale
    tw, th = w + 2 * m, h + 2 * m + 22
    title = f"{q.name} — {face}  外形 {_fmt(W)} x {_fmt(H)} mm"
    sub = ("縮尺 1:1 (100%で印刷して型紙に使用 / 基準辺を材料の端に合わせる)" if scale == 1
           else f"縮尺 1:{scale} (型紙ではない。寸法は穴位置表 CSV を使用)")
    X = lambda a: m + a / scale
    Y = lambda b: m + 14 + (h - b / scale)   # v を上向きに
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{tw:.1f}mm" height="{th:.1f}mm" '
          f'viewBox="0 0 {tw:.1f} {th:.1f}" font-family="{SVG_FONT}">',
          f'<rect x="0" y="0" width="{tw:.1f}" height="{th:.1f}" fill="white"/>',
          f'<text x="{m}" y="7" font-size="4">{title}</text>',
          f'<text x="{m}" y="12" font-size="3" fill="#555">{sub}</text>',
          f'<rect x="{X(0):.2f}" y="{Y(H):.2f}" width="{w:.2f}" height="{h:.2f}" fill="none" stroke="black" stroke-width="0.3"/>',
          f'<text x="{X(0):.1f}" y="{Y(0) + 5:.1f}" font-size="3">原点 ({u.upper()}→, {v.upper()}↑)</text>']
    fs = 2.2 if scale == 1 else 1.8
    for r in hs:
        cx, cy, rr = X(r["pu"]), Y(r["pv"]), r["dia"] / 2 / scale
        el.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{rr:.2f}" fill="none" stroke="red" stroke-width="0.25"/>')
        if r["cbore"]:
            el.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r["cbore"] / 2 / scale:.2f}" fill="none" '
                      f'stroke="red" stroke-width="0.15" stroke-dasharray="0.8,0.6"/>')
        el.append(f'<path d="M{cx - 2:.2f},{cy:.2f}H{cx + 2:.2f}M{cx:.2f},{cy - 2:.2f}V{cy + 2:.2f}" '
                  f'stroke="red" stroke-width="0.15"/>')
        el.append(f'<text x="{cx + rr + 0.8:.2f}" y="{cy - 0.8:.2f}" font-size="{fs}">'
                  f'Φ{_fmt(r["dia"])} ({_fmt(r["pu"])}, {_fmt(r["pv"])})</text>')
    # 100mm スケールバーで印刷倍率を確認
    y0 = th - 5
    el.append(f'<path d="M{m},{y0}h{100 / scale:.2f}" stroke="black" stroke-width="0.5"/>')
    el.append(f'<text x="{m}" y="{y0 - 1.5}" font-size="2.5">100 mm</text>')
    el.append("</svg>")
    return "\n".join(el)


# ----------------------------------------------------------------- render
def render_png(parts, path, views=None, size=(16, 11), dpi=110):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris, cols = [], []
    light = np.array([0.35, -0.55, 0.75])
    light /= np.linalg.norm(light)
    for q in parts:
        verts, faces = q.shape.tessellate(1.0, 0.5)
        V = np.array([(p.x, p.y, p.z) for p in verts])
        F = np.array(faces)
        if len(F) == 0:
            continue
        T = _subdivide(V[F], 40.0)
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        shade = 0.45 + 0.55 * np.abs(n @ light)
        c = np.clip(np.array(q.color)[None, :] * shade[:, None], 0, 1)
        tris.append(T)
        cols.append(c)
    T = np.concatenate(tris)
    C = np.concatenate(cols)
    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    views = views or [("アイソメ", 22, -58), ("正面 (-Y から)", 0, -90), ("側面 (+X から)", 0, 0), ("上面", 90, -90)]
    plt.rcParams["font.family"] = _jp_font()
    fig = plt.figure(figsize=size, dpi=dpi)
    ncol = 2 if len(views) > 1 else 1
    nrow = math.ceil(len(views) / ncol)
    for i, (title, elev, azim) in enumerate(views):
        ax = fig.add_subplot(nrow, ncol, i + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(T, facecolors=C, edgecolors="none", linewidths=0))
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
        ax.set_box_aspect(hi - lo, zoom=1.25)
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def _subdivide(T, max_edge):
    """長い三角形を分割して matplotlib の奥行きソートの破綻を減らす。"""
    import numpy as np
    out = []
    while len(T):
        e = np.stack([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1),
                      np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], axis=1)
        long_ = e.max(axis=1) > max_edge
        out.append(T[~long_])
        T = T[long_]
        if not len(T):
            break
        k = e[long_].argmax(axis=1)
        a = T[np.arange(len(T)), k]
        b = T[np.arange(len(T)), (k + 1) % 3]
        c = T[np.arange(len(T)), (k + 2) % 3]
        m = (a + b) / 2
        T = np.concatenate([np.stack([a, m, c], 1), np.stack([m, b, c], 1)])
    return np.concatenate(out)


def _jp_font():
    from matplotlib import font_manager
    for name in ("Noto Sans CJK JP", "IPAexGothic", "IPAGothic", "TakaoGothic", "Hiragino Sans", "Yu Gothic"):
        if any(f.name == name for f in font_manager.fontManager.ttflist):
            return name
    return "DejaVu Sans"


# ----------------------------------------------------------------- summary
def write_summary(p, L, parts, path, svgs, warns=()):
    fab, pur = cut_list(parts)
    tip_lo = L.tip_min
    lines = [
        "# 簡易 PrintNC フレーム 設計サマリー",
        "",
        "`python build.py` で自動生成。寸法は mm。",
        "",
        "## 主要寸法",
        "",
        "| 項目 | 値 |",
        "|---|---|",
        f"| 加工範囲 X × Y × Z | {_fmt(p.cut_x)} × {_fmt(p.cut_y)} × {_fmt(p.cut_z)} |",
        f"| フレーム外形 (X × Y) | {_fmt(L.y_span + p.tube_w)} × {_fmt(L.y_frame_len)} |",
        f"| ガントリー上面高さ | {_fmt(L.z_gt)} |",
        f"| 左右Yチューブ中心間 | {_fmt(L.y_span)} |",
        f"| ガントリー長 | {_fmt(L.gantry_len)} |",
        f"| X/Y レール長 | {_fmt(L.x_rail_len)} / {_fmt(L.y_rail_len)} |",
        f"| ガントリー下面の高さ (捨て板上面から) | {_fmt(L.z_gb - L.wb_top)} |",
        f"| 支柱の高さ | {_fmt(L.upright_h)} |",
        f"| Zストローク | {_fmt(L.z_travel)} |",
        f"| 工具先端の到達範囲 (捨て板上面基準) | {_fmt(tip_lo - L.wb_top)} 〜 {_fmt(L.tip_max - L.wb_top)} |",
        f"| 主軸のガントリー中心からの前方オフセット | {_fmt(-L.sp_y_off)} |",
        f"| 捨て板 (X × Y) | {_fmt(2 * L.wb_half_x)} × {_fmt(L.wb_y[1] - L.wb_y[0])} |",
        "",
        "## 自動チェック",
        "",
        ("- 穴の縁距離・穴間の肉厚: すべて 3mm 以上" if not warns else
         "\n".join(f"- ⚠ {w}" for w in warns)),
        "",
        "## 加工品 (切断リスト)",
        "",
        "| 部品 | 素材 | 切断長 | 外形 | 数量 | 備考 |",
        "|---|---|---|---|---|---|",
    ]
    for g in fab.values():
        lines.append(f"| {g['bom']} | {g['stock']} | {g['length']} | {g['dims']} | {g['qty']} | {g['note']} |")
    lines += ["", "## 購入品", "", "| 部品 | 型番/仕様 | 数量 |", "|---|---|---|"]
    for g in pur.values():
        lines.append(f"| {g['bom']} | {g['stock']} | {g['qty']} |")
    tube_total = sum(q.length for q in parts if q.category == "fabricated" and q.stock.startswith("角パイプ"))
    lines += ["", f"角パイプ合計長さ: 約 {_fmt(tube_total)} mm (切り代・端材別)", "",
              "## 穴あけ図 (drawings/)", "",
              "1:1 と書かれたものは 100% で印刷してポンチ打ちの型紙として使える。100mm スケールバーで倍率を確認すること。", ""]
    for s in svgs:
        lines.append(f"- [{s}](drawings/{s})")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
