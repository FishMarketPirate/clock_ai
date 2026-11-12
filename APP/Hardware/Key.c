#include "stm32f10x.h"
#include "Delay.h"
#include "Key.h"

//KEY1接PA1，KEY2接PA3，按下为低
#define KEY1_PIN    GPIO_Pin_1
#define KEY2_PIN    GPIO_Pin_3
#define KEY_PORT    GPIOA

static uint8_t Key1Last = 1;
static uint8_t Key2Last = 1;

//初始化
void Key_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_InitStructure.GPIO_Pin = KEY1_PIN | KEY2_PIN;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(KEY_PORT, &GPIO_InitStructure);
}

//读一个按键，只有从松开变按下才算一次
static uint8_t Key_Read(uint16_t pin, uint8_t *last)
{
    uint8_t raw;

    raw = GPIO_ReadInputDataBit(KEY_PORT, pin);
    if (raw == 0 && *last == 1)
    {
        Delay_ms(20);                     //消抖
        if (GPIO_ReadInputDataBit(KEY_PORT, pin) == 0)
        {
            *last = 0;
            return 1;
        }
    }

    *last = GPIO_ReadInputDataBit(KEY_PORT, pin);
    return 0;
}

//返回0没有按键，1=KEY1，2=KEY2，按住不放只返回一次
uint8_t Key_GetNum(void)
{
    if (Key_Read(KEY1_PIN, &Key1Last))
    {
        return 1;
    }
    if (Key_Read(KEY2_PIN, &Key2Last))
    {
        return 2;
    }
    return 0;
}
