#ifndef __OLEDSHOW_H
#define __OLEDSHOW_H

#include "stm32f10x.h"
#include "Time.h"

//OLED显示封装，主函数只调这里，不直接操作OLED
void OLEDShow_Init(void);        //初始化并清屏

//主界面
void OLEDShow_ShowTime(RTC_TimeTypeDef *t);                          //日期、星期、时间
void OLEDShow_ShowTempHum(uint8_t temp, uint8_t hum, uint8_t valid); //温湿度，valid=0显示--
void OLEDShow_ShowAlarm(ALARM_TypeDef *a);                           //闹钟时间和开关

//编辑界面，当前修改项用[]标出
void OLEDShow_EditTime(RTC_TimeTypeDef *t, uint8_t field);
void OLEDShow_EditAlarm(ALARM_TypeDef *a, uint8_t field);

//闹钟响铃时第4行闪烁
void OLEDShow_ShowRing(uint8_t visible);

//第4行显示一行提示
void OLEDShow_ShowMessage(char *msg);

//设置OLED显示方向：1=旋转180°（翻转后正着看），0=正常
void OLEDShow_SetFlip(uint8_t flip);

//第二页：MPU6500状态、倾斜方向、温湿度、闹钟
void OLEDShow_ShowSensorPage(uint8_t mpu_ok, uint8_t flipped,
                              uint8_t temp, uint8_t hum, uint8_t valid,
                              ALARM_TypeDef *a);

#endif
