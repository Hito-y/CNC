"""設計パラメータ (単位: mm)

PrintNC V4 の Fusion ユーザーパラメータ (reference/printnc_v4_user_parameters.csv) に合わせた値。
[V4: 名前] は対応する V4 のパラメータ名。
ここを書き換えて build.py を実行すれば、寸法・切断リスト・穴位置がすべて再計算される。
"""
from dataclasses import dataclass, fields


@dataclass
class Params:
    # --- 加工範囲 (工具先端が届く範囲) [V4: XCuttingArea / YCuttingArea] ---
    cut_x: float = 300.0
    cut_y: float = 400.0
    cut_z: float = 150.0     # V4 にはない。ガントリー下の高さと Z ストロークをここから決める

    # --- フレーム角パイプ [V4: FrameLong / FrameShort / FrameThick] ---
    tube_h: float = 75.0
    tube_w: float = 50.0
    tube_t: float = 3.0

    # --- ガントリー 75x75x4 [V4: XGantryHeight / Width / Thick] ---
    gantry_h: float = 75.0
    gantry_w: float = 75.0
    gantry_t: float = 4.0
    gantry_offset: float = 25.0   # [V4: XGantryOffset] Yローラー中心からガントリーを後ろへずらす量

    # --- Yローラー: 幅 75 x 高さ [V4: YRollerHeight] (0 = cut_z から自動で 50/75/100/125/150 を選ぶ) ---
    y_roller_h: float = 0.0
    roller_t: float = 3.0         # [V4: YRollerThick / XTopRollerThick]

    # --- Xローラー [V4: XTopRoller / XBottomRoller / XRollerShimThick] ---
    x_top_roller_h: float = 50.0
    x_bottom_angle_h: float = 50.0    # 下側ローラー (アルミ山形) の立ち上がり
    x_bottom_angle_t: float = 6.0
    x_shim_t: float = 8.0
    roller_plate_t: float = 12.0      # [V4: RollerPlateThick] 12 = 切削アルミ (15 は3Dプリント用)

    # --- ガントリーブレース 75x50x6 [V4: GantryBrace*] ---
    brace_h: float = 75.0
    brace_w: float = 50.0
    brace_t: float = 6.0

    # --- Xフレーム (寝かせて足にする) [V4: XFrameFrontOffset / XFrameBackOffset] ---
    n_x_frame: int = 3
    x_frame_front_off: float = 50.0
    x_frame_back_off: float = 50.0

    # --- Xレール端と Yローラーの隙間 [V4: XRailtoYRollerLeftGap / RightGap] ---
    x_gap_left: float = 5.0
    x_gap_right: float = 20.0

    # --- キャリッジ数 (1本のレールあたり, 1 or 2) [V4: YCarriageCount / XCarriageCount] ---
    y_car_count: int = 2
    x_car_count: int = 2
    car_pitch: float = 80.0           # 2個並べたときの中心間 (HGW20CC 長さ 77.5 + 隙間)

    # --- リニアレール HGR20 / HGW20CC ---
    r20_w: float = 20.0
    r20_h: float = 17.5
    r20_pitch: float = 60.0
    r20_e: float = 20.0
    c20_w: float = 63.0
    c20_l: float = 77.5
    c20_h: float = 30.0
    c20_b: float = 53.0      # [V4: YCarriageB / XCarriageB]
    c20_c: float = 40.0      # [V4: YCarriageC / XCarriageC]

    # --- Z軸: HGR15 x2 / HGH15CA x2/本 [V4: ZCarriageCount=2] ---
    r15_w: float = 15.0
    r15_h: float = 15.0
    r15_pitch: float = 60.0
    r15_e: float = 20.0
    c15_w: float = 34.0
    c15_l: float = 61.4
    c15_h: float = 28.0
    c15_b: float = 26.0
    c15_c: float = 26.0
    z_car_pitch: float = 75.0
    z_car_x: float = 50.0
    z_spacer_w: float = 20.0
    z_spacer_t: float = 10.0
    plate_t: float = 12.0            # Zプレート

    # --- 平鋼・山形鋼 ---
    spacer_t: float = 10.0
    wasteboard_t: float = 25.0

    # --- 主軸 [V4: SpindleClampHoleHorizontal / Vertical] ---
    spindle_d: float = 80.0
    spindle_len: float = 200.0
    spindle_below: float = 40.0
    tool_stickout: float = 25.0
    clamp_hole_h: float = 125.0
    clamp_hole_v: float = 64.0
    z_margin_low: float = 5.0
    z_margin_high: float = 10.0
    work_clear: float = 10.0         # ワーク最大高さとガントリー下の隙間

    # --- 表示用の可動部位置 (0.0〜1.0) ---
    pos_x: float = 0.5
    pos_y: float = 0.5
    pos_z: float = 0.5

    @classmethod
    def field_names(cls):
        return [f.name for f in fields(cls)]
