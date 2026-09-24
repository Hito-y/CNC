# 簡易 PrintNC フレーム 設計サマリー

`python build.py` で自動生成。寸法は mm。

## 主要寸法

| 項目 | 値 |
|---|---|
| 加工範囲 X × Y × Z | 400 × 300 × 150 |
| フレーム外形 (X × Y) | 725 × 772 |
| ガントリー上面高さ | 430 |
| 左右Yチューブ中心間 | 675 |
| ガントリー長 | 750 |
| X/Y レール長 | 640 / 620 |
| ガントリー下面の高さ (捨て板上面から) | 180 |
| 支柱の高さ | 125 |
| Zストローク | 165 |
| 工具先端の到達範囲 (捨て板上面基準) | -5 〜 160 |
| 主軸のガントリー中心からの前方オフセット | 167 |
| 捨て板 (X × Y) | 426 × 320 |

## 自動チェック

- 穴の縁距離・穴間の肉厚: すべて 3mm 以上

## 加工品 (切断リスト)

| 部品 | 素材 | 切断長 | 外形 | 数量 | 備考 |
|---|---|---|---|---|---|
| Y Frame Tubing | 角パイプ 75x50x3 | 772 | 772 x 75 x 50 | 2 |  |
| X Frame Tubing | 角パイプ 75x50x3 | 625 | 625 x 75 x 50 | 3 | Yチューブ間に突合せ、内部に M6 全ネジ 2本を通して締結 |
| Y Roller Tubing | 角パイプ 75x50x3 | 300 | 300 x 75 x 50 | 2 |  |
| Y Roller Tubing (upright) | 角パイプ 75x50x3 | 125 | 125 x 75 x 50 | 2 | Yローラー上に立て、両側ブレースで挟んで締結 |
| Y Roller Brace (inner) | 平板 t=6 (鋼/アルミ) |  | 300 x 170 x 6 | 2 |  |
| Y Roller Brace (outer) | 平板 t=6 (鋼/アルミ) |  | 325 x 300 x 6 | 2 |  |
| Y Nut Bracket (angle) | 山形鋼 L75x75x6 | 75 | 75 x 75 x 75 | 2 | V4 の印刷ナットマウントの代替 |
| Mount Spacer Plate | 平鋼 t=10 |  | 80 x 45 x 10 | 6 |  |
| X Gantry Tubing | 角パイプ 75x50x3 | 750 | 750 x 75 x 50 | 2 | 2段重ね。内部に M6 全ネジ 2本を通し両端の外側ブレースで締結 |
| X Roller Plate | アルミ板 t=12 |  | 225 x 220 x 12 | 1 | V4 の X Roller tubing + angle + shim の代替 |
| X Nut Bracket (angle) | 山形鋼 L100x75x10 | 60 | 100 x 75 x 60 | 1 | V4 の印刷ナットマウントの代替 |
| Z Plate (2Z) | アルミ板 t=12 |  | 350 x 165 x 12 | 1 | V4 の 1Z Plate 相当。HGR15 ×2 をスペーサー経由で背面に固定 |
| Z Rail Spacer (flat bar) | 平鋼 20x10 | 350 | 350 x 20 x 10 | 2 | ナットブロックの逃げ代を作る |
| Z Top Angle | 山形鋼 L75x75x8 | 80 | 80 x 75 x 75 | 1 | HM10-57 を載せる。V4 印刷部品の代替 |

## 購入品

| 部品 | 型番/仕様 | 数量 |
|---|---|---|
| HGR20 Rail (Y) | HGR20 L=620 | 2 |
| HGW20CC Carriage | HGW20CC | 8 |
| M6 Threaded Rod (X base) | M6 全ネジ L=755 | 6 |
| Wasteboard | 合板/MDF t=25 | 1 |
| SFU1610 Ballscrew (Y) | SFU1610 L≈782 | 2 |
| SFU1610 Nut | SFU1610 | 3 |
| HM12-57 | HM12-57 | 3 |
| NEMA23 Motor | NEMA23 57x57x76 | 4 |
| BF12 | BF12 | 3 |
| HGR20 Rail (X) | HGR20 L=640 | 2 |
| M6 Threaded Rod (X gantry) | M6 全ネジ L=792 | 4 |
| SFU1610 Ballscrew (X) | SFU1610 L≈730 | 1 |
| HGH15CA Carriage | HGH15CA | 4 |
| HGR15 Rail (Z) | HGR15 L=350 | 2 |
| HM10-57 | HM10-57 | 1 |
| SFU1204 Ballscrew (Z) | SFU1204 L≈320 | 1 |
| SFU1204 Nut + Block | SFU1204 + ナットブロック | 1 |
| 80mm Spindle Clamp | 80mm 3穴クランプ | 1 |
| Spindle 80mm | Φ80 スピンドル | 1 |

角パイプ合計長さ: 約 5769 mm (切り代・端材別)

## 穴あけ図 (drawings/)

1:1 と書かれたものは 100% で印刷してポンチ打ちの型紙として使える。100mm スケールバーで倍率を確認すること。

- [Y_Frame_Tube_L_xp.svg](drawings/Y_Frame_Tube_L_xp.svg)
- [Y_Frame_Tube_L_zp_wall.svg](drawings/Y_Frame_Tube_L_zp_wall.svg)
- [Y_Frame_Tube_R_xp.svg](drawings/Y_Frame_Tube_R_xp.svg)
- [Y_Frame_Tube_R_zp_wall.svg](drawings/Y_Frame_Tube_R_zp_wall.svg)
- [X_Frame_Tube_1_zp_wall.svg](drawings/X_Frame_Tube_1_zp_wall.svg)
- [X_Frame_Tube_3_zp_wall.svg](drawings/X_Frame_Tube_3_zp_wall.svg)
- [Y_Roller_L_zp_wall.svg](drawings/Y_Roller_L_zp_wall.svg)
- [Y_Roller_L_xm.svg](drawings/Y_Roller_L_xm.svg)
- [Y_Roller_L_zm_wall.svg](drawings/Y_Roller_L_zm_wall.svg)
- [Upright_L_xm.svg](drawings/Upright_L_xm.svg)
- [Y_Roller_Brace_Inner_L_xm.svg](drawings/Y_Roller_Brace_Inner_L_xm.svg)
- [Y_Roller_Brace_Outer_L_xm.svg](drawings/Y_Roller_Brace_Outer_L_xm.svg)
- [Y_Nut_Bracket_L_xm.svg](drawings/Y_Nut_Bracket_L_xm.svg)
- [Y_Nut_Bracket_L_ym.svg](drawings/Y_Nut_Bracket_L_ym.svg)
- [Y_HM12-57_Spacer_L_zp.svg](drawings/Y_HM12-57_Spacer_L_zp.svg)
- [Y_BF12_Spacer_L_zp.svg](drawings/Y_BF12_Spacer_L_zp.svg)
- [Y_Roller_R_xp.svg](drawings/Y_Roller_R_xp.svg)
- [Y_Roller_R_zp_wall.svg](drawings/Y_Roller_R_zp_wall.svg)
- [Y_Roller_R_zm_wall.svg](drawings/Y_Roller_R_zm_wall.svg)
- [Upright_R_xp.svg](drawings/Upright_R_xp.svg)
- [Y_Roller_Brace_Inner_R_xp.svg](drawings/Y_Roller_Brace_Inner_R_xp.svg)
- [Y_Roller_Brace_Outer_R_xp.svg](drawings/Y_Roller_Brace_Outer_R_xp.svg)
- [Y_Nut_Bracket_R_xp.svg](drawings/Y_Nut_Bracket_R_xp.svg)
- [Y_Nut_Bracket_R_ym.svg](drawings/Y_Nut_Bracket_R_ym.svg)
- [Y_HM12-57_Spacer_R_zp.svg](drawings/Y_HM12-57_Spacer_R_zp.svg)
- [Y_BF12_Spacer_R_zp.svg](drawings/Y_BF12_Spacer_R_zp.svg)
- [X_Gantry_Tube_Lower_ym_wall.svg](drawings/X_Gantry_Tube_Lower_ym_wall.svg)
- [X_Gantry_Tube_Upper_zp_wall.svg](drawings/X_Gantry_Tube_Upper_zp_wall.svg)
- [X_Gantry_Tube_Upper_ym_wall.svg](drawings/X_Gantry_Tube_Upper_ym_wall.svg)
- [X_HM12-57_Spacer_zp.svg](drawings/X_HM12-57_Spacer_zp.svg)
- [X_BF12_Spacer_zp.svg](drawings/X_BF12_Spacer_zp.svg)
- [X_Roller_Plate_ym.svg](drawings/X_Roller_Plate_ym.svg)
- [X_Nut_Bracket_yp.svg](drawings/X_Nut_Bracket_yp.svg)
- [X_Nut_Bracket_xm.svg](drawings/X_Nut_Bracket_xm.svg)
- [Z_Plate_ym.svg](drawings/Z_Plate_ym.svg)
- [Z_Rail_Spacer_ym.svg](drawings/Z_Rail_Spacer_ym.svg)
- [Z_Top_Angle_zp.svg](drawings/Z_Top_Angle_zp.svg)
- [Z_Top_Angle_ym.svg](drawings/Z_Top_Angle_ym.svg)
