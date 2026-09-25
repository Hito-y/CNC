"""PrintNC V4 ベース簡易フレームの形状生成 (V4 ユーザーパラメータ準拠版)。

V4 パラメータから読み取った構成:
  * Xフレーム (75x50 を寝かせる) が足になり、その上に Yフレーム (75x50 を立てる) を載せる
  * Yローラー (幅 75) の上にガントリー (75x75x4) を直接載せ、25mm 後ろへずらす。
    前側の空いた部分にガントリーブレース (75x50x6) を置いて留める
  * Xレールはガントリーの上面と下面の 2 本。上側は角パイプのトップローラー、
    下側はアルミ山形のボトムローラーで受け、両者の前面にローラープレートを付ける
  * Zは HGR15 x2 / HGH15CA x2 (2Z)

3Dプリント不要化:
  * ローラープレートは 12mm アルミ (V4 でも切削版の指定)
  * ナットマウントは山形鋼、ドリルガイドは穴位置表と 1:1 型紙で代替

V4 パラメータに現れず推定で置いた部分 (仮置き):
  * Yボールねじ: Yフレームの外側 (Yローラー外側面からブラケットで駆動)
  * Xボールねじ: ガントリーの後ろ (トップローラー背面からブラケットで駆動)
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
TENTATIVE = (0.80, 0.35, 0.25)   # 仮置き部品の色

SFU1610_BORE = 29.0
SFU1610_FLANGE = 48.0
SFU1610_PCD = 38.0
TAP_M5 = 4.2
TAP_M6 = 5.0
CLR_M4 = 4.5
CLR_M5 = 5.5
CLR_M6 = 6.6
CLR_M8 = 9.0
CSK_M6 = 12.0
RIVNUT_M8 = 11.0
ROLLER_HEIGHTS = (50.0, 75.0, 100.0, 125.0, 150.0)


def ceil5(v):
    return math.ceil(v / 5.0 - 1e-9) * 5.0


def compute_layout(p):
    if p.x_car_count != 2 or p.y_car_count != 2:
        raise ValueError("キャリッジ数は V4 既定の 2 (1本のレールに2個) のみ対応")
    L = SimpleNamespace(warnings=[])
    Th, Tw = p.tube_h, p.tube_w
    L.RW = max(Th, Tw)                                    # Yローラー幅 [V4: YRollerWidth]
    L.yr_len = 50.0 + 50.0 * p.y_car_count                # [V4: YRollerLength]
    L.xr_len = 50.0 + 50.0 * p.x_car_count                # [V4: XRollerLength]
    L.y_group = (p.y_car_count - 1) * p.car_pitch + p.c20_l
    L.x_group = (p.x_car_count - 1) * p.car_pitch + p.c20_l
    L.nut_r = SFU1610_FLANGE / 2

    # ---------------- 高さ ----------------
    L.z_yf0 = Tw                                          # Xフレーム上面 = Yフレーム下面
    L.z_yf1 = Tw + Th                                     # Yレール取付面
    L.z_ycar = L.z_yf1 + p.c20_h                          # Yローラー下面
    L.wb_top = Tw + p.wasteboard_t
    L.drop = p.c20_h + p.x_bottom_angle_t                 # ガントリー下面から下に出る量 (下レール+キャリッジ+山形)
    need = L.wb_top + p.cut_z + p.work_clear + L.drop - L.z_ycar
    if p.y_roller_h > 0:
        L.RH = p.y_roller_h
    else:
        L.RH = next((h for h in ROLLER_HEIGHTS if h >= need), ROLLER_HEIGHTS[-1])
    if L.RH < need:
        L.warnings.append(f"Yローラー高さ {L.RH:g} ではワーク高さ {p.cut_z:g} が通らない (必要 {need:.0f})")
    L.z_gb = L.z_ycar + L.RH                              # ガントリー下面
    L.z_gt = L.z_gb + p.gantry_h
    L.z_tr0 = L.z_gt + p.c20_h                            # トップローラー下面
    L.z_tr1 = L.z_tr0 + p.x_top_roller_h
    L.zb0 = L.z_gb - L.drop                               # ボトムローラー(山形) 下面 = ガントリー周りの最下点
    L.under = L.zb0 - L.wb_top                            # 捨て板上面からガントリー下までの高さ
    L.ys_z = L.z_yf1 + 5.0                                # Yねじ軸高さ
    L.xs_z = L.z_gb + p.gantry_h / 2                      # Xねじ軸高さ

    # ---------------- Z ----------------
    L.tip_min = L.wb_top - p.z_margin_low
    L.tip_max = L.wb_top + p.cut_z + p.z_margin_high
    L.z_travel = L.tip_max - L.tip_min
    L.zpb_min = L.tip_min + p.spindle_below + p.tool_stickout
    L.zpb_max = L.zpb_min + L.z_travel
    L.z_row1 = max(L.zpb_max + 10.0 + p.c15_l / 2, L.zb0 + p.c15_l / 2 + 5.0)
    L.z_row2 = L.z_row1 + p.z_car_pitch
    L.z_nut = (L.z_row1 + L.z_row2) / 2
    L.rp_top = L.zb0 + ceil5(max(L.z_tr1, L.z_row2 + p.c15_l / 2 + 5.0) - L.zb0)
    L.zplate_h = ceil5(L.rp_top + 5.0 - L.zpb_min)
    L.zplate_w = ceil5(max(2 * (p.z_car_x + p.c15_w / 2) + 10.0, p.clamp_hole_h + 2 * 9.0))

    # ---------------- X ----------------
    L.x_rail_len = ceil5(p.cut_x + L.x_group + 5.0)
    L.span = L.x_rail_len + L.RW + p.x_gap_left + p.x_gap_right   # 左右Yフレーム中心間
    L.gantry_len = L.span + L.RW                           # [V4: XGantryLength]
    L.x_frame_len = L.span + Tw
    L.x_rail0 = -L.span / 2 + L.RW / 2 + p.x_gap_left
    L.x_rail1 = L.x_rail0 + L.x_rail_len
    L.x_mid = (L.x_rail0 + L.x_rail1) / 2
    L.xp = L.x_mid - p.cut_x / 2 + p.pos_x * p.cut_x

    # ---------------- Y ----------------
    L.y_rail_len = ceil5(p.cut_y + L.y_group + 2 * p.r20_e)
    L.yr = -p.cut_y / 2 + p.pos_y * p.cut_y                # Yローラー中心
    L.g0 = L.yr - p.gantry_w / 2 + p.gantry_offset         # ガントリー前面
    L.g1 = L.g0 + p.gantry_w
    L.gy = (L.g0 + L.g1) / 2
    L.y_rpb = L.g0 - p.x_shim_t                            # ローラープレート背面
    L.y_xpf = L.y_rpb - p.roller_plate_t                   # ローラープレート前面
    L.z_gap = p.c15_h + p.z_spacer_t
    L.y_zpb = L.y_xpf - L.z_gap
    L.y_zpf = L.y_zpb - p.plate_t
    L.zs_y = L.y_xpf - L.z_gap / 2
    L.sp_y = L.y_zpf - 10.0 - p.spindle_d / 2
    L.sp_off = L.sp_y - L.yr
    L.tool_y = (-p.cut_y / 2 + L.sp_off, p.cut_y / 2 + L.sp_off)
    L.wb_y = (L.tool_y[0] - 10.0, L.tool_y[1] + 10.0)
    L.yf0 = min(-L.y_rail_len / 2 - 70.0, L.wb_y[0] - 10.0)
    L.yf1 = max(L.y_rail_len / 2 + 70.0, L.wb_y[1] + 10.0)
    L.y_frame_len = L.yf1 - L.yf0
    L.wb_half_x = L.span / 2 - Tw / 2 - 2.0
    L.xs_y = L.g1 + 3.0 + 10.0 + 30.0                      # Xねじ軸 (仮置き)
    L.ys_off = L.RW / 2 + 6.0 + 30.0                       # Yねじ: Yフレーム中心から外側 (仮置き)
    L.width = L.span + 2 * (L.ys_off + L.nut_r + 20.0)

    L.summary = [
        ("加工範囲 X × Y × Z", f"{p.cut_x:g} × {p.cut_y:g} × {p.cut_z:g}"),
        ("フレーム外形 X × Y (Yねじ・モーター除く)", f"{L.x_frame_len:g} × {L.y_frame_len:g}"),
        ("全幅 (Yねじ含む, 目安)", f"{L.width:.0f}"),
        ("ガントリー上面 / トップローラー上面の高さ", f"{L.z_gt:g} / {L.z_tr1:g}"),
        ("左右Yフレーム中心間", f"{L.span:g}"),
        ("ガントリー (75x75x4) 長さ", f"{L.gantry_len:g}"),
        ("X / Y レール長", f"{L.x_rail_len:g} / {L.y_rail_len:g}"),
        ("Yローラー高さ (自動選択)", f"{L.RH:g}"),
        ("捨て板上面からガントリー下 (最下点) まで", f"{L.under:g}"),
        ("Zストローク", f"{L.z_travel:g}"),
        ("工具先端の到達範囲 (捨て板上面基準)", f"{L.tip_min - L.wb_top:g} 〜 {L.tip_max - L.wb_top:g}"),
        ("主軸の Yローラー中心からの前方オフセット", f"{-L.sp_off:g}"),
        ("捨て板 X × Y", f"{2 * L.wb_half_x:g} × {L.wb_y[1] - L.wb_y[0]:g}"),
    ]
    return L


def build(p):
    L = compute_layout(p)
    parts = []
    Th, Tw, t = p.tube_h, p.tube_w, p.tube_t
    frame_stock = f"角パイプ {Th:g}x{Tw:g}x{t:g}"

    def add(part):
        parts.append(part)
        return part

    def rail_positions(length, e, pitch):
        n = int((length - 2 * e) // pitch) + 1
        return [e + k * pitch for k in range(n)]

    def car_offsets(n):
        return [(k - (n - 1) / 2) * p.car_pitch for k in range(n)]

    # ================= Xフレーム (足) =================
    xf_y = [L.yf0 + p.x_frame_front_off + Th / 2, L.yf1 - p.x_frame_back_off - Th / 2]
    n_mid = max(0, p.n_x_frame - 2)
    for k in range(n_mid):
        xf_y.insert(-1, xf_y[0] + (k + 1) * (xf_y[-1] - xf_y[0]) / (n_mid + 1))
    xframes = []
    for i, cy in enumerate(xf_y):
        bb = (-L.x_frame_len / 2, L.x_frame_len / 2, cy - Th / 2, cy + Th / 2, 0, Tw)
        xframes.append(add(Part(f"X Frame Tube {i + 1}", "X Frame Tubing", "fabricated", frame_stock, bb,
                                tube(bb, "x", t), STEEL, axis="x", wall=t,
                                note="75面を下に寝かせて足にする。Yフレームを上に載せて M8 で縦に締結")))

    # ================= Yフレーム / Yレール / Yローラー =================
    rollers = {}
    for s, tag in ((-1, "L"), (1, "R")):
        xc = s * L.span / 2
        bb = (xc - Tw / 2, xc + Tw / 2, L.yf0, L.yf1, L.z_yf0, L.z_yf1)
        yt = add(Part(f"Y Frame Tube {tag}", "Y Frame Tubing", "fabricated", frame_stock, bb,
                      tube(bb, "y", t), STEEL, axis="y", wall=t))
        for yy in rail_positions(L.y_rail_len, p.r20_e, p.r20_pitch):
            yt.add_hole("z", 1, (xc, -L.y_rail_len / 2 + yy, 0), TAP_M5, False, "Yレール M5タップ")
        for xf, cy in zip(xframes, xf_y):
            for dy in (-20, 20):
                pt = (xc, cy + dy, 0)
                yt.add_hole("z", -1, pt, RIVNUT_M8, False, "Y-Xフレーム M8 リベットナット")
                xf.add_hole("z", 1, pt, CLR_M8, False, "Y-Xフレーム M8 (下から締める)")
                xf.add_hole("z", -1, pt, 16.0, False, "工具挿入穴 (M8用)")
        rb = (xc - p.r20_w / 2, xc + p.r20_w / 2, -L.y_rail_len / 2, L.y_rail_len / 2, L.z_yf1, L.z_yf1 + p.r20_h)
        add(Part(f"Y Rail {tag}", "HGR20 Rail (Y)", "purchased", f"HGR20 L={L.y_rail_len:g}", rb, box(*rb), RAIL, axis="y"))

        # Yローラー
        bb = (xc - L.RW / 2, xc + L.RW / 2, L.yr - L.yr_len / 2, L.yr + L.yr_len / 2, L.z_ycar, L.z_gb)
        rstock = f"角パイプ {max(L.RH, L.RW):g}x{min(L.RH, L.RW):g}x{p.roller_t:g}"
        roller = add(Part(f"Y Roller {tag}", "Y Roller Tubing", "fabricated", rstock, bb,
                          tube(bb, "y", p.roller_t), STEEL, axis="y", wall=p.roller_t,
                          note=f"幅 {L.RW:g} を横、高さ {L.RH:g}。先にキャリッジを留めてからガントリーを載せる"))
        rollers[s] = roller
        for dy in car_offsets(p.y_car_count):
            cy = L.yr + dy
            cb = (xc - p.c20_w / 2, xc + p.c20_w / 2, cy - p.c20_l / 2, cy + p.c20_l / 2, L.z_yf1 + 4.6, L.z_ycar)
            add(Part(f"Y Carriage {tag}", "HGW20CC Carriage", "purchased", "HGW20CC", cb, box(*cb), CAR))
            for bx in (-p.c20_b / 2, p.c20_b / 2):
                for by in (-p.c20_c / 2, p.c20_c / 2):
                    pt = (xc + bx, cy + by, 0)
                    roller.add_hole("z", -1, pt, CLR_M6, False, "Yキャリッジ M6")
                    roller.add_hole("z", 1, pt, 12.0, False, "工具挿入穴 (M6頭用)")

    # ================= ガントリー =================
    gb = (-L.gantry_len / 2, L.gantry_len / 2, L.g0, L.g1, L.z_gb, L.z_gt)
    gantry = add(Part("X Gantry Tube", "X Gantry Tubing", "fabricated",
                      f"角パイプ {p.gantry_h:g}x{p.gantry_w:g}x{p.gantry_t:g}", gb,
                      tube(gb, "x", p.gantry_t), STEEL, axis="x", wall=p.gantry_t,
                      note=f"Yローラーに直接載せ、ローラー中心から {p.gantry_offset:g} 後ろへずらす"))
    for xx in rail_positions(L.x_rail_len, p.r20_e, p.r20_pitch):
        gantry.add_hole("z", 1, (L.x_rail0 + xx, L.gy, 0), TAP_M5, False, "上Xレール M5タップ")
        gantry.add_hole("z", -1, (L.x_rail0 + xx, L.gy, 0), TAP_M5, False, "下Xレール M5タップ")
    for k, (z0, z1) in enumerate(((L.z_gt, L.z_gt + p.r20_h), (L.z_gb - p.r20_h, L.z_gb))):
        rb = (L.x_rail0, L.x_rail1, L.gy - p.r20_w / 2, L.gy + p.r20_w / 2, z0, z1)
        add(Part(f"X Rail {'Top' if k == 0 else 'Bottom'}", "HGR20 Rail (X)", "purchased",
                 f"HGR20 L={L.x_rail_len:g}", rb, box(*rb), RAIL, axis="x"))

    for s, tag in ((-1, "L"), (1, "R")):
        xc = s * L.span / 2
        roller = rollers[s]
        for dy in (-20, 20):
            gantry.add_hole("z", 1, (xc, L.gy + dy, 0), CLR_M8, True, "ガントリー-Yローラー M8")
            roller.add_hole("z", 1, (xc, L.gy + dy, 0), CLR_M8, False, "ガントリー-Yローラー M8 (ナットはローラー端から)")
        # ガントリーブレース: ガントリー前の空いたローラー上面に置く
        bb = (xc - L.RW / 2, xc + L.RW / 2, L.g0 - p.brace_w, L.g0, L.z_gb, L.z_gb + p.brace_h)
        br = add(Part(f"Gantry Brace {tag}", "Gantry Brace", "fabricated",
                      f"角パイプ {p.brace_h:g}x{p.brace_w:g}x{p.brace_t:g}", bb, tube(bb, "x", p.brace_t), STEEL,
                      axis="x", wall=p.brace_t, note="ガントリー前面と Yローラー上面をつなぐ [V4: GantryBrace]"))
        for dx in (-20, 20):
            br.add_hole("y", -1, (xc + dx, 0, L.z_gb + p.brace_h / 2), CLR_M8, True, "ブレース-ガントリー M8")
            gantry.add_hole("y", -1, (xc + dx, 0, L.z_gb + p.brace_h / 2), RIVNUT_M8, False, "ブレース M8 リベットナット")
            br.add_hole("z", 1, (xc + dx, L.g0 - p.brace_w / 2, 0), CLR_M8, True, "ブレース-Yローラー M8")
            roller.add_hole("z", 1, (xc + dx, L.g0 - p.brace_w / 2, 0), CLR_M8, False, "ブレース-Yローラー M8")

    # ================= X キャリッジ / ローラー =================
    xr0, xr1 = L.xp - L.xr_len / 2, L.xp + L.xr_len / 2
    for dx in car_offsets(p.x_car_count):
        cx = L.xp + dx
        for z0, z1 in ((L.z_gt + 4.6, L.z_tr0), (L.z_gb - p.c20_h, L.z_gb - 4.6)):
            cb = (cx - p.c20_l / 2, cx + p.c20_l / 2, L.gy - p.c20_w / 2, L.gy + p.c20_w / 2, z0, z1)
            add(Part("X Carriage", "HGW20CC Carriage", "purchased", "HGW20CC", cb, box(*cb), CAR))

    bb = (xr0, xr1, L.g0, L.g0 + max(Th, p.gantry_w), L.z_tr0, L.z_tr1)
    top = add(Part("X Top Roller", "X Top Roller (X Roller Tubing)", "fabricated",
                   f"角パイプ {max(Th, p.gantry_w):g}x{p.x_top_roller_h:g}x{p.roller_t:g}", bb,
                   tube(bb, "x", p.roller_t), STEEL, axis="x", wall=p.roller_t, note="上Xキャリッジに載せる"))
    bb = (xr0, xr1, L.y_rpb, L.g0, L.z_tr0, L.z_tr1)
    shim = add(Part("X Roller Shim", "X Roller Shim", "fabricated", f"平鋼/アルミ t={p.x_shim_t:g}", bb, box(*bb), FLAT))
    aw = max(75.0, 25.0 * math.ceil((max(Th, p.gantry_w) + p.x_shim_t - 6.0) / 25.0))
    at = p.x_bottom_angle_t
    bb = (xr0, xr1, L.y_rpb, L.y_rpb + aw, L.zb0, L.zb0 + p.x_bottom_angle_h)
    bot = add(Part("X Bottom Roller", "X Bottom Roller (X Roller Angle)", "fabricated",
                   f"アルミ山形 L{aw:g}x{p.x_bottom_angle_h:g}x{at:g}", bb, slabs(bb, ["-y", "-z"], at), ALU,
                   axis="x", note="下Xキャリッジの下に付け、立ち上がりをローラープレートに留める"))
    bb = (xr0, xr1, L.y_xpf, L.y_rpb, L.zb0, L.rp_top)
    plate = add(Part("Roller Plate", "Roller Plate", "fabricated", f"アルミ板 t={p.roller_plate_t:g}", bb, box(*bb),
                     ALU, note="V4 の RollerPlate (切削版 12mm)。3Dプリント版の代替"))
    for dx in car_offsets(p.x_car_count):
        for bx in (-p.c20_c / 2, p.c20_c / 2):
            for by in (-p.c20_b / 2, p.c20_b / 2):
                pt = (L.xp + dx + bx, L.gy + by, 0)
                top.add_hole("z", -1, pt, CLR_M6, False, "上Xキャリッジ M6")
                top.add_hole("z", 1, pt, 12.0, False, "工具挿入穴 (M6頭用)")
                bot.add_hole("z", -1, pt, CLR_M6, True, "下Xキャリッジ M6 (下から)")
    z_top_bolt = L.z_tr0 + p.x_top_roller_h / 2
    z_bot_bolt = L.zb0 + at + (p.x_bottom_angle_h - at) / 2
    for dx in (-50.0, -15.0, 15.0, 50.0):
        for q in (plate, shim, top):
            q.add_hole("y", -1, (L.xp + dx, 0, z_top_bolt), CLR_M6, True, "プレート-トップローラー M6 皿",
                       cbore=CSK_M6 if q is plate else 0.0)
        plate.add_hole("y", -1, (L.xp + dx, 0, z_bot_bolt), CLR_M6, True, "プレート-ボトムローラー M6 皿", cbore=CSK_M6)
        bot.add_hole("y", -1, (L.xp + dx, 0, z_bot_bolt), TAP_M6, True, "プレート-ボトムローラー M6タップ")

    # ================= Xボールねじ (仮置き: ガントリー後ろ) =================
    xa_b = L.xs_y + 30.0 - (L.g1 + 3.0)
    bb = (L.xp - 5.0, L.xp + 70.0, L.g1 + 3.0, L.xs_y + 30.0, L.xs_z - 30.0, L.z_tr1)
    xang = add(Part("X Nut Bracket", "X Nut Bracket (angle)", "fabricated", f"山形鋼 L75x{xa_b:g}x10 (仮置き)", bb,
                    slabs(bb, ["-y", "-x"], 10.0), TENTATIVE, axis="z",
                    note="トップローラー背面に 3mm スペーサーを挟んで共締め。Xねじ位置は V4 未確認"))
    bb = (L.xp - 5.0, L.xp + 70.0, L.g1, L.g1 + 3.0, L.z_tr0, L.z_tr1)
    xsp = add(Part("X Nut Spacer", "X Nut Spacer", "fabricated", "平鋼 t=3 (仮置き)", bb, box(*bb), TENTATIVE))
    for dx in (15.0, 50.0):
        for q in (xang, xsp):
            q.add_hole("y", -1, (L.xp + dx, 0, z_top_bolt), CLR_M6, True, "プレート-トップローラー M6 皿")
    xang.add_hole("x", -1, (0, L.xs_y, L.xs_z), SFU1610_BORE, True, "SFU1610 ナット胴")
    for a in (45, 135, 225, 315):
        r = SFU1610_PCD / 2
        xang.add_hole("x", -1, (0, L.xs_y + r * math.cos(math.radians(a)), L.xs_z + r * math.sin(math.radians(a))),
                      CLR_M5, True, "ナットフランジ M5 (現物合わせ)")
    add(Part("X Nut", "SFU1610 Nut", "purchased", "SFU1610", (0,) * 6,
             cyl("x", (0, L.xs_y, L.xs_z), SFU1610_FLANGE, L.xp + 5, L.xp + 15)
             .fuse(cyl("x", (0, L.xs_y, L.xs_z), 28.0, L.xp - 37, L.xp + 5)), SCREW))
    sp_t = L.xs_y - 25.0 - L.g1
    x_m = L.gantry_len / 2 - 40.0
    for xx, kind in ((x_m, "HM12-57"), (-x_m, "BF12")):
        bb = (xx - 22.5, xx + 22.5, L.g1, L.g1 + sp_t, L.xs_z - 35, L.xs_z + 35)
        sp = add(Part(f"X {kind} Spacer", "Mount Spacer Plate", "fabricated", f"平鋼 t={sp_t:g} (仮置き)", bb, box(*bb),
                      TENTATIVE))
        for dz in (-23, 23):
            sp.add_hole("y", 1, (xx, 0, L.xs_z + dz), TAP_M5, True, f"{kind} 取付 M5タップ")
        for dx in (-12, 12):
            sp.add_hole("y", 1, (xx + dx, 0, L.xs_z), CLR_M5, True, "台座固定 M5 皿ボルト", cbore=10.5)
            gantry.add_hole("y", 1, (xx + dx, 0, L.xs_z), TAP_M5, False, f"X {kind} 台座 M5タップ")
        along = 45.0 if kind.startswith("HM") else 25.0
        mb = (xx - along / 2, xx + along / 2, L.g1 + sp_t, L.xs_y + (30.0 if kind.startswith("HM") else 18.0),
              L.xs_z - 30, L.xs_z + 30)
        add(Part(kind, kind, "purchased", kind, mb, box(*mb), MOUNT))
        if kind.startswith("HM"):
            mb = (xx + along / 2, xx + along / 2 + 76, L.xs_y - 28.5, L.xs_y + 28.5, L.xs_z - 28.5, L.xs_z + 28.5)
            add(Part("NEMA23 Motor X", "NEMA23 Motor", "purchased", "NEMA23 57x57x76", mb, box(*mb), MOTOR))
    add(Part("X Ballscrew", "SFU1610 Ballscrew (X)", "purchased", f"SFU1610 L≈{2 * x_m + 60:g}", (0,) * 6,
             cyl("x", (0, L.xs_y, L.xs_z), 16.0, -x_m - 30, x_m + 30), SCREW, axis="x"))

    # ================= Yボールねじ (仮置き: Yフレーム外側) =================
    for s, tag in ((-1, "L"), (1, "R")):
        xc = s * L.span / 2
        roller = rollers[s]
        x_out = xc + s * L.RW / 2
        ysx = xc + s * L.ys_off
        xa = x_out + s * 65.0
        bb = (min(x_out, xa), max(x_out, xa), L.yr - 40.0, L.yr + 40.0, L.ys_z - 30.0, L.z_gb)
        face_b = "-x" if s > 0 else "+x"
        ang = add(Part(f"Y Nut Bracket {tag}", "Y Nut Bracket (angle)", "fabricated", "山形鋼 L65x80x6 (仮置き)", bb,
                       slabs(bb, ["-y", face_b], 6.0), TENTATIVE, axis="z",
                       note="Yローラー外側面に共締め。Yねじ位置は V4 未確認"))
        for dy in (-25.0, 25.0):
            for q in (roller, ang):
                q.add_hole("x", s, (0, L.yr + dy, L.z_ycar + L.RH / 2), CLR_M6, True, "Yナットブラケット M6 貫通")
        ang.add_hole("y", -1, (ysx, 0, L.ys_z), SFU1610_BORE, True, "SFU1610 ナット胴")
        for a in (45, 135, 225, 315):
            r = SFU1610_PCD / 2
            ang.add_hole("y", -1, (ysx + r * math.cos(math.radians(a)), 0, L.ys_z + r * math.sin(math.radians(a))),
                         CLR_M5, True, "ナットフランジ M5 (現物合わせ)")
        y_front = L.yr - 40.0
        add(Part(f"Y Nut {tag}", "SFU1610 Nut", "purchased", "SFU1610", (0,) * 6,
                 cyl("y", (ysx, 0, L.ys_z), SFU1610_FLANGE, y_front - 10, y_front)
                 .fuse(cyl("y", (ysx, 0, L.ys_z), 28.0, y_front, y_front + 38)), SCREW))
        # 端のマウント用アングル
        y_ends = (L.yf0 + 35.0, L.yf1 - 35.0)
        for ye, kind in zip(y_ends, ("HM12-57", "BF12")):
            xa2 = xc + s * (Tw / 2 + 100.0)
            bb = (min(xc + s * Tw / 2, xa2), max(xc + s * Tw / 2, xa2), ye - 30, ye + 30, L.z_yf0, L.ys_z - 25.0)
            face_v = "-x" if s > 0 else "+x"
            ma = add(Part(f"Y {kind} Angle {tag}", "Y Mount Angle", "fabricated", "山形鋼 L100x65x10 (仮置き)", bb,
                          slabs(bb, [face_v, "+z"], 10.0), TENTATIVE, axis="y",
                          note="Yフレーム外側面に M8 で固定し、上に BK/BF/HM を載せる"))
            yt = [q for q in parts if q.name == f"Y Frame Tube {tag}"][0]
            for dy in (-15, 15):
                for q in (ma, yt):
                    q.add_hole("x", s, (0, ye + dy, L.z_yf0 + 25.0), CLR_M8, True, "Yマウント M8 貫通")
            for dx in (-23, 23):
                ma.add_hole("z", 1, (ysx + dx, ye, 0), TAP_M5, True, f"{kind} 取付 M5タップ")
            along = 45.0 if kind.startswith("HM") else 25.0
            top_z = L.ys_z + (30.0 if kind.startswith("HM") else 18.0)
            yc_m = ye - 30.0 + along / 2 if kind.startswith("HM") else ye   # HM はモーターがアングルの外に出るよう前端に寄せる
            mb = (ysx - 30, ysx + 30, yc_m - along / 2, yc_m + along / 2, L.ys_z - 25.0, top_z)
            add(Part(kind, kind, "purchased", kind, mb, box(*mb), MOUNT))
            if kind.startswith("HM"):
                y0 = yc_m - along / 2
                mb = (ysx - 28.5, ysx + 28.5, y0 - 76, y0, L.ys_z - 28.5, L.ys_z + 28.5)
                add(Part(f"NEMA23 Motor Y{tag}", "NEMA23 Motor", "purchased", "NEMA23 57x57x76", mb, box(*mb), MOTOR))
        add(Part(f"Y Ballscrew {tag}", "SFU1610 Ballscrew (Y)", "purchased",
                 f"SFU1610 L≈{y_ends[1] - y_ends[0] + 60:g}", (0,) * 6,
                 cyl("y", (ysx, 0, L.ys_z), 16.0, y_ends[0] - 30, y_ends[1] + 30), SCREW, axis="y"))

    # ================= 捨て板 =================
    bb = (-L.wb_half_x, L.wb_half_x, L.wb_y[0], L.wb_y[1], L.z_yf0, L.wb_top)
    add(Part("Wasteboard", "Wasteboard", "purchased", f"合板/MDF t={p.wasteboard_t:g}", bb, box(*bb), WOOD))

    # ================= Z 軸 =================
    for zr in (L.z_row1, L.z_row2):
        for sx in (-1, 1):
            for bx in (-p.c15_b / 2, p.c15_b / 2):
                for bz in (-p.c15_c / 2, p.c15_c / 2):
                    plate.add_hole("y", -1, (L.xp + sx * p.z_car_x + bx, 0, zr + bz), CLR_M4, True, "Zキャリッジ M4")
            cb = (L.xp + sx * p.z_car_x - p.c15_w / 2, L.xp + sx * p.z_car_x + p.c15_w / 2,
                  L.y_xpf - (p.c15_h - 4.3), L.y_xpf, zr - p.c15_l / 2, zr + p.c15_l / 2)
            add(Part("Z Carriage", "HGH15CA Carriage", "purchased", "HGH15CA", cb, box(*cb), CAR))
    for dx in (-18, 18):
        for dz in (-12, 12):
            plate.add_hole("y", -1, (L.xp + dx, 0, L.z_nut + dz), CLR_M5, True, "Zナットブロック M5 (現物合わせ)")

    ztop = L.zpb_min + p.pos_z * L.z_travel + L.zplate_h
    zpb = ztop - L.zplate_h
    bb = (L.xp - L.zplate_w / 2, L.xp + L.zplate_w / 2, L.y_zpf, L.y_zpb, zpb, ztop)
    zplate = add(Part("Z Plate", "Z Plate (2Z)", "fabricated", f"アルミ板 t={p.plate_t:g}", bb, box(*bb), ALU,
                      note="HGR15 x2 をスペーサー経由で背面に固定 (レール可動)"))
    for sx in (-1, 1):
        x_r = L.xp + sx * p.z_car_x
        sb = (x_r - p.z_spacer_w / 2, x_r + p.z_spacer_w / 2, L.y_zpb, L.y_zpb + p.z_spacer_t, zpb, ztop)
        sp = add(Part("Z Rail Spacer", "Z Rail Spacer (flat bar)", "fabricated", f"平鋼 {p.z_spacer_w:g}x{p.z_spacer_t:g}",
                      sb, box(*sb), FLAT, axis="z", note="ナットブロックの逃げ代を作る"))
        rb = (x_r - p.r15_w / 2, x_r + p.r15_w / 2, L.y_zpb + p.z_spacer_t, L.y_zpb + p.z_spacer_t + p.r15_h, zpb, ztop)
        add(Part("Z Rail", "HGR15 Rail (Z)", "purchased", f"HGR15 L={L.zplate_h:g}", rb, box(*rb), RAIL, axis="z"))
        for zz in rail_positions(L.zplate_h, p.r15_e, p.r15_pitch):
            for q in (zplate, sp):
                q.add_hole("y", -1, (x_r, 0, zpb + zz), CLR_M4, True, "Zレール M4 (前面から皿ボルト)")
    for sx in (-1, 1):
        for dz in (20.0, 20.0 + p.clamp_hole_v):
            zplate.add_hole("y", -1, (L.xp + sx * p.clamp_hole_h / 2, 0, zpb + dz), CLR_M6, True,
                            "スピンドルクランプ M6 [V4: SpindleClampHole]")

    zt = 8.0
    bb = (L.xp - 40, L.xp + 40, L.y_zpf - zt, L.y_zpf - zt + 75.0, ztop + zt - 75.0, ztop + zt)
    zang = add(Part("Z Top Angle", "Z Top Angle", "fabricated", f"山形鋼 L75x75x{zt:g}", bb,
                    slabs(bb, ["-y", "+z"], zt), STEEL, axis="x", note="HM10-57 を載せる"))
    for dx in (-25, 25):
        for q in (zang, zplate):
            q.add_hole("y", -1, (L.xp + dx, 0, ztop - 25), CLR_M6, True, "Z上部アングル M6")
    zang.add_hole("z", 1, (L.xp, L.zs_y, 0), 22.0, True, "Zねじ逃げ")
    for dx in (-23.57, 23.57):
        for dy in (-23.57, 23.57):
            zang.add_hole("z", 1, (L.xp + dx, L.zs_y + dy, 0), CLR_M5, True, "HM10-57 M5 (現物合わせ)")
    mb = (L.xp - 30, L.xp + 30, L.zs_y - 30, L.zs_y + 30, ztop + zt, ztop + zt + 40)
    add(Part("HM10-57", "HM10-57", "purchased", "HM10-57", mb, box(*mb), MOUNT))
    mb = (L.xp - 28.5, L.xp + 28.5, L.zs_y - 28.5, L.zs_y + 28.5, ztop + zt + 40, ztop + zt + 116)
    add(Part("NEMA23 Motor Z", "NEMA23 Motor", "purchased", "NEMA23 57x57x76", mb, box(*mb), MOTOR))
    zs_len = ceil5(L.zpb_max + L.zplate_h + zt + 20 - (L.z_nut - 30))
    add(Part("Z Ballscrew", "SFU1204 Ballscrew (Z)", "purchased", f"SFU1204 L≈{zs_len:g}", (0,) * 6,
             cyl("z", (L.xp, L.zs_y, 0), 12.0, ztop + zt + 20 - zs_len, ztop + zt + 20), SCREW, axis="z"))
    nb = (L.xp - 25, L.xp + 25, L.zs_y - (L.z_gap - 4) / 2, L.zs_y + (L.z_gap - 4) / 2, L.z_nut - 20, L.z_nut + 20)
    add(Part("Z Nut Block", "SFU1204 Nut + Block", "purchased", "SFU1204 + ナットブロック", nb, box(*nb), MOUNT))

    cw = p.clamp_hole_h + 20.0
    cb = (L.xp - cw / 2, L.xp + cw / 2, L.y_zpf - 95, L.y_zpf, zpb + 5, zpb + 35 + p.clamp_hole_v)
    clamp = box(*cb).cut(cyl("z", (L.xp, L.sp_y, 0), p.spindle_d, cb[4] - 1, cb[5] + 1))
    add(Part("Spindle Clamp", "80mm Spindle Clamp", "purchased", "80mm クランプ", cb, clamp, MOUNT))
    z_nose = zpb - p.spindle_below
    add(Part("Spindle", "Spindle 80mm", "purchased", f"Φ{p.spindle_d:g} スピンドル", (0,) * 6,
             cyl("z", (L.xp, L.sp_y, 0), p.spindle_d, z_nose, z_nose + p.spindle_len)
             .fuse(cyl("z", (L.xp, L.sp_y, 0), 6.0, z_nose - p.tool_stickout, z_nose)), SPINDLE))

    for q in parts:
        if q.bbox == (0,) * 6:
            bb = q.shape.BoundingBox()
            q.bbox = (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)
        q.finalize()
    return parts, L
