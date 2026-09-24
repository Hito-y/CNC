"""部品と穴の表現。すべての部品はワールド座標の軸平行な形状で作る。

座標系: X=ガントリー方向(左右), Y=前後(-Yが手前), Z=上。原点は床面上のフレーム中心。
"""
from dataclasses import dataclass, field

import cadquery as cq

AXES = "xyz"


@dataclass
class Hole:
    axis: str            # 穴の向き 'x' | 'y' | 'z'
    side: int            # 加工する面 +1 / -1 (その軸の正側/負側の面)
    p: tuple             # 穴中心線が通る点 (axis 方向成分は無視)
    dia: float
    through: bool = True  # False なら手前の1枚の壁だけ (角パイプ用)
    note: str = ""
    cbore: float = 0.0    # 座ぐり径 (0 = なし)


@dataclass
class Part:
    name: str                    # 個別名 (例: "Y Frame Tube L")
    bom: str                     # V4 BOM 名に対応するグループ名
    category: str                # "fabricated" | "purchased" | "reference"
    stock: str                   # 素材 (例: "角パイプ 75x50x3")
    bbox: tuple                  # (x0, x1, y0, y1, z0, z1)
    shape: cq.Shape
    color: tuple
    axis: str = ""               # 長手方向 (切断長の基準)
    wall: float = 0.0            # through=False の穴深さ
    holes: list = field(default_factory=list)
    note: str = ""

    @property
    def dims(self):
        b = self.bbox
        return (b[1] - b[0], b[3] - b[2], b[5] - b[4])

    @property
    def length(self):
        return self.dims[AXES.index(self.axis)] if self.axis else max(self.dims)

    def add_hole(self, axis, side, p, dia, through=True, note="", cbore=0.0):
        self.holes.append(Hole(axis, side, tuple(p), dia, through, note, cbore))
        return self

    def finalize(self):
        """穴をブーリアンで抜いた形状に置き換える。"""
        if not self.holes:
            return self
        b = self.bbox
        cutters = []
        for h in self.holes:
            i = AXES.index(h.axis)
            lo, hi = b[2 * i], b[2 * i + 1]
            if h.through:
                start, length = lo - 1.0, hi - lo + 2.0
            else:
                depth = self.wall + 0.5
                start = hi - depth if h.side > 0 else lo - 1.0
                length = depth + 1.0
            pnt = list(h.p)
            pnt[i] = start
            d = [0.0, 0.0, 0.0]
            d[i] = 1.0
            cutters.append(cq.Solid.makeCylinder(h.dia / 2, length, cq.Vector(*pnt), cq.Vector(*d)))
        self.shape = self.shape.cut(cq.Compound.makeCompound(cutters)).clean()
        return self


def box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def tube(bbox, axis, t) -> cq.Shape:
    """axis 方向に中空の角パイプ (角R は省略)。"""
    x0, x1, y0, y1, z0, z1 = bbox
    inner = [x0 + t, x1 - t, y0 + t, y1 - t, z0 + t, z1 - t]
    i = AXES.index(axis)
    inner[2 * i] -= 1.0
    inner[2 * i + 1] += 1.0
    return box(*bbox).cut(box(*inner))


def slabs(bbox, faces, t) -> cq.Shape:
    """bbox の指定面に厚さ t の板を貼った形 (山形鋼 = 2面)。faces 例: ['-y', '+x']"""
    solids = []
    for f in faces:
        s, a = f[0], AXES.index(f[1])
        b = list(bbox)
        if s == "+":
            b[2 * a] = b[2 * a + 1] - t
        else:
            b[2 * a + 1] = b[2 * a] + t
        solids.append(box(*b))
    out = solids[0]
    for s in solids[1:]:
        out = out.fuse(s)
    return out.clean()


def cyl(axis, center, dia, lo, hi) -> cq.Shape:
    i = AXES.index(axis)
    p = list(center)
    p[i] = lo
    d = [0.0, 0.0, 0.0]
    d[i] = 1.0
    return cq.Solid.makeCylinder(dia / 2, hi - lo, cq.Vector(*p), cq.Vector(*d))


def check_holes(parts, min_web=3.0):
    """穴同士・穴と外形端の肉厚が min_web 未満の箇所を返す (座ぐり径を考慮)。"""
    import math
    warns = []
    for q in parts:
        if q.category != "fabricated":
            continue
        hs = q.holes
        for i, a in enumerate(hs):
            ra = max(a.dia, a.cbore) / 2
            ia = AXES.index(a.axis)
            for k in range(3):
                if k == ia:
                    continue
                edge = min(a.p[k] - q.bbox[2 * k], q.bbox[2 * k + 1] - a.p[k]) - ra
                if edge < min_web:
                    warns.append(f"{q.name}: 穴 {a.note} が {AXES[k].upper()} 端に近い (肉 {edge:.1f}mm)")
            for b in hs[i + 1:]:
                if b.axis != a.axis or (not a.through and not b.through and a.side != b.side):
                    continue
                if "ナット" in a.note and "ナット" in b.note:   # SFU ナット自体の寸法 (胴Φ28 / PCD38)
                    continue
                d = math.dist([a.p[k] for k in range(3) if k != ia], [b.p[k] for k in range(3) if k != ia])
                web = d - ra - max(b.dia, b.cbore) / 2
                if web < min_web:
                    warns.append(f"{q.name}: 穴 [{a.note}] と [{b.note}] の間の肉 {web:.1f}mm")
    return warns
