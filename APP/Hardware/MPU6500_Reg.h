#ifndef __MPU6500_REG_H
#define __MPU6500_REG_H

//================ MPU6050 寄存器宏定义 ================
//采样率分频寄存器
#define	MPU6050_SMPLRT_DIV		0x19
//配置寄存器，低通滤波等参数配置
#define	MPU6050_CONFIG			0x1A
//陀螺仪配置寄存器，配置陀螺仪量程、自检
#define	MPU6050_GYRO_CONFIG		0x1B
//加速度计配置寄存器，配置加速度计量程、自检
#define	MPU6050_ACCEL_CONFIG	0x1C

//加速度计输出寄存器（高字节+低字节）
#define	MPU6050_ACCEL_XOUT_H	0x3B	//X轴加速度 高8位
#define	MPU6050_ACCEL_XOUT_L	0x3C	//X轴加速度 低8位
#define	MPU6050_ACCEL_YOUT_H	0x3D	//Y轴加速度 高8位
#define	MPU6050_ACCEL_YOUT_L	0x3E	//Y轴加速度 低8位
#define	MPU6050_ACCEL_ZOUT_H	0x3F	//Z轴加速度 高8位
#define	MPU6050_ACCEL_ZOUT_L	0x40	//Z轴加速度 低8位

//片内温度传感器输出寄存器
#define	MPU6050_TEMP_OUT_H		0x41	//温度高8位
#define	MPU6050_TEMP_OUT_L		0x42	//温度低8位

//陀螺仪输出寄存器（高字节+低字节）
#define	MPU6050_GYRO_XOUT_H		0x43	//X轴陀螺仪 高8位
#define	MPU6050_GYRO_XOUT_L		0x44	//X轴陀螺仪 低8位
#define	MPU6050_GYRO_YOUT_H		0x45	//Y轴陀螺仪 高8位
#define	MPU6050_GYRO_YOUT_L		0x46	//Y轴陀螺仪 低8位
#define	MPU6050_GYRO_ZOUT_H		0x47	//Z轴陀螺仪 高8位
#define	MPU6050_GYRO_ZOUT_L		0x48	//Z轴陀螺仪 低8位

//电源管理寄存器1：唤醒、复位、时钟源选择
#define	MPU6050_PWR_MGMT_1		0x6B
//电源管理寄存器2：加速度计/陀螺仪各轴单独休眠控制
#define	MPU6050_PWR_MGMT_2		0x6C
//WHO_AM_I 器件ID寄存器，用来校验芯片是否正常通信，默认读出0x68
#define	MPU6050_WHO_AM_I		0x75

#endif
