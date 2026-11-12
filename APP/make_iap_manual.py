# -*- coding: utf-8 -*-
"""生成《STM32 IAP Bootloader 串口升级 学习手册》Word 文档及配套代码。"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT_DIR = os.path.join(os.getcwd(), "IAP_Bootloader_学习包")
CODE_DIR = os.path.join(OUT_DIR, "code")
DOCX_PATH = os.path.join(OUT_DIR, "STM32_IAP_Bootloader_学习手册.docx")

os.makedirs(CODE_DIR, exist_ok=True)

# ---------------- 颜色与字体 ----------------
BLUE = RGBColor(0x1F, 0x4E, 0x79)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x66, 0x66, 0x66)
LIGHT = RGBColor(0xF2, 0xF2, 0xF2)
CODE_BG = "F5F7FA"
HEADER_BG = "1F4E79"
NOTE_BG = "EAF1FB"
WARN_BG = "FFF4E5"

CN_FONT = "微软雅黑"
MONO_FONT = "Consolas"


def set_run_font(run, name=CN_FONT, size=10.5, bold=False, color=DARK, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    rFonts.set(qn("w:eastAsia"), CN_FONT if name == CN_FONT else name)


def add_rich(paragraph, text, size=10.5, color=DARK):
    """支持 **加粗** 的简单行内格式。"""
    import re
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = paragraph.add_run(part[2:-2])
            set_run_font(r, size=size, bold=True, color=color)
        else:
            r = paragraph.add_run(part)
            set_run_font(r, size=size, color=color)


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def cell_margins(cell, top=60, bottom=60, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for tag, val in (("top", top), ("bottom", bottom), ("start", left), ("end", right)):
        el = OxmlElement("w:" + tag)
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcPr.append(mar)


def table_borders(table, color="BFBFBF", sz=4):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def page_num_footer(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = paragraph.add_run("第 ")
    set_run_font(r, size=8.5, color=GRAY)
    run = paragraph.add_run()
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = "PAGE"
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "separate")
    fldChar3 = OxmlElement("w:fldChar")
    fldChar3.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)
    r2 = paragraph.add_run(" 页")
    set_run_font(r2, size=8.5, color=GRAY)


doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.1)
sec.bottom_margin = Cm(1.9)
sec.left_margin = Cm(2.2)
sec.right_margin = Cm(2.2)
sec.header_distance = Cm(1.0)
sec.footer_distance = Cm(0.9)

# 默认样式
normal = doc.styles["Normal"]
normal.font.name = CN_FONT
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)
normal.paragraph_format.line_spacing = 1.28
normal.paragraph_format.space_after = Pt(3)

# 代码样式
code_style = doc.styles.add_style("CodeBlock", 1)  # paragraph
code_style.font.name = MONO_FONT
code_style.font.size = Pt(8.5)
code_style.font.color.rgb = RGBColor(0x20, 0x20, 0x20)
code_style.element.rPr.rFonts.set(qn("w:eastAsia"), MONO_FONT)
code_style.paragraph_format.space_before = Pt(0)
code_style.paragraph_format.space_after = Pt(0)
code_style.paragraph_format.line_spacing = 1.0

# 页眉
header = sec.header
hp = header.paragraphs[0]
hp.text = ""
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = hp.add_run("STM32 IAP Bootloader 串口升级 · 学习手册")
set_run_font(r, size=8.5, color=GRAY)

# 页脚
page_num_footer(sec.footer.paragraphs[0])

# ---------------- 基础排版函数 ----------------
def H1(text, page_break=True):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 1"]
    p.paragraph_format.page_break_before = page_break
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    set_run_font(r, size=17, bold=True, color=BLUE)
    # 标题下横线
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), "1F4E79")
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def H2(text):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 2"]
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    set_run_font(r, size=13, bold=True, color=BLUE)


def H3(text):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 3"]
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    set_run_font(r, size=11, bold=True, color=DARK)


def P(text, size=10.5, color=DARK, after=3, before=0, indent=0, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.first_line_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    add_rich(p, text, size=size, color=color)
    return p


def B(text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(0.6 + 0.55 * level)
    p.paragraph_format.first_line_indent = Cm(-0.45)
    p.paragraph_format.space_after = Pt(2)
    add_rich(p, text, size=10.5)
    return p


def CODE(code, caption=None):
    if caption:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run("代码：" + caption)
        set_run_font(r, size=9, bold=True, color=GRAY)
    lines = code.strip("\n").split("\n")
    for i, line in enumerate(lines):
        p = doc.add_paragraph(style="CodeBlock")
        p.paragraph_format.left_indent = Cm(0.3)
        p.paragraph_format.right_indent = Cm(0.2)
        p.paragraph_format.space_before = Pt(1 if i == 0 else 0)
        p.paragraph_format.space_after = Pt(1 if i == len(lines) - 1 else 0)
        # 短代码块整体保持；长代码块允许自然分页，避免出现大段空白
        p.paragraph_format.keep_together = True
        if len(lines) <= 14:
            p.paragraph_format.keep_with_next = (i < len(lines) - 1)
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), CODE_BG)
        pPr.append(shd)
        r = p.add_run(line if line else " ")
        set_run_font(r, name=MONO_FONT, size=8.5, color=DARK)


def TABLE(headers, rows, widths=None, font_size=9, header_fill=HEADER_BG):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table_borders(table)
    hdr = table.rows[0]
    # repeat header
    trPr = hdr._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = ""
        shade_cell(cell, header_fill)
        cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_run_font(r, size=font_size, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            cell_margins(cells[i])
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            add_rich(p, str(val), size=font_size)
    if widths:
        for i, w in enumerate(widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def NOTE(title, text, warn=False):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table_borders(table, color="D6E4F0" if not warn else "F0C36D")
    cell = table.rows[0].cells[0]
    cell.width = Cm(16.2)
    shade_cell(cell, WARN_BG if warn else NOTE_BG)
    cell_margins(cell, 100, 100, 140, 140)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(("⚠ " if warn else "💡 ") + title + "：")
    set_run_font(r, size=9.5, bold=True, color=RGBColor(0xB5, 0x6A, 0x00) if warn else BLUE)
    add_rich(p, text, size=9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def PAGEBREAK():
    doc.add_page_break()


# =====================================================================
# 封面
# =====================================================================
for _ in range(3):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("STM32 IAP Bootloader")
set_run_font(r, size=30, bold=True, color=BLUE)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("串口升级 · 学习手册")
set_run_font(r, size=18, bold=True, color=DARK)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("从 Flash 读写到 A/B 双槽回滚")
set_run_font(r, size=12.5, color=GRAY)

doc.add_paragraph()
# 分隔线
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
pPr = p._p.get_or_add_pPr()
pBdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"), "single")
bottom.set(qn("w:sz"), "12")
bottom.set(qn("w:space"), "1")
bottom.set(qn("w:color"), "1F4E79")
pBdr.append(bottom)
pPr.append(pBdr)

for _ in range(2):
    doc.add_paragraph()

cover_info = [
    ("芯片平台", "STM32F103C8T6（Cortex-M3，72MHz，64KB Flash / 20KB SRAM）"),
    ("开发工具", "STM32CubeMX + Keil MDK（ARMCC V5）+ STM32F1 HAL V1.8.7"),
    ("上位机", "Python 3 + pyserial + zlib（CRC32）"),
    ("对应项目", "项目二：基于 HAL 的 STM32 IAP Bootloader 串口升级"),
    ("版本", "v1.0 · 2026-11"),
]
t = doc.add_table(rows=0, cols=2)
t.alignment = WD_TABLE_ALIGNMENT.CENTER
t.autofit = False
table_borders(t, color="FFFFFF")
for k, v in cover_info:
    cells = t.add_row().cells
    cells[0].width = Cm(3.2)
    cells[1].width = Cm(11.5)
    p = cells[0].paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run(k + "：")
    set_run_font(r, size=10, bold=True, color=BLUE)
    p = cells[1].paragraphs[0]
    add_rich(p, v, size=10, color=DARK)

for _ in range(3):
    doc.add_paragraph()

P("配套代码：code/uart_retarget.c、code/flash_ops.c、code/bootloader_jump.c、code/protocol.h、code/host_tool.py",
  size=9, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER)
P("说明：本手册中的代码为学习/参考模板，实际工程请结合自己的引脚、时钟和 Flash 分区调整。",
  size=9, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER)

# =====================================================================
# 前言
# =====================================================================
H1("前言：怎么用这本手册", page_break=True)

P("这本手册对应项目二：**基于 HAL 的 STM32 IAP Bootloader 串口升级**。"
  "目标不是“背概念”，而是让你能自己写出一个能用的 Bootloader，并且能在面试时讲清楚每一行为什么这么写。")

H2("适合谁")
B("已经能点亮 LED、会用 CubeMX 生成 Keil 工程。")
B("会 C 语言指针、结构体、位运算。")
B("想搞懂 Flash、启动流程、中断向量表、串口协议和 A/B 回滚。")

H2("怎么读")
B("**第一遍**：按第 1～6 章顺序看，先建立整体框架，不要一上来抠寄存器。")
B("**第二遍**：打开 Keil，把第 4～6 章的代码自己敲一遍，每敲完一段就下载验证。")
B("**第三遍**：看第 7～8 章的协议和 A/B，把项目从“能跳转”升级到“能可靠升级”。")
B("**面试前**：直接看第 10 章题库和第 11 章计划。")

H2("标记说明")
B("💡 提示：经验、技巧、容易忽略的点。")
B("⚠ 注意：接错会烧片、擦错会丢程序、跳错会 HardFault。")
B("“代码：”下面是参考代码，行号/参数在正文中解释。")

NOTE("重要",
     "Bootloader 工程和 App 工程必须是两个独立工程；不要在电子钟工程里直接改，"
     "否则链接地址、向量表和 Flash 分区会互相打架。")

# =====================================================================
# 目录
# =====================================================================
H1("目录", page_break=True)
toc = [
    ("第 1 章", "项目总览：IAP、ICP、OTA 到底有什么区别"),
    ("第 2 章", "STM32F103C8 的 Flash、启动流程和中断向量表"),
    ("第 3 章", "HAL 与 CubeMX：工程是怎么生成的"),
    ("第 4 章", "串口与 printf：从接线到重定向"),
    ("第 5 章", "Flash 编程：第 3 课代码逐行解析"),
    ("第 6 章", "Bootloader：Flash 分区、有效性检查和跳转"),
    ("第 7 章", "串口升级协议：帧、CRC、状态机、上位机"),
    ("第 8 章", "A/B 双槽、元数据、掉电与回滚"),
    ("第 9 章", "调试与测试：串口、Flash、跳转三大故障"),
    ("第 10 章", "面试题库：15 个高频问题"),
    ("第 11 章", "5 天实施计划与验收标准"),
    ("附录", "地址/常量速查、术语表、代码索引、参考资料"),
]
for chap, title in toc:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(chap + "　")
    set_run_font(r, size=10.5, bold=True, color=BLUE)
    r = p.add_run(title)
    set_run_font(r, size=10.5, color=DARK)

# =====================================================================
# 第 1 章
# =====================================================================
H1("第 1 章　项目总览：IAP、ICP、OTA 到底有什么区别")

H2("1.1 项目要做什么")
P("给 STM32F103C8T6 写一个 **Bootloader（引导程序）**：上电先运行它，它负责判断 App 是否有效、"
  "要不要升级；如果需要升级，就通过 **USART1 串口**接收电脑发来的固件，写进 Flash，校验通过后跳转到 App。")
P("整个过程不需要 ST-Link，只需要一根 USB-TTL；升级失败或断电时，Bootloader 还在，可以重新刷，不会变砖。")

H2("1.2 最终效果")
B("正常上电：Bootloader 检查 App → 跳转 App，电子钟正常跑。")
B("电脑发升级命令：Bootloader 进入升级模式，接收 `.bin`，写入 Slot B。")
B("CRC 校验通过：更新元数据，跳转新 App。")
B("校验失败/断电：继续使用旧 Slot A，或停在 Bootloader 等待重试。")
B("App 无效：停在 Bootloader，可以重新升级。")

H2("1.3 IAP、ICP、OTA 的区别")
TABLE(["名称", "全称/含义", "用什么升级", "特点"], [
    ["ICP", "In-Circuit Programming，在电路编程", "ST-Link / J-Link / SWD", "开发阶段最常用，需要调试器"],
    ["IAP", "In-Application Programming，在应用编程", "Bootloader + 串口/CAN/SPI 等", "产品现场升级，不需要调试器"],
    ["OTA", "Over-The-Air，空中升级", "WiFi/蓝牙/4G + Bootloader", "无线升级，本项目的进阶形态"],
], widths=[2.2, 5.0, 5.2, 4.0])

P("本项目做的是 **IAP**；如果后面把 ESP8266 接上，让 ESP 从服务器下载固件再通过串口转给 STM32，就变成了 **OTA**。")

H2("1.4 学习路线")
TABLE(["课", "内容", "验收现象"], [
    ["第 1 课", "CubeMX + HAL 点灯", "PC13 LED 1Hz 闪烁"],
    ["第 2 课", "USART1 + printf", "串口打印 Bootloader Start，能回显"],
    ["第 3 课", "Flash 擦除/写入/读取", "E/W/R 命令，复位后数据还在"],
    ["第 4 课", "App 偏移 + 跳转", "Bootloader 能跳转到 App"],
    ["第 5 课", "串口升级协议 + 上位机", "电脑把 bin 写进 Flash"],
    ["第 6 课", "A/B 双槽 + CRC + 回滚", "刷坏/断电还能回滚"],
], widths=[2.0, 6.2, 7.2])

H2("1.5 硬件清单")
TABLE(["器材", "作用", "注意"], [
    ["STM32F103C8T6 最小系统板", "运行 Bootloader/App", "Blue Pill 板载 LED 在 PC13，低电平点亮"],
    ["ST-Link V2", "第一次烧 Bootloader、调试", "SWDIO→PA13，SWCLK→PA14，GND 共地"],
    ["USB-TTL（CH340/CP2102）", "串口升级、printf", "TX/RX 要交叉，GND 必须接"],
    ["杜邦线若干", "接线", "尽量短，接触可靠"],
    ["面包板", "搭建电路", "注意电源正负极不要接反"],
], widths=[5.0, 5.0, 6.4])

NOTE("接线口诀",
     "USB-TTL 的 TX 接单片机 RX（PA10），USB-TTL 的 RX 接单片机 TX（PA9），GND 对 GND；"
     "板子已独立供电时，USB-TTL 的 VCC 不要接。")

H2("1.6 软件环境")
TABLE(["软件", "版本/说明"], [
    ["STM32CubeMX", "安装 STM32Cube FW_F1 V1.8.7 固件包"],
    ["Keil MDK", "ARMCC V5.06，安装 STM32F1xx_DFP 器件包"],
    ["串口助手", "115200、8N1、无流控；发送用 ASCII，不要勾 HEX 发送"],
    ["Python", "3.10+，安装 pyserial（上位机）"],
], widths=[4.3, 11.9])

H2("1.7 工程结构建议")
CODE(r'''
D:\STM32_Project\
├── IAP_Bootloader\        Bootloader 工程，0x08000000
│   ├── Core\
│   ├── Drivers\
│   └── MDK-ARM\
├── IAP_App\               App 工程，0x08002000
│   ├── Core\
│   ├── Drivers\
│   └── MDK-ARM\
└── host\
    ├── host_tool.py       上位机
    └── app.bin             Keil 生成的固件
''', "推荐的工程目录")

NOTE("不要混在一起",
     "Bootloader 和 App 都从 0x08000000 链接的话，下载时会互相覆盖。"
     "从第 4 课开始，App 必须把 IROM 起始地址改成 0x08002000。")

# =====================================================================
# 第 2 章
# =====================================================================
H1("第 2 章　STM32F103C8 的 Flash、启动流程和中断向量表")

H2("2.1 芯片资源")
TABLE(["项目", "参数"], [
    ["内核", "ARM Cortex-M3，最高 72MHz"],
    ["Flash", "64KB（0x08000000 ~ 0x0800FFFF）"],
    ["SRAM", "20KB（0x20000000 ~ 0x20004FFF）"],
    ["Flash 页大小", "1KB（0x400）"],
    ["Flash 编程单位", "半字（16 位）"],
    ["调试接口", "SWD：PA13/SWDIO、PA14/SWCLK"],
], widths=[4.0, 12.2])

H2("2.2 Flash 地图")
CODE(r'''
0x08000000  ┌──────────────────────┐
            │  Bootloader (8KB)    │  0x08000000 ~ 0x08001FFF
0x08002000  ├──────────────────────┤
            │  Slot A (24KB)       │  0x08002000 ~ 0x08007FFF
0x08008000  ├──────────────────────┤
            │  Slot B (24KB)       │  0x08008000 ~ 0x0800DFFF
0x0800E000  ├──────────────────────┤
            │  Config (2KB)        │  元数据、CRC、当前槽
0x0800E800  ├──────────────────────┤
            │  预留/未使用          │
0x08010000  └──────────────────────┘
''', "A/B 双槽 Flash 分区（64KB）")

P("当前电子钟 App 约 10.4KB，放进 24KB 的 Slot 完全够用。"
  "如果以后 App 超过 24KB，就要改成单槽 + 外部 SPI Flash 备份，或者换更大 Flash 的芯片。")

H2("2.3 上电启动流程")
CODE(r'''
上电/复位
   ↓
从 0x08000000 取第 1 个字 → 赋给 MSP（主栈指针）
从 0x08000004 取第 2 个字 → 赋给 PC（Reset_Handler）
   ↓
执行启动文件 startup_stm32f10x_md.s
   ↓
SystemInit() → 配置时钟
   ↓
__main() → 初始化 C 库、清零 .bss、拷贝 .data
   ↓
main()
''', "Cortex-M3 复位序列")

P("Cortex-M3 硬件规定：**向量表第 0 项是 MSP 初值，第 1 项是 Reset_Handler 地址**。"
  "所以 App 的固件前 8 个字节必须是一个合理的栈顶和一个合法的复位向量，Bootloader 才能安全跳过去。")

H2("2.4 中断向量表和 VTOR")
P("STM32F103 的向量表默认在 Flash 起始 `0x08000000`。每个中断入口占 4 字节，"
  "例如复位、NMI、HardFault、SysTick、USART1 等。")
P("当 App 被链接到 `0x08002000` 时，它的向量表也在 `0x08002000`。"
  "如果 App 里发生了中断，而 `SCB->VTOR` 还指向 `0x08000000`，CPU 就会跳到 Bootloader 的向量表，"
  "轻则进错中断，重则 HardFault。")
CODE(r'''
/* App 启动时必须把向量表搬到自己身上 */
SCB->VTOR = 0x08002000;
''', "App 设置向量表偏移")
P("Bootloader 跳转前也会设置一次 `SCB->VTOR = APP_ADDR`，App 启动后再确认一次，双保险。")

H2("2.5 为什么 App 必须改链接地址")
P("Keil 默认把代码链接到 `0x08000000`。如果 App 也放这里，下载时会把 Bootloader 覆盖掉，"
  "而且 App 的中断向量表地址也不对。")
P("所以 App 工程要做两件事：")
B("Keil → Options for Target → Target → IROM1 起始地址改成 **0x08002000**，大小 **0x6000**（24KB）。")
B("代码里设置 `SCB->VTOR = 0x08002000`。")
NOTE("常见错误",
     "只改了 IROM 起始地址，忘了改 VTOR：程序能跑，但一进中断就飞。"
     "或者只改了 VTOR，没改链接地址：编译出来的向量表还在 0x08000000，跳过去也是错的。")

H2("2.6 地址规划速查")
TABLE(["区域", "起始", "大小", "结束", "用途"], [
    ["Bootloader", "0x08000000", "8KB", "0x08001FFF", "升级逻辑，永不擦"],
    ["Slot A", "0x08002000", "24KB", "0x08007FFF", "App A"],
    ["Slot B", "0x08008000", "24KB", "0x0800DFFF", "App B / 升级目标"],
    ["Config", "0x0800E000", "2KB", "0x0800E7FF", "魔数、版本、CRC、当前槽"],
    ["测试页", "0x0800F800", "1KB", "0x0800FBFF", "第 3 课 Flash 实验用"],
], widths=[3.0, 3.0, 2.2, 3.2, 4.8])

P("第 3 课的测试页 `0x0800F800` 只是教学用；正式 Bootloader 里，这个位置会被 Config 或预留区替代，"
  "测试代码要删掉或改地址。")

# =====================================================================
# 第 3 章
# =====================================================================
H1("第 3 章　HAL 与 CubeMX：工程是怎么生成的")

H2("3.1 CubeMX 建工程的关键步骤")
B("选择芯片 `STM32F103C8Tx`。")
B("SYS → Debug 选 **Serial Wire**（不配可能下载一次后连不上）。")
B("RCC → HSE 选 **Crystal/Ceramic Resonator**（蓝板 8MHz 晶振）。")
B("Clock Configuration：HSE 8MHz → PLL ×9 → SYSCLK 72MHz；APB1 /2 = 36MHz；APB2 /1 = 72MHz。")
B("GPIO：PC13 设为 GPIO_Output，User Label 写 LED。")
B("USART1：Asynchronous，115200，8N1，无流控。")
B("Project Manager：Toolchain 选 MDK-ARM V5，勾选 Copy only necessary library files。")
B("Code Generator：勾选 Keep User Code when re-generating，否则重新生成会覆盖你写的代码。")

H2("3.2 生成的文件结构")
CODE(r'''
Core/
├── Inc/
│   ├── main.h
│   ├── gpio.h
│   ├── usart.h
│   └── stm32f1xx_hal_conf.h
└── Src/
    ├── main.c
    ├── gpio.c
    ├── usart.c
    ├── stm32f1xx_hal_msp.c
    └── stm32f1xx_it.c
Drivers/
├── STM32F1xx_HAL_Driver/
└── CMSIS/
MDK-ARM/
└── demo.uvprojx
''', "CubeMX 生成的典型结构")

H2("3.3 HAL 初始化顺序")
CODE(r'''
HAL_Init();                  // 中断优先级分组、SysTick、HAL 初始化
SystemClock_Config();        // 72MHz
MX_GPIO_Init();
MX_USART1_UART_Init();
/* 用户代码 */
while (1) { ... }
''', "main() 里的初始化顺序")

P("HAL_Init() 必须最先调用；SystemClock_Config() 决定 UART 波特率准不准；"
  "MX_USART1_UART_Init() 内部会调用 HAL_UART_Init()，最终走到 HAL_UART_MspInit() 配置 GPIO 和时钟。")

H2("3.4 HAL 句柄和 MSP")
P("`UART_HandleTypeDef huart1;` 是 HAL 的“设备句柄”，里面保存实例、波特率、状态、回调等。")
P("`HAL_UART_MspInit()` 是 MSP（MCU Support Package）回调，CubeMX 把 GPIO、时钟、NVIC 配置生成在这里。"
  "如果你手动改引脚，要改 `usart.c`/`stm32f1xx_hal_msp.c` 里的配置。")

H2("3.5 本项目常用的 HAL API")
TABLE(["模块", "函数", "作用"], [
    ["GPIO", "HAL_GPIO_WritePin / TogglePin", "写/翻转引脚"],
    ["UART", "HAL_UART_Init", "初始化串口"],
    ["UART", "HAL_UART_Transmit", "阻塞发送"],
    ["UART", "HAL_UART_Receive", "阻塞接收（带超时）"],
    ["UART", "HAL_UART_Receive_IT", "中断接收（升级协议用）"],
    ["FLASH", "HAL_FLASH_Unlock / Lock", "解锁/上锁"],
    ["FLASH", "HAL_FLASHEx_Erase", "按页擦除"],
    ["FLASH", "HAL_FLASH_Program", "按半字编程"],
    ["CRC", "HAL_CRC_Calculate", "CRC32（可选）"],
], widths=[2.6, 7.2, 6.4])

H2("3.6 Keil 关键设置")
B("Options for Target → Target → 勾选 **Use MicroLIB**（printf 重定向需要）。")
B("Options for Target → Debug → 选 **ST-Link Debugger** → Settings → Port 选 SW。")
B("Flash Download → 勾选 **Reset and Run**，下载后自动运行。")
B("生成 bin：`fromelf --bin --output app.bin .\\Objects\\app.axf`。")
B("App 工程：IROM1 起始 `0x08002000`，大小 `0x6000`。")

H2("3.7 HAL 和标准库怎么选")
P("你现在的电子钟用标准库，项目二用 HAL，这是好事：面试可以讲两套的区别。")
TABLE(["对比", "标准库（StdPeriph）", "HAL"], [
    ["抽象层次", "接近寄存器，代码短", "封装更厚，移植性好"],
    ["配置方式", "手写 RCC/GPIO 结构体", "CubeMX 图形化生成"],
    ["中断/回调", "自己写 IRQHandler", "HAL 回调 + MSP"],
    ["适合", "老项目、资源紧张、想懂寄存器", "新项目、跨系列、快速开发"],
], widths=[3.0, 6.6, 6.6])

# =====================================================================
# 第 4 章
# =====================================================================
H1("第 4 章　串口与 printf：从接线到重定向")

H2("4.1 UART 一帧长什么样")
P("本项目使用 USART1：**PA9 = TX，PA10 = RX**，115200、8 数据位、无校验、1 停止位（8N1）。")
CODE(r'''
空闲高 ──┐          ┌── 停止位(高)
         └─ 起始位(低) ─ 8 个数据位(低位先发) ─┘
''', "8N1 的一帧 = 1 起始位 + 8 数据位 + 1 停止位 = 10 位")
TABLE(["波特率", "1 位时间", "1 字节（10 位）时间"], [
    ["9600", "约 104 µs", "约 1.04 ms"],
    ["115200", "约 8.68 µs", "约 86.8 µs"],
], widths=[4.0, 5.5, 6.0])
P("所以 115200 下，一个字节只占 86.8µs。用 `HAL_UART_Receive()` 轮询时，如果主循环里做了耗时操作，"
  "很容易丢字节。教学版单字符命令可以轮询；正式升级协议必须中断/DMA + 缓冲。")

H2("4.2 接线：TX/RX 必须交叉")
CODE(r'''
CH340 TX  ──►  PA10  (USART1_RX)
CH340 RX  ◄──  PA9   (USART1_TX)
CH340 GND ───  GND
''', "正确接线")
NOTE("最常见的坑",
     "接成 CH340 TX→PA9、CH340 RX→PA10（直连）时：PA9（单片机 TX）有波形，"
     "PA10（单片机 RX）没波形，串口助手也收不到任何东西。就是 TX/RX 接反了。", warn=True)
B("板子独立供电时，CH340 的 VCC 不要接。")
B("CH340 电压跳线选 3.3V；至少 GND 必须共地。")
B("串口助手：COM 口选 CH340 对应的口（例如 COM6），不要选蓝牙串口。")
B("发送区用 ASCII/文本，不要勾“HEX 发送”，否则发 `E` 实际发的是 `0x0E`。")

H2("4.3 CubeMX 配置 USART1")
B("Connectivity → USART1 → Mode: Asynchronous。")
B("Baud Rate 115200，Word Length 8 Bits，Parity None，Stop Bits 1，Flow Control None。")
B("NVIC Settings 里勾 USART1 global interrupt（升级协议用；只做 printf 可以先不勾）。")

H2("4.4 printf 重定向代码逐行解析")
CODE(r'''
#include <stdio.h>

extern UART_HandleTypeDef huart1;

int fputc(int ch, FILE *f)
{
    (void)f;
    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, HAL_MAX_DELAY);
    return ch;
}
''', "Keil MicroLIB 下的 printf 重定向")
TABLE(["代码", "解释"], [
    ["#include <stdio.h>", "使用 printf，需要标准输入输出头文件"],
    ["extern UART_HandleTypeDef huart1;", "huart1 定义在 main.c 或 usart.c 里，这里声明外部引用"],
    ["int fputc(int ch, FILE *f)", "C 库把 printf 的每个字符交给 fputc 输出"],
    ["(void)f;", "参数 f 用不到，强转成 void 避免编译警告"],
    ["HAL_UART_Transmit(...)", "把 1 个字节通过 USART1 发出去，HAL_MAX_DELAY 表示一直等到发完"],
    ["return ch;", "返回写入的字符，告诉 C 库成功"],
], widths=[7.0, 9.0])
NOTE("MicroLIB",
     "Keil 的 Options for Target → Target 里必须勾选 Use MicroLIB，否则 printf 可能进半主机（semihosting）卡死。")

H2("4.5 轮询接收与中断接收")
CODE(r'''
uint8_t ch;

while (1)
{
    if (HAL_UART_Receive(&huart1, &ch, 1, 10) == HAL_OK)
    {
        HAL_UART_Transmit(&huart1, &ch, 1, 100);   // 回显
    }
}
''', "轮询接收：最多等 10ms，收到 1 字节就回显")
P("轮询的缺点：主循环被 `HAL_UART_Receive` 阻塞；如果一边收一边擦 Flash，Flash 操作期间会丢字节。"
  "正式 Bootloader 要用 **中断 + 环形缓冲区 + 状态机**，把“收字节”和“处理协议”解耦。")
CODE(r'''
#define RX_BUF_SIZE 512
static uint8_t rx_buf[RX_BUF_SIZE];
static volatile uint16_t rx_head = 0;
static volatile uint16_t rx_tail = 0;

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        uint16_t next = (rx_head + 1) % RX_BUF_SIZE;
        if (next != rx_tail)       // 缓冲区没满
        {
            rx_buf[rx_head] = rx_byte;
            rx_head = next;
        }
        HAL_UART_Receive_IT(&huart1, &rx_byte, 1);  // 重新挂接收
    }
}
''', "中断接收 + 环形缓冲（升级协议的基础，详见第 7 章）")

H2("4.6 用逻辑分析仪看 UART")
B("通道接 PA9（单片机 TX），GND 接板子 GND。")
B("采样率 ≥ 1MHz，触发方式选下降沿。")
B("Logic 2 → Analyzers → UART → 115200、8 数据位、无校验、1 停止位、LSB First。")
B("如果解码出 `Bootloader Start` 或 `0x41 'A'`，说明数据正确；乱码多半是波特率/时钟不对。")
NOTE("波形不是越乱越坏",
     "UART 的数据位本来就长短不一；关键看：空闲高、每组 10 位、位宽一致、停止位为高。")

H2("4.7 串口故障排查表")
TABLE(["现象", "优先检查"], [
    ["串口助手完全没反应", "TX/RX 是否交叉、GND 是否共地、COM 口是否选对、是否被别的软件占用"],
    ["有波形但电脑收不到", "CH340 RX 是否接到 PA9；PA9 是否接到了 CH340 TX（接反）"],
    ["收到乱码", "波特率、HSE 晶振频率、时钟树是否为 72MHz"],
    ["发 E 收到 ?", "串口助手可能勾了 HEX 发送，实际发的是 0x0E；改成 ASCII 发送"],
    ["printf 没输出但 HAL_UART_Transmit 有", "MicroLIB 没勾、fputc 没链接、huart1 未初始化"],
    ["发数据时 PA10 没波形", "CH340 TX 没接到 PA10；或串口助手根本没发出去（看 TX LED）"],
], widths=[6.2, 9.8])

# =====================================================================
# 第 5 章
# =====================================================================
H1("第 5 章　Flash 编程：第 3 课代码逐行解析")

H2("5.1 Flash 的三条铁律")
B("**写之前必须擦**：擦除后是 0xFF，写入只能把 1 变 0，不能把 0 变 1。")
B("**擦除最小单位是页**：F103C8 一页 1KB，不能按字节擦。")
B("**写入单位是半字**：16 位；地址必须半字对齐（偶数地址）。")

H2("5.2 Flash 相关 HAL API")
TABLE(["函数", "作用", "备注"], [
    ["HAL_FLASH_Unlock()", "解锁 Flash", "不调用则擦/写失败"],
    ["HAL_FLASH_Lock()", "上锁", "操作完必须调用"],
    ["HAL_FLASHEx_Erase()", "按页擦除", "PageAddress 必须页对齐"],
    ["HAL_FLASH_Program()", "编程半字", "地址必须半字对齐"],
    ["__IO uint16_t *", "直接读 Flash", "不需要解锁"],
], widths=[5.2, 6.4, 4.4])

H2("5.3 HAL 背后做了什么（寄存器层）")
CODE(r'''
FLASH->KEYR = 0x45670123;       // 解锁钥匙 1
FLASH->KEYR = 0xCDEF89AB;       // 解锁钥匙 2

FLASH->CR |= FLASH_CR_PER;      // 选择页擦除
FLASH->AR  = page_address;      // 页地址
FLASH->CR |= FLASH_CR_STRT;     // 开始擦除
while (FLASH->SR & FLASH_SR_BSY);// 等待忙结束

FLASH->CR |= FLASH_CR_PG;       // 选择编程
*(__IO uint16_t *)addr = data;  // 写半字
while (FLASH->SR & FLASH_SR_BSY);// 等待忙结束
''', "HAL 内部大致做的事情（了解即可）")
P("HAL 只是把这些步骤封装成了函数；面试时能说出 KEYR/CR/AR/SR/BSY，会比只会调 HAL 更加分。")

H2("5.4 擦除函数逐行解析")
CODE(r'''
#define FLASH_TEST_ADDR   0x0800F800U
#define FLASH_TEST_WORDS  8

static void Flash_Test_Erase(void)
{
    FLASH_EraseInitTypeDef erase;
    uint32_t page_error = 0;

    erase.TypeErase   = FLASH_TYPEERASE_PAGES;
    erase.PageAddress = FLASH_TEST_ADDR;
    erase.NbPages     = 1;

    HAL_FLASH_Unlock();

    if (HAL_FLASHEx_Erase(&erase, &page_error) == HAL_OK)
    {
        printf("ERASE OK\r\n");
    }
    else
    {
        printf("ERASE FAIL, page_error=%lu\r\n", page_error);
    }

    HAL_FLASH_Lock();
}
''', "Flash_Test_Erase：擦除测试页")
TABLE(["代码", "解释"], [
    ["FLASH_TEST_ADDR 0x0800F800", "64KB Flash 倒数第二页，1KB 对齐，不会擦到程序"],
    ["FLASH_TEST_WORDS 8", "写 8 个半字 = 16 字节"],
    ["FLASH_EraseInitTypeDef", "HAL 的擦除参数结构体"],
    ["TypeErase = FLASH_TYPEERASE_PAGES", "按页擦除（不是全片擦除）"],
    ["PageAddress", "要擦的页首地址，必须 1KB 对齐"],
    ["NbPages = 1", "只擦 1 页（1KB）"],
    ["HAL_FLASH_Unlock()", "Flash 默认上锁，必须先解锁"],
    ["HAL_FLASHEx_Erase()", "真正执行擦除，返回 HAL_OK / HAL_ERROR"],
    ["page_error", "失败时 HAL 写入出错页地址；成功一般为 0xFFFFFFFF"],
    ["HAL_FLASH_Lock()", "无论成功失败都要重新上锁"],
], widths=[7.0, 9.0])

H2("5.5 写入函数逐行解析")
CODE(r'''
static void Flash_Test_Write(void)
{
    uint16_t data[FLASH_TEST_WORDS] =
    {
        0x1111, 0x2222, 0x3333, 0x4444,
        0x5555, 0x6666, 0x7777, 0x8888
    };
    uint32_t i;
    HAL_StatusTypeDef status = HAL_OK;

    HAL_FLASH_Unlock();

    for (i = 0; i < FLASH_TEST_WORDS; i++)
    {
        status = HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD,
                                   FLASH_TEST_ADDR + i * 2,
                                   data[i]);
        if (status != HAL_OK)
        {
            break;
        }
    }

    HAL_FLASH_Lock();

    if (status == HAL_OK)
    {
        printf("WRITE OK\r\n");
    }
    else
    {
        printf("WRITE FAIL at word %lu\r\n", i);
    }
}
''', "Flash_Test_Write：写 8 个半字")
B("`data` 用 `uint16_t`，因为 F103 编程单位是半字。")
B("地址 `FLASH_TEST_ADDR + i * 2`：每个半字占 2 字节。")
B("`FLASH_TYPEPROGRAM_HALFWORD`：告诉 HAL 写 16 位。")
B("写之前必须先执行 `E` 擦除；否则可能写失败或数据变成旧值 AND 新值。")
B("`status` 失败就 `break`，并打印失败位置，方便定位。")

H2("5.6 读取函数逐行解析")
CODE(r'''
static void Flash_Test_Read(void)
{
    uint32_t i;

    printf("READ:");

    for (i = 0; i < FLASH_TEST_WORDS; i++)
    {
        printf(" %04X", *(__IO uint16_t *)(FLASH_TEST_ADDR + i * 2));
    }

    printf("\r\n");
}
''', "Flash_Test_Read：直接按内存读")
TABLE(["写法", "含义"], [
    ["(__IO uint16_t *)addr", "把地址强制转换成指向 16 位 volatile 数据的指针"],
    ["*(...) ", "取这个地址里的值"],
    ["__IO", "volatile，告诉编译器每次都要真的去内存读，不能优化"],
    ["%04X", "十六进制大写，至少 4 位，不够补 0"],
], widths=[6.0, 10.0])
P("Flash 读取不需要解锁，也不经过 HAL，直接当普通内存读即可。")

H2("5.7 命令解析逐行解析")
CODE(r'''
uint8_t cmd;

printf("\r\nBootloader Start\r\n");
printf("Flash test page: 0x%08X\r\n", FLASH_TEST_ADDR);
printf("Commands: E=erase W=write R=read\r\n");

while (1)
{
    if (HAL_UART_Receive(&huart1, &cmd, 1, 10) == HAL_OK)
    {
        switch (cmd)
        {
            case 'E':
            case 'e':
                Flash_Test_Erase();
                break;

            case 'W':
            case 'w':
                Flash_Test_Write();
                break;

            case 'R':
            case 'r':
                Flash_Test_Read();
                break;

            case '\r':
            case '\n':
                break;

            default:
                printf("? 0x%02X\r\n", cmd);
                break;
        }
    }
}
''', "E/W/R 单字符命令解析")
B("`HAL_UART_Receive` 最多等 10ms；收到 1 字节返回 HAL_OK。")
B("`case 'E': case 'e':` 大小写都支持。")
B("`\\r`/`\\n` 是串口助手“发送新行”带来的，直接忽略。")
B("`default` 打印收到的十六进制，是排查“发 E 却收到 ?”的最好工具：")
CODE(r'''
? 0x0E   → 串口助手在 HEX 发送（E 被当成 0x0E）
? 0x20   → 你发了一个空格
? 0x45   → 真的是字符 E（0x45），检查大小写匹配
''', "default 打印的典型值")

H2("5.8 完整测试流程")
TABLE(["步骤", "发送", "预期输出"], [
    ["1", "E", "ERASE OK"],
    ["2", "R", "READ: FFFF FFFF FFFF FFFF FFFF FFFF FFFF FFFF"],
    ["3", "W", "WRITE OK"],
    ["4", "R", "READ: 1111 2222 3333 4444 5555 6666 7777 8888"],
    ["5", "复位/重新上电", "Bootloader Start ..."],
    ["6", "R", "仍然是 1111 2222 ...（掉电不丢，说明写进 Flash）"],
    ["7", "E → R", "回到全 FFFF"],
], widths=[2.0, 4.5, 9.5])

NOTE("你遇到过的现象",
     "输出里只有 `?` 和 `READ: FFFF...`，没有 `ERASE OK`：说明 E 没被识别，"
     "大概率是串口助手勾了 HEX 发送，实际发的是 0x0E。改成 ASCII 发送，E 就会打印 ERASE OK。", warn=True)

H2("5.9 Flash 常见故障")
TABLE(["现象", "原因/解决"], [
    ["ERASE FAIL", "地址不是页首；没解锁；芯片容量不对；擦到了受保护页"],
    ["WRITE FAIL", "没先擦除；地址不是半字对齐；Flash 没解锁"],
    ["读出来不是写入值", "地址偏移算错；按 uint16_t 读；写入顺序反了"],
    ["擦完程序跑飞", "擦到了代码所在页；测试地址必须放最后"],
    ["复位后数据没了", "写的是 RAM 变量，不是 Flash 地址"],
    ["多字节命令丢字符", "轮询方式只适合单字符；升级协议要中断/DMA"],
], widths=[6.0, 10.0])

H2("5.10 小实验")
B("把 `FLASH_TEST_WORDS` 改成 16，写 32 字节。")
B("把数据改成 `0xA5A5, 0x5A5A...`，观察读回。")
B("故意不擦除直接 `W`，观察 `WRITE FAIL`。")
B("把地址改成 `0x0800F801`（不对齐），观察擦除报错。")

# =====================================================================
# 第 6 章
# =====================================================================
H1("第 6 章　Bootloader：Flash 分区、有效性检查和跳转")

H2("6.1 Bootloader 到底在做什么")
P("Bootloader 是上电后最先运行的一小段程序。它只做四件事：")
B("判断 App 是否有效（栈顶、复位向量、CRC）。")
B("判断有没有升级请求。")
B("有升级请求：通过串口接收固件并写 Flash。")
B("没有升级请求：跳转到 App。")

CODE(r'''
上电/复位
   ↓
Bootloader
   ↓
读取 Config：有升级标志？
   ├─ 有 → 串口升级流程 → 校验 → 更新元数据 → 跳转
   └─ 无 → 检查 App 有效性
            ├─ 有效 → 跳转 App
            └─ 无效 → 停在 Bootloader，等待重新升级
''', "Bootloader 主流程")

H2("6.2 为什么用 A/B 双槽")
P("单槽方案：Bootloader + App + Config。升级时直接擦 App，如果升级失败，旧 App 也没了，只能停在 Bootloader。")
P("双槽方案：Bootloader + Slot A + Slot B + Config。升级时写“非当前槽”，成功后再切换；失败则继续用旧槽，"
  "实现回滚和防变砖。")

TABLE(["方案", "优点", "缺点"], [
    ["单槽", "Flash 利用率高，App 可以做得大", "升级失败旧 App 丢失，只能重刷"],
    ["A/B 双槽", "可回滚、防变砖、升级时不影响旧 App", "每个槽只有一半空间；Bootloader 和 Config 占空间"],
], widths=[3.2, 7.5, 5.3])

P("F103C8 只有 64KB，所以每个槽 24KB。当前 App 10.4KB 够用；如果 App 继续变大，要重新规划或换芯片。")

H2("6.3 App 有效性检查")
P("跳转前必须确认 App 不是空片、不是半包、不是乱码。最少的检查：")
CODE(r'''
#define APP_ADDR       0x08002000U
#define APP_SLOT_SIZE  0x6000U
#define SRAM_START     0x20000000U
#define SRAM_END       0x20005000U

static uint8_t App_IsValid(uint32_t app_addr)
{
    uint32_t msp   = *(uint32_t *)app_addr;
    uint32_t reset = *(uint32_t *)(app_addr + 4);

    /* 1. 栈顶必须落在 SRAM 范围内，且 8 字节对齐 */
    if (msp < SRAM_START || msp > SRAM_END || (msp & 0x7) != 0)
    {
        return 0;
    }

    /* 2. 复位向量必须在 App 槽内，且 Thumb 位为 1 */
    if ((reset & 1) == 0 ||
        reset < app_addr ||
        reset >= app_addr + APP_SLOT_SIZE)
    {
        return 0;
    }

    /* 3. 可选：再算一次 CRC32，和 Config 里的值比较 */
    return 1;
}
''', "App 有效性检查（最小版）")
P("空片时 Flash 全是 0xFF，MSP = 0xFFFFFFFF、reset = 0xFFFFFFFF，第一条就失败，所以不会跳过去。"
  "如果只判断“不等于 0xFFFFFFFF”，不够严谨；按 SRAM 范围和 Thumb 位判断更可靠。")

H2("6.4 跳转代码逐行解析")
CODE(r'''
typedef void (*pFunction)(void);

static void JumpToApp(uint32_t app_addr)
{
    uint32_t msp   = *(uint32_t *)app_addr;
    uint32_t reset = *(uint32_t *)(app_addr + 4);
    pFunction jump = (pFunction)reset;

    __disable_irq();                 // 1. 关总中断
    HAL_DeInit();                    // 2. 复位 HAL 和外设（可选但推荐）
    SysTick->CTRL = 0;               // 3. 关 SysTick
    SysTick->LOAD = 0;
    SysTick->VAL  = 0;
    SCB->VTOR = app_addr;            // 4. 向量表搬到 App
    __set_MSP(msp);                  // 5. 设置主栈指针
    jump();                          // 6. 跳转到 App 的 Reset_Handler
}
''', "跳转函数（核心 6 步）")
TABLE(["步骤", "为什么"], [
    ["__disable_irq()", "跳转过程中如果来中断，向量表还没切过去，可能进错中断/ HardFault"],
    ["HAL_DeInit()", "把 Bootloader 用过的外设、时钟、中断恢复到复位状态，避免影响 App"],
    ["关 SysTick", "HAL_Delay 依赖 SysTick；App 会重新配置，先关掉避免跳转瞬间进中断"],
    ["SCB->VTOR = app_addr", "让 CPU 知道 App 的向量表在哪里"],
    ["__set_MSP(msp)", "把主栈指针切换到 App 的栈顶"],
    ["jump()", "跳到 App 的 Reset_Handler，开始执行 App"],
], widths=[5.2, 10.8])

NOTE("跳转前的清理",
     "只关中断不关外设，App 里重新初始化 UART/GPIO 时可能出现“外设还在忙/标志没清”的问题。"
     "最稳的做法是 HAL_DeInit() + 关闭 SysTick + 清 pending 中断。")

H2("6.5 App 工程怎么改")
B("复制一份 Bootloader 工程，改名 `IAP_App`。")
B("Keil → Options for Target → Target → IROM1：Start `0x08002000`，Size `0x6000`。")
B("App 的 `main()` 开头、`HAL_Init()` 之前或之后设置 `SCB->VTOR = 0x08002000;`。")
B("App 编译生成 `.bin`：`fromelf --bin --output app.bin .\\Objects\\app.axf`。")
B("App 里不要再擦写 Bootloader 所在的 0x08000000 ~ 0x08001FFF。")

CODE(r'''
/* App 的 main() 里，越早越好 */
SCB->VTOR = 0x08002000;

/* 如果 App 用中断，必须确保向量表已经切过来再开中断 */
__enable_irq();
''', "App 设置向量表")

H2("6.6 跳转失败的典型现象")
TABLE(["现象", "可能原因"], [
    ["跳过去就 HardFault", "VTOR 没设、MSP 不对、App 链接地址不对、App 中断向量表不在 0x08002000"],
    ["能跑但不进中断", "VTOR 设错；或者 App 的启动文件/链接地址没改"],
    ["跳到 0xFFFFFFFF", "App 是空片；MSP/reset 检查没做；升级没写进去"],
    ["跑一下就复位", "看门狗/时钟配置冲突；App 的 SystemInit 与 Bootloader 冲突"],
    ["串口输出乱码", "App 的时钟配置和 Bootloader 不一致；HSE 起振失败"],
], widths=[5.5, 10.5])

H2("6.7 本课实验步骤")
B("先让 Bootloader 只做“检查 App + 跳转”，不做串口升级。")
B("App 用第 1 课的 LED 闪灯程序，链接到 0x08002000。")
B("用 ST-Link 分别下载 Bootloader 和 App。")
B("复位，观察 LED 是否由 App 控制闪烁。")
B("在 Bootloader 里把 `APP_ADDR` 改错，观察是否停在 Bootloader（验证有效性检查）。")

# =====================================================================
# 第 7 章
# =====================================================================
H1("第 7 章　串口升级协议：帧、CRC、状态机、上位机")

H2("7.1 为什么不用裸数据")
P("如果电脑直接把 bin 字节流发给单片机，Bootloader 无法知道：")
B("一包从哪里开始、到哪里结束。")
B("这是第几个包、有没有丢包。")
B("总长度多少、CRC 是多少。")
B("收到的是命令还是固件数据。")
P("所以必须定义帧格式：帧头、命令、序号、长度、偏移、数据、校验。")

H2("7.2 帧格式")
TABLE(["字段", "长度", "说明"], [
    ["帧头", "2B", "固定 0xAA 0x55，用来找包起点"],
    ["CMD", "1B", "START/DATA/END/ACK/NAK"],
    ["SEQ", "1B", "包序号，0~255 循环，用来发现丢包/重复"],
    ["LEN", "2B", "DATA 长度，小端"],
    ["OFFSET", "4B", "数据在固件中的偏移，小端"],
    ["DATA", "N B", "固件数据，建议 128/256 字节"],
    ["CRC16", "2B", "对 CMD~DATA 计算，小端"],
], widths=[3.0, 2.2, 11.0])

CODE(r'''
+--------+-----+-----+-------+--------+----------+-------+
| AA 55  | CMD | SEQ |  LEN  | OFFSET |   DATA   | CRC16 |
+--------+-----+-----+-------+--------+----------+-------+
   2B       1B    1B    2B      4B       N B        2B
''', "帧结构")

H2("7.3 命令字")
TABLE(["CMD", "名称", "方向", "作用"], [
    ["0x01", "START", "PC → MCU", "总长度、总 CRC32、版本号；MCU 擦除非当前槽"],
    ["0x02", "DATA", "PC → MCU", "偏移 + 数据；MCU 写入对应地址"],
    ["0x03", "END", "PC → MCU", "结束；MCU 计算整片 CRC32 并校验"],
    ["0x04", "ACK", "MCU → PC", "成功，可带状态/已接收长度"],
    ["0x05", "NAK", "MCU → PC", "失败，PC 重发或中止"],
], widths=[2.2, 3.0, 3.0, 8.0])

H2("7.4 CRC16 与 CRC32")
P("帧内 CRC16 用来保证“这一包数据没坏”；整片 CRC32 用来保证“整个固件没坏”。")
CODE(r'''
/* CRC16-CCITT：poly=0x1021，init=0xFFFF */
uint16_t CRC16_Calc(const uint8_t *data, uint16_t len)
{
    uint16_t crc = 0xFFFF;
    for (uint16_t i = 0; i < len; i++)
    {
        crc ^= (uint16_t)data[i] << 8;
        for (uint8_t b = 0; b < 8; b++)
        {
            if (crc & 0x8000) crc = (crc << 1) ^ 0x1021;
            else              crc <<= 1;
        }
    }
    return crc;
}
''', "CRC16-CCITT 软件实现")
P("整片 CRC32 可以用 STM32F1 的硬件 CRC 外设（HAL_CRC_Calculate），也可以用 Python 的 `zlib.crc32`。"
  "关键是 **PC 和 MCU 必须使用同一种算法、同一个初值、同样的字节序**。")

H2("7.5 Bootloader 状态机")
CODE(r'''
IDLE
  │ 收到 START
  ▼
ERASE ──失败──► ERROR
  │ 成功
  ▼
RECEIVING ──收到 DATA──► 写 Flash ──失败──► ERROR
  │ 收到 END
  ▼
VERIFY ──CRC 不对──► ERROR
  │ CRC 正确
  ▼
DONE ──► 更新元数据 ──► 跳转/复位
''', "升级状态机")

P("状态机的好处：任何时刻都知道自己在等什么，收到意外命令可以回 NAK，不会死等。")

H2("7.6 超时、重传、序号")
B("PC 每发一包，等 ACK；超时（例如 500ms）重发，最多 3 次。")
B("MCU 收到重复 SEQ，直接回 ACK，不重复写 Flash。")
B("OFFSET 必须连续/在范围内，防止写飞。")
B("LEN 不能超过最大包长，也不能超过剩余固件长度。")
B("擦除/写入失败，回 NAK，PC 中止或重试。")

H2("7.7 Bootloader 协议处理骨架")
CODE(r'''
typedef enum {
    UP_IDLE = 0,
    UP_RECEIVING,
    UP_VERIFY,
    UP_ERROR
} UpdateState;

static UpdateState up_state = UP_IDLE;
static uint32_t fw_total_size = 0;
static uint32_t fw_received = 0;
static uint32_t fw_crc32_expect = 0;
static uint32_t fw_crc32_calc = 0xFFFFFFFF;

/* 收到一帧后调用 */
static void Protocol_HandleFrame(const uint8_t *frame, uint16_t frame_len)
{
    uint8_t cmd = frame[2];

    switch (cmd)
    {
        case 0x01:  /* START */
            fw_total_size   = ReadU32LE(&frame[6]);
            fw_crc32_expect = ReadU32LE(&frame[10]);
            fw_received     = 0;
            fw_crc32_calc   = 0xFFFFFFFF;
            Flash_EraseSlot(INACTIVE_SLOT_ADDR, fw_total_size);
            up_state = UP_RECEIVING;
            SendAck(0x01, 0);
            break;

        case 0x02:  /* DATA */
        {
            uint32_t offset = ReadU32LE(&frame[6]);
            uint16_t len    = ReadU16LE(&frame[4]);
            if (offset != fw_received || len > 256) { SendNak(0x02, 1); break; }
            if (Flash_Write(INACTIVE_SLOT_ADDR + offset, &frame[12], len) != 0)
            {
                SendNak(0x02, 2);
                up_state = UP_ERROR;
                break;
            }
            fw_received += len;
            SendAck(0x02, fw_received);
            break;
        }

        case 0x03:  /* END */
            if (fw_received != fw_total_size) { SendNak(0x03, 3); break; }
            fw_crc32_calc = CRC32_CalcSlot(INACTIVE_SLOT_ADDR, fw_total_size);
            if (fw_crc32_calc != fw_crc32_expect) { SendNak(0x03, 4); up_state = UP_ERROR; break; }
            Metadata_SwitchToInactiveSlot();
            SendAck(0x03, 0);
            up_state = UP_IDLE;
            NVIC_SystemReset();
            break;

        default:
            SendNak(cmd, 0xFF);
            break;
    }
}
''', "协议处理骨架（伪代码级，需按实际 Flash 分区补全）")

H2("7.8 Python 上位机骨架")
CODE(r'''
import serial, struct, zlib, time

def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

def frame(cmd, seq, offset, payload):
    body = struct.pack('<BBHI', cmd, seq, len(payload), offset) + payload
    return b'\xAA\x55' + body + struct.pack('<H', crc16(body))

def send_and_wait(ser, pkt, timeout=0.5):
    ser.write(pkt)
    ser.timeout = timeout
    return ser.read(16)

def upload(port, bin_path):
    fw = open(bin_path, 'rb').read()
    ser = serial.Serial(port, 115200, timeout=0.5)
    time.sleep(0.2)
    # START：总长度 + CRC32
    start = struct.pack('<II', len(fw), zlib.crc32(fw) & 0xFFFFFFFF)
    send_and_wait(ser, frame(0x01, 0, 0, start))
    # DATA：256 字节一包
    seq = 0
    for off in range(0, len(fw), 256):
        chunk = fw[off:off+256]
        send_and_wait(ser, frame(0x02, seq, off, chunk))
        seq = (seq + 1) & 0xFF
    # END
    send_and_wait(ser, frame(0x03, seq, len(fw), b''))
    ser.close()
''', "Python 上位机骨架（pyserial）")
NOTE("先跑通再优化",
     "上位机第一版不要做进度条、断点续传、加密；先做到“能完整传完 + CRC 通过 + 跳转”。"
     "等基础稳定后再加超时重传、日志、校验失败重试。")

H2("7.9 安全性（进阶）")
B("CRC32 只能防传输错误，不能防恶意篡改。")
B("需要防篡改时，增加固件签名（ECDSA/RSA）或 AES 加密；Bootloader 验签通过才跳转。")
B("产品里还要考虑：回滚版本号、防降级、密钥存储。")

# =====================================================================
# 第 8 章
# =====================================================================
H1("第 8 章　A/B 双槽、元数据、掉电与回滚")

H2("8.1 元数据放在哪里")
P("Config 区建议放两页（2KB），用两个副本 + 序号，防止写元数据时掉电把唯一副本写坏。")
CODE(r'''
#define CONFIG_ADDR   0x0800E000U
#define CONFIG_MAGIC  0x424F4F54U   /* 'BOOT' */

typedef struct
{
    uint32_t magic;         /* CONFIG_MAGIC */
    uint32_t seq;           /* 每次更新 +1，选择 seq 较大的有效副本 */
    uint32_t active_slot;   /* 0=Slot A, 1=Slot B */
    uint32_t version;       /* 固件版本号 */
    uint32_t fw_size;       /* 固件长度 */
    uint32_t fw_crc32;      /* 固件 CRC32 */
    uint32_t update_flag;   /* 1=请求升级 */
    uint32_t reserved[9];   /* 补齐到 64 字节 */
} BootConfig;
''', "BootConfig 元数据结构")

H2("8.2 升级流程（A/B）")
CODE(r'''
当前运行 Slot A
   ↓
PC 发 START：目标 = 非当前槽（Slot B）
   ↓
擦除 Slot B → 逐包写 Slot B → 整片 CRC32 校验
   ├─ 失败 → Slot A 不变，继续用 A
   └─ 成功 → 写 Config：active_slot=B, seq+1
                ↓
             复位 → Bootloader 选择 Slot B → 跳转
''', "A/B 升级流程")

H2("8.3 掉电场景")
TABLE(["掉电时机", "结果", "下次上电"], [
    ["擦除 Slot B 中", "B 不完整，A 完好", "Config 仍指向 A，继续用旧版"],
    ["写 Slot B 中", "B 不完整，A 完好", "Config 仍指向 A，继续用旧版"],
    ["CRC 校验失败", "B 标记无效", "继续用 A；可重新升级"],
    ["写 Config 中", "旧副本或新副本之一有效", "选择 seq 较大的有效副本"],
    ["跳转后 App 崩溃", "App 自身问题", "看门狗/复位后仍回到 Bootloader，可重新升级"],
], widths=[4.0, 5.5, 6.5])
NOTE("关键原则",
     "先擦/写“非当前槽”，最后一步才改 Config。只要 Config 没改，旧 App 就还在，永远不会因为升级失败而变砖。")

H2("8.4 回滚")
P("回滚不是“把新固件删掉”，而是 **Config 指回旧槽**。旧槽一直保留，直到下一次升级把它覆盖。")
B("升级成功后保留旧槽，不立即擦除。")
B("新 App 启动后如果自检失败，可以写 Config 请求回滚，然后复位。")
B("Bootloader 选择“有效且版本更高”的槽；如果新槽无效，退回旧槽。")

H2("8.5 防变砖 checklist")
B("Bootloader 自己永远不擦除自己。")
B("Config 双副本 + seq。")
B("App 有效性检查（MSP、reset、CRC）。")
B("升级失败不回写 Config。")
B("看门狗：Bootloader 等待升级时喂狗，避免一直复位。")
B("保留恢复入口：上电按住某个按键进入 Bootloader，不跳 App。")

H2("8.6 测试矩阵")
TABLE(["用例", "操作", "预期"], [
    ["正常升级", "A→B，完整传输", "CRC 通过，跳转新 App"],
    ["CRC 错误", "故意改一个字节", "NAK，旧 App 仍可启动"],
    ["传输中断", "传到一半拔 USB-TTL", "复位后旧 App 正常"],
    ["空片", "擦除 App 区", "停在 Bootloader，可重新升级"],
    ["重复升级", "A→B→A→B", "每次都能正常切换"],
    ["非法 App", "写入随机数据", "有效性检查失败，不跳转"],
    ["掉电", "升级中断电", "旧 App 可启动"],
], widths=[3.0, 7.0, 6.0])

# =====================================================================
# 第 9 章
# =====================================================================
H1("第 9 章　调试与测试：串口、Flash、跳转三大故障")

H2("9.1 串口没输出：按顺序排查")
CODE(r'''
A. 串口助手能打开 COM 口吗？
   ├─ 不能 → 被别的软件占用 / 驱动问题
   └─ 能 → B
B. USB-TTL 自环（TX 短接 RX）能收到自己发的字符吗？
   ├─ 不能 → 模块/驱动/串口助手问题
   └─ 能 → C
C. CH340 TX→PA10、RX→PA9、GND→GND，复位后有 Bootloader Start 吗？
   ├─ 没有 → D
   └─ 有 → 正常
D. 代码里直接 HAL_UART_Transmit("HELLO") 有输出吗？
   ├─ 有 → printf 重定向问题（MicroLIB/fputc）
   └─ 没有 → 板子没跑/时钟不对/UART 没初始化
''', "串口故障决策树")
NOTE("实际案例",
     "PA9 有波形、PA10 没波形、串口助手没反应：CH340 的 TX/RX 接成了直连。"
     "PA9 是单片机 TX，应该接 CH340 RX；PA10 是单片机 RX，应该接 CH340 TX。", warn=True)

H2("9.2 逻辑分析仪解码 UART")
B("通道接 PA9/PA10，GND 共地，采样率 ≥ 1MHz。")
B("触发：下降沿；先开始采集，再发数据。")
B("Logic 2 → Analyzers → UART：115200、8 数据位、无校验、1 停止位、LSB First。")
B("解码出 `0x41 'A'` 说明数据正确；乱码查波特率/时钟。")

H2("9.3 Flash 故障")
TABLE(["现象", "排查"], [
    ["ERASE FAIL", "地址是否 1KB 对齐；是否 Unlock；是否擦到代码页"],
    ["WRITE FAIL", "是否先擦除；地址是否半字对齐；是否 Lock 了"],
    ["读回不对", "地址偏移；按 uint16_t 读；写入顺序"],
    ["复位丢失", "写的是 RAM 变量；Flash 地址写错"],
], widths=[5.5, 10.5])

H2("9.4 跳转故障")
TABLE(["现象", "排查"], [
    ["HardFault", "VTOR、MSP、App 链接地址、向量表"],
    ["跳到 0xFFFFFFFF", "App 为空/未写入；有效性检查没做"],
    ["能跑不进中断", "VTOR 没设；App 启动文件没改"],
    ["跑一下就复位", "看门狗；时钟冲突；中断 pending 没清"],
], widths=[5.5, 10.5])

H2("9.5 演示流程（面试/答辩）")
B("上电，App 正常显示/闪灯。")
B("电脑打开上位机，选择 COM 口和 app.bin。")
B("点击升级，显示进度和 CRC 结果。")
B("复位，新 App 运行，版本号变化。")
B("故意传错固件/中途拔线，演示旧 App 仍能启动。")

# =====================================================================
# 第 10 章
# =====================================================================
H1("第 10 章　面试题库：15 个高频问题")

qa = [
    ("为什么 Bootloader 放在 0x08000000？",
     "Cortex-M3 复位后从 0x08000000 取 MSP、从 0x08000004 取 Reset_Handler；Bootloader 必须占据这个默认入口。"),
    ("App 为什么要改链接地址和 VTOR？",
     "App 不在 0x08000000，中断向量表也跟着偏移；链接地址决定代码/向量表位置，VTOR 告诉 CPU 去哪里找向量表。"),
    ("跳转前为什么要关中断、设 MSP、关 SysTick？",
     "防止跳转瞬间进 Bootloader 的中断；MSP 要换成 App 的栈顶；SysTick 是 Bootloader 的时基，App 会重新配置。"),
    ("Flash 写入前为什么必须擦除？",
     "Flash 只能 1→0，不能 0→1；擦除把整页恢复为 0xFF，才能写入新数据。"),
    ("F103C8 的 Flash 页多大？写入单位是什么？",
     "页 1KB；编程单位是半字（16 位）。"),
    ("如何判断 App 是否有效？",
     "检查 MSP 在 SRAM 范围、Reset 向量在 App 槽内且 Thumb 位为 1，再可选做 CRC32 校验。"),
    ("升级中掉电怎么办？",
     "先写非当前槽，最后才改 Config；Config 不改，旧 App 仍有效，不会变砖。"),
    ("A/B 双槽怎么回滚？",
     "Config 记录 active_slot；新槽校验失败就继续用旧槽；成功后才切换 active_slot。"),
    ("CRC16 和 CRC32 分别干什么？",
     "CRC16 校验每一帧数据；CRC32 校验整个固件，防止半包/错包。"),
    ("为什么升级协议要序号和偏移？",
     "序号发现丢包/重复；偏移保证数据写到正确位置，避免错位。"),
    ("为什么正式协议不能用轮询收字节？",
     "115200 下字节间隔 86.8µs，擦 Flash/printf 会阻塞导致丢字节；要用中断/DMA + 环形缓冲 + 状态机。"),
    ("Bootloader 怎么防止擦到自己？",
     "地址范围检查；只擦 App 槽；Bootloader 区永不擦除。"),
    ("HAL 和标准库有什么区别？",
     "HAL 封装更厚、CubeMX 生成、跨系列移植好；标准库更接近寄存器、代码小。两者都要能看懂。"),
    ("如果 App 很大，24KB 槽放不下怎么办？",
     "改单槽 + 外部 SPI Flash 备份；换更大 Flash 的芯片；或压缩固件。"),
    ("怎么证明你的 Bootloader 可靠？",
     "给出测试矩阵：正常升级、CRC 错误、传输中断、掉电、空片、重复升级，并说明每种情况下的恢复结果。"),
]
for i, (q, a) in enumerate(qa, 1):
    H3(f"Q{i}. {q}")
    P(a)

# =====================================================================
# 第 11 章
# =====================================================================
H1("第 11 章　5 天实施计划与验收标准")

TABLE(["天", "任务", "验收"], [
    ["D1", "CubeMX 建 Bootloader 工程；USART1 printf；Flash E/W/R", "串口能打印、能擦写、复位后数据还在"],
    ["D2", "Bootloader 跳 App；App 改 IROM/VTOR；LED 闪灯", "复位后 App 的 LED 闪，Bootloader 不跑飞"],
    ["D3", "升级协议 START/DATA/END；Python 上位机", "能完整传一个 bin，CRC 通过"],
    ["D4", "A/B 双槽；元数据；掉电/CRC 错误测试", "失败时旧 App 仍能启动"],
    ["D5", "演示视频、README、简历更新、面试题", "3 分钟演示 + 测试记录"],
], widths=[1.8, 8.2, 6.0])

H2("验收标准")
B("Bootloader 独立工程，链接 0x08000000，大小 ≤ 8KB。")
B("App 独立工程，链接 0x08002000，大小 ≤ 24KB。")
B("串口 115200 能升级，CRC 校验通过。")
B("升级失败/断电，旧 App 仍可启动。")
B("能讲清楚 VTOR、MSP、Flash 页、CRC、A/B 切换。")
B("有测试记录和演示视频。")

H2("简历写法")
P("做完后，把简历里的“在研”改成“个人项目”，并补实测数据，例如：")
CODE(r'''
基于 HAL 的 STM32 IAP Bootloader 串口升级（个人项目 | 2026.11）
- 设计 Boot(8KB) + Slot A/B(各24KB) + Config(2KB) 的 Flash 分区，
  实现跳转前关中断、HAL_DeInit、SCB->VTOR 重定位和 MSP 切换。
- 实现 UART 帧协议（AA55/CMD/SEQ/LEN/OFFSET/CRC16）与整片 CRC32 校验，
  Python 上位机分片发送固件，升级 10.4KB 固件约 X 秒。
- 实现 A/B 双槽与元数据双副本，CRC 错误/传输中断/掉电测试均可回滚，
  Bootloader 区永不擦除，防止变砖。
''', "简历项目描述模板（把 X 换成实测值）")

# =====================================================================
# 附录
# =====================================================================
H1("附录 A　地址/常量速查")
TABLE(["名称", "值", "说明"], [
    ["Flash 起始", "0x08000000", "Bootloader"],
    ["Slot A", "0x08002000", "App A，24KB"],
    ["Slot B", "0x08008000", "App B，24KB"],
    ["Config", "0x0800E000", "元数据，2KB"],
    ["测试页", "0x0800F800", "第 3 课实验用"],
    ["SRAM", "0x20000000~0x20004FFF", "20KB"],
    ["USART1", "PA9=TX, PA10=RX", "115200 8N1"],
    ["BOOT0", "0", "从 Flash 启动"],
], widths=[3.6, 6.0, 7.0])

H1("附录 B　术语表")
TABLE(["术语", "解释"], [
    ["IAP", "在应用编程：程序自己通过通信接口改 Flash"],
    ["ICP", "在电路编程：用 SWD/JTAG 调试器烧录"],
    ["OTA", "空中升级：通过无线方式下载固件"],
    ["Bootloader", "上电先运行、负责升级和跳转的小程序"],
    ["MSP", "主栈指针，Cortex-M3 复位时从向量表第 0 项加载"],
    ["VTOR", "向量表偏移寄存器，告诉 CPU 向量表在哪里"],
    ["A/B 双槽", "两份 App 分区，升级写非当前槽，失败可回滚"],
    ["CRC", "循环冗余校验，用来发现数据错误"],
], widths=[3.2, 13.2])

H1("附录 C　配套代码索引")
TABLE(["文件", "内容", "对应章节"], [
    ["code/uart_retarget.c", "printf 重定向 fputc", "第 4 章"],
    ["code/flash_ops.c", "Flash 擦除/写入/读取 + E/W/R 命令", "第 5 章"],
    ["code/bootloader_jump.c", "App 有效性检查 + 跳转", "第 6 章"],
    ["code/protocol.h", "帧格式、命令字、CRC16、元数据结构", "第 7/8 章"],
    ["code/host_tool.py", "Python 上位机骨架", "第 7 章"],
], widths=[5.4, 7.2, 3.8])

H1("附录 D　参考资料")
B("ST RM0008：STM32F10xxx 参考手册（Flash、USART、RCC、NVIC）。")
B("ST PM0075：STM32F10xxx Flash 编程手册（页大小、擦写时序）。")
B("ST AN2557：STM32F10xxx in-application programming using the USART。")
B("ST UM1853：STM32F1 HAL 驱动用户手册。")
B("ARM Cortex-M3 权威指南 / Cortex-M3 编程手册（向量表、MSP、VTOR）。")
B("Keil MDK 文档：fromelf、MicroLIB、分散加载。")
B("Python pyserial 文档。")

P("—— 完 ——", size=12, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, before=12)
P("建议：先按第 1～6 章把“能跳转”跑通，再按第 7～8 章把“可靠升级”做完。不要一开始就追求完美协议。",
  size=9.5, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER)

doc.core_properties.title = "STM32 IAP Bootloader 串口升级 学习手册"
doc.core_properties.author = "学习手册"
doc.core_properties.subject = "STM32F103C8T6 / HAL / IAP Bootloader / 串口升级"

doc.save(DOCX_PATH)
print("saved:", DOCX_PATH)

# =====================================================================
# 配套参考代码（不是完整工程，按自己的引脚/分区调整）
# =====================================================================
UART_CODE = r'''#include "main.h"
#include <stdio.h>

extern UART_HandleTypeDef huart1;

/* Keil: Options for Target -> Target -> 勾选 Use MicroLIB */
int fputc(int ch, FILE *f)
{
    (void)f;
    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, HAL_MAX_DELAY);
    return ch;
}
'''

FLASH_CODE = r'''#include "main.h"
#include <stdio.h>

extern UART_HandleTypeDef huart1;

#define FLASH_TEST_ADDR   0x0800F800U
#define FLASH_TEST_WORDS  8

static void Flash_Test_Erase(void)
{
    FLASH_EraseInitTypeDef erase;
    uint32_t page_error = 0;

    erase.TypeErase   = FLASH_TYPEERASE_PAGES;
    erase.PageAddress = FLASH_TEST_ADDR;
    erase.NbPages     = 1;

    HAL_FLASH_Unlock();

    if (HAL_FLASHEx_Erase(&erase, &page_error) == HAL_OK)
        printf("ERASE OK\r\n");
    else
        printf("ERASE FAIL, page_error=%lu\r\n", page_error);

    HAL_FLASH_Lock();
}

static void Flash_Test_Write(void)
{
    uint16_t data[FLASH_TEST_WORDS] =
    {
        0x1111, 0x2222, 0x3333, 0x4444,
        0x5555, 0x6666, 0x7777, 0x8888
    };
    uint32_t i;
    HAL_StatusTypeDef status = HAL_OK;

    HAL_FLASH_Unlock();

    for (i = 0; i < FLASH_TEST_WORDS; i++)
    {
        status = HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD,
                                   FLASH_TEST_ADDR + i * 2,
                                   data[i]);
        if (status != HAL_OK)
            break;
    }

    HAL_FLASH_Lock();

    if (status == HAL_OK)
        printf("WRITE OK\r\n");
    else
        printf("WRITE FAIL at word %lu\r\n", i);
}

static void Flash_Test_Read(void)
{
    uint32_t i;
    printf("READ:");
    for (i = 0; i < FLASH_TEST_WORDS; i++)
        printf(" %04X", *(__IO uint16_t *)(FLASH_TEST_ADDR + i * 2));
    printf("\r\n");
}

/* 放在 main() 的 while(1) 里：
    uint8_t cmd;
    if (HAL_UART_Receive(&huart1, &cmd, 1, 10) == HAL_OK) {
        switch (cmd) {
        case 'E': case 'e': Flash_Test_Erase(); break;
        case 'W': case 'w': Flash_Test_Write(); break;
        case 'R': case 'r': Flash_Test_Read();  break;
        case '\r': case '\n': break;
        default: printf("? 0x%02X\r\n", cmd); break;
        }
    }
*/
'''

JUMP_CODE = r'''#include "stm32f1xx_hal.h"

#define APP_ADDR       0x08002000U
#define APP_SLOT_SIZE  0x6000U
#define SRAM_START     0x20000000U
#define SRAM_END       0x20005000U

typedef void (*pFunction)(void);

uint8_t App_IsValid(uint32_t app_addr)
{
    uint32_t msp   = *(uint32_t *)app_addr;
    uint32_t reset = *(uint32_t *)(app_addr + 4);

    if (msp < SRAM_START || msp > SRAM_END || (msp & 0x7U) != 0U)
        return 0;

    if ((reset & 1U) == 0U ||
        reset < app_addr ||
        reset >= app_addr + APP_SLOT_SIZE)
        return 0;

    return 1;
}

void JumpToApp(uint32_t app_addr)
{
    uint32_t msp   = *(uint32_t *)app_addr;
    uint32_t reset = *(uint32_t *)(app_addr + 4);
    pFunction jump = (pFunction)reset;

    __disable_irq();
    HAL_DeInit();
    SysTick->CTRL = 0;
    SysTick->LOAD = 0;
    SysTick->VAL  = 0;
    SCB->VTOR = app_addr;
    __set_MSP(msp);
    jump();
}
'''

PROTOCOL_H = r'''#ifndef __BOOT_PROTOCOL_H
#define __BOOT_PROTOCOL_H

#include <stdint.h>

#define FRAME_HEAD0      0xAAU
#define FRAME_HEAD1      0x55U

#define CMD_START        0x01U
#define CMD_DATA         0x02U
#define CMD_END          0x03U
#define CMD_ACK          0x04U
#define CMD_NAK          0x05U

#define MAX_PAYLOAD      256U

#define CONFIG_ADDR      0x0800E000U
#define CONFIG_MAGIC     0x424F4F54U  /* 'BOOT' */

typedef struct
{
    uint32_t magic;
    uint32_t seq;
    uint32_t active_slot;   /* 0=Slot A, 1=Slot B */
    uint32_t version;
    uint32_t fw_size;
    uint32_t fw_crc32;
    uint32_t update_flag;
    uint32_t reserved[9];
} BootConfig;

uint16_t CRC16_Calc(const uint8_t *data, uint16_t len);
uint32_t CRC32_Calc(const uint8_t *data, uint32_t len);

#endif
'''

HOST_CODE = r'''#!/usr/bin/env python3
# 参考上位机骨架：pip install pyserial
import argparse, struct, sys, time, zlib
import serial


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def make_frame(cmd: int, seq: int, offset: int, payload: bytes) -> bytes:
    body = struct.pack('<BBHI', cmd, seq, len(payload), offset) + payload
    return b'\xAA\x55' + body + struct.pack('<H', crc16(body))


def transact(ser, pkt: bytes, timeout=0.5) -> bytes:
    ser.timeout = timeout
    ser.write(pkt)
    return ser.read(32)


def upload(port: str, bin_path: str):
    fw = open(bin_path, 'rb').read()
    ser = serial.Serial(port, 115200, timeout=0.5)
    time.sleep(0.2)

    # START: 总长度 + CRC32
    payload = struct.pack('<II', len(fw), zlib.crc32(fw) & 0xFFFFFFFF)
    print('START:', transact(ser, make_frame(0x01, 0, 0, payload)).hex())

    # DATA: 256 字节一包
    seq = 0
    for off in range(0, len(fw), 256):
        chunk = fw[off:off + 256]
        pkt = make_frame(0x02, seq, off, chunk)
        print('DATA', off, transact(ser, pkt).hex())
        seq = (seq + 1) & 0xFF

    # END
    print('END:', transact(ser, make_frame(0x03, seq, len(fw), b'')).hex())
    ser.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True, help='例如 COM6')
    ap.add_argument('--bin', required=True, help='app.bin')
    args = ap.parse_args()
    upload(args.port, args.bin)
'''

with open(os.path.join(CODE_DIR, "uart_retarget.c"), "w", encoding="utf-8") as f:
    f.write(UART_CODE)
with open(os.path.join(CODE_DIR, "flash_ops.c"), "w", encoding="utf-8") as f:
    f.write(FLASH_CODE)
with open(os.path.join(CODE_DIR, "bootloader_jump.c"), "w", encoding="utf-8") as f:
    f.write(JUMP_CODE)
with open(os.path.join(CODE_DIR, "protocol.h"), "w", encoding="utf-8") as f:
    f.write(PROTOCOL_H)
with open(os.path.join(CODE_DIR, "host_tool.py"), "w", encoding="utf-8") as f:
    f.write(HOST_CODE)

README = '''STM32 IAP Bootloader 学习包
============================

内容：
1. STM32_IAP_Bootloader_学习手册.docx
   - 项目总览、Flash/启动/向量表、HAL/CubeMX、串口/printf
   - 第 3 课 Flash 代码逐行解析
   - Bootloader 跳转、升级协议、A/B 回滚、调试、面试题、5 天计划

2. code/
   - uart_retarget.c      printf 重定向 fputc
   - flash_ops.c          Flash 擦除/写入/读取 + E/W/R 命令
   - bootloader_jump.c    App 有效性检查 + 跳转
   - protocol.h           帧格式、命令字、CRC16、元数据结构
   - host_tool.py         Python 上位机骨架（需要 pyserial）

注意：
- 这些是参考模板，不是完整可编译工程；请按自己的引脚、时钟、Flash 分区调整。
- 先跑通第 1~6 章（点灯、串口、Flash、跳转），再做第 7~8 章（协议、A/B）。
- Bootloader 和 App 必须两个独立工程；App 的 IROM 起始地址要改到 0x08002000。
- 烧录/升级前备份自己的工程，避免擦错 Flash 页。
'''
with open(os.path.join(OUT_DIR, "README.txt"), "w", encoding="utf-8") as f:
    f.write(README)

print("package dir:", OUT_DIR)





