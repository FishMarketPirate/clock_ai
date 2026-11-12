#ifndef __IAP_H__
#define __IAP_H__

#include "stm32f1xx_hal.h"

#define IAP_CMD_START    0x01u
#define IAP_CMD_DATA     0x02u
#define IAP_CMD_END      0x03u
#define IAP_CMD_ACK      0x04u
#define IAP_CMD_NAK      0x05u

#define IAP_MAX_DATA     256u

typedef struct
{
    uint8_t  cmd;
    uint8_t  seq;
    uint16_t len;
    uint32_t offset;
    uint8_t  data[IAP_MAX_DATA];
} IAP_Frame;

uint16_t IAP_CRC16(const uint8_t *p, uint32_t len);
void     IAP_Run(void);

#endif