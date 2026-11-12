#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 5 课：整包升级 + END CRC32 校验
用法: py -3 iap_test.py COM6 [bin路径]
"""
import re, struct, sys, time, zlib
import serial

DEFAULT_BIN = r"D:\STM32_Project\clock+AI\APP\Objects\project.bin"
PACKET = 256

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

def make_frame(cmd, seq, offset, payload=b''):
    body = struct.pack('<BBHI', cmd, seq, len(payload), offset) + payload
    return b'\xAA\x55' + body + struct.pack('<H', crc16(body))

def wait_resp(ser, timeout=1.5, echo=False):
    buf = b''
    t0 = time.time()
    while time.time() - t0 < timeout:
        b = ser.read(1)
        if not b:
            continue
        buf += b
        i = buf.find(b'\xAA\x55')
        if i >= 0 and len(buf) - i >= 7:
            pkt = buf[i:i+7]
            body = pkt[2:5]
            if echo:
                for t in re.findall(rb'[\x20-\x7E]{4,}', buf[:i]):
                    print('        MCU:', t.decode('ascii', 'replace').strip())
            return {'cmd': body[0], 'seq': body[1], 'status': body[2],
                    'crc_ok': crc16(body) == struct.unpack('<H', pkt[5:7])[0]}
    if echo:
        for t in re.findall(rb'[\x20-\x7E]{4,}', buf):
            print('        MCU:', t.decode('ascii', 'replace').strip())
    return None

def upload(ser, data, label, expected_crc):
    print('\n===== %s：%d 字节 =====' % (label, len(data)))
    ser.reset_input_buffer()
    ser.write(make_frame(0x01, 0, 0, struct.pack('<II', len(data), expected_crc)))
    r = wait_resp(ser, 3.0, echo=True)
    print('START ->', r)
    if not r or r['cmd'] != 0x04 or r['status'] != 0:
        print('START 失败，中止')
        return False

    seq = 1
    t0 = time.time()
    for off in range(0, len(data), PACKET):
        chunk = data[off:off+PACKET]
        ser.write(make_frame(0x02, seq, off, chunk))
        r = wait_resp(ser, 1.5)
        if not r or r['cmd'] != 0x04 or r['status'] != 0:
            print('DATA off=%d seq=%d 失败: %r' % (off, seq, r))
            return False
        seq = (seq + 1) & 0xFF
        if (off // PACKET) % 8 == 0:
            print('  ... %d/%d  (%.2fs)' % (off + len(chunk), len(data), time.time() - t0))

    ser.write(make_frame(0x03, seq, len(data), b''))
    r = wait_resp(ser, 2.0, echo=True)
    print('END ->', r)
    return r

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else 'COM6'
    path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BIN
    fw = open(path, 'rb').read()
    crc = zlib.crc32(fw) & 0xFFFFFFFF
    print('固件: %s   %d 字节   crc32=0x%08X' % (path, len(fw), crc))

    ser = serial.Serial(port, 115200, timeout=0.05)
    time.sleep(0.2); ser.reset_input_buffer()

    # 负测试：最后一个字节改坏，START 仍带正确 CRC32 → END 应 NAK 0x0C
    bad = bytearray(fw); bad[-1] ^= 0xFF
    upload(ser, bytes(bad), '负测试：改坏最后一个字节', crc)
    time.sleep(0.3)

    # 正测试：真实固件 → 应 ACK + 复位
    r = upload(ser, fw, '正测试：真实固件', crc)
    if r and r['cmd'] == 0x04 and r['status'] == 0:
        print('\nEND ACK，等板子复位（2.5s 窗口后跳 App）...')
        time.sleep(4.0)
        raw = ser.read(ser.in_waiting) if ser.in_waiting else b''
        print('复位后的串口输出：')
        for t in re.findall(rb'[\x20-\x7E]{4,}', raw):
            print('   ', t.decode('ascii', 'replace').strip())
    ser.close()

if __name__ == '__main__':
    main()