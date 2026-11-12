#include "stm32f10x.h"
#include "Delay.h"
#include "MyRTC.h"
#include "Time.h"
#include "Key.h"
#include "Encoder.h"
#include "DH11.h"
#include "Buzzer.h"
#include "OLEDShow.h"
#include "MPU6050.h"
 
//工作模式
#define MODE_NORMAL       0     //正常显示
#define MODE_EDIT_TIME    1     //修改时间
#define MODE_EDIT_ALARM   2     //修改闹钟
#define MODE_RING         3     //闹钟响铃

//按主循环轮次计数，一轮约10ms
#define TEMP_READ_LOOPS   200   //每200轮读一次温湿度
#define RING_BEEP_LOOPS   20    //每20轮翻转一次蜂鸣器
#define RING_BLINK_LOOPS  50    //每50轮闪一次提示
#define RING_TIMEOUT_SEC  30    //响铃最长30秒

//MPU6500翻转检测
#define MPU_READ_LOOPS    5     //每5轮（约50ms）读一次
#define FLIP_CONFIRM_CNT  3     //连续3次确认，约150ms
#define FLIP_Z_THRESHOLD  8000  //±2g量程，约0.5g
#define FLIP_Z_SIGN       1     //若翻转检测方向反了，改成-1


#define VECT_TAB_OFFSET  0x3000

static uint8_t mode = MODE_NORMAL;

//编辑用的临时时间/闹钟，保存后才写回
static RTC_TimeTypeDef edit_time;
static ALARM_TypeDef edit_alarm;
static uint8_t edit_field = 0;

//温湿度
static uint8_t temp_value = 0;
static uint8_t hum_value = 0;
static uint8_t th_valid = 0;
static uint16_t temp_loop = 0;

//响铃
static uint32_t ring_start_sec = 0;
static uint16_t ring_loop = 0;
static uint8_t ring_display_on = 1;

static uint16_t last_minute_key = 0xFFFF;   //上一次的时:分，用来判断进入新的一分钟
static uint8_t display_sec = 0xFF;          //上次刷新的秒数

//MPU6500/flip
static uint8_t mpu_ok = 0;                  //MPU6050/6500是否在线
static uint8_t board_flip = 0;              //0=正面，1=翻转
static uint8_t flip_cnt = 0;
static int32_t az_filter = 0;
static uint16_t mpu_loop = 0;
static uint8_t display_page = 0;            //0=时钟页，1=传感器页
static uint16_t sensor_loop = 0;

static void Main_ShowHome(void);   //前置声明，供Main_ShowPage调用

//显示当前页
static void Main_ShowPage(void)
{
    if (display_page == 0)
    {
        Main_ShowHome();
    }
    else
    {
        OLEDShow_ShowSensorPage(mpu_ok, board_flip, temp_value, hum_value, th_valid, &alarm_cfg);
    }
}

//读MPU6050/6500，检测面包板翻转
static void Main_UpdateMPU(void)
{
    int16_t ax, ay, az, gx, gy, gz;
    int32_t z;
    uint8_t target;

    if (!mpu_ok)
    {
        return;
    }

    MPU6050_Get(&ax, &ay, &az, &gx, &gy, &gz);

    //简单滑动平均，过滤手抖
    az_filter = (az_filter * 3 + az) / 4;
    z = (int32_t)FLIP_Z_SIGN * az_filter;

    if (z < -FLIP_Z_THRESHOLD)
    {
        target = 1;
    }
    else if (z > FLIP_Z_THRESHOLD)
    {
        target = 0;
    }
    else
    {
        target = board_flip;
    }

    if (target != board_flip)
    {
        if (++flip_cnt >= FLIP_CONFIRM_CNT)
        {
            flip_cnt = 0;
            board_flip = target;
            OLEDShow_SetFlip(board_flip);   //翻转后OLED也转180°，文字仍正着看

            if (board_flip)                 //每次翻到背面，切换一次显示页
            {
                display_page = display_page ? 0 : 1;
                sensor_loop = 0;
            }
            Main_ShowPage();
        }
    }
    else
    {
        flip_cnt = 0;
    }
}

//显示主界面
static void Main_ShowHome(void)
{
    OLEDShow_ShowTime(&now_time);
    OLEDShow_ShowTempHum(temp_value, hum_value, th_valid);
    OLEDShow_ShowAlarm(&alarm_cfg);
    display_sec = now_time.sec;
}

//读一次温湿度
static void Main_ReadTempHum(void)
{
    th_valid = DH11_Rec_Data();
    if (th_valid)
    {
        temp_value = rec_data[2];
        hum_value = rec_data[0];
    }
}

//主函数
//KEY1(PA1)：主界面改时间，编辑界面保存
//KEY2(PA3)：主界面改闹钟，编辑界面换下一项
//编码器旋转：调数值
//编码器按键(PA9)：主界面开关闹钟，编辑界面取消
//响铃时任意键或旋转停止
int main(void)
{
	SCB->VTOR = 0x08003000;
	
    uint32_t tick;
    uint16_t minute_key;
    int16_t delta;
    uint8_t key;
    uint8_t enc_key;
    uint8_t mpu_id;

    MyRTC_Init();        //RTC初始化
    Time_Init();         //读时间、恢复闹钟
    Key_Init();
    Encoder_Init();
    Buzzer_Init();
    OLEDShow_Init();
    Buzzer_OFF();

    //MPU6500初始化并读ID：0x68=MPU6050，0x70=MPU6500
    MPU6050_Init();
    mpu_id = MPU6050_ReadID();
    mpu_ok = (mpu_id == 0x68 || mpu_id == 0x70);
    OLEDShow_SetFlip(0);

    Time_Read(&now_time);
    Main_ReadTempHum();  //上电先读一次
    Main_ShowPage();

    while (1)
    {
        tick = MyRTC_GetCounter();
        Time_Read(&now_time);

        key = Key_GetNum();
        enc_key = Encoder_Key_Get();
        delta = Encoder_Get();

        //传感器页时，任意按键/旋转先回到时钟页
        if (display_page == 1 && (key != 0 || enc_key || delta != 0))
        {
            display_page = 0;
            Main_ShowPage();
            key = 0;
            enc_key = 0;
            delta = 0;
        }

        //正常界面下每50ms读一次MPU，检测翻转
        if (mode == MODE_NORMAL)
        {
            mpu_loop++;
            if (mpu_loop >= MPU_READ_LOOPS)
            {
                mpu_loop = 0;
                Main_UpdateMPU();
            }
        }

        //进入新的一分钟就查一次闹钟，编辑界面也响应
        minute_key = (uint16_t)(((uint16_t)now_time.hour << 8) | now_time.min);
        if (minute_key != last_minute_key)
        {
            last_minute_key = minute_key;
            if (alarm_cfg.enable &&
                now_time.hour == alarm_cfg.hour &&
                now_time.min == alarm_cfg.min &&
                mode != MODE_RING)
            {
                //在编辑界面/传感器页触发的，先回时钟页
                if (mode == MODE_EDIT_TIME || mode == MODE_EDIT_ALARM || display_page == 1)
                {
                    display_page = 0;
                    Main_ShowPage();
                }
                mode = MODE_RING;
                ring_start_sec = tick;
                ring_loop = 0;
                ring_display_on = 1;
                Buzzer_ON();
                OLEDShow_ShowRing(1);
                //这一轮的按键/编码器输入作废，防止刚响就停
                key = 0;
                enc_key = 0;
                delta = 0;
            }
        }

        switch (mode)
        {
            case MODE_NORMAL:
                //秒变了才刷新，避免刷屏
                if (display_page == 0 && now_time.sec != display_sec)
                {
                    display_sec = now_time.sec;
                    OLEDShow_ShowTime(&now_time);
                }

                if (enc_key)            //编码器按键：开关闹钟
                {
                    alarm_cfg.enable = alarm_cfg.enable ? 0 : 1;
                    Alarm_Save();
                    OLEDShow_ShowAlarm(&alarm_cfg);
                }
                else if (key == 1)      //KEY1：改时间
                {
                    edit_time = now_time;
                    edit_field = TIME_FIELD_HOUR;
                    mode = MODE_EDIT_TIME;
                    OLEDShow_EditTime(&edit_time, edit_field);
                }
                else if (key == 2)      //KEY2：改闹钟
                {
                    edit_alarm = alarm_cfg;
                    edit_field = ALARM_FIELD_HOUR;
                    mode = MODE_EDIT_ALARM;
                    OLEDShow_EditAlarm(&edit_alarm, edit_field);
                }
                break;

            case MODE_EDIT_TIME:
                if (delta != 0)         //旋转编码器调数值
                {
                    Time_Adjust(&edit_time, edit_field, delta);
                    OLEDShow_EditTime(&edit_time, edit_field);
                }

                if (key == 2)           //KEY2换下一项
                {
                    edit_field++;
                    if (edit_field >= TIME_FIELD_NUM)
                    {
                        edit_field = 0;
                    }
                    OLEDShow_EditTime(&edit_time, edit_field);
                }
                else if (key == 1)      //KEY1保存返回
                {
                    Time_Set(&edit_time);
                    Time_Read(&now_time);
                    mode = MODE_NORMAL;
                    Main_ShowHome();
                }
                else if (enc_key)       //编码器按键取消
                {
                    mode = MODE_NORMAL;
                    Main_ShowHome();
                }
                break;

            case MODE_EDIT_ALARM:
                if (delta != 0)         //旋转编码器调数值
                {
                    Alarm_Adjust(&edit_alarm, edit_field, delta);
                    OLEDShow_EditAlarm(&edit_alarm, edit_field);
                }

                if (key == 2)           //KEY2换下一项
                {
                    edit_field++;
                    if (edit_field >= ALARM_FIELD_NUM)
                    {
                        edit_field = 0;
                    }
                    OLEDShow_EditAlarm(&edit_alarm, edit_field);
                }
                else if (key == 1)      //KEY1保存返回
                {
                    alarm_cfg = edit_alarm;
                    Alarm_Save();
                    mode = MODE_NORMAL;
                    Main_ShowHome();
                }
                else if (enc_key)       //编码器按键取消
                {
                    mode = MODE_NORMAL;
                    Main_ShowHome();
                }
                break;

            case MODE_RING:
                ring_loop++;
                if ((ring_loop % RING_BEEP_LOOPS) == 0)
                {
                    Buzzer_Turn();      //滴—滴—
                }
                if ((ring_loop % RING_BLINK_LOOPS) == 0)
                {
                    ring_display_on = ring_display_on ? 0 : 1;
                    OLEDShow_ShowRing(ring_display_on);
                }

                //响铃时时间继续走
                if (now_time.sec != display_sec)
                {
                    display_sec = now_time.sec;
                    OLEDShow_ShowTime(&now_time);
                }

                //任意键/旋转/30秒超时停止
                if (key != 0 || enc_key || delta != 0 ||
                    (uint32_t)(tick - ring_start_sec) >= RING_TIMEOUT_SEC)
                {
                    Buzzer_OFF();
                    mode = MODE_NORMAL;
                    Main_ShowHome();
                }
                break;

            default:
                mode = MODE_NORMAL;
                Main_ShowHome();
                break;
        }

        //定时读温湿度
        temp_loop++;
        if (temp_loop >= TEMP_READ_LOOPS)
        {
            temp_loop = 0;
            Main_ReadTempHum();
            if (mode == MODE_NORMAL && display_page == 0)
            {
                OLEDShow_ShowTempHum(temp_value, hum_value, th_valid);
            }
        }

        //传感器页每500ms刷新一次
        if (display_page == 1)
        {
            sensor_loop++;
            if (sensor_loop >= 50)
            {
                sensor_loop = 0;
                OLEDShow_ShowSensorPage(mpu_ok, board_flip,
                                        temp_value, hum_value, th_valid,
                                        &alarm_cfg);
            }
        }
        else
        {
            sensor_loop = 0;
        }

        Delay_ms(10);
    }
}
