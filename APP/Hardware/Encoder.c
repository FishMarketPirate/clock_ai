#include "stm32f10x.h"
#include "Delay.h"
#include "Encoder.h"

//编码器：A相PA4，B相PA5，按键PA9
#define EC_a     GPIO_Pin_4
#define EC_b     GPIO_Pin_5
#define EC_sw    GPIO_Pin_9
#define EC_PORT  GPIOA

volatile int16_t Encoder_Counter = 0;
static uint8_t Encoder_SWLast = 1;

//初始化：A/B相用外部中断，按键上拉输入
void Encoder_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    EXTI_InitTypeDef EXTI_InitStruct;
    NVIC_InitTypeDef NVIC_InitStruct;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);

    //A/B相和按键都在GPIOA
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_InitStructure.GPIO_Pin = EC_a | EC_b | EC_sw;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(EC_PORT, &GPIO_InitStructure);

    GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinSource4);
    GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinSource5);

    EXTI_InitStruct.EXTI_Line = EXTI_Line4 | EXTI_Line5;
    EXTI_InitStruct.EXTI_LineCmd = ENABLE;
    EXTI_InitStruct.EXTI_Mode = EXTI_Mode_Interrupt;
    EXTI_InitStruct.EXTI_Trigger = EXTI_Trigger_Falling;
    EXTI_Init(&EXTI_InitStruct);

    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);

    NVIC_InitStruct.NVIC_IRQChannel = EXTI4_IRQn;
    NVIC_InitStruct.NVIC_IRQChannelCmd = ENABLE;
    NVIC_InitStruct.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStruct.NVIC_IRQChannelSubPriority = 1;
    NVIC_Init(&NVIC_InitStruct);

    NVIC_InitStruct.NVIC_IRQChannel = EXTI9_5_IRQn;
    NVIC_InitStruct.NVIC_IRQChannelCmd = ENABLE;
    NVIC_InitStruct.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStruct.NVIC_IRQChannelSubPriority = 2;
    NVIC_Init(&NVIC_InitStruct);
}

//读转动量，正转为正、反转为负，读完清零
int16_t Encoder_Get(void)
{
    int16_t Temp;

    __disable_irq();        //防止读的时候被中断打断
    Temp = Encoder_Counter;
    Encoder_Counter = 0;
    __enable_irq();
    return Temp;
}

//读编码器按键，返回1表示按下，0表示没按
uint8_t Encoder_Key_Get(void)
{
    uint8_t raw;

    raw = GPIO_ReadInputDataBit(EC_PORT, EC_sw);
    if (raw == 0 && Encoder_SWLast == 1)
    {
        Delay_ms(20);
        if (GPIO_ReadInputDataBit(EC_PORT, EC_sw) == 0)
        {
            Encoder_SWLast = 0;
            return 1;
        }
    }

    Encoder_SWLast = GPIO_ReadInputDataBit(EC_PORT, EC_sw);
    return 0;
}

//A相下降沿，B相为低是反转
void EXTI4_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line4) == SET)
    {
        if (GPIO_ReadInputDataBit(EC_PORT, EC_b) == 0)
        {
            Encoder_Counter--;
        }
        EXTI_ClearITPendingBit(EXTI_Line4);
    }
}

//B相下降沿，A相为低是正转
void EXTI9_5_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line5) == SET)
    {
        if (GPIO_ReadInputDataBit(EC_PORT, EC_a) == 0)
        {
            Encoder_Counter++;
        }
        EXTI_ClearITPendingBit(EXTI_Line5);
    }
}
