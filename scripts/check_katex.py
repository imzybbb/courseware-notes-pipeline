# -*- coding: utf-8 -*-
"""出图前 md 预检：把 $…$ / $$…$$ 全部交给 KaTeX 真渲染一遍，逮解析错误。

用法:  python check_katex.py <笔记.md>
依赖:  node + E:\\AI\\tools\\note_build\\katex\\katex.min.js（KATEX_DIR 可覆盖）

为什么需要它（2026-10-19 实际项目中实测）：KaTeX 对 `\\,^\\circ`、`10^{-6}^{\\circ}`
这类写法会抛 "Got group of unknown type: 'internal'" / "Double superscript"，
nb.py 不报错、PDF 照出，但页面上是一串**红色 LaTeX 源码**——只有翻图或 grep
PDF 文本层里的反斜杠才发现。跑这一遍 30 秒，能省一次整链重渲。

正确写法：角度 `^\\circ` 前不要留 `\\,`；紧跟幂次时写 `10^{-6}\\,{}^{\\circ}\\mathrm{C}^{-1}`。
"""
import json
import os
import re
import subprocess
import sys
import tempfile

KATEX = os.environ.get('KATEX_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'katex'))

JS = r"""const fs=require('fs');
const katex=require(KATEX_JS);
const list=JSON.parse(fs.readFileSync(LIST_JSON,'utf8'));
let bad=0;
list.forEach(([kind,tex],i)=>{
  try{katex.renderToString(tex,{displayMode:kind==='D',throwOnError:true,strict:false});}
  catch(e){bad++;console.log('FAIL#'+i+' ['+kind+'] '+tex.slice(0,110));console.log('    '+e.message.split('\n')[0].slice(0,110));}
});
console.log('KaTeX 校验: '+list.length+' 条，失败 '+bad+(bad?' ✗':' ✓'));
process.exit(bad?1:0);
"""


def main():
    if len(sys.argv) < 2:
        print('用法: python check_katex.py <笔记.md>')
        return 2
    md = open(sys.argv[1], encoding='utf-8').read()

    maths = [['D', m.group(1)] for m in re.finditer(r'\$\$(.+?)\$\$', md, flags=re.S)]
    maths += [['I', m.group(1)] for m in re.finditer(r'\$([^\$\n]+?)\$', md)]
    seen, uniq = set(), []
    for k, t in maths:
        if t not in seen:
            seen.add(t)
            uniq.append([k, t])

    tmpd = tempfile.mkdtemp(prefix='kx_')
    jp = os.path.join(tmpd, 'math.json')
    jsp = os.path.join(tmpd, 'check.js')
    json.dump(uniq, open(jp, 'w', encoding='utf-8'), ensure_ascii=False)
    js = (JS.replace('KATEX_JS', json.dumps(os.path.join(KATEX, 'katex.min.js')))
            .replace('LIST_JSON', json.dumps(jp)))
    open(jsp, 'w', encoding='utf-8').write(js)

    r = subprocess.run(['node', jsp], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = (r.stdout or '').strip() or (r.stderr or '').strip()
    print(out)
    return r.returncode


if __name__ == '__main__':
    sys.exit(main())
