#include "stm32f10x.h"
#include "OLED.h"
#include "OLEDShow.h"

//星期名称，0=周日
static char WeekName[7][4] = {"SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"};

//初始化并清屏
void OLEDShow_Init(void)
{
    OLED_Init();
    OLED_Clear();
}

//从第col列清到行尾，防止上一屏长内容残留
static void OLEDShow_ClearToEnd(uint8_t line, uint8_t col)
{
    while (col <= 16)
    {
        OLED_ShowChar(line, col, ' ');
        col++;
    }
}

//显示日期、星期、时间
void OLEDShow_ShowTime(RTC_TimeTypeDef *t)
{
    uint8_t week = t->week;

    if (week > 6)
    {
        week = 0;
    }

    //第1行：2026-10-25 SUN
    OLED_ShowNum(1, 1, t->year, 4);
    OLED_ShowChar(1, 5, '-');
    OLED_ShowNum(1, 6, t->month, 2);
    OLED_ShowChar(1, 8, '-');
    OLED_ShowNum(1, 9, t->day, 2);
    OLED_ShowString(1, 12, WeekName[week]);

    //第2行：TIME 20:31:55
    OLED_ShowString(2, 1, "TIME ");
    OLED_ShowNum(2, 6, t->hour, 2);
    OLED_ShowChar(2, 8, ':');
    OLED_ShowNum(2, 9, t->min, 2);
    OLED_ShowChar(2, 11, ':');
    OLED_ShowNum(2, 12, t->sec, 2);

    //清掉行尾，防止从编辑界面回来残留字符
    OLEDShow_ClearToEnd(1, 15);
    OLEDShow_ClearToEnd(2, 14);
}

//显示温湿度，valid=0时显示--
void OLEDShow_ShowTempHum(uint8_t temp, uint8_t hum, uint8_t valid)
{
    uint8_t col;

    OLED_ShowString(3, 1, "T:");
    if (valid)
    {
        OLED_ShowNum(3, 3, temp, 2);
    }
    else
    {
        OLED_ShowString(3, 3, "--");
    }
    OLED_ShowChar(3, 5, 'C');
    OLED_ShowChar(3, 6, ' ');       //第6列固定空格，防止编辑界面残留

    OLED_ShowString(3, 7, "H:");
    col = 9;
    if (valid)
    {
        if (hum >= 100)             //湿度100%用3位显示，不然会显示成00
        {
            OLED_ShowNum(3, col, hum, 3);
            col += 3;
        }
        else
        {
            OLED_ShowNum(3, col, hum, 2);
            col += 2;
        }
    }
    else
    {
        OLED_ShowString(3, col, "--");
        col += 2;
    }
    OLED_ShowChar(3, col, '%');
    col++;
    OLEDShow_ClearToEnd(3, col);     //清掉行尾
}

//显示闹钟时间和开关状态
void OLEDShow_ShowAlarm(ALARM_TypeDef *a)
{
    OLED_ShowString(4, 1, "ALM:");
    OLED_ShowNum(4, 5, a->hour, 2);
    OLED_ShowChar(4, 7, ':');
    OLED_ShowNum(4, 8, a->min, 2);
    OLED_ShowChar(4, 10, ' ');
    if (a->enable)
    {
        OLED_ShowString(4, 11, "ON ");
    }
    else
    {
        OLED_ShowString(4, 11, "OFF");
    }
    OLEDShow_ClearToEnd(4, 14);     //清掉行尾
}

//时间设置界面，field是当前修改项
void OLEDShow_EditTime(RTC_TimeTypeDef *t, uint8_t field)
{
    uint8_t col;

    //第1行标题
    OLED_ShowString(1, 1, "EDIT TIME");
    OLEDShow_ClearToEnd(1, 10);

    //第2行日期，如[2026]-10-25
    col = 1;
    if (field == TIME_FIELD_YEAR)
    {
        OLED_ShowChar(2, col++, '[');
    }
    OLED_ShowNum(2, col, t->year, 4);
    col += 4;
    if (field == TIME_FIELD_YEAR)
    {
        OLED_ShowChar(2, col++, ']');
    }
    OLED_ShowChar(2, col++, '-');

    if (field == TIME_FIELD_MONTH)
    {
        OLED_ShowChar(2, col++, '[');
    }
    OLED_ShowNum(2, col, t->month, 2);
    col += 2;
    if (field == TIME_FIELD_MONTH)
    {
        OLED_ShowChar(2, col++, ']');
    }
    OLED_ShowChar(2, col++, '-');

    if (field == TIME_FIELD_DAY)
    {
        OLED_ShowChar(2, col++, '[');
    }
    OLED_ShowNum(2, col, t->day, 2);
    col += 2;
    if (field == TIME_FIELD_DAY)
    {
        OLED_ShowChar(2, col++, ']');
    }
    OLEDShow_ClearToEnd(2, col);

    //第3行时间，如20:[31]:55
    col = 1;
    if (field == TIME_FIELD_HOUR)
    {
        OLED_ShowChar(3, col++, '[');
    }
    OLED_ShowNum(3, col, t->hour, 2);
    col += 2;
    if (field == TIME_FIELD_HOUR)
    {
        OLED_ShowChar(3, col++, ']');
    }
    OLED_ShowChar(3, col++, ':');

    if (field == TIME_FIELD_MIN)
    {
        OLED_ShowChar(3, col++, '[');
    }
    OLED_ShowNum(3, col, t->min, 2);
    col += 2;
    if (field == TIME_FIELD_MIN)
    {
        OLED_ShowChar(3, col++, ']');
    }
    OLED_ShowChar(3, col++, ':');

    if (field == TIME_FIELD_SEC)
    {
        OLED_ShowChar(3, col++, '[');
    }
    OLED_ShowNum(3, col, t->sec, 2);
    col += 2;
    if (field == TIME_FIELD_SEC)
    {
        OLED_ShowChar(3, col++, ']');
    }
    OLEDShow_ClearToEnd(3, col);

    //第4行操作提示
    OLED_ShowString(4, 1, "K1:SAVE K2:NEXT");
    OLEDShow_ClearToEnd(4, 16);
}

//闹钟设置界面，field是当前修改项
void OLEDShow_EditAlarm(ALARM_TypeDef *a, uint8_t field)
{
    uint8_t col;

    //第1行标题
    OLED_ShowString(1, 1, "EDIT ALARM");
    OLEDShow_ClearToEnd(1, 11);

    //第2行：ALARM [07]:30
    OLED_ShowString(2, 1, "ALARM ");
    col = 7;
    if (field == ALARM_FIELD_HOUR)
    {
        OLED_ShowChar(2, col++, '[');
    }
    OLED_ShowNum(2, col, a->hour, 2);
    col += 2;
    if (field == ALARM_FIELD_HOUR)
    {
        OLED_ShowChar(2, col++, ']');
    }
    OLED_ShowChar(2, col++, ':');

    if (field == ALARM_FIELD_MIN)
    {
        OLED_ShowChar(2, col++, '[');
    }
    OLED_ShowNum(2, col, a->min, 2);
    col += 2;
    if (field == ALARM_FIELD_MIN)
    {
        OLED_ShowChar(2, col++, ']');
    }
    OLEDShow_ClearToEnd(2, col);

    //第3行开关，固定5个字符宽，切换修改项时不残留
    OLED_ShowString(3, 1, "SWITCH ");
    col = 8;
    if (field == ALARM_FIELD_ENABLE)
    {
        if (a->enable)
        {
            OLED_ShowString(3, col, "[ON ]");
        }
        else
        {
            OLED_ShowString(3, col, "[OFF]");
        }
    }
    else
    {
        if (a->enable)
        {
            OLED_ShowString(3, col, " ON  ");
        }
        else
        {
            OLED_ShowString(3, col, " OFF ");
        }
    }
    OLEDShow_ClearToEnd(3, (uint8_t)(col + 5));

    //第4行操作提示
    OLED_ShowString(4, 1, "K1:SAVE K2:NEXT");
    OLEDShow_ClearToEnd(4, 16);
}

//响铃时第4行闪烁
void OLEDShow_ShowRing(uint8_t visible)
{
    if (visible)
    {
        OLED_ShowString(4, 1, " *** ALARM ***");
        OLEDShow_ClearToEnd(4, 15);
    }
    else
    {
        OLEDShow_ClearToEnd(4, 1);
    }
}

//第4行显示提示，后面用空格补齐
void OLEDShow_ShowMessage(char *msg)
{
    uint8_t col = 1;

    while (msg[col - 1] != '\0' && col <= 16)
    {
        OLED_ShowChar(4, col, msg[col - 1]);
        col++;
    }
    OLEDShow_ClearToEnd(4, col);
}

//设置OLED显示方向：面包板翻转后旋转180°，文字仍然正着看
void OLEDShow_SetFlip(uint8_t flip)
{
    OLED_Flip(flip);
}

//第二页：MPU6500状态、倾斜方向、温湿度、闹钟
void OLEDShow_ShowSensorPage(uint8_t mpu_ok, uint8_t flipped,
                              uint8_t temp, uint8_t hum, uint8_t valid,
                              ALARM_TypeDef *a)
{
    uint8_t col;

    //第1行：MPU6500 OK/ERR
    OLED_ShowString(1, 1, "MPU6500 ");
    if (mpu_ok)
    {
        OLED_ShowString(1, 9, "OK   ");
    }
    else
    {
        OLED_ShowString(1, 9, "ERR  ");
    }
    OLEDShow_ClearToEnd(1, 14);

    //第2行：倾斜方向
    OLED_ShowString(2, 1, "TILT: ");
    if (flipped)
    {
        OLED_ShowString(2, 7, "UPSIDE");
    }
    else
    {
        OLED_ShowString(2, 7, "NORMAL");
    }
    OLEDShow_ClearToEnd(2, 13);

    //第3行：温湿度
    OLED_ShowString(3, 1, "T:");
    if (valid)
    {
        OLED_ShowNum(3, 3, temp, 2);
    }
    else
    {
        OLED_ShowString(3, 3, "--");
    }
    OLED_ShowChar(3, 5, 'C');
    OLED_ShowChar(3, 6, ' ');
    OLED_ShowString(3, 7, "H:");

    col = 9;
    if (valid)
    {
        if (hum >= 100)
        {
            OLED_ShowNum(3, col, hum, 3);
            col += 3;
        }
        else
        {
            OLED_ShowNum(3, col, hum, 2);
            col += 2;
        }
    }
    else
    {
        OLED_ShowString(3, col, "--");
        col += 2;
    }
    OLED_ShowChar(3, col, '%');
    col++;
    OLEDShow_ClearToEnd(3, col);

    //第4行：闹钟
    OLED_ShowString(4, 1, "ALM:");
    OLED_ShowNum(4, 5, a->hour, 2);
    OLED_ShowChar(4, 7, ':');
    OLED_ShowNum(4, 8, a->min, 2);
    OLED_ShowChar(4, 10, ' ');
    if (a->enable)
    {
        OLED_ShowString(4, 11, "ON ");
    }
    else
    {
        OLED_ShowString(4, 11, "OFF");
    }
    OLEDShow_ClearToEnd(4, 14);
}
