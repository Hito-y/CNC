"""簡易 PrintNC フレームを生成する。

例:
    python build.py                       # 既定値 (300 x 400 x 150)
    python build.py --cut_x 400 --cut_y 300 --out output_400x300
    python build.py --no-step --no-render # 表・図面だけ素早く更新
"""
import argparse
import dataclasses
import time
from pathlib import Path

from printnc_simple import Params, build
from printnc_simple import export
from printnc_simple.geometry import check_holes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for f in dataclasses.fields(Params):
        if f.type in (float, int, "float", "int"):
            ap.add_argument(f"--{f.name}", type=float if f.type in (float, "float") else int, default=None)
    ap.add_argument("--out", default="output")
    ap.add_argument("--no-step", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()

    p = Params(**{k: v for k, v in vars(a).items() if k in Params.field_names() and v is not None})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    parts, L = build(p)
    print(f"部品 {len(parts)} 点を生成 ({time.time() - t0:.1f}s)")

    export.write_cut_list_csv(parts, out / "cut_list.csv")
    export.write_drill_csv(parts, out / "drill_holes.csv")
    svgs = export.write_svgs(parts, out / "drawings")
    warns = check_holes(parts)
    for w in warns:
        print("警告:", w)
    export.write_summary(p, L, parts, out / "summary.md", svgs, warns)
    if not a.no_step:
        export.export_step(parts, out / "printnc_simple.step")
        export.export_stl(parts, out / "printnc_simple.stl")
    if not a.no_render:
        export.render_png(parts, out / "preview.png")
        export.render_png(parts, out / "preview_iso.png", views=[("", 22, -58)], size=(12, 9))
    print(f"出力: {out.resolve()}  ({time.time() - t0:.1f}s)")
    print(f"  フレーム外形 {L.y_span + p.tube_w:.0f} x {L.y_frame_len:.0f} mm, ガントリー上面 {L.z_gt:.0f} mm")


if __name__ == "__main__":
    main()
