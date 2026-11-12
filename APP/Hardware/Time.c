#include "stm32f10x.h"
#include "Time.h"
#include "MyRTC.h"

//当前时间、闹钟（默认 07:00，关闭）
RTC_TimeTypeDef now_time;
ALARM_TypeDef alarm_cfg = {7, 0, 0};

//闹钟存在后备寄存器，掉电不丢
#define ALARM_BKP_MAGIC        0x5AA5
#define ALARM_BKP_REG_MAGIC    BKP_DR2
#define ALARM_BKP_REG_TIME     BKP_DR3   //高字节时，低字节分
#define ALARM_BKP_REG_ENABLE   BKP_DR4

//平年每月天数，闰年2月单独处理
static const uint8_t MonthDays[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

//判断闰年
uint8_t IsLeapYear(uint16_t y)
{
    return (uint8_t)((y % 4 == 0 && y % 100 != 0) || (y % 400 == 0));
}

//返回某年某月的天数
uint8_t Time_DaysInMonth(uint16_t y, uint8_t m)
{
    if (m < 1 || m > 12)
    {
        return 31;
    }
    if (m == 2 && IsLeapYear(y))
    {
        return 29;
    }
    return MonthDays[m - 1];
}

//由年月日算星期，0=周日（蔡勒公式）
uint8_t Time_WeekDay(uint16_t y, uint8_t m, uint8_t d)
{
    uint16_t k, j, h;

    if (m < 3)
    {
        m += 12;
        y--;
    }
    k = y % 100;
    j = y / 100;
    h = (uint16_t)(d + (13 * (m + 1)) / 5 + k + k / 4 + j / 4 + 5 * j);
    return (uint8_t)((h + 6) % 7);
}

//初始化：读时间、恢复闹钟（要先调用 MyRTC_Init）
void Time_Init(void)
{
    Time_Read(&now_time);
    Alarm_Load();
}

//从RTC读时间
void Time_Read(RTC_TimeTypeDef *t)
{
    MyRTC_ReadTime();

    t->year  = MyRTC_Time[0];
    t->month = (uint8_t)MyRTC_Time[1];
    t->day   = (uint8_t)MyRTC_Time[2];
    t->hour  = (uint8_t)MyRTC_Time[3];
    t->min   = (uint8_t)MyRTC_Time[4];
    t->sec   = (uint8_t)MyRTC_Time[5];
    t->week  = Time_WeekDay(t->year, t->month, t->day);
}

//把时间写入RTC
void Time_Set(RTC_TimeTypeDef *t)
{
    MyRTC_Time[0] = t->year;
    MyRTC_Time[1] = t->month;
    MyRTC_Time[2] = t->day;
    MyRTC_Time[3] = t->hour;
    MyRTC_Time[4] = t->min;
    MyRTC_Time[5] = t->sec;

    MyRTC_SetTime();
    t->week = Time_WeekDay(t->year, t->month, t->day);
}

//调整时间字段，step>0正转，<0反转
void Time_Adjust(RTC_TimeTypeDef *t, uint8_t field, int16_t step)
{
    int16_t v;
    uint8_t dim;

    if (step == 0)
    {
        return;
    }

    switch (field)
    {
        case TIME_FIELD_YEAR:
            //越界先拉回来；范围2000~2037，避免2038年time_t溢出
            if (t->year < 2000) t->year = 2000;
            if (t->year > 2037) t->year = 2037;
            v = (int16_t)(t->year + step);
            while (v > 2037) v -= 38;
            while (v < 2000) v += 38;
            t->year = (uint16_t)v;
            break;

        case TIME_FIELD_MONTH:
            v = (int16_t)(t->month + step);
            while (v > 12) v -= 12;
            while (v < 1)  v += 12;
            t->month = (uint8_t)v;
            break;

        case TIME_FIELD_DAY:
            dim = Time_DaysInMonth(t->year, t->month);
            v = (int16_t)(t->day + step);
            while (v > (int16_t)dim) v -= (int16_t)dim;
            while (v < 1)            v += (int16_t)dim;
            t->day = (uint8_t)v;
            break;

        case TIME_FIELD_HOUR:
            v = (int16_t)(t->hour + step);
            while (v > 23) v -= 24;
            while (v < 0)  v += 24;
            t->hour = (uint8_t)v;
            break;

        case TIME_FIELD_MIN:
            v = (int16_t)(t->min + step);
            while (v > 59) v -= 60;
            while (v < 0)  v += 60;
            t->min = (uint8_t)v;
            break;

        case TIME_FIELD_SEC:
            v = (int16_t)(t->sec + step);
            while (v > 59) v -= 60;
            while (v < 0)  v += 60;
            t->sec = (uint8_t)v;
            break;

        default:
            break;
    }

    //改完年/月，日期不能超过当月天数
    dim = Time_DaysInMonth(t->year, t->month);
    if (t->day > dim)
    {
        t->day = dim;
    }
    if (t->day < 1)
    {
        t->day = 1;
    }
    t->week = Time_WeekDay(t->year, t->month, t->day);
}

//调整闹钟字段
void Alarm_Adjust(ALARM_TypeDef *a, uint8_t field, int16_t step)
{
    int16_t v;

    if (step == 0)
    {
        return;
    }

    switch (field)
    {
        case ALARM_FIELD_HOUR:
            v = (int16_t)(a->hour + step);
            while (v > 23) v -= 24;
            while (v < 0)  v += 24;
            a->hour = (uint8_t)v;
            break;

        case ALARM_FIELD_MIN:
            v = (int16_t)(a->min + step);
            while (v > 59) v -= 60;
            while (v < 0)  v += 60;
            a->min = (uint8_t)v;
            break;

        case ALARM_FIELD_ENABLE:
            //右转开，左转关
            a->enable = (step > 0) ? 1 : 0;
            break;

        default:
            break;
    }
}

//从后备寄存器读闹钟
void Alarm_Load(void)
{
    if (BKP_ReadBackupRegister(ALARM_BKP_REG_MAGIC) == ALARM_BKP_MAGIC)
    {
        uint16_t time = BKP_ReadBackupRegister(ALARM_BKP_REG_TIME);

        alarm_cfg.hour = (uint8_t)((time >> 8) & 0xFF);
        alarm_cfg.min  = (uint8_t)(time & 0xFF);
        if (alarm_cfg.hour > 23) alarm_cfg.hour = 7;
        if (alarm_cfg.min > 59)  alarm_cfg.min = 0;
        alarm_cfg.enable = (uint8_t)(BKP_ReadBackupRegister(ALARM_BKP_REG_ENABLE) & 0x01);
    }
    else
    {
        //第一次上电，用默认值
        alarm_cfg.hour = 7;
        alarm_cfg.min = 0;
        alarm_cfg.enable = 0;
        Alarm_Save();
    }
}

//保存闹钟：先写数据，最后写magic，防止掉电后数据不一致
void Alarm_Save(void)
{
    BKP_WriteBackupRegister(ALARM_BKP_REG_TIME, (uint16_t)(((uint16_t)alarm_cfg.hour << 8) | alarm_cfg.min));
    BKP_WriteBackupRegister(ALARM_BKP_REG_ENABLE, alarm_cfg.enable);
    BKP_WriteBackupRegister(ALARM_BKP_REG_MAGIC, ALARM_BKP_MAGIC);
}
