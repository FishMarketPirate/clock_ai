#include "stm32f10x.h"                  // Device header
#include <time.h>
#include "Delay.h"
#include "MyRTC.h"

//显示时间比计数器快8小时，读的时候加、写的时候减
#define TZ_OFFSET_SEC   (8 * 60 * 60)

uint16_t MyRTC_Time[] = {2026,10,25,21,31,55};

//读RTC计数器，读两次CNTH，防止进位时读错
uint32_t MyRTC_GetCounter(void)
{
	uint32_t high1, high2, low;

	do
	{
		high1 = RTC->CNTH;
		low = RTC->CNTL;
		high2 = RTC->CNTH;
	} while (high1 != high2);

	return (high1 << 16) | (low & 0xFFFF);
}

//等RCC标志置位，带超时
static uint8_t MyRTC_WaitFlag(uint8_t flag, uint16_t timeout_ms)
{
	uint16_t t = 0;

	while(RCC_GetFlagStatus(flag)!=SET && t<timeout_ms)
	{
		Delay_ms(1);
		t++;
	}
	return (RCC_GetFlagStatus(flag)==SET) ? 1 : 0;
}

//等RTC寄存器同步，带超时
static uint8_t MyRTC_WaitSynchro(uint16_t timeout_ms)
{
	uint16_t t = 0;

	while(RTC_GetFlagStatus(RTC_FLAG_RSF)==RESET && t<timeout_ms)
	{
		Delay_ms(1);
		t++;
	}
	return (RTC_GetFlagStatus(RTC_FLAG_RSF)==SET) ? 1 : 0;
}

//等RTC上一次写完成，带超时
static void MyRTC_WaitLastTask(void)
{
	uint16_t t = 100;

	while(RTC_GetFlagStatus(RTC_FLAG_RTOFF)==RESET && t>0)
	{
		Delay_ms(1);
		t--;
	}
}

//配置备份域和RTC时钟：先试LSE，5秒不起振就用LSI
static void MyRTC_ConfigBackupDomain(void)
{
	uint16_t wait_ms = 0;
	uint16_t prescaler;

	//打开外部32.768kHz晶振
	RCC_LSEConfig(RCC_LSE_ON);
	while(RCC_GetFlagStatus(RCC_FLAG_LSERDY)!=SET && wait_ms<5000)
	{
		Delay_ms(1);
		wait_ms++;
	}

	if(RCC_GetFlagStatus(RCC_FLAG_LSERDY)==SET)
	{
		RCC_RTCCLKConfig(RCC_RTCCLKSource_LSE);
		prescaler = 32768-1;
	}
	else
	{
		//晶振没起来，用内部LSI，精度低但不黑屏
		RCC_LSEConfig(RCC_LSE_OFF);
		RCC_LSICmd(ENABLE);
		while(RCC_GetFlagStatus(RCC_FLAG_LSIRDY)!=SET);
		RCC_RTCCLKConfig(RCC_RTCCLKSource_LSI);
		prescaler = 40000-1;
	}

	RCC_RTCCLKCmd(ENABLE);

	MyRTC_WaitSynchro(500);
	MyRTC_WaitLastTask();

	//分频
	RTC_SetPrescaler(prescaler);
	MyRTC_WaitLastTask();

	//写初始时间，记下已初始化标志
	MyRTC_SetTime();
	BKP_WriteBackupRegister(BKP_DR1,0xA5A5);
}

//RTC初始化
void MyRTC_Init(void)
{
	uint32_t rtcsel;

	RCC_APB1PeriphClockCmd(RCC_APB1Periph_PWR,ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_BKP,ENABLE);

	PWR_BackupAccessCmd(ENABLE);

	if(BKP_ReadBackupRegister(BKP_DR1)==0xA5A5)
	{
		//备份域已有时间，确认时钟源还在振荡
		uint8_t clock_ok = 0;

		rtcsel = RCC->BDCR & RCC_BDCR_RTCSEL;

		if(rtcsel==RCC_BDCR_RTCSEL_LSE)
		{
			RCC_LSEConfig(RCC_LSE_ON);
			clock_ok = MyRTC_WaitFlag(RCC_FLAG_LSERDY, 5000);
		}
		else if(rtcsel==RCC_BDCR_RTCSEL_LSI)
		{
			//LSI复位后LSION会清零，要重新打开
			RCC_LSICmd(ENABLE);
			clock_ok = MyRTC_WaitFlag(RCC_FLAG_LSIRDY, 1000);
		}
		else if(rtcsel==RCC_BDCR_RTCSEL_HSE)
		{
			RCC_HSEConfig(RCC_HSE_ON);
			clock_ok = MyRTC_WaitFlag(RCC_FLAG_HSERDY, 2000);
		}

		if(clock_ok)
		{
			RCC_RTCCLKCmd(ENABLE);
			if(MyRTC_WaitSynchro(500))
			{
				MyRTC_WaitLastTask();
				return;			//RTC正常，沿用原来的时间
			}
		}

		//时钟源异常，复位备份域重新初始化
		BKP_DeInit();
		PWR_BackupAccessCmd(ENABLE);
	}

	//首次上电或备份域刚复位
	MyRTC_ConfigBackupDomain();
}


//把MyRTC_Time写入RTC
void MyRTC_SetTime(void)
{
	time_t time_cnt;
	struct tm time_date;

	time_date.tm_year = MyRTC_Time[0]-1900;
	time_date.tm_mon = MyRTC_Time[1]-1;
	time_date.tm_mday = MyRTC_Time[2];
	time_date.tm_hour = MyRTC_Time[3];
	time_date.tm_min = MyRTC_Time[4];
	time_date.tm_sec = MyRTC_Time[5];
	time_date.tm_wday = 0;		//这三个成员不初始化，mktime结果不确定
	time_date.tm_yday = 0;
	time_date.tm_isdst = 0;

	//读的时候加了8小时，写的时候减回来
	time_cnt = mktime(&time_date) - TZ_OFFSET_SEC;

	RTC_SetCounter(time_cnt);
	MyRTC_WaitLastTask();
}


//从RTC读出时间到MyRTC_Time
void MyRTC_ReadTime(void)
{
	time_t time_cnt;
	struct tm time_date;

	time_cnt = MyRTC_GetCounter() + TZ_OFFSET_SEC;

	time_date = *localtime(&time_cnt);

	MyRTC_Time[0] = time_date.tm_year +1900;
	MyRTC_Time[1] = time_date.tm_mon +1;
	MyRTC_Time[2] = time_date.tm_mday;
	MyRTC_Time[3] = time_date.tm_hour;
	MyRTC_Time[4] = time_date.tm_min;
	MyRTC_Time[5] = time_date.tm_sec ;
}
