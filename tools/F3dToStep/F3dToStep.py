"""Fusion スクリプト: .f3d を STEP に変換する (ユーザーパラメータ一覧も CSV で書き出す)

使い方 (Fusion の中で実行する。通常の Python では動かない):
  1. Fusion → ユーティリティ → アドイン → 「スクリプトとアドイン」→ スクリプトの「+」
     → このフォルダ (F3dToStep) を選ぶ
  2. F3dToStep を選んで「実行」
  3. .f3d を選ぶ (複数可)。同じフォルダに <名前>.step と <名前>_params.csv ができる
     ファイル選択をキャンセルすると、いま開いているデザインを書き出す

PARAM_OVERRIDES にパラメータを書くと、書き出す前にその値へ変更する
(例: PrintNC の加工範囲 XCuttingArea / YCuttingArea)。元の .f3d は変更しない。
"""
import csv
import os
import traceback

import adsk.core
import adsk.fusion

# 書き出す前に変更するユーザーパラメータ {名前: 式}。空なら変更しない。
PARAM_OVERRIDES = {
    # "XCuttingArea": "300 mm",
    # "YCuttingArea": "400 mm",
}


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        dlg = ui.createFileDialog()
        dlg.title = "STEP に変換する .f3d を選択 (キャンセルで現在のデザインを書き出し)"
        dlg.filter = "Fusion Archive (*.f3d)"
        dlg.isMultiSelectEnabled = True
        if dlg.showOpen() == adsk.core.DialogResults.DialogOK:
            results = [convert_file(app, path) for path in dlg.filenames]
        else:
            results = [export_active(app, ui)]
        results = [r for r in results if r]
        if results:
            ui.messageBox("書き出し完了:\n\n" + "\n\n".join(results))
    except Exception:
        ui.messageBox("エラー:\n{}".format(traceback.format_exc()))


def convert_file(app, f3d_path):
    """ローカルの .f3d を新しいドキュメントとして開き、STEP を書き出して閉じる (保存しない)。"""
    im = app.importManager
    doc = im.importToNewDocument(im.createFusionArchiveImportOptions(f3d_path))
    try:
        design = _design(doc)
        base = os.path.splitext(f3d_path)[0]
        return export_design(design, base)
    finally:
        doc.close(False)


def export_active(app, ui):
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("開いているデザインがありません。")
        return None
    dlg = ui.createFolderDialog()
    dlg.title = "STEP の保存先フォルダ"
    if dlg.showDialog() != adsk.core.DialogResults.DialogOK:
        return None
    base = os.path.join(dlg.folder, _safe_name(app.activeDocument.name))
    return export_design(design, base)


def export_design(design, base):
    changed = apply_overrides(design)
    write_params_csv(design, base + "_params.csv")
    step_path = base + ".step"
    em = design.exportManager
    if not em.execute(em.createSTEPExportOptions(step_path, design.rootComponent)):
        raise RuntimeError("STEP の書き出しに失敗: " + step_path)
    msg = step_path
    if changed:
        msg += "\n  変更したパラメータ: " + ", ".join(changed)
    return msg


def apply_overrides(design):
    changed = []
    for name, expr in PARAM_OVERRIDES.items():
        p = design.userParameters.itemByName(name)
        if p is None:
            continue
        p.expression = expr
        changed.append("{}={}".format(name, expr))
    if changed:
        design.computeAll()
    return changed


def write_params_csv(design, path):
    um = design.unitsManager
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["name", "expression", "value", "unit", "comment"])
        for p in design.userParameters:
            value = um.formatInternalValue(p.value, p.unit, False) if p.unit else str(p.value)
            w.writerow([p.name, p.expression, value, p.unit, p.comment])


def _design(doc):
    return adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))


def _safe_name(name):
    return "".join(c if c not in '\\/:*?"<>|' else "_" for c in name)
