# 课件 → 复习笔记（courseware-notes-pipeline）

> 把课堂课件（PPT，包括老式 `.ppt`）整理成"可以直接拿去复习"的图文笔记：公式正规排版、重点自动标出、例题原题＋全过程、**A4 整页 200dpi** 出图。
>
> 一个 Agent Skill：把目录放进技能目录，Agent 读到 `SKILL.md` 就按这套流程干活。

## 它解决什么问题

- 课件里的公式大多是图片——普通工具只能提取标题级文字，"公式"一抓就瞎；
- 老式 `.ppt` 各种工具打不开、转出来残缺不全；
- 复习笔记的关键不在"抄"，而在**分辨什么该留、什么该重点**——多数工具只会搬运，不会提炼。

## 它特别在哪

- **逐页"看"课件**：每页导出成图片逐页核对，不依赖纯文字提取——公式、图表、细节一个不落；
- **正规数学排版**：分数、上下标、求和、积分、希腊字母都按教材样式渲染（KaTeX），组合数用教材式上下标 `$\mathrm{C}_n^k$`；
- **会分辨重点**：按"定义/定理/公式、课件反复强调、易错点"等信号自动拣出重点，用荧光高亮＋★标记＋速记卡收口；遵循来源分级（课件＞教材＞补充资料），课件有印刷错会按正确值计算并附勘误小注；
- **例题全收录**：原题原文＋计算全过程，逐题编号核对、一道不漏；每道例题配图（优先裁课件原图，其次自绘示意）；
- **验收到细节**：出图后逐张复核（页数、尺寸、荧光块、结尾行），改哪页复检哪页。

## 输入 / 输出

| | 内容 |
|---|---|
| **输入** | `.pptx`、老式 `.ppt`（2003 格式，靠 Windows + PowerPoint COM 逐页导出）、`PDF`（有文本层直接抽，公式页再渲染核对）；配套练习 PDF 一起处理 |
| **输出** | **A4 整页 PNG**（200 dpi，1653×2339，页数随内容不限）＋同名 PDF；分节 Markdown 源文件；课件清单 / 进度表 / 勘误记录 |
| **风格** | 瑞士风主题：IKB 克莱因蓝 `#002FA7` 强调色 + 黄色荧光块；KaTeX 公式排版；★ 标重点、`==荧光高亮==` 核心结论、每节 ★速记卡 |

## 快速开始

```bash
# 1) 依赖
pip install -r requirements.txt          # pywin32 / Pillow / PyMuPDF
#   出 PDF 用本机已装的 Chrome（headless 打印），无需额外装浏览器

# 2) 放进 Agent 的技能目录（三选一，按你用的宿主）
#    Hermes   : <HERMES_HOME>/skills/courseware-notes-pipeline/
#    DSH      : ~/.dsh/skills/courseware-notes-pipeline/
#    Claude   : .claude/skills/courseware-notes-pipeline/
git clone https://github.com/imzybbb/courseware-notes-pipeline.git ~/.dsh/skills/courseware-notes-pipeline

# 3) 导出课件（.ppt 需要 Windows + 已装 PowerPoint；PDF 课件跳过这步）
python scripts/export_slides.py "<课件路径glob>" "<工作目录>" <tag>
python scripts/export_slides_hi.py "<课件路径glob>" "<工作目录>" <tag>   # 裁配图用的高清版

# 4) 写 md → 预检 → 出图
python scripts/check_md.py 笔记.md
python scripts/check_math_cjk.py 笔记.md
python scripts/check_katex.py 笔记.md            # 需 node + KaTeX 资产
python scripts/check_restate.py 笔记.md          # 需 sympy（查总结框重述的系数）
python pipeline/nb.py 笔记.md --outdir <图片版目录> --senddir <发送目录>
```

`nb.py` 会把 md 渲染成 HTML → Chrome 打印 A4 PDF → PyMuPDF 200dpi 逐页转 PNG，同时在 `--outdir` 与 `--senddir` 各留一份 PDF。

## 目录结构

```
courseware-notes-pipeline/
├── SKILL.md                 Agent 执行手册（流程、标准、红线）
├── README.md
├── requirements.txt
├── pipeline/
│   ├── nb.py                md → A4 PDF/PNG（主题注入、==高亮、公式保护）
│   ├── nb_swiss.css         瑞士风主题（改样式只动这个文件）
│   └── md2pdf_any.py        极简 md → html → Chrome 打印
└── scripts/
    ├── export_slides.py     .ppt/.pptx → 文字 dump + 每页 PNG(1280×960)
    ├── export_slides_hi.py  .ppt/.pptx → 每页 PNG(2560×1920)，裁配图用
    ├── check_md.py          逮 `==` 混进数学块 / 跨行未闭合
    ├── check_math_cjk.py    逮 `$…$` 里裸中文（应写 \text{…}）
    ├── check_katex.py       用 node+KaTeX 真渲染一遍，逮解析错误
    └── check_restate.py     逮「记 X=…，则 Y=…」重述里的系数错（sympy 回代）
```

## 已知坑（都踩过，写进 SKILL.md 了）

- **`\,^\circ` 会让 KaTeX 解析失败**：`\,^\circ`、`\,^{\circ}`、`10^{-6}^{\circ}` 分别抛 `Got group of unknown type`、`Double superscript`。`nb.py` 不报错、PDF 照出，**页面上是一串红色 LaTeX 源码**——所以出图前必须跑 `check_katex.py`。
- **`==…==` 不能写进 `$…$` / `$$…$$` 内部**：数学提取会把标记吞掉，渲染成裸露的 `==`。`check_md.py` 专逮这个。
- **`$…$` 里的中文一律 `\text{…}`**，否则 KaTeX 直接失败（`check_math_cjk.py`）。
- **16:9 课件别用 4:3 的尺寸导出**，形状会被拉变形；按 `pt/72*192` 算原生比例。
- **「量纲核对」查不出系数**：曾写过 `记 A₀=2πrt，则 τ=T/(2A₀r)`，回代是 `T/(4πr²t)`，比推导小一半，而旁边的量纲核对照样打勾。系数错只能靠回代复核——`check_restate.py` 就是干这个的，实测在 58 处「记…则…」里只报 1 处、且是真错。
- **PowerPoint 可能正开着课件**：只动副本，`Slide.Export` / `Open` 路径必须 `os.path.normpath` 成反斜杠。
- 本机 KaTeX 静态文件不随仓库分发：`curl -sL https://registry.npmmirror.com/katex/-/katex-0.16.11.tgz` 解包 `package/dist` 到 `katex/`，或用 `KATEX_DIR` 环境变量指过去。

## 运行成本（参考）

用 DeepSeek API 跑完整一条（逐页看图 → 写 md → 渲染 → 复检 → 交付）的实测：

| | 谷时 | 峰时 |
|---|---|---|
| 每份笔记（A4 10–20 页） | ≈ ¥0.4 | ≈ ¥0.8 |

量级：单份输入 7–15 万 token（含缓存命中 4–11 百万）、输出 3–7 万 token；成本一半来自输出。换更小的模型或拆更细的节会再低，但逐页看图的输入省不掉。

## 许可证

MIT License —— 随意使用、修改、分享，保留版权声明即可（详见 [LICENSE](LICENSE)）。

---
*2026-10 · courseware-notes-pipeline v3.1（A4 整页 + 瑞士主题）*
