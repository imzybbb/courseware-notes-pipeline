# -*- coding: utf-8 -*-
"""通用: 任意 md -> html -> pdf (Chrome headless)"""
import re, os, sys, subprocess

def conv(MD):
    base = os.path.splitext(MD)[0]
    HTML, PDF = base + ".html", base + ".pdf"
    lines = open(MD, encoding="utf-8").read().split("\n")
    out, i, in_ul = [], 0, False
    def inline(s):
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        return s.replace("✅", '<span class="ok">✅</span>').replace("⚠️", '<span class="warn">⚠️</span>')
    while i < len(lines):
        ln = lines[i]
        if ln.strip() == "---":
            out.append("<hr>"); i += 1; continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            if len(rows) >= 2 and set(rows[1][0]) <= set("-: "):
                head, body = rows[0], rows[2:]
            else:
                head, body = rows[0], rows[1:]
            out.append("<table><thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in head) + "</tr></thead><tbody>")
            for r in body:
                out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            out.append("</tbody></table>"); continue
        if ln.startswith("#"):
            n = len(ln) - len(ln.lstrip("#"))
            out.append("<h%d>%s</h%d>" % (n, inline(ln[n:].strip()), n)); i += 1; continue
        if ln.strip().startswith(">"):
            out.append("<blockquote>%s</blockquote>" % inline(ln.strip()[1:].strip())); i += 1; continue
        m = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.*)$", ln)
        if m:
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append("<li>%s</li>" % inline(m.group(1))); i += 1; continue
        if in_ul:
            out.append("</ul>"); in_ul = False
        if not ln.strip():
            i += 1; continue
        out.append("<p>%s</p>" % inline(ln.strip())); i += 1
    if in_ul:
        out.append("</ul>")
    html = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@page{size:A4;margin:13mm 11mm}
body{font-family:"Noto Sans SC","Microsoft YaHei",sans-serif;font-size:10.5pt;line-height:1.55;color:#111}
table{page-break-inside:auto;border-collapse:collapse;width:100%;margin:6px 0;font-size:9.5pt}
thead{display:table-header-group}
tr,li,h2,h3{page-break-inside:avoid}
h1{font-size:18pt;border-bottom:2px solid #333;padding-bottom:4px}
h2{font-size:13.5pt;margin-top:14px;border-left:5px solid #2b6cb0;padding:3px 0 3px 8px;background:#f2f7fd}
h3{font-size:11.5pt;margin-top:11px;color:#1a4e8a}
th,td{border:1px solid #999;padding:3px 6px;vertical-align:top}
th{background:#eef3f9;font-weight:700}
tr:nth-child(even) td{background:#fafbfd}
hr{border:0;border-top:1px dashed #bbb;margin:12px 0}
blockquote{margin:6px 0;padding:5px 10px;background:#f7f7f7;border-left:4px solid #bbb;color:#444}
ul{margin:4px 0 4px 18px;padding:0}
code{background:#f2f2f2;padding:0 3px}
.warn{color:#b7791f}.ok{color:#2f855a}
</style></head><body>
""" + "\n".join(out) + "</body></html>"
    open(HTML, "w", encoding="utf-8").write(html)
    CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--no-pdf-header-footer", "--print-to-pdf=" + PDF,
                        "file:///" + HTML.replace("\\", "/").replace(" ", "%20")],
                       capture_output=True, text=True, timeout=180)
    print("rc=%s  pdf=%s bytes" % (r.returncode, os.path.getsize(PDF) if os.path.exists(PDF) else 0))

if __name__ == "__main__":
    for p in sys.argv[1:]:
        conv(p)
