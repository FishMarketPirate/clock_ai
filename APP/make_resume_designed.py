# -*- coding: utf-8 -*-
"""生成设计版嵌入式软件实习简历（蓝色版式，一页）"""
import os
import tempfile
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image, ImageDraw, ImageFont

DOC_PATH = os.environ.get("RESUME_OUT", "嵌入式软件实习简历（设计版）.docx")
PHOTO_PATH = os.path.join(tempfile.gettempdir(), "resume_photo_placeholder.png")

BLUE = "1F5C99"
BLUE2 = "2E75B6"
LIGHT = "DEEBF7"
DARK = "17375E"
TEXT = "333333"
GRAY = "666666"

CJK_FONT = "微软雅黑"
ASCII_FONT = "Arial"


def set_run(run, size=9.5, bold=False, color=TEXT, east=CJK_FONT, ascii_font=ASCII_FONT):
    run.font.name = ascii_font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), east)
    rFonts.set(qn("w:ascii"), ascii_font)
    rFonts.set(qn("w:hAnsi"), ascii_font)


def fmt(p, before=0, after=1.2, line=1.18, align=None, left=0, first=0):
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if align is not None:
        p.alignment = align
    if left:
        pf.left_indent = Cm(left)
    if first:
        pf.first_line_indent = Cm(first)


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def cell_no_border(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tcPr.append(borders)


def table_setup(table, width_cm, cell_borders=True):
    table.autofit = False
    table.alignment = 1  # center
    for col in table.columns:
        col.width = Cm(width_cm / len(table.columns))
    for row in table.rows:
        for cell in row.cells:
            cell.width = Cm(width_cm / len(table.columns))
            if cell_borders:
                cell_no_border(cell)


def cell_margins(cell, top=0.02, bottom=0.02, left=0.12, right=0.12):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for name, value in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        el = OxmlElement("w:" + name)
        el.set(qn("w:w"), str(int(value * 567)))
        el.set(qn("w:type"), "dxa")
        tcMar.append(el)
    tcPr.append(tcMar)


def set_row_height(row, height):
    row.height = Cm(height)
    row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST


def section_banner(doc, text):
    table = doc.add_table(rows=1, cols=1)
    table_setup(table, 17.8)
    cell = table.cell(0, 0)
    shade(cell, BLUE2)
    cell_margins(cell, 0.05, 0.05, 0.16, 0.1)
    set_row_height(table.rows[0], 0.58)
    p = cell.paragraphs[0]
    fmt(p, after=0, line=1.0)
    r1 = p.add_run("▌ ")
    set_run(r1, size=10.5, bold=True, color="BDD7EE")
    r2 = p.add_run(text)
    set_run(r2, size=11, bold=True, color="FFFFFF")
    gap = doc.add_paragraph()
    gap.paragraph_format.space_before = Pt(0)
    gap.paragraph_format.space_after = Pt(0)
    gap.paragraph_format.line_spacing = Pt(2)
    set_run(gap.add_run(" "), size=1)


def body_bullet(doc, text, bold_prefix=None, indent=0.4):
    p = doc.add_paragraph()
    fmt(p, after=1.2, left=indent, first=-indent)
    marker = p.add_run("▸ ")
    set_run(marker, size=10, bold=True, color=BLUE2)
    if bold_prefix:
        r = p.add_run(bold_prefix)
        set_run(r, size=10, bold=True, color=DARK)
    r = p.add_run(text)
    set_run(r, size=9.5)
    return p


def project_title(doc, title, date):
    p = doc.add_paragraph()
    fmt(p, before=2.5, after=1.2)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(17.8), WD_TAB_ALIGNMENT.RIGHT)
    r = p.add_run(title)
    set_run(r, size=11, bold=True, color=DARK)
    r = p.add_run("\t" + date)
    set_run(r, size=8.5, color=GRAY)


def make_photo(path):
    w, h = 320, 400
    img = Image.new("RGB", (w, h), (238, 243, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(180, 199, 231), width=5)
    try:
        f1 = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 40)
        f2 = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 16)
    except Exception:
        f1 = f2 = ImageFont.load_default()

    def center(text, font, y, fill):
        box = d.textbbox((0, 0), text, font=font)
        d.text(((w - (box[2] - box[0])) / 2, y), text, font=font, fill=fill)

    center("照片", f1, 150, (120, 140, 165))
    center("替换为证件照", f2, 210, (150, 165, 185))
    img.save(path, "PNG")


# ================= 文档 =================
doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(1.2)
sec.bottom_margin = Cm(1.0)
sec.left_margin = Cm(1.6)
sec.right_margin = Cm(1.6)

normal = doc.styles["Normal"]
normal.font.name = ASCII_FONT
normal.font.size = Pt(10)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), CJK_FONT)
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(1.2)
normal.paragraph_format.line_spacing = 1.18

# ---------- 顶部蓝条 ----------
header = doc.add_table(rows=1, cols=1)
table_setup(header, 17.8)
hc = header.cell(0, 0)
shade(hc, BLUE)
cell_margins(hc, 0.14, 0.12, 0.3, 0.3)
set_row_height(header.rows[0], 1.35)
p = hc.paragraphs[0]
fmt(p, after=0, line=1.0)
r = p.add_run("求职简历")
set_run(r, size=22, bold=True, color="FFFFFF")
r = p.add_run("    PERSONAL RESUME")
set_run(r, size=8.5, color="D6E4F5")
p2 = hc.add_paragraph()
fmt(p2, before=1, after=0, line=1.0)
r = p2.add_run("嵌入式软件 / 单片机开发 · 2027 届毕业生")
set_run(r, size=8.5, color="D6E4F5")

# 浅蓝细线
strip = doc.add_table(rows=1, cols=1)
table_setup(strip, 17.8)
sc = strip.cell(0, 0)
shade(sc, LIGHT)
cell_margins(sc, 0, 0, 0, 0)
set_row_height(strip.rows[0], 0.1)
fmt(sc.paragraphs[0], after=0, line=1.0)
set_run(sc.paragraphs[0].add_run(" "), size=1)

# ---------- 基本信息 ----------
section_banner(doc, "基本信息")
make_photo(PHOTO_PATH)

outer = doc.add_table(rows=1, cols=2)
outer.autofit = False
for col, w in zip(outer.columns, (14.5, 3.3)):
    col.width = Cm(w)
left, right = outer.cell(0, 0), outer.cell(0, 1)
left.width, right.width = Cm(14.5), Cm(3.3)
for c in (left, right):
    cell_no_border(c)
cell_margins(left, 0.02, 0.02, 0, 0.15)
cell_margins(right, 0.02, 0.02, 0.15, 0)
right.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

def info_line(cell, l1, v1, l2, v2):
    """一行两组“标签 + 值”，列位置固定"""
    p = cell.paragraphs[0] if not cell.paragraphs[0].text else cell.add_paragraph()
    fmt(p, after=1.0, line=1.25)
    ts = p.paragraph_format.tab_stops
    for tab in (2.9, 8.1, 10.7):
        ts.add_tab_stop(Cm(tab))
    for text, is_label in ((l1, True), (v1, False), (l2, True), (v2, False)):
        if is_label:
            r = p.add_run(text if text is l1 else "\t" + text)
            set_run(r, size=9, bold=True, color=BLUE)
        else:
            r = p.add_run("\t" + text)
            set_run(r, size=9, color=TEXT)
    return p

# 第一行
info_line(left, "姓名：", "【姓名】", "学历：", "本科（2027 届）")
info_line(left, "电话：", "【138-XXXX-XXXX】", "邮箱：", "【xxxx@xx.com】")
info_line(left, "求职意向：", "嵌入式软件 / 单片机开发", "意向城市：", "南京/苏州/无锡/深圳")
info_line(left, "GitHub：", "【github.com/xxx】", "可实习：", "立即到岗，长期实习")

photo_p = right.paragraphs[0]
fmt(photo_p, after=0, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
photo_p.add_run().add_picture(PHOTO_PATH, width=Cm(2.9))

# ---------- 自我评价 ----------
section_banner(doc, "自我评价")
body_bullet(doc, "有完整软硬件项目经验，习惯用串口日志、波形与时序定位问题，能独立排查通信类故障。")
body_bullet(doc, "C 语言基础扎实，熟悉 STM32 外设开发流程，正在深入 Bootloader/IAP 与通信协议。")

# ---------- 教育背景 ----------
section_banner(doc, "教育背景")
p = doc.add_paragraph()
fmt(p, after=1.2)
p.paragraph_format.tab_stops.add_tab_stop(Cm(17.8), WD_TAB_ALIGNMENT.RIGHT)
r = p.add_run("宿迁学院")
set_run(r, size=11, bold=True, color=DARK)
r = p.add_run("　软件工程　本科")
set_run(r, size=9.5)
r = p.add_run("　CET-4 已通过")
set_run(r, size=8.5, color=GRAY)
r = p.add_run("\t2023.09 – 2027.06")
set_run(r, size=8.5, color=GRAY)
body_bullet(doc, "C/C++ 程序设计、数据结构、计算机组成原理、操作系统、计算机网络、数据库原理", "主修课程：")

# ---------- 项目经历 ----------
section_banner(doc, "项目经历")
project_title(doc, "基于 STM32 的多功能电子时钟", "个人项目 | 2026.09 – 至今")
body_bullet(doc, "独立完成 RTC 走时、DHT11 温湿度、OLED 显示、按键+旋转编码器设置时间/闹钟，闹钟经 BKP 掉电保存、蜂鸣器响铃；采用状态机 + OLEDShow 分层与非阻塞边沿检测。")
body_bullet(doc, "修复时区偏差 8 小时、RTC 计数器进位竞态、LSE 不起振死锁（超时回退 LSI）等问题；Keil 0 error/0 warning，ROM 10.2KB、RAM 1.7KB。")
body_bullet(doc, "集成 MPU6050 姿态检测：滑动平均 + 连续确认实现翻转识别，翻转后 OLED 旋转 180° 并切换传感器页；时间/温湿度/传感器页分级刷新，降低 I2C 负载。")

project_title(doc, "基于 HAL 的 STM32 IAP Bootloader 串口升级", "个人项目（进行中） | 2026.11 – 至今")
body_bullet(doc, "设计 Boot(12KB) + Slot A/B(各 24KB) + Config(2KB) 分区，App 链接 0x08003000；跳转前关中断、HAL_DeInit、关 SysTick、重定位 SCB->VTOR 并切换 MSP。")
body_bullet(doc, "实现 AA55 帧协议（CMD/SEQ/LEN/OFFSET + CRC16-CCITT）、256B 分片、整片 CRC32 校验与 ACK/NAK 状态机；Python 上位机支持自动进 Boot、超时重传、进度与 CRC 对拍。")
body_bullet(doc, "实现 1KB 页擦除、半字编程与写后读回校验；处理 Boot 8KB 溢出（扩至 12KB）、App 链接地址与 VTOR 重定位、PC/MCU CRC32 参数一致性等问题；正在实现 Config 双副本与 A/B 回滚。")

# ---------- 专业技能 ----------
section_banner(doc, "专业技能")
body_bullet(doc, "C（指针、结构体、位操作、内存管理）；Python（上位机脚本）；了解 C++", "编程语言：")
body_bullet(doc, "STM32F103 标准库，GPIO/EXTI/RTC/BKP/定时器/I2C/单总线；HAL/CubeMX（IAP、Flash、USART）", "嵌入式开发：")
body_bullet(doc, "UART/I2C/SPI、自定义帧协议（AA55/CRC16/CRC32）", "通信/协议：")
body_bullet(doc, "Keil MDK、ST-Link、逻辑分析仪、万用表、Git；能看原理图与时序，习惯用串口日志定位问题", "调试/工具：")

# ---------- 荣誉奖项 ----------
section_banner(doc, "荣誉奖项")
body_bullet(doc, "蓝桥杯全国软件和信息技术专业人才大赛　C/C++ 大学 B 组　省赛三等奖")

doc.core_properties.title = "嵌入式软件实习简历（设计版）"
doc.core_properties.author = "【姓名】"
doc.save(DOC_PATH)

try:
    os.remove(PHOTO_PATH)
except OSError:
    pass
print("saved:", DOC_PATH)
