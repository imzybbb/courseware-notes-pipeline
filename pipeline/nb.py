# -*- coding: utf-8 -*-
"""笔记 md → 高清长图切片 v2（2026-10-03 起：KaTeX 数学渲染版）

用法:
    python nb.py <笔记.md> [--outdir 图片版目录] [--senddir 发送副本目录]
                 [--seg-min 3] [--seg-max 4] [--seg-h 2500]

特性:
    · 数学公式: $...$ 行内 / $$...$$ 独立行 —— 用本机 KaTeX 正规排版（分数/上下标/求和/积分/希腊字母）
    · ==文字== → 黄色荧光高亮（画重点用）
    · ^/_ 上下标后处理（守卫字符集内生效）
    · Chrome headless 截图（900 宽 @2x）→ 空白行处切 3~4 张长图
    · 产物: <outdir>（默认 <md上层>/图片版） + <senddir> 去空格发送副本

依赖: 本目录同一层的 katex/ 或 KATEX_DIR（KaTeX 静态文件，已内置）；md2pdf_any.py（E:\\AI\\dachuang）
"""
import argparse, glob, math, os, re, subprocess, sys, tempfile
from PIL import Image

CHROME = os.environ.get('CHROME', r'C:\Program Files\Google\Chrome\Application\chrome.exe')
MD2PDF_DIR = os.environ.get('MD2PDF_DIR', os.path.dirname(os.path.abspath(__file__)))
KATEX = os.environ.get('KATEX_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'katex')).replace(chr(92), '/')


def extract_math(md):
    """把 $...$ / $$...$$ 换成安全占位符，返回 (保护后的md, [(kind, tex), ...])"""
    maths = []

    def take(kind):
        def fn(m):
            maths.append((kind, m.group(1)))
            return '@@M%d@@' % (len(maths) - 1)
        return fn

    s = re.sub(r'\$\$(.+?)\$\$', take('D'), md, flags=re.S)
    s = re.sub(r'\$([^\$\n]+?)\$', take('I'), s)
    return s, maths


def math_html(kind, tex):
    t = tex.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return ('\\[' + t + '\\]') if kind == 'D' else ('\\(' + t + '\\)')


def scan_pair(s, i, oc, cc):
    depth = 0; j = i; n = len(s)
    while j < n:
        if s[j] == oc: depth += 1
        elif s[j] == cc:
            depth -= 1
            if depth == 0: break
        j += 1
    if j < n and depth == 0: return s[i + 1:j], j
    return None, i


def fix_scripts(s):
    out = []; i = 0; n = len(s); cs = cb = 0
    GUARD = '∫fFΣXxAnSpaĀλ'
    while i < n:
        c = s[i]
        if c == '^' and i + 1 < n:
            nxt = s[i + 1]
            if nxt in '({（':
                oc = '（' if nxt == '（' else ('{' if nxt == '{' else '(')
                cc = '）' if nxt == '（' else ('}' if nxt == '{' else ')')
                inner, j = scan_pair(s, i + 1, oc, cc)
                if inner is not None:
                    out.append('<sup>' + inner + '</sup>'); cs += 1; i = j + 1; continue
            elif nxt.isascii() and nxt.isalnum():
                j = i + 1
                while j < n and s[j].isascii() and s[j].isalnum(): j += 1
                out.append('<sup>' + s[i + 1:j] + '</sup>'); cs += 1; i = j; continue
        elif c == '_':
            prev = s[i - 1] if i > 0 else ''
            if prev in GUARD:
                nxt = s[i + 1] if i + 1 < n else ''
                if nxt == '{':
                    inner, j = scan_pair(s, i + 1, '{', '}')
                    if inner is not None:
                        out.append('<sub>' + inner + '</sub>'); cb += 1; i = j + 1; continue
                elif nxt == '(':
                    inner, j = scan_pair(s, i + 1, '(', ')')
                    if inner is not None:
                        out.append('<sub>' + inner + '</sub>'); cb += 1; i = j + 1; continue
                elif nxt.isascii() and (nxt.isalpha() or nxt.isdigit()):
                    j = i + 1
                    while j < n and s[j].isascii() and (s[j].isalpha() or s[j].isdigit()): j += 1
                    out.append('<sub>' + s[i + 1:j] + '</sub>'); cb += 1; i = j; continue
        out.append(c); i += 1
    return ''.join(out), cs, cb


KATEX_HEAD = '''<link rel="stylesheet" href="file:///{kat}/katex.min.css">
<script src="file:///{kat}/katex.min.js"></script>
<script src="file:///{kat}/contrib/auto-render.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function () {{
  if (window.renderMathInElement) {{
    renderMathInElement(document.body, {{
      delimiters: [
        {{left: "$$", right: "$$", display: true}},
        {{left: "\\\\[", right: "\\\\]", display: true}},
        {{left: "\\\\(", right: "\\\\)", display: false}}
      ],
      throwOnError: false
    }});
  }}
}});
</script>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('md')
    ap.add_argument('--outdir', default=None)
    ap.add_argument('--senddir', default=None)
    ap.add_argument('--seg-min', type=int, default=3)
    ap.add_argument('--seg-max', type=int, default=4)
    ap.add_argument('--seg-h', type=int, default=2500)
    args = ap.parse_args()

    md = os.path.abspath(args.md)
    base = os.path.splitext(os.path.basename(md))[0]
    raw_md = open(md, encoding='utf-8').read()
    prot, maths = extract_math(raw_md)
    print('math spans: %d (display %d)' % (len(maths), sum(1 for k, _ in maths if k == 'D')))

    figs = []
    def _ftake(m):
        figs.append((m.group(1).strip(), m.group(2) or '88'))
        return '@@F%d@@' % (len(figs) - 1)
    prot = re.sub(r'(?m)^[ \t]*\[FIG:([^|\]\n]+?)(?:\|(\d+))?\]\s*$', _ftake, prot)

    tmpd = tempfile.mkdtemp(prefix='nb_')
    tmp_md = os.path.join(tmpd, base + '.md')
    open(tmp_md, 'w', encoding='utf-8').write(prot)

    sys.path.insert(0, MD2PDF_DIR)
    import md2pdf_any
    md2pdf_any.conv(tmp_md)
    hp = os.path.join(tmpd, base + '.html')
    h = open(hp, encoding='utf-8').read()

    h, cs, cb = fix_scripts(h)
    for m in list(re.finditer(r'.{14}[\^_].{14}', h))[:6]:
        print('  残留上下文:', m.group(0).replace(chr(10), ' ')[:90])
    nm = len(re.findall(r'==[^\n]+?==', h))
    h = re.sub(r'==([^\n]+?)==', r'<mark>\1</mark>', h)

    def mrepl(m):
        i = int(m.group(1)); k, t = maths[i]
        return math_html(k, t)
    h = re.sub(r'@@M(\d+)@@', mrepl, h)
    # —— 题图嵌入（第二阶段）：@@F#@@ → base64 内嵌图（2026-10-05）——
    import base64 as _b64
    _fok = 0
    for _fi, (_fp, _fw) in enumerate(figs):
        try:
            _b64s = _b64.b64encode(open(_fp, 'rb').read()).decode('ascii')
            _tag = '<div class="fig"><img style="width:%s%%" src="data:image/png;base64,%s"></div>' % (_fw, _b64s)
            _fok += 1
        except Exception:
            _tag = '<div class="fig">［图缺失: %s］</div>' % _fp
        _pat = r'<p[^>]*>\s*@@F%d@@\s*</p>' % _fi
        if re.search(_pat, h):
            h = re.sub(_pat, lambda m, t=_tag: t, h, count=1)
        else:
            h = h.replace('@@F%d@@' % _fi, _tag)
    print('figs=%d' % _fok)


    h = h.replace('</head>', KATEX_HEAD.format(kat=KATEX) + '</head>', 1)
    # —— 主题 CSS 注入（Swiss 风；改样式只动 nb_swiss.css，不动本代码）2026-10-05 ——
    theme_path = os.environ.get('NB_THEME', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nb_swiss.css'))
    theme = open(theme_path, encoding='utf-8').read() if os.path.exists(theme_path) else 'mark{background:#ffe58f;padding:0 2px}'
    h = h.replace('</head>', '<style>\n' + theme + '\n</style></head>', 1)
    outp_html = os.path.join(tmpd, base + '_v2.html')
    open(outp_html, 'w', encoding='utf-8').write(h)
    print('sup=%d sub=%d marks=%d | 残留 ^=%d _=%d' % (cs, cb, nm, h.count('^'), h.count('_')))

    # —— A4 整页输出（2026-10-05 她要求）：Chrome 打印 A4 PDF → 逐页 PNG（同比例、张数不限）——
    pdf = os.path.join(tmpd, base + '.pdf')
    url = 'file:///' + outp_html.replace(os.sep, '/').replace(' ', '%20')
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--allow-file-access-from-files',
                    '--no-pdf-header-footer', '--print-to-pdf-no-header',
                    '--virtual-time-budget=20000', '--print-to-pdf=' + pdf, url],
                   capture_output=True, timeout=300)
    if not os.path.exists(pdf):
        print('!! Chrome 打印 PDF 失败'); return
    try:
        import fitz  # PyMuPDF
    except ImportError:
        import pymupdf as fitz
    doc = fitz.open(pdf)
    outdir = args.outdir or os.path.join(os.path.dirname(os.path.dirname(md)), '图片版')
    senddir = args.senddir or os.path.join(tempfile.gettempdir(), 'notes_send')
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(senddir, exist_ok=True)
    sb = base.replace(' ', '')
    for i in range(doc.page_count):
        pix = doc[i].get_pixmap(dpi=200)
        p1 = os.path.join(outdir, '%s_%d.png' % (base, i + 1))
        p2 = os.path.join(senddir, '%s_%d.png' % (sb, i + 1))
        pix.save(p1); pix.save(p2)
        print('page %d/%d %dx%d %d bytes -> %s' % (i + 1, doc.page_count, pix.width, pix.height, os.path.getsize(p1), p1))
    import shutil as _sh
    _pdf1 = os.path.join(outdir, base + '.pdf')
    _pdf2 = os.path.join(senddir, sb + '.pdf')
    _sh.copyfile(pdf, _pdf1); _sh.copyfile(pdf, _pdf2)
    print('PDF: %s (%.2f MB) + %s' % (_pdf1, os.path.getsize(_pdf1) / 1048576.0, _pdf2))
    print('DONE. 共 %d 张（A4 整页）＋PDF 版。发送副本目录: %s' % (doc.page_count, senddir))


if __name__ == '__main__':
    main()
