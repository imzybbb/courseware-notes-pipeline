# -*- coding: utf-8 -*-
"""预检：笔记 md 的 $…$ / $$…$$ 内是否含裸中文（\\text{…} 之外）。

用法: python check_math_cjk.py <笔记.md>
退出码: 0 = 通过；1 = 有裸中文（逐条打印）。
背景: 2026-10-10 某次实际笔记漏 9 处 cases 裸中文（“其它/若/存在”），渲染前手工修掉；此脚本固化该检查。
"""
import re
import sys
from pathlib import Path

CJK = re.compile(r'[\u4e00-\u9fff]')


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_math_cjk.py <note.md>")
        return 2
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    bad = []
    for m in re.finditer(r'\$\$?(.+?)\$\$?', text, flags=re.S):
        inner = re.sub(r'\\text\{[^}]*\}', '', m.group(1))
        if CJK.search(inner):
            bad.append(inner[:100].replace("\n", " "))
    if bad:
        print("发现 %d 处 $…$ 内裸中文（请改成 \\text{…}）:" % len(bad))
        for b in bad:
            print("  -", b)
        return 1
    print("check_math_cjk 通过：$…$ 内无裸中文 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
