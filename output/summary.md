# 簡易 PrintNC フレーム 設計サマリー

`python build.py` で自動生成。寸法は mm。

## 主要寸法

| 項目 | 値 |
|---|---|
| 加工範囲 X × Y × Z | 300 × 400 × 150 |
| フレーム外形 X × Y (Yねじ・モーター除く) | 615 × 740 |
| 全幅 (Yねじ含む, 目安) | 800 |
| ガントリー上面 / トップローラー上面の高さ | 355 / 435 |
| 左右Yフレーム中心間 | 565 |
| ガントリー (75x75x4) 長さ | 640 |
| X / Y レール長 | 465 / 600 |
| Yローラー高さ (自動選択) | 125 |
| 捨て板上面からガントリー下 (最下点) まで | 169 |
| Zストローク | 165 |
| 工具先端の到達範囲 (捨て板上面基準) | -5 〜 160 |
| 主軸の Yローラー中心からの前方オフセット | 132.5 |
| 捨て板 X × Y | 511 × 420 |

## 自動チェック

- 穴の縁距離・穴間の肉厚: すべて 3mm 以上

赤茶色の部品 (Xねじ/Yねじまわり) は V4 パラメータに情報がない仮置き。

## 加工品 (切断リスト)

| 部品 | 素材 | 切断長 | 外形 | 数量 | 備考 |
|---|---|---|---|---|---|
| X Frame Tubing | 角パイプ 75x50x3 | 615 | 615 x 75 x 50 | 3 | 75面を下に寝かせて足にする。Yフレームを上に載せて M8 で縦に締結 |
| Y Frame Tubing | 角パイプ 75x50x3 | 740 | 740 x 75 x 50 | 2 |  |
| Y Roller Tubing | 角パイプ 125x75x3 | 150 | 150 x 125 x 75 | 2 | 幅 75 を横、高さ 125。先にキャリッジを留めてからガントリーを載せる |
| X Gantry Tubing | 角パイプ 75x75x4 | 640 | 640 x 75 x 75 | 1 | Yローラーに直接載せ、ローラー中心から 25 後ろへずらす |
| Gantry Brace | 角パイプ 75x50x6 | 75 | 75 x 75 x 50 | 2 | ガントリー前面と Yローラー上面をつなぐ [V4: GantryBrace] |
| X Top Roller (X Roller Tubing) | 角パイプ 75x50x3 | 150 | 150 x 75 x 50 | 1 | 上Xキャリッジに載せる |
| X Roller Shim | 平鋼/アルミ t=8 |  | 150 x 50 x 8 | 1 |  |
| X Bottom Roller (X Roller Angle) | アルミ山形 L100x50x6 | 150 | 150 x 100 x 50 | 1 | 下Xキャリッジの下に付け、立ち上がりをローラープレートに留める |
| Roller Plate | アルミ板 t=12 |  | 210 x 150 x 12 | 1 | V4 の RollerPlate (切削版 12mm)。3Dプリント版の代替 |
| X Nut Bracket (angle) | 山形鋼 L75x70x10 (仮置き) | 147.5 | 147.5 x 75 x 70 | 1 | トップローラー背面に 3mm スペーサーを挟んで共締め。Xねじ位置は V4 未確認 |
| X Nut Spacer | 平鋼 t=3 (仮置き) |  | 75 x 50 x 3 | 1 |  |
| Mount Spacer Plate | 平鋼 t=18 (仮置き) |  | 70 x 45 x 18 | 2 |  |
| Y Nut Bracket (angle) | 山形鋼 L65x80x6 (仮置き) | 180 | 180 x 80 x 65 | 2 | Yローラー外側面に共締め。Yねじ位置は V4 未確認 |
| Y Mount Angle | 山形鋼 L100x65x10 (仮置き) | 60 | 100 x 60 x 55 | 4 | Yフレーム外側面に M8 で固定し、上に BK/BF/HM を載せる |
| Z Plate (2Z) | アルミ板 t=12 |  | 325 x 145 x 12 | 1 | HGR15 x2 をスペーサー経由で背面に固定 (レール可動) |
| Z Rail Spacer (flat bar) | 平鋼 20x10 | 325 | 325 x 20 x 10 | 2 | ナットブロックの逃げ代を作る |
| Z Top Angle | 山形鋼 L75x75x8 | 80 | 80 x 75 x 75 | 1 | HM10-57 を載せる |

## 購入品

| 部品 | 型番/仕様 | 数量 |
|---|---|---|
| HGR20 Rail (Y) | HGR20 L=600 | 2 |
| HGW20CC Carriage | HGW20CC | 8 |
| HGR20 Rail (X) | HGR20 L=465 | 2 |
| SFU1610 Nut | SFU1610 | 3 |
| HM12-57 | HM12-57 | 3 |
| NEMA23 Motor | NEMA23 57x57x76 | 4 |
| BF12 | BF12 | 3 |
| SFU1610 Ballscrew (X) | SFU1610 L≈620 | 1 |
| SFU1610 Ballscrew (Y) | SFU1610 L≈730 | 2 |
| Wasteboard | 合板/MDF t=25 | 1 |
| HGH15CA Carriage | HGH15CA | 4 |
| HGR15 Rail (Z) | HGR15 L=325 | 2 |
| HM10-57 | HM10-57 | 1 |
| SFU1204 Ballscrew (Z) | SFU1204 L≈305 | 1 |
| SFU1204 Nut + Block | SFU1204 + ナットブロック | 1 |
| 80mm Spindle Clamp | 80mm クランプ | 1 |
| Spindle 80mm | Φ80 スピンドル | 1 |

角パイプ合計長さ: 約 4565 mm (切り代・端材別)

## 穴あけ図 (drawings/)

1:1 と書かれたものは 100% で印刷してポンチ打ちの型紙として使える。100mm スケールバーで倍率を確認すること。

- [X_Frame_Tube_1_zp_wall.svg](drawings/X_Frame_Tube_1_zp_wall.svg)
- [X_Frame_Tube_1_zm_wall.svg](drawings/X_Frame_Tube_1_zm_wall.svg)
- [X_Frame_Tube_2_zp_wall.svg](drawings/X_Frame_Tube_2_zp_wall.svg)
- [X_Frame_Tube_2_zm_wall.svg](drawings/X_Frame_Tube_2_zm_wall.svg)
- [X_Frame_Tube_3_zp_wall.svg](drawings/X_Frame_Tube_3_zp_wall.svg)
- [X_Frame_Tube_3_zm_wall.svg](drawings/X_Frame_Tube_3_zm_wall.svg)
- [Y_Frame_Tube_L_zp_wall.svg](drawings/Y_Frame_Tube_L_zp_wall.svg)
- [Y_Frame_Tube_L_xm.svg](drawings/Y_Frame_Tube_L_xm.svg)
- [Y_Frame_Tube_L_zm_wall.svg](drawings/Y_Frame_Tube_L_zm_wall.svg)
- [Y_Roller_L_zp_wall.svg](drawings/Y_Roller_L_zp_wall.svg)
- [Y_Roller_L_xm.svg](drawings/Y_Roller_L_xm.svg)
- [Y_Roller_L_zm_wall.svg](drawings/Y_Roller_L_zm_wall.svg)
- [Y_Frame_Tube_R_xp.svg](drawings/Y_Frame_Tube_R_xp.svg)
- [Y_Frame_Tube_R_zp_wall.svg](drawings/Y_Frame_Tube_R_zp_wall.svg)
- [Y_Frame_Tube_R_zm_wall.svg](drawings/Y_Frame_Tube_R_zm_wall.svg)
- [Y_Roller_R_xp.svg](drawings/Y_Roller_R_xp.svg)
- [Y_Roller_R_zp_wall.svg](drawings/Y_Roller_R_zp_wall.svg)
- [Y_Roller_R_zm_wall.svg](drawings/Y_Roller_R_zm_wall.svg)
- [X_Gantry_Tube_yp_wall.svg](drawings/X_Gantry_Tube_yp_wall.svg)
- [X_Gantry_Tube_zp_wall.svg](drawings/X_Gantry_Tube_zp_wall.svg)
- [X_Gantry_Tube_zp.svg](drawings/X_Gantry_Tube_zp.svg)
- [X_Gantry_Tube_ym_wall.svg](drawings/X_Gantry_Tube_ym_wall.svg)
- [X_Gantry_Tube_zm_wall.svg](drawings/X_Gantry_Tube_zm_wall.svg)
- [Gantry_Brace_L_zp.svg](drawings/Gantry_Brace_L_zp.svg)
- [Gantry_Brace_L_ym.svg](drawings/Gantry_Brace_L_ym.svg)
- [Gantry_Brace_R_zp.svg](drawings/Gantry_Brace_R_zp.svg)
- [Gantry_Brace_R_ym.svg](drawings/Gantry_Brace_R_ym.svg)
- [X_Top_Roller_zp_wall.svg](drawings/X_Top_Roller_zp_wall.svg)
- [X_Top_Roller_ym.svg](drawings/X_Top_Roller_ym.svg)
- [X_Top_Roller_zm_wall.svg](drawings/X_Top_Roller_zm_wall.svg)
- [X_Roller_Shim_ym.svg](drawings/X_Roller_Shim_ym.svg)
- [X_Bottom_Roller_ym.svg](drawings/X_Bottom_Roller_ym.svg)
- [X_Bottom_Roller_zm.svg](drawings/X_Bottom_Roller_zm.svg)
- [Roller_Plate_ym.svg](drawings/Roller_Plate_ym.svg)
- [X_Nut_Bracket_xm.svg](drawings/X_Nut_Bracket_xm.svg)
- [X_Nut_Bracket_ym.svg](drawings/X_Nut_Bracket_ym.svg)
- [X_Nut_Spacer_ym.svg](drawings/X_Nut_Spacer_ym.svg)
- [X_HM12-57_Spacer_yp.svg](drawings/X_HM12-57_Spacer_yp.svg)
- [X_BF12_Spacer_yp.svg](drawings/X_BF12_Spacer_yp.svg)
- [Y_Nut_Bracket_L_xm.svg](drawings/Y_Nut_Bracket_L_xm.svg)
- [Y_Nut_Bracket_L_ym.svg](drawings/Y_Nut_Bracket_L_ym.svg)
- [Y_HM12-57_Angle_L_zp.svg](drawings/Y_HM12-57_Angle_L_zp.svg)
- [Y_HM12-57_Angle_L_xm.svg](drawings/Y_HM12-57_Angle_L_xm.svg)
- [Y_BF12_Angle_L_zp.svg](drawings/Y_BF12_Angle_L_zp.svg)
- [Y_BF12_Angle_L_xm.svg](drawings/Y_BF12_Angle_L_xm.svg)
- [Y_Nut_Bracket_R_xp.svg](drawings/Y_Nut_Bracket_R_xp.svg)
- [Y_Nut_Bracket_R_ym.svg](drawings/Y_Nut_Bracket_R_ym.svg)
- [Y_HM12-57_Angle_R_xp.svg](drawings/Y_HM12-57_Angle_R_xp.svg)
- [Y_HM12-57_Angle_R_zp.svg](drawings/Y_HM12-57_Angle_R_zp.svg)
- [Y_BF12_Angle_R_xp.svg](drawings/Y_BF12_Angle_R_xp.svg)
- [Y_BF12_Angle_R_zp.svg](drawings/Y_BF12_Angle_R_zp.svg)
- [Z_Plate_ym.svg](drawings/Z_Plate_ym.svg)
- [Z_Rail_Spacer_ym.svg](drawings/Z_Rail_Spacer_ym.svg)
- [Z_Top_Angle_zp.svg](drawings/Z_Top_Angle_zp.svg)
- [Z_Top_Angle_ym.svg](drawings/Z_Top_Angle_ym.svg)
