#include "stm32f10x.h"
#include "Buzzer.h"

//蜂鸣器接PA7，低电平响
#define BUZZER_PORT GPIOA
#define BUZZER_PIN  GPIO_Pin_7

//初始化，默认关闭
void Buzzer_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Pin = BUZZER_PIN;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(BUZZER_PORT, &GPIO_InitStructure);

    Buzzer_OFF();
}

void Buzzer_ON(void)
{
    GPIO_ResetBits(BUZZER_PORT, BUZZER_PIN);
}

void Buzzer_OFF(void)
{
    GPIO_SetBits(BUZZER_PORT, BUZZER_PIN);
}

void Buzzer_Turn(void)
{
    if (GPIO_ReadOutputDataBit(BUZZER_PORT, BUZZER_PIN) == 0)
    {
        GPIO_SetBits(BUZZER_PORT, BUZZER_PIN);
    }
    else
    {
        GPIO_ResetBits(BUZZER_PORT, BUZZER_PIN);
    }
}
