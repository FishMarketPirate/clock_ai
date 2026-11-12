#include "iap.h"
#include <stdio.h>
#include <string.h>

extern UART_HandleTypeDef huart1;

#define IAP_BYTE_TIMEOUT   200u                  /* 帧内单字节超时(ms) */
#define IAP_RX_BUF_LEN     (12u + IAP_MAX_DATA)  /* AA55 + 8 头 + 数据 + 2 CRC */

static uint8_t iap_rx[IAP_RX_BUF_LEN];

#define SLOT_A_ADDR      0x08003000u
#define SLOT_A_SIZE      0x6000u
#define IAP_FLASH_PAGE   0x400u

static uint8_t  iap_started     = 0u;   /* 1=已收到合法 START */
static uint32_t fw_size         = 0u;
static uint32_t fw_crc32_expect = 0u;
static uint32_t fw_received     = 0u;   /* 第 4 课才会用 */



/* CRC16-CCITT: poly=0x1021, init=0xFFFF, 不反射, 不取反 */
uint16_t IAP_CRC16(const uint8_t *p, uint32_t len)
{
    uint16_t crc = 0xFFFFu;
    uint32_t i;
    uint8_t  b;

    for (i = 0; i < len; i++)
    {
        crc ^= (uint16_t)p[i] << 8;
        for (b = 0; b < 8u; b++)
        {
            if (crc & 0x8000u)
                crc = (uint16_t)((crc << 1) ^ 0x1021u);
            else
                crc = (uint16_t)(crc << 1);
        }
    }
    return crc;
}

/* CRC32: 与 Python zlib.crc32 完全一致
   poly=0xEDB88320(反射), init=0xFFFFFFFF, xorout=0xFFFFFFFF */
static uint32_t IAP_CRC32(const uint8_t *p, uint32_t len)
{
    uint32_t crc = 0xFFFFFFFFu;
    uint32_t i;
    uint8_t  b;

    for (i = 0; i < len; i++)
    {
        crc ^= (uint32_t)p[i];
        for (b = 0; b < 8u; b++)
        {
            if (crc & 1u)
                crc = (crc >> 1) ^ 0xEDB88320u;
            else
                crc >>= 1;
        }
    }
    return crc ^ 0xFFFFFFFFu;
}
/* 发应答帧: AA 55 | CMD | SEQ | STATUS | CRC16 */
static void IAP_SendResp(uint8_t cmd, uint8_t seq, uint8_t status)
{
    uint8_t  tx[7];
    uint16_t crc;

    tx[0] = 0xAAu;
    tx[1] = 0x55u;
    tx[2] = cmd;
    tx[3] = seq;
    tx[4] = status;

    crc   = IAP_CRC16(&tx[2], 3u);
    tx[5] = (uint8_t)(crc & 0xFFu);//低位
    tx[6] = (uint8_t)(crc >> 8);//高位

    HAL_UART_Transmit(&huart1, tx, 7u, 100u);
}

static uint8_t IAP_WaitByte(uint8_t *b, uint32_t timeout)
{
    return (HAL_UART_Receive(&huart1, b, 1u, timeout) == HAL_OK) ? 1u : 0u;
}

/* 收一帧完整请求: 返回 1=有效帧(CRC 已校验), 0=没收到/无效 */
static uint8_t IAP_RecvFrame(IAP_Frame *f)
{
    uint8_t  b;
    uint16_t i;
    uint16_t crc_calc;
    uint16_t crc_recv;

    /* 1. 等帧头 AA，再等 55；不是就丢掉 */
    if (!IAP_WaitByte(&b, 1u))
        return 0u;
    if (b != 0xAAu)
        return 0u;

    iap_rx[0] = 0xAAu;
    if (!IAP_WaitByte(&b, IAP_BYTE_TIMEOUT) || b != 0x55u)
        return 0u;
    iap_rx[1] = 0x55u;

    /* 2. 8 字节固定头: CMD SEQ LEN(2) OFFSET(4) */
    for (i = 0; i < 8u; i++)
    {
        if (!IAP_WaitByte(&iap_rx[2u + i], IAP_BYTE_TIMEOUT))
            return 0u;
    }

    f->cmd    = iap_rx[2];
    f->seq    = iap_rx[3];
    f->len    = (uint16_t)iap_rx[4] | ((uint16_t)iap_rx[5] << 8);
    f->offset = (uint32_t)iap_rx[6]
              | ((uint32_t)iap_rx[7] << 8)
              | ((uint32_t)iap_rx[8] << 16)
              | ((uint32_t)iap_rx[9] << 24);

    if (f->len > IAP_MAX_DATA)
    {
        IAP_SendResp(IAP_CMD_NAK, f->seq, 0x10u);   /* 长度超限 */
        return 0u;
    }

    /* 3. DATA + CRC16 */
    for (i = 0; i < (uint16_t)(f->len + 2u); i++)
    {
        if (!IAP_WaitByte(&iap_rx[10u + i], IAP_BYTE_TIMEOUT))
            return 0u;
    }

    crc_calc = IAP_CRC16(&iap_rx[2], 8u + f->len);
    crc_recv = (uint16_t)iap_rx[10u + f->len]
             | ((uint16_t)iap_rx[11u + f->len] << 8);

    if (crc_calc != crc_recv)
    {
        printf("CRC ERROR\r\n");
        IAP_SendResp(IAP_CMD_NAK, f->seq, 0x01u);   /* CRC 错 */
        return 0u;
    }

    memcpy(f->data, &iap_rx[10], f->len);
    return 1u;
}





static uint32_t ReadU32LE(const uint8_t *p)
{
    return (uint32_t)p[0]
         | ((uint32_t)p[1] << 8)
         | ((uint32_t)p[2] << 16)
         | ((uint32_t)p[3] << 24);
}

/* 擦除 [addr, addr+size) 覆盖到的所有 1KB 页；返回 0=成功 */
static uint8_t Flash_EraseRange(uint32_t addr, uint32_t size)
{
    FLASH_EraseInitTypeDef erase;
    uint32_t page_error = 0;
    uint32_t pages;
    HAL_StatusTypeDef st;

    pages = (size + IAP_FLASH_PAGE - 1u) / IAP_FLASH_PAGE;

    erase.TypeErase   = FLASH_TYPEERASE_PAGES;
    erase.PageAddress = addr;
    erase.NbPages     = pages;

    HAL_FLASH_Unlock();
    st = HAL_FLASHEx_Erase(&erase, &page_error);
    HAL_FLASH_Lock();

    if (st != HAL_OK)
    {
        printf("ERASE FAIL page_error=0x%08lX\r\n", (unsigned long)page_error);
        return 1u;
    }
    return 0u;
}
/* 把 len 字节写到 addr；奇数长度末尾补 0xFF；返回 0=成功 */
static uint8_t Flash_WriteBytes(uint32_t addr, const uint8_t *data, uint16_t len)
{
    uint16_t i;
    uint16_t half;
    HAL_StatusTypeDef st;

    HAL_FLASH_Unlock();

    for (i = 0; i < len; i = (uint16_t)(i + 2u))
    {
        if ((uint16_t)(i + 1u) < len)
        {
            half = (uint16_t)data[i] | ((uint16_t)data[i + 1u] << 8);
        }
        else
        {
            half = (uint16_t)data[i] | 0xFF00u;   /* 末字节奇数，补 0xFF */
        }

        st = HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD,
                               addr + i, (uint64_t)half);
        if (st != HAL_OK)
        {
            HAL_FLASH_Lock();
            printf("WRITE FAIL @0x%08lX\r\n", (unsigned long)(addr + i));
            return 1u;
        }
    }

    HAL_FLASH_Lock();
    return 0u;
}



static void IAP_HandleFrame(IAP_Frame *f)
{
    printf("FRAME cmd=%02X seq=%u len=%u off=%lu\r\n",
           (unsigned)f->cmd, (unsigned)f->seq,
           (unsigned)f->len, (unsigned long)f->offset);

    switch (f->cmd)
    {
        case IAP_CMD_START:
        {
            uint32_t t0;
            uint32_t ms;

            if (f->len != 8u || f->offset != 0u)
            {
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x03u);
                break;
            }

            fw_size         = ReadU32LE(&f->data[0]);
            fw_crc32_expect = ReadU32LE(&f->data[4]);

            if (fw_size == 0u || fw_size > SLOT_A_SIZE)
            {
                printf("BAD SIZE: %lu\r\n", (unsigned long)fw_size);
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x04u);
                break;
            }

             printf("START: slot=0x%08lX size=%lu crc=0x%08lX, erasing...\r\n",
                   (unsigned long)SLOT_A_ADDR,
                   (unsigned long)fw_size,
                   (unsigned long)fw_crc32_expect);

            t0 = HAL_GetTick();
            if (Flash_EraseRange(SLOT_A_ADDR, fw_size) != 0u)
            {
                iap_started = 0u;
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x05u);
                break;
            }
            ms = HAL_GetTick() - t0;

            fw_received = 0u;
            iap_started = 1u;

            printf("ERASE OK, %lu ms (实际更久，见说明)\r\n", (unsigned long)ms);
            IAP_SendResp(IAP_CMD_ACK, f->seq, 0x00u);
            break;
        }

        case IAP_CMD_DATA:
        {
            uint32_t write_addr;

            if (!iap_started)
            {
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x06u);   /* 还没 START */
                break;
            }

            if ((f->offset & 1u) != 0u || f->offset != fw_received)
            {
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x07u);   /* 偏移不连续 */
                break;
            }

            if (f->len == 0u || (f->offset + f->len) > fw_size)
            {
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x08u);   /* 长度越界 */
                break;
            }

            write_addr = SLOT_A_ADDR + f->offset;

            if (Flash_WriteBytes(write_addr, f->data, f->len) != 0u)
            {
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x09u);   /* 写失败 */
                break;
            }

            /* 写后读回逐字节比较，不一致直接 NAK */
            if (memcmp((const void *)(uintptr_t)write_addr, f->data, f->len) != 0)
            {
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x0Au);   /* 读回不一致 */
                break;
            }

            fw_received += f->len;
            printf("DATA ok: total=%lu/%lu\r\n",
                   (unsigned long)fw_received, (unsigned long)fw_size);
            IAP_SendResp(IAP_CMD_ACK, f->seq, 0x00u);
            break;
        }

                case IAP_CMD_END:
        {
            uint32_t crc;

            if (!iap_started)
            {
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x06u);
                break;
            }

            if (fw_received != fw_size)
            {
                printf("END: recv=%lu size=%lu\r\n",
                       (unsigned long)fw_received, (unsigned long)fw_size);
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x0Bu);   /* 数据没传完 */
                break;
            }

            crc = IAP_CRC32((const uint8_t *)(uintptr_t)SLOT_A_ADDR, fw_size);
            printf("END: crc=0x%08lX expect=0x%08lX\r\n",
                   (unsigned long)crc, (unsigned long)fw_crc32_expect);

            if (crc != fw_crc32_expect)
            {
                IAP_SendResp(IAP_CMD_NAK, f->seq, 0x0Cu);   /* CRC32 不匹配 */
                break;
            }

            printf("CRC OK, rebooting...\r\n");
            IAP_SendResp(IAP_CMD_ACK, f->seq, 0x00u);
            HAL_Delay(20);              /* 确保 ACK 发完 */
            NVIC_SystemReset();         /* 复位，Boot 会跳新 App */
            break;
        }
    }
}
void IAP_Run(void)
{
    IAP_Frame f;

    printf("IAP ready.\r\n");
    while (1)
    {
        if (IAP_RecvFrame(&f))
        {
            IAP_HandleFrame(&f);
        }
    }
}