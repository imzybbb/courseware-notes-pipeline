#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""出图前 md 预检（courseware-notes-pipeline，2026-10-06 立）。

逮三类 `==` 事故（nb.py 先提取数学、后处理 ==，所以 == 混进数学块必翻车）：
  1) == 出现在 $$…$$ 块内部      → 渲染成裸露 ==
  2) == 出现在 $…$ 行内数学内部   → 同上
  3) 本行 == 个数为奇数（跨行/漏收尾；管线约定必须单行成对）

用法: python check_md.py <笔记.md> [更多.md ...]
exit 0 = 通过；1 = 有危险行（先修 md 再出图）。
"""
import re
import sys


def blank_blocks(s):
    """把 $$…$$ 块换成同数量换行，保持后续行号不变。"""
    return re.sub(r"\$\$.+?\$\$", lambda m: "\n" * m.group(0).count("\n"), s, flags=re.S)


def check(path):
    src = open(path, encoding="utf-8").read()
    lines = src.split("\n")
    problems = []

    for m in re.finditer(r"\$\$(.+?)\$\$", src, re.S):
        if "==" in m.group(1):
            ln = src.count("\n", 0, m.start()) + 1
            problems.append((ln, "== 混进 $$…$$ 块 → " + m.group(1).strip()[:80]))

    stripped = blank_blocks(src)
    for m in re.finditer(r"(?<!\$)\$([^$\n]+?)\$(?!\$)", stripped):
        if "==" in m.group(1):
            ln = stripped.count("\n", 0, m.start()) + 1
            problems.append((ln, "== 混进 $…$ → " + m.group(1).strip()[:80]))

    for i, ln in enumerate(lines, 1):
        if len(re.findall(r"==", ln)) % 2 == 1:
            problems.append((i, "== 个数为奇数（跨行或漏收尾）→ " + ln.strip()[:80]))

    problems.sort()
    print("== 预检 %s ==" % path)
    if not problems:
        print("  通过：0 危险行 ✓")
    for ln, msg in problems:
        print("  L%d: %s" % (ln, msg))
    return len(problems)


def main():
    if len(sys.argv) < 2:
        print("用法: python check_md.py <笔记.md> [更多.md ...]")
        sys.exit(2)
    bad = sum(check(p) for p in sys.argv[1:])
    print("合计危险行: %d" % bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
