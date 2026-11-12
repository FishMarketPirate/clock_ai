#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在现有简历 docx 上做内容替换，保留原有版式与图片。"""
import copy
import sys

from docx import Document
from docx.text.paragraph import Paragraph


def find_para(doc, prefix):
    for p in doc.paragraphs:
        if p.text.strip().startswith(prefix):
            return p
    raise RuntimeError("paragraph not found: " + prefix)


def set_bullet_text(p, text):
    """保留第一个 '▸ ' run 的格式，替换正文 run，删除多余 run。"""
    runs = p.runs
    if len(runs) >= 2:
        runs[1].text = text
        for r in runs[2:]:
            r._r.getparent().remove(r._r)
    else:
        runs[0].text = text


def main():
    path = sys.argv[1]
    doc = Document(path)

    # 1) 自我评价第二行
    set_bullet_text(find_para(doc, "▸ C 语言基础扎实"),
                    "C 语言基础扎实，熟悉 STM32 外设开发流程，正在深入 Bootloader/IAP 与通信协议。")

    # 2) 项目一：标题、修复项、MPU6050；删除 ESP8266 那条
    p = find_para(doc, "基于 STM32 + ESP8266")
    p.runs[0].text = "基于 STM32 的多功能电子时钟"

    set_bullet_text(find_para(doc, "▸ 修复时区偏差"),
                    "修复时区偏差 8 小时、RTC 进位竞态、LSE 不起振死锁（超时回退 LSI）；Keil 0 error/0 warning，ROM 10.2KB、RAM 1.7KB。")

    set_bullet_text(find_para(doc, "▸ 通过 AstrBot"),
                    "集成 MPU6050 姿态检测：滑动平均 + 连续确认识别翻转，翻转后 OLED 旋转 180° 并切换传感器页。")

    esp = find_para(doc, "▸ 正在实现 ESP8266")
    esp._p.getparent().remove(esp._p)

    # 3) 项目二：标题状态 + 三条 bullet
    p2 = find_para(doc, "基于 HAL 的 STM32 IAP Bootloader")
    p2.runs[2].text = "个人项目（进行中） | 2026.11 – 至今"

    b1 = find_para(doc, "▸ 设计 Boot + App 双区")
    set_bullet_text(b1,
                    "设计 Boot(12KB)+Slot A/B(24KB)+Config(2KB) 分区，App 链接 0x08003000；跳转前关中断、HAL_DeInit、重定位 VTOR 并切换 MSP。")

    b2 = find_para(doc, "▸ 实现 UART 升级协议")
    set_bullet_text(b2,
                    "实现 AA55 帧协议、256B 分片、整片 CRC32 与 ACK/NAK；Python 上位机自动进 Boot、重传、进度与 CRC 对拍。")

    new_el = copy.deepcopy(b2._p)
    b2._p.addnext(new_el)
    new_p = Paragraph(new_el, b2._parent)
    set_bullet_text(new_p,
                    "实现 1KB 页擦除/半字编程/写后读回；处理 Boot 8KB 溢出、App 地址与 VTOR、CRC32 一致性；正在做 Config 与 A/B 回滚。")

    # 4) 技能
    set_bullet_text(find_para(doc, "▸ 编程语言"),
                    "C（指针、结构体、位操作、内存管理）；Python（上位机脚本）；了解 C++")
    set_bullet_text(find_para(doc, "▸ 嵌入式开发"),
                    "STM32F103 标准库，GPIO/EXTI/RTC/BKP/定时器/I2C/单总线；HAL/CubeMX（IAP、Flash、USART）")
    p3 = find_para(doc, "▸ 通信/物联网")
    p3.runs[1].text = "通信/协议："
    p3.runs[2].text = "UART/I2C/SPI、自定义帧协议（AA55/CRC16/CRC32）"

    doc.save(path)
    print("saved:", path)


if __name__ == "__main__":
    main()
