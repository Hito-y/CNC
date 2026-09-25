"""部品同士の干渉を調べる (可動部の位置を変えて何通りか試す)。

    python tools/check_clash.py                      # 既定寸法、可動部を中央/両端に置いて確認
    python tools/check_clash.py cut_z=100

レールとキャリッジ、ねじとナット/サポート、工具と捨て板 (最下点で 5mm 食い込む設定) の
重なりは簡略形状による想定内のものなので除外して表示する。
"""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from printnc_simple import Params, build  # noqa: E402

EXPECTED = ("Rail", "Ballscrew", "Z Nut Block")
POSES = [(0.5, 0.5, 0.5), (0, 0, 0), (1, 1, 1), (0, 1, 1), (1, 0, 0)]


def clashes(p):
    parts, _ = build(p)
    out = []
    for a, b in itertools.combinations(parts, 2):
        A, B = a.bbox, b.bbox
        if any(A[2 * i + 1] <= B[2 * i] + 0.01 or B[2 * i + 1] <= A[2 * i] + 0.01 for i in range(3)):
            continue
        names = a.name + " " + b.name
        if any(e in names for e in EXPECTED) or {a.name, b.name} == {"Wasteboard", "Spindle"}:
            continue
        v = a.shape.intersect(b.shape).Volume()
        if v > 1.0:
            out.append((round(v), a.name, b.name))
    return out


def main():
    kw = {k: float(v) for k, v in (arg.split("=") for arg in sys.argv[1:])}
    bad = 0
    for pos in POSES:
        p = Params(**kw, pos_x=pos[0], pos_y=pos[1], pos_z=pos[2])
        res = clashes(p)
        bad += len(res)
        print(f"位置 {pos}: {'干渉なし' if not res else res}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
