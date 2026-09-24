"""PrintNC V4 ベース簡易フレームの形状生成。

V4 からの主な変更 (3Dプリンター不要化):
  * 印刷/切削部品 (ボールねじナットマウント等) → 市販の山形鋼・平鋼を切って穴あけ
  * 印刷ドリルガイド・組立治具 → 本スクリプトが出力する穴位置表と 1:1 型紙 (SVG)
  * ガントリー/ベースは溶接せず M6 全ネジで締結 (V4 BOM の threaded rod 構成に準拠)
  * Z軸は HGR15 ×2 本 (2Z 構成) を 12mm アルミ板に取付け、レール可動・キャリッジ固定
"""
import math
from types import SimpleNamespace

from .geometry import Part, box, cyl, slabs, tube

STEEL = (0.30, 0.32, 0.36)
ALU = (0.78, 0.80, 0.83)
FLAT = (0.55, 0.45, 0.40)
RAIL = (0.60, 0.62, 0.66)
CAR = (0.16, 0.36, 0.72)
MOTOR = (0.10, 0.10, 0.10)
MOUNT = (0.40, 0.40, 0.44)
SCREW = (0.86, 0.74, 0.36)
WOOD = (0.82, 0.68, 0.45)
SPINDLE = (0.93, 0.93, 0.93)

SFU1610_BORE = 29.0   # ナット胴 Φ28 + 逃げ
SFU1610_FLANGE = 48.0
SFU1610_PCD = 38.0
TAP_M5 = 4.2
CLR_M6 = 6.6
CLR_M5 = 5.5
CLR_M4 = 4.5
ROD_M6 = 7.0


def ceil5(v):
    return math.ceil(v / 5.0 - 1e-9) * 5.0


def compute_layout(p):
    """パラメータから主要寸法と可動部の位置を決める。"""
    L = SimpleNamespace()
    Th, Tw = p.tube_h, p.tube_w
    ya, yb, yt = p.y_angle
    L.nut_r = SFU1610_FLANGE / 2

    # --- 高さ方向 (z=0 は床) ---
    L.z_ft = Th                                 # フレーム上面 (Yレール取付面)
    L.z_ycar = L.z_ft + p.c20_h                 # Yキャリッジ上面
    L.z_rt = L.z_ycar + Tw                      # Yローラー上面 (75幅を下向き)
    L.wb_top = L.z_ft + p.wasteboard_t
    L.z_gb = max(L.wb_top + p.cut_z + p.gantry_clear, L.z_rt)
    L.upright_h = L.z_gb - L.z_rt
    L.z_gt = L.z_gb + 2 * Th                    # ガントリー (2段重ね) 上面
    L.ys_z = L.z_ft + p.spacer_t + 25.0         # Yねじ軸高さ (BK12 中心高 25)
    L.xs_z = L.z_gt + p.spacer_t + 25.0         # Xねじ軸高さ

    # --- Yねじ位置: Yチューブ中心から内側へのオフセット ---
    L.ys_off = Th / 2 + p.brace_t + yt + 30.0

    # --- Z軸 ---
    L.tip_min = L.wb_top - p.z_margin_low
    L.tip_max = L.wb_top + p.cut_z + p.z_margin_high
    L.z_travel = L.tip_max - L.tip_min
    L.zpb_min = L.tip_min + p.spindle_below + p.tool_stickout   # Zプレート下端 (最下点)
    L.zpb_max = L.zpb_min + L.z_travel
    L.z_row1 = L.zpb_max + 10.0 + p.c15_l / 2                   # Zキャリッジ下段中心
    L.z_row2 = L.z_row1 + p.z_car_pitch
    L.z_nut = (L.z_row1 + L.z_row2) / 2
    L.xa_h = max(60.0, 2 * (L.nut_r + 6.0))                     # Xナットアングル長さ
    L.xa_z0 = L.z_gt + 5.0
    L.brace_in_top = L.z_gb - 5.0                               # 内側ブレース上端 (Xプレートの逃げ)
    L.xplate_z0 = min(L.z_gb + Th / 2 - p.c20_b / 2 - 12.0, L.z_gb + 3.0)   # 下段Xキャリッジ穴の縁距離 12
    assert L.xplate_z0 > L.brace_in_top + 2.0, "Xプレート下端が内側ブレースに当たる"
    L.xplate_z1 = L.xplate_z0 + ceil5(max(L.xa_z0 + L.xa_h, L.z_row2 + p.c15_l / 2 + 5.0) - L.xplate_z0)
    L.zplate_h = ceil5(L.xplate_z1 + 5.0 - L.zpb_min)
    L.zplate_w = ceil5(2 * (p.z_car_x + p.c15_w / 2) + 10.0)
    L.xplate_w = ceil5(max(p.x_car_pitch + p.c20_l + 20.0, L.zplate_w))

    # --- X方向 ---
    L.x_rail_len = ceil5(p.cut_x + p.x_car_pitch + p.c20_l + 2 * p.r20_e)
    wb_side = max(L.ys_off + L.nut_r, Th / 2 + p.brace_t + ya) + 6.0
    span_wb = p.cut_x + 20.0 + 2 * wb_side                      # 捨て板が加工範囲を覆う
    span_z = p.cut_x + L.zplate_w + 20.0 + Th + 2 * p.brace_t   # Zプレートが内側ブレースに当たらない
    span_rail = L.x_rail_len - Th
    L.y_span = ceil5(max(span_wb, span_z, span_rail))           # 左右Yチューブ中心間
    L.gantry_len = L.y_span + Th
    L.x_frame_len = L.y_span - Tw
    L.wb_half_x = L.y_span / 2 - wb_side

    # --- 前後方向 ---
    L.y_rail_len = ceil5(p.cut_y + p.y_car_pitch + p.c20_l + 2 * p.r20_e)
    L.gy = -p.cut_y / 2 + p.pos_y * p.cut_y                     # ガントリー中心 y
    L.xp = -p.cut_x / 2 + p.pos_x * p.cut_x                     # Xキャリッジ群中心 x
    L.zpb = L.zpb_min + p.pos_z * L.z_travel
    L.y_gf = L.gy - Tw / 2                                      # ガントリー前面
    L.y_xpb = L.y_gf - p.c20_h                                  # Xプレート背面
    L.y_xpf = L.y_xpb - p.plate_t                               # Xプレート前面
    L.z_gap = p.c15_h + p.z_spacer_t
    L.y_zpb = L.y_xpf - L.z_gap                                 # Zプレート背面
    L.y_zpf = L.y_zpb - p.plate_t
    L.zs_y = L.y_xpf - L.z_gap / 2                              # Zねじ軸 y
    L.sp_y_off = (L.y_zpf - 10.0 - p.spindle_d / 2) - L.gy      # 主軸のガントリー中心からの y オフセット
    L.tool_y = (-p.cut_y / 2 + L.sp_y_off, p.cut_y / 2 + L.sp_y_off)
    L.wb_y = (L.tool_y[0] - 10.0, L.tool_y[1] + 10.0)
    # 端の横桁とその上の BK/BF/HM がスピンドル (半径分) に当たらない位置まで延ばす
    reach = p.spindle_d / 2 + 5.0
    L.yf0 = min(-L.y_rail_len / 2 - Tw, L.wb_y[0] - Tw, L.tool_y[0] - reach - Tw)
    L.yf1 = max(L.y_rail_len / 2 + Tw, L.wb_y[1] + Tw, L.tool_y[1] + reach + Tw)
    L.y_frame_len = L.yf1 - L.yf0
    return L


def build(p):
    """部品リストと Layout を返す。"""
    L = compute_layout(p)
    parts = []
    Th, Tw, t = p.tube_h, p.tube_w, p.tube_t
    tube_stock = f"角パイプ {Th:g}x{Tw:g}x{t:g}"

    def add(part):
        parts.append(part)
        return part

    def rail_positions(length, e, pitch):
        n = int((length - 2 * e) // pitch) + 1
        return [e + k * pitch for k in range(n)]

    # ============================ ベースフレーム ============================
    cross_y = [L.yf0 + Tw / 2, L.yf1 - Tw / 2]
    n_mid = max(0, p.n_x_frame - 2)
    for k in range(n_mid):
        cross_y.insert(-1, L.yf0 + Tw / 2 + (k + 1) * (L.y_frame_len - Tw) / (n_mid + 1))

    for s, tag in ((-1, "L"), (1, "R")):
        xc = s * L.y_span / 2
        bb = (xc - Tw / 2, xc + Tw / 2, L.yf0, L.yf1, 0, Th)
        yt_ = add(Part(f"Y Frame Tube {tag}", "Y Frame Tubing", "fabricated", tube_stock, bb,
                       tube(bb, "y", t), STEEL, axis="y", wall=t))
        for yy in rail_positions(L.y_rail_len, p.r20_e, p.r20_pitch):
            yt_.add_hole("z", 1, (xc, -L.y_rail_len / 2 + yy, 0), TAP_M5, False, "Yレール M5タップ")
        for cy in cross_y:
            for dz in (-18, 18):
                yt_.add_hole("x", 1, (0, cy, Th / 2 + dz), ROD_M6, True, "横桁締結 M6全ネジ")
        # Yレール / キャリッジ
        add(Part(f"Y Rail {tag}", "HGR20 Rail (Y)", "purchased", f"HGR20 L={L.y_rail_len:g}",
                 (xc - p.r20_w / 2, xc + p.r20_w / 2, -L.y_rail_len / 2, L.y_rail_len / 2, Th, Th + p.r20_h),
                 box(xc - p.r20_w / 2, xc + p.r20_w / 2, -L.y_rail_len / 2, L.y_rail_len / 2, Th, Th + p.r20_h),
                 RAIL, axis="y"))
        for dy in (-p.y_car_pitch / 2, p.y_car_pitch / 2):
            cy = L.gy + dy
            bb = (xc - p.c20_w / 2, xc + p.c20_w / 2, cy - p.c20_l / 2, cy + p.c20_l / 2, Th + 4.6, L.z_ycar)
            add(Part(f"Y Carriage {tag}", "HGW20CC Carriage", "purchased", "HGW20CC", bb, box(*bb), CAR))

    for i, cy in enumerate(cross_y):
        bb = (-L.x_frame_len / 2, L.x_frame_len / 2, cy - Tw / 2, cy + Tw / 2, 0, Th)
        add(Part(f"X Frame Tube {i + 1}", "X Frame Tubing", "fabricated", tube_stock, bb,
                 tube(bb, "x", t), STEEL, axis="x", wall=t,
                 note="Yチューブ間に突合せ、内部に M6 全ネジ 2本を通して締結"))
        for dz in (-18, 18):
            add(Part("Base Tie Rod", "M6 Threaded Rod (X base)", "purchased",
                     f"M6 全ネジ L={L.y_span + Tw + 30:g}", (0,) * 6,
                     cyl("x", (0, cy, Th / 2 + dz), 6.0, -(L.y_span + Tw) / 2 - 15, (L.y_span + Tw) / 2 + 15),
                     SCREW, axis="x"))
    # 捨て板
    bb = (-L.wb_half_x, L.wb_half_x, L.wb_y[0], L.wb_y[1], Th, L.wb_top)
    add(Part("Wasteboard", "Wasteboard", "purchased", f"合板/MDF t={p.wasteboard_t:g}", bb, box(*bb), WOOD))

    # ============================ Y ローラー / 支柱 / ブレース ============================
    ya, yb, yt = p.y_angle
    z_rb = L.z_ycar + Tw / 2   # ローラー締結ボルト高さ
    for s, tag in ((-1, "L"), (1, "R")):
        xc = s * L.y_span / 2
        x_in = xc - s * Th / 2     # 内側面
        x_out = xc + s * Th / 2    # 外側面
        # Yローラー (75 面を下にして Y キャリッジ 2 個に載せる)
        bb = (xc - Th / 2, xc + Th / 2, L.gy - p.y_roller_len / 2, L.gy + p.y_roller_len / 2, L.z_ycar, L.z_rt)
        roller = add(Part(f"Y Roller {tag}", "Y Roller Tubing", "fabricated", tube_stock, bb,
                          tube(bb, "y", t), STEEL, axis="y", wall=t))
        for dy in (-p.y_car_pitch / 2, p.y_car_pitch / 2):
            for bx in (-p.c20_b / 2, p.c20_b / 2):
                for by in (-p.c20_c / 2, p.c20_c / 2):
                    pt = (xc + bx, L.gy + dy + by, 0)
                    roller.add_hole("z", -1, pt, CLR_M6, False, "Yキャリッジ M6")
                    roller.add_hole("z", 1, pt, 12.0, False, "工具挿入穴 (M6頭用)")
        # 支柱
        upright = None
        if L.upright_h > 1:
            bb = (xc - Th / 2, xc + Th / 2, L.gy - Tw / 2, L.gy + Tw / 2, L.z_rt, L.z_gb)
            upright = add(Part(f"Upright {tag}", "Y Roller Tubing (upright)", "fabricated", tube_stock, bb,
                               tube(bb, "z", t), STEEL, axis="z", wall=t,
                               note="Yローラー上に立て、両側ブレースで挟んで締結"))
        # ブレース (内側: ガントリー下面まで / 外側: ガントリー上面まで)
        def brace_bb(side, z1):
            if side == "in":
                xa, xb_ = (x_in - s * p.brace_t, x_in)
            else:
                xa, xb_ = (x_out, x_out + s * p.brace_t)
            return (min(xa, xb_), max(xa, xb_), L.gy - p.y_roller_len / 2, L.gy + p.y_roller_len / 2, L.z_ycar, z1)
        bb_in = brace_bb("in", L.brace_in_top)
        bb_out = brace_bb("out", L.z_gt)
        brace_in = add(Part(f"Y Roller Brace Inner {tag}", "Y Roller Brace (inner)", "fabricated",
                            f"平板 t={p.brace_t:g} (鋼/アルミ)", bb_in, box(*bb_in), FLAT))
        brace_out = add(Part(f"Y Roller Brace Outer {tag}", "Y Roller Brace (outer)", "fabricated",
                             f"平板 t={p.brace_t:g} (鋼/アルミ)", bb_out, box(*bb_out), FLAT))
        for dy in (-100.0, -20.0, 20.0, 100.0):
            for q in (roller, brace_in, brace_out):
                q.add_hole("x", s, (0, L.gy + dy, z_rb), CLR_M6, True, "ローラー貫通ボルト M6")
        if upright is not None:
            uh = L.brace_in_top - L.z_rt
            zs = [L.z_rt + uh / 3, L.z_rt + 2 * uh / 3] if uh >= 60 else [L.z_rt + uh / 2]
            for zz in zs:
                for q in (upright, brace_in, brace_out):
                    q.add_hole("x", s, (0, L.gy, zz), CLR_M6, True, "支柱貫通ボルト M6")
        for k in range(2):
            zc = L.z_gb + Th / 2 + k * Th
            for dz in (-18, 18):
                brace_out.add_hole("x", s, (0, L.gy, zc + dz), ROD_M6, True, "ガントリー締結 M6全ネジ")

        # Yナットブラケット (山形鋼): 脚B を内側ブレースにボルト留め、脚A にナット
        xb0 = x_in - s * p.brace_t                  # 内側ブレースの内面
        xa1 = xb0 - s * ya
        bb = (min(xb0, xa1), max(xb0, xa1), L.gy - yb / 2, L.gy + yb / 2, L.ys_z - 30.0, L.z_rt)
        face_b = "-x" if s < 0 else "+x"
        ang = add(Part(f"Y Nut Bracket {tag}", "Y Nut Bracket (angle)", "fabricated",
                       f"山形鋼 L{ya:g}x{yb:g}x{yt:g}", bb, slabs(bb, ["-y", face_b], yt), STEEL, axis="z",
                       note="V4 の印刷ナットマウントの代替"))
        ysx = xc - s * L.ys_off
        ang.add_hole("y", -1, (ysx, 0, L.ys_z), SFU1610_BORE, True, "SFU1610 ナット胴")
        for a in (45, 135, 225, 315):
            r = SFU1610_PCD / 2
            ang.add_hole("y", -1, (ysx + r * math.cos(math.radians(a)), 0, L.ys_z + r * math.sin(math.radians(a))),
                         CLR_M5, True, "ナットフランジ M5 (現物合わせ)")
        for dy in (-20.0, 20.0):
            ang.add_hole("x", s, (0, L.gy + dy, z_rb), CLR_M6, True, "ブレース経由でローラーに共締め")
        # Yボールねじ・ナット・BK/BF/HM
        y_bk = L.yf0 + Tw / 2
        y_bf = L.yf1 - Tw / 2
        add(Part(f"Y Ballscrew {tag}", "SFU1610 Ballscrew (Y)", "purchased",
                 f"SFU1610 L≈{y_bf - y_bk + 60:g}", (0,) * 6,
                 cyl("y", (ysx, 0, L.ys_z), 16.0, y_bk - 30, y_bf + 30), SCREW, axis="y"))
        add(Part(f"Y Nut {tag}", "SFU1610 Nut", "purchased", "SFU1610", (0,) * 6,
                 cyl("y", (ysx, 0, L.ys_z), SFU1610_FLANGE, L.gy - yb / 2 - 10, L.gy - yb / 2)
                 .fuse(cyl("y", (ysx, 0, L.ys_z), 28.0, L.gy - yb / 2, L.gy - yb / 2 + 32)), SCREW))
        for (yy, kind) in ((y_bk, "HM12-57"), (y_bf, "BF12")):
            cross = [q for q in parts if q.bom == "X Frame Tubing" and abs((q.bbox[2] + q.bbox[3]) / 2 - yy) < 1][0]
            sp_bb = (ysx - 40, ysx + 40, yy - 22.5, yy + 22.5, Th, Th + p.spacer_t)
            sp = add(Part(f"Y {kind} Spacer {tag}", "Mount Spacer Plate", "fabricated",
                          f"平鋼 t={p.spacer_t:g}", sp_bb, box(*sp_bb), FLAT))
            for dx in (-23, 23):
                sp.add_hole("z", 1, (ysx + dx, yy, 0), TAP_M5, True, f"{kind} 取付 M5タップ")
            for dy in (-12, 12):
                sp.add_hole("z", 1, (ysx, yy + dy, 0), CLR_M5, True, "台座固定 M5 皿ボルト", cbore=10.5)
                cross.add_hole("z", 1, (ysx, yy + dy, 0), TAP_M5, False, f"Y {kind} 台座 M5タップ")
            add_mount(add, kind, "y", (ysx, yy, L.ys_z), Th + p.spacer_t, outward=-1)

    # ============================ ガントリー ============================
    gantry = []
    for k in range(2):
        z0 = L.z_gb + k * Th
        bb = (-L.gantry_len / 2, L.gantry_len / 2, L.gy - Tw / 2, L.gy + Tw / 2, z0, z0 + Th)
        g = add(Part(f"X Gantry Tube {'Lower' if k == 0 else 'Upper'}", "X Gantry Tubing", "fabricated",
                     tube_stock, bb, tube(bb, "x", t), STEEL, axis="x", wall=t,
                     note="2段重ね。内部に M6 全ネジ 2本を通し両端の外側ブレースで締結"))
        gantry.append(g)
        zc = z0 + Th / 2
        for xx in rail_positions(L.x_rail_len, p.r20_e, p.r20_pitch):
            g.add_hole("y", -1, (-L.x_rail_len / 2 + xx, 0, zc), TAP_M5, False, "Xレール M5タップ")
        add(Part(f"X Rail {k + 1}", "HGR20 Rail (X)", "purchased", f"HGR20 L={L.x_rail_len:g}",
                 (-L.x_rail_len / 2, L.x_rail_len / 2, L.y_gf - p.r20_h, L.y_gf, zc - p.r20_w / 2, zc + p.r20_w / 2),
                 box(-L.x_rail_len / 2, L.x_rail_len / 2, L.y_gf - p.r20_h, L.y_gf, zc - p.r20_w / 2, zc + p.r20_w / 2),
                 RAIL, axis="x"))
        for dz in (-18, 18):
            add(Part("Gantry Tie Rod", "M6 Threaded Rod (X gantry)", "purchased",
                     f"M6 全ネジ L={L.gantry_len + 2 * p.brace_t + 30:g}", (0,) * 6,
                     cyl("x", (0, L.gy, zc + dz), 6.0, -L.gantry_len / 2 - p.brace_t - 15,
                         L.gantry_len / 2 + p.brace_t + 15), SCREW, axis="x"))
        for dx in (-p.x_car_pitch / 2, p.x_car_pitch / 2):
            cx = L.xp + dx
            bb = (cx - p.c20_l / 2, cx + p.c20_l / 2, L.y_xpb, L.y_gf - 4.6, zc - p.c20_w / 2, zc + p.c20_w / 2)
            add(Part("X Carriage", "HGW20CC Carriage", "purchased", "HGW20CC", bb, box(*bb), CAR))

    # Xボールねじ (ガントリー上面)
    x_hm = L.gantry_len / 2 - 40.0
    for xx, kind in ((x_hm, "HM12-57"), (-x_hm, "BF12")):
        sp_bb = (xx - 22.5, xx + 22.5, L.gy - 40, L.gy + 40, L.z_gt, L.z_gt + p.spacer_t)
        sp = add(Part(f"X {kind} Spacer", "Mount Spacer Plate", "fabricated", f"平鋼 t={p.spacer_t:g}",
                      sp_bb, box(*sp_bb), FLAT))
        for dy in (-23, 23):
            sp.add_hole("z", 1, (xx, L.gy + dy, 0), TAP_M5, True, f"{kind} 取付 M5タップ")
        for dx in (-12, 12):
            sp.add_hole("z", 1, (xx + dx, L.gy, 0), CLR_M5, True, "台座固定 M5 皿ボルト", cbore=10.5)
            gantry[1].add_hole("z", 1, (xx + dx, L.gy, 0), TAP_M5, False, f"X {kind} 台座 M5タップ")
        add_mount(add, kind, "x", (xx, L.gy, L.xs_z), L.z_gt + p.spacer_t, outward=1)
    add(Part("X Ballscrew", "SFU1610 Ballscrew (X)", "purchased", f"SFU1610 L≈{2 * x_hm + 60:g}", (0,) * 6,
             cyl("x", (0, L.gy, L.xs_z), 16.0, -x_hm - 30, x_hm + 30), SCREW, axis="x"))

    # Xローラープレート (V4 の X Roller tubing/angle/shim をアルミ板 1 枚に置換)
    bb = (L.xp - L.xplate_w / 2, L.xp + L.xplate_w / 2, L.y_xpf, L.y_xpb, L.xplate_z0, L.xplate_z1)
    xplate = add(Part("X Roller Plate", "X Roller Plate", "fabricated", f"アルミ板 t={p.plate_t:g}",
                      bb, box(*bb), ALU, note="V4 の X Roller tubing + angle + shim の代替"))
    for k in range(2):
        zc = L.z_gb + Th / 2 + k * Th
        for dx in (-p.x_car_pitch / 2, p.x_car_pitch / 2):
            for bx in (-p.c20_c / 2, p.c20_c / 2):
                for bz in (-p.c20_b / 2, p.c20_b / 2):
                    xplate.add_hole("y", -1, (L.xp + dx + bx, 0, zc + bz), CLR_M6, True,
                                    "Xキャリッジ M6 (前面から座ぐりΦ11 深6.5)", cbore=11.0)
    for zr in (L.z_row1, L.z_row2):
        for sx in (-1, 1):
            for bx in (-p.c15_b / 2, p.c15_b / 2):
                for bz in (-p.c15_c / 2, p.c15_c / 2):
                    xplate.add_hole("y", -1, (L.xp + sx * p.z_car_x + bx, 0, zr + bz), CLR_M4, True, "Zキャリッジ M4")
            bb = (L.xp + sx * p.z_car_x - p.c15_w / 2, L.xp + sx * p.z_car_x + p.c15_w / 2,
                  L.y_xpf - (p.c15_h - 4.3), L.y_xpf, zr - p.c15_l / 2, zr + p.c15_l / 2)
            add(Part("Z Carriage", "HGH15CA Carriage", "purchased", "HGH15CA", bb, box(*bb), CAR))
    for dx in (-18, 18):
        for dz in (-12, 12):
            xplate.add_hole("y", -1, (L.xp + dx, 0, L.z_nut + dz), CLR_M5, True, "Zナットブロック M5 (現物合わせ)")

    # Xナットブラケット (不等辺山形鋼): 脚A を X プレート背面、脚B にナット
    xa, xb, xt = p.x_angle
    bb = (L.xp - xt / 2, L.xp - xt / 2 + xb, L.y_xpb, L.y_xpb + xa, L.xa_z0, L.xa_z0 + L.xa_h)
    xang = add(Part("X Nut Bracket", "X Nut Bracket (angle)", "fabricated", f"山形鋼 L{xa:g}x{xb:g}x{xt:g}",
                    bb, slabs(bb, ["-y", "-x"], xt), STEEL, axis="z", note="V4 の印刷ナットマウントの代替"))
    xang.add_hole("x", -1, (0, L.gy, L.xs_z), SFU1610_BORE, True, "SFU1610 ナット胴")
    for a in (45, 135, 225, 315):
        r = SFU1610_PCD / 2
        xang.add_hole("x", -1, (0, L.gy + r * math.cos(math.radians(a)), L.xs_z + r * math.sin(math.radians(a))),
                      CLR_M5, True, "ナットフランジ M5 (現物合わせ)")
    for dx in (15.0, 32.0):
        for q in (xang, xplate):
            q.add_hole("y", 1, (L.xp + dx, 0, L.xa_z0 + L.xa_h / 2), CLR_M6, True,
                       "Xナットブラケット M6")
    add(Part("X Nut", "SFU1610 Nut", "purchased", "SFU1610", (0,) * 6,
             cyl("x", (0, L.gy, L.xs_z), SFU1610_FLANGE, L.xp + xt / 2, L.xp + xt / 2 + 10)
             .fuse(cyl("x", (0, L.gy, L.xs_z), 28.0, L.xp - xt / 2 - 32, L.xp + xt / 2)), SCREW))

    # ============================ Z 軸 ============================
    ztop = L.zpb + L.zplate_h
    bb = (L.xp - L.zplate_w / 2, L.xp + L.zplate_w / 2, L.y_zpf, L.y_zpb, L.zpb, ztop)
    zplate = add(Part("Z Plate", "Z Plate (2Z)", "fabricated", f"アルミ板 t={p.plate_t:g}", bb, box(*bb), ALU,
                      note="V4 の 1Z Plate 相当。HGR15 ×2 をスペーサー経由で背面に固定"))
    z_rail_pos = rail_positions(L.zplate_h, p.r15_e, p.r15_pitch)
    for sx in (-1, 1):
        x_r = L.xp + sx * p.z_car_x
        sp_bb = (x_r - p.z_spacer_w / 2, x_r + p.z_spacer_w / 2, L.y_zpb, L.y_zpb + p.z_spacer_t, L.zpb, ztop)
        sp = add(Part("Z Rail Spacer", "Z Rail Spacer (flat bar)", "fabricated",
                      f"平鋼 {p.z_spacer_w:g}x{p.z_spacer_t:g}", sp_bb, box(*sp_bb), FLAT, axis="z",
                      note="ナットブロックの逃げ代を作る"))
        rb = (x_r - p.r15_w / 2, x_r + p.r15_w / 2, L.y_zpb + p.z_spacer_t, L.y_zpb + p.z_spacer_t + p.r15_h, L.zpb, ztop)
        add(Part("Z Rail", "HGR15 Rail (Z)", "purchased", f"HGR15 L={L.zplate_h:g}", rb, box(*rb), RAIL, axis="z"))
        for zz in z_rail_pos:
            for q in (zplate, sp):
                q.add_hole("y", -1, (x_r, 0, L.zpb + zz), CLR_M4, True, "Zレール M4 (前面から皿ボルト)")
    for dx in (-35, 0, 35):
        zplate.add_hole("y", -1, (L.xp + dx, 0, L.zpb + 45), CLR_M6, True, "スピンドルクランプ M6 (現物合わせ)")

    # Z 上部アングル + HM10-57 + モーター
    za, zb, zt = p.z_angle
    bb = (L.xp - 40, L.xp + 40, L.y_zpf - zt, L.y_zpf - zt + za, ztop + zt - zb, ztop + zt)
    zang = add(Part("Z Top Angle", "Z Top Angle", "fabricated", f"山形鋼 L{za:g}x{zb:g}x{zt:g}", bb,
                    slabs(bb, ["-y", "+z"], zt), STEEL, axis="x", note="HM10-57 を載せる。V4 印刷部品の代替"))
    for dx in (-25, 25):
        for q in (zang, zplate):
            q.add_hole("y", -1, (L.xp + dx, 0, ztop - 25), CLR_M6, True, "Z上部アングル M6")
    zang.add_hole("z", 1, (L.xp, L.zs_y, 0), 22.0, True, "Zねじ逃げ")
    for dx in (-23.57, 23.57):
        for dy in (-23.57, 23.57):
            zang.add_hole("z", 1, (L.xp + dx, L.zs_y + dy, 0), CLR_M5, True, "HM10-57 M5 (現物合わせ)")
    add_mount(add, "HM10-57", "z", (L.xp, L.zs_y, 0), ztop + zt, outward=1)
    zs_len = ceil5(L.zpb_max + L.zplate_h + zt + 20 - (L.z_nut - 30))
    add(Part("Z Ballscrew", "SFU1204 Ballscrew (Z)", "purchased", f"SFU1204 L≈{zs_len:g}", (0,) * 6,
             cyl("z", (L.xp, L.zs_y, 0), 12.0, ztop + zt + 20 - zs_len, ztop + zt + 20), SCREW, axis="z"))
    nb = (L.xp - 25, L.xp + 25, L.zs_y - (L.z_gap - 4) / 2, L.zs_y + (L.z_gap - 4) / 2, L.z_nut - 20, L.z_nut + 20)
    add(Part("Z Nut Block", "SFU1204 Nut + Block", "purchased", "SFU1204 + ナットブロック", nb, box(*nb), MOUNT))

    # スピンドル
    sp_y = L.gy + L.sp_y_off
    cb = (L.xp - 55, L.xp + 55, L.y_zpf - 95, L.y_zpf, L.zpb + 10, L.zpb + 80)
    clamp = box(*cb).cut(cyl("z", (L.xp, sp_y, 0), p.spindle_d, cb[4] - 1, cb[5] + 1))
    add(Part("Spindle Clamp", "80mm Spindle Clamp", "purchased", "80mm 3穴クランプ", cb, clamp, MOUNT))
    z_nose = L.zpb - p.spindle_below
    add(Part("Spindle", "Spindle 80mm", "purchased", f"Φ{p.spindle_d:g} スピンドル", (0,) * 6,
             cyl("z", (L.xp, sp_y, 0), p.spindle_d, z_nose, z_nose + p.spindle_len)
             .fuse(cyl("z", (L.xp, sp_y, 0), 6.0, z_nose - p.tool_stickout, z_nose)), SPINDLE))

    for q in parts:
        if q.bbox == (0,) * 6 or q.name.endswith("Tie Rod"):
            bb = q.shape.BoundingBox()
            q.bbox = (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)
        q.finalize()
    return parts, L


def add_mount(add, kind, axis, c, z_base, outward):
    """BK/BF/HM ねじサポートとモーターを簡易ブロックで配置 (購入品)。

    axis: ねじ方向, c: ねじ軸上の点, z_base: 取付面高さ, outward: モーターの向き (+1/-1)
    """
    x, y, z = c
    if axis == "z":   # HM10-57 を水平面に載せ、モーターを上へ
        bb = (x - 30, x + 30, y - 30, y + 30, z_base, z_base + 40)
        add(Part(kind, kind, "purchased", kind, bb, box(*bb), MOUNT))
        mb = (x - 28.5, x + 28.5, y - 28.5, y + 28.5, z_base + 40, z_base + 116)
        add(Part("NEMA23 Motor Z", "NEMA23 Motor", "purchased", "NEMA23 57x57x76", mb, box(*mb), MOTOR))
        return
    along = 45.0 if kind.startswith("HM") else 25.0
    h = (z - z_base) + (30.0 if kind.startswith("HM") else 18.0)
    if axis == "y":
        bb = (x - 30, x + 30, y - along / 2, y + along / 2, z_base, z_base + h)
    else:
        bb = (x - along / 2, x + along / 2, y - 30, y + 30, z_base, z_base + h)
    add(Part(kind, kind, "purchased", kind, bb, box(*bb), MOUNT))
    if kind.startswith("HM"):
        if axis == "y":
            y0 = y + outward * along / 2
            mb = (x - 28.5, x + 28.5, min(y0, y0 + outward * 76), max(y0, y0 + outward * 76), z - 28.5, z + 28.5)
        else:
            x0 = x + outward * along / 2
            mb = (min(x0, x0 + outward * 76), max(x0, x0 + outward * 76), y - 28.5, y + 28.5, z - 28.5, z + 28.5)
        add(Part(f"NEMA23 Motor {axis.upper()}", "NEMA23 Motor", "purchased", "NEMA23 57x57x76", mb, box(*mb), MOTOR))
