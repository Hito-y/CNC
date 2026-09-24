"""設計パラメータ (単位: mm)

PrintNC V4 の構成 (75x50x3 角パイプ / HGR20 レール / 1610 ボールねじ) をベースに、
3Dプリント部品を使わない簡易版フレームを組むための入力値。
ここを書き換えて build.py を実行すれば、寸法・切断リスト・穴位置がすべて再計算される。
"""
from dataclasses import dataclass, fields


@dataclass
class Params:
    # --- 加工範囲 (工具先端が届く範囲) ---
    cut_x: float = 300.0
    cut_y: float = 400.0
    cut_z: float = 150.0

    # --- 角パイプ (V4 標準: 75x50x3) ---
    tube_h: float = 75.0   # 長辺
    tube_w: float = 50.0   # 短辺
    tube_t: float = 3.0    # 肉厚

    # --- 平板・アングル ---
    plate_t: float = 12.0      # Xローラープレート / Zプレート (アルミ推奨)
    brace_t: float = 6.0       # Yローラーブレース (Y Roller Brace)
    spacer_t: float = 10.0     # BK/BF/HM 台座スペーサー
    y_angle: tuple = (75.0, 75.0, 6.0)    # Yナットブラケット 山形鋼 (脚A, 脚B, 厚)
    x_angle: tuple = (100.0, 75.0, 10.0)  # Xナットブラケット 不等辺山形鋼
    z_angle: tuple = (75.0, 75.0, 8.0)    # Z上部アングル (HM10-57 取付)
    z_spacer_w: float = 20.0   # Zレール下スペーサー (平鋼) 幅
    z_spacer_t: float = 10.0   # 同 厚み (ナットブロックの逃げを作る)
    wasteboard_t: float = 25.0

    # --- リニアレール HGR20 / HGW20CC (X, Y) ---
    r20_w: float = 20.0
    r20_h: float = 17.5
    r20_pitch: float = 60.0
    r20_e: float = 20.0
    c20_w: float = 63.0
    c20_l: float = 77.5
    c20_h: float = 30.0      # レール底面〜キャリッジ上面
    c20_b: float = 53.0      # 取付穴 横ピッチ (M6)
    c20_c: float = 40.0      # 取付穴 縦ピッチ

    # --- リニアレール HGR15 / HGH15CA (Z, 2Z構成) ---
    r15_w: float = 15.0
    r15_h: float = 15.0
    r15_pitch: float = 60.0
    r15_e: float = 20.0
    c15_w: float = 34.0
    c15_l: float = 61.4
    c15_h: float = 28.0
    c15_b: float = 26.0      # 取付穴ピッチ (M4)
    c15_c: float = 26.0

    # --- キャリッジ配置 ---
    y_car_pitch: float = 200.0   # 片側2個のYキャリッジ中心間
    x_car_pitch: float = 120.0   # 1本のXレール上の2個の中心間
    z_car_pitch: float = 100.0   # Zキャリッジ上下段の中心間
    z_car_x: float = 60.0        # Zレール左右の中心からの距離 (Xキャリッジのボルトを避ける位置)
    y_roller_len: float = 300.0

    # --- 構成 ---
    n_x_frame: int = 3           # X方向フレーム (横桁) 本数 (両端を含む)
    gantry_clear: float = 30.0   # ガントリー下面とワーク最大高さの隙間

    # --- 主軸 (80mm スピンドル想定) ---
    spindle_d: float = 80.0
    spindle_len: float = 200.0
    spindle_below: float = 40.0  # Zプレート下端からスピンドル先端まで
    tool_stickout: float = 25.0
    z_margin_low: float = 5.0    # 捨て板上面より下まで届かせる量
    z_margin_high: float = 10.0  # cut_z より上に逃がす量

    # --- 表示用の可動部位置 (0.0〜1.0, 0.5=中央) ---
    pos_x: float = 0.5
    pos_y: float = 0.5
    pos_z: float = 0.5

    @classmethod
    def field_names(cls):
        return [f.name for f in fields(cls)]
