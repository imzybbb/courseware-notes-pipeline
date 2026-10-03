# -*- coding: utf-8 -*-
"""导出课程 PPT：文字 dump + 每页 PNG。
用法:
  python export_slides.py "<课件目录>/第X章*.ppt" "<工作目录>/g01" ch01
产物:
  <workdir>/ppt_ch01.ppt          工作副本（不动原件）
  <workdir>/slides_ch01/sNN.png   每页 PNG
  <workdir>/dump_ch01.txt         每页文字 dump
要点: DispatchEx 新实例；只读打开副本；Export 路径必须 normpath（forward slash 会失败）。
"""
import sys, io, os, glob, shutil
import win32com.client as wc, pythoncom

def main():
    pat, work, tag = sys.argv[1], sys.argv[2], sys.argv[3]
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    cs = glob.glob(pat)
    assert cs, 'no ppt matched: ' + pat
    src = cs[0]
    print('found:', src)
    slides_dir = work + '/slides_' + tag
    os.makedirs(slides_dir, exist_ok=True)
    ppt = work + '/ppt_' + tag + '.ppt'
    shutil.copyfile(src, ppt)
    pythoncom.CoInitialize()
    app = wc.DispatchEx('PowerPoint.Application')
    p = None
    try:
        try:
            p = app.Presentations.Open(os.path.normpath(ppt), ReadOnly=True, Untitled=False, WithWindow=False)
        except Exception:
            p = app.Presentations.Open(os.path.normpath(ppt), ReadOnly=True)
        n = p.Slides.Count
        print('SLIDES:', n)
        out = []
        for i in range(1, n + 1):
            s = p.Slides(i)
            ts = []
            for sh in s.Shapes:
                try:
                    if sh.HasTextFrame and sh.TextFrame.HasText:
                        x = ' '.join(sh.TextFrame.TextRange.Text.split())
                        if x and x not in ts:
                            ts.append(x)
                except Exception:
                    pass
            out.append('----- %02d -----' % i)
            out.append(' | '.join(ts)[:600])
        with open(work + '/dump_' + tag + '.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(out))
        ok = 0
        for i in range(1, n + 1):
            try:
                p.Slides(i).Export(os.path.normpath(slides_dir + '/s%02d.png' % i), 'PNG', 1280, 960)
                ok += 1
            except Exception as e:
                print('expfail', i, repr(e)[:80])
        print('exported', ok)
    finally:
        try:
            if p: p.Close()
        except Exception:
            pass
        try:
            app.Quit()
        except Exception:
            pass
    print('DONE')

if __name__ == '__main__':
    main()