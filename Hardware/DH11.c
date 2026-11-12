#include "stm32f10x.h"
#include "DH11.h"
#include "Delay.h"

uint8_t rec_data[4];

//数据脚切输出
void DH11_Out_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
}

//数据脚切输入，上拉
void DH11_In_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
}

//起始信号：主机拉低至少18ms，再释放等响应
void DH11_Start(void)
{
    DH11_Out_Init();

    dht11_high;
    Delay_us(30);

    dht11_low;
    Delay_ms(20);

    dht11_high;
    Delay_us(30);

    DH11_In_Init();
}

//等电平离开level，超时返回0，防止传感器没接时卡死
static uint8_t DH11_WaitLevel(uint8_t level)
{
    uint16_t timeout = 6000;

    while (Read_Data == level)
    {
        if (timeout-- == 0)
        {
            return 0;
        }
    }
    return 1;
}

//收一个字节，高位在前
char DH11_Rec_Byte(void)
{
    uint8_t i;
    uint8_t data = 0;

    for (i = 0; i < 8; i++)
    {
        if (!DH11_WaitLevel(0))        //等50us低电平结束
        {
            return (char)data;
        }

        Delay_us(40);                   //40us后还是高就是1
        data <<= 1;
        if (Read_Data == 1)
        {
            data |= 1;
        }

        if (!DH11_WaitLevel(1))         //等高电平结束
        {
            return (char)data;
        }
    }
    return (char)data;
}

//读一次温湿度，1成功，0失败
uint8_t DH11_Rec_Data(void)
{
    uint8_t RH, RL, TH, TL, CHECK;

    DH11_Start();

    if (!DH11_WaitLevel(1))        //等DHT11拉低响应
    {
        return 0;
    }
    if (!DH11_WaitLevel(0))        //等响应低电平结束
    {
        return 0;
    }
    if (!DH11_WaitLevel(1))        //等响应高电平结束
    {
        return 0;
    }

    RH    = (uint8_t)DH11_Rec_Byte();
    RL    = (uint8_t)DH11_Rec_Byte();
    TH    = (uint8_t)DH11_Rec_Byte();
    TL    = (uint8_t)DH11_Rec_Byte();
    CHECK = (uint8_t)DH11_Rec_Byte();

    //引脚已切回输入，总线由外部上拉拉高
    if ((uint8_t)(RH + RL + TH + TL) != CHECK)
    {
        return 0;
    }

    rec_data[0] = RH;
    rec_data[1] = RL;
    rec_data[2] = TH;
    rec_data[3] = TL;
    return 1;
}
