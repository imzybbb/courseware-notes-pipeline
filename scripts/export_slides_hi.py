# -*- coding: utf-8 -*-
"""课件 .ppt → 高清整页 PNG（2560x1920），供配图裁切用。

用法:
  python export_slides_hi.py "<课件路径glob>" "<工作目录>" <tag>
例:
  python export_slides_hi.py "<课件目录>/第二章-04*.ppt" "./work/g204" p204
产出: <工作目录>/slides_hi_<tag>/sNN.png（2560x1920）

要点:
- 精读拼版仍用 export_slides.py 的 1280x960 版（提速）；裁配图从本脚本的高清版裁（1280 裁出来放大会糊）。
- 需 pywin32（win32com）；路径参数传原生盘符（C:/...）。
- 开工先 tasklist 看 POWERPNT.EXE——用户可能正开着课件；本脚本只动副本。
- Slide.Export / Open 路径必须 os.path.normpath 成反斜杠。
- 实测 2026-10-10：42/23/28 页全过，约 20~30s/40 页。
"""
import glob
import io
import os
import shutil
import sys

import pythoncom
import win32com.client as wc


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    pat, work, tag = sys.argv[1], sys.argv[2], sys.argv[3]
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    cs = glob.glob(pat)
    if not cs:
        print('no match:', pat)
        return 1
    src = cs[0]
    outdir = os.path.join(work, 'slides_hi_' + tag)
    os.makedirs(outdir, exist_ok=True)
    ppt = os.path.join(work, 'ppt_hi_' + tag + '.ppt')
    shutil.copyfile(src, ppt)
    pythoncom.CoInitialize()
    app = wc.DispatchEx('PowerPoint.Application')
    p = None
    ok = 0
    try:
        try:
            p = app.Presentations.Open(os.path.normpath(ppt), ReadOnly=True, Untitled=False, WithWindow=False)
        except Exception:
            p = app.Presentations.Open(os.path.normpath(ppt), ReadOnly=True)
        n = p.Slides.Count
        for i in range(1, n + 1):
            try:
                p.Slides(i).Export(os.path.normpath(os.path.join(outdir, 's%02d.png' % i)), 'PNG', 2560, 1920)
                ok += 1
            except Exception as e:
                print('fail', i, repr(e)[:80])
        print('EXPORTED', ok, 'of', n)
        return 0 if ok == n else 1
    finally:
        try:
            if p:
                p.Close()
        except Exception:
            pass
        try:
            app.Quit()
        except Exception:
            pass


if __name__ == '__main__':
    sys.exit(main())
