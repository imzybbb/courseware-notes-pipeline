# -*- coding: utf-8 -*-
"""窄口径校验：逮「记 X=…，则 Y=…」这种总结框重述里的系数错。

为什么只查这一种：
- 全文公式对账误报太多（单位换算、近似号、多段连等），人工过不完；
- 而"先定义一个新量、再回代给别人看"是**最容易写错系数**的位置——
  量纲核对查不出系数（实测有过 τ 少一半、量纲照样打勾的案例）。

用法: python check_restate.py <笔记.md ...>
退出码 0 = 未发现问题；1 = 发现可疑重述（逐条打印，需人工确认）
依赖: sympy + antlr4-python3-runtime==4.11
"""
import re
import sys
import glob
from pathlib import Path

from sympy.parsing.latex import parse_latex
from sympy import simplify, Symbol

PAT = re.compile(r"记[^$]{0,24}\$([^$]+?)\$[^$]{0,10}?(?:则|那么|于是)\s*\$([^$]+?)\$")


def norm(s):
    s = s.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    s = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\text\{[^}]*\}", "", s)
    s = s.replace(r"\,", " ").replace(r"\;", " ")
    s = s.replace(r"\left", "").replace(r"\right", "")
    return s.strip()


def check(definition, restated):
    """definition 形如 A_0=2*pi*r*t；restated 形如 tau=T/(2*A_0*r)"""
    d = parse_latex(norm(definition), strict=False)
    r = parse_latex(norm(restated), strict=False)
    if getattr(d, "lhs", None) is None or getattr(r, "rhs", None) is None:
        return None, "解析失败"
    mapping = {d.lhs: d.rhs}
    diff = simplify(r.rhs.subs(mapping) - r.lhs)
    return diff, ""


def main(paths):
    bad = 0
    total = 0
    for p in paths:
        txt = Path(p).read_text(encoding="utf-8", errors="ignore")
        for m in PAT.finditer(txt):
            total += 1
            definition, restated = m.group(1), m.group(2)
            try:
                diff, err = check(definition, restated)
            except Exception as e:
                print(f"[跳过] {Path(p).name}: {definition} → {restated}  ({type(e).__name__})")
                continue
            if err:
                continue
            # 差值只含常量或能化简为 0 → 通过
            try:
                if diff == 0 or (diff.is_number and abs(float(diff)) < 1e-12):
                    continue
            except Exception:
                pass
            bad += 1
            line = txt[: m.start()].count("\n") + 1
            print(f"\n[可疑] {Path(p).name}:{line}")
            print(f"   定义   {definition}")
            print(f"   重述   {restated}")
            print(f"   回代后差 = {diff}")
    print(f"\n共检查 {total} 处「记…则…」，可疑 {bad} 处")
    return 1 if bad else 0


if __name__ == "__main__":
    args = sys.argv[1:] or ["*.md"]
    paths = []
    for a in args:
        paths.extend(glob.glob(a, recursive=True))
    sys.exit(main(paths))
