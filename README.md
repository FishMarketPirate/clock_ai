# clock_ai

基于 STM32F103C8T6 的多功能电子时钟 + IAP 串口升级 Bootloader。

## 功能

- **APP**（标准外设库，链接 `0x08003000`）
  - RTC 走时、DHT11 温湿度、OLED 显示
  - 按键 + 旋转编码器设置时间/闹钟，闹钟经 BKP 掉电保存，蜂鸣器响铃
  - MPU6050 姿态检测：翻转识别后 OLED 旋转 180° 并切换传感器页
  - 状态机 + OLEDShow 分层、非阻塞按键检测
- **BOOT**（HAL / CubeMX，12KB，`0x08000000`）
  - 2.5 秒启动窗口，串口接收固件
  - Flash 页擦除、半字编程、写后读回校验
  - AA55 帧协议（CMD/SEQ/LEN/OFFSET + CRC16）、整片 CRC32、ACK/NAK
  - 跳转前关中断、HAL_DeInit、关 SysTick、重定位 VTOR、切换 MSP

> A/B 双槽、Config 元数据双副本与失败回滚正在实现中。

## Flash 分区

| 区域 | 起始地址 | 大小 | 说明 |
|---|---|---|---|
| Bootloader | `0x08000000` | 12KB | 升级逻辑，不擦除 |
| Slot A | `0x08003000` | 24KB | 当前 App |
| Slot B | `0x08009000` | 24KB | 预留（A/B） |
| Config | `0x0800F000` | 2KB | 预留（元数据） |

## 目录结构

```
APP/        Keil 标准库工程（智能时钟）
BOOT/       Keil HAL 工程（CubeMX 生成的 Bootloader）
upload.py   Python 上位机（串口升级）
iap_test.py 协议测试脚本
```

## 硬件

- STM32F103C8T6 最小系统板
- SSD1306 OLED（I2C，PB8/PB9）
- DHT11（单总线）、MPU6050（I2C，PB10/PB11）
- 旋转编码器、按键、蜂鸣器
- USB-TTL（PA9/PA10，115200 8N1）、ST-Link

## 编译与烧录

1. 用 Keil MDK 打开 `APP/project.uvprojx` 和 `BOOT/MDK-ARM/demo.uvprojx`；
2. 先烧录 BOOT 到 `0x08000000`，再烧录 APP 到 `0x08003000`（APP 的 IROM1 已配置为 `0x08003000`，大小 `0x6000`）；
3. 调试串口：PA9(TX)/PA10(RX)，115200 8N1。

> `APP/Objects/`、`BOOT/MDK-ARM/demo/` 等编译产物不在仓库中，需本地编译生成。

## 串口升级

```bash
py -3 -m pip install pyserial
py -3 upload.py COM6 APP/Objects/project.bin
```

运行脚本后，如果板子还在运行 App，在 10 秒内按一次复位键，脚本会自动发送 START 进入升级模式；升级完成后板子自动复位运行新固件。

## 协议摘要

请求帧：

```
AA 55 | CMD | SEQ | LEN(2,LE) | OFFSET(4,LE) | DATA[LEN] | CRC16(2,LE)
```

- `CMD`：`0x01 START` / `0x02 DATA` / `0x03 END`
- `CRC16`：CRC16-CCITT（poly `0x1021`，init `0xFFFF`，不反射），覆盖 `CMD..DATA`
- `CRC32`：与 Python `zlib.crc32` 一致，用于整片固件校验
- 应答帧：`AA 55 | CMD(0x04=ACK/0x05=NAK) | SEQ | STATUS | CRC16`

## 状态

- [x] Boot + App 分区、串口升级、CRC32 校验、跳转
- [x] Python 上位机（自动进 Boot、重传、进度、CRC 对拍）
- [ ] A/B 双槽切换与回滚
- [ ] Config 元数据双副本
