/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "iap.h"
/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define FLASH_TEST_ADDR   0x0800F800U
#define FLASH_TEST_WORDS  8

#define APP_ADDR       0x08003000U
#define APP_SLOT_SIZE  0x6000U
#define SRAM_START     0x20000000U
#define SRAM_END       0x20005000U
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART1_UART_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
#include <stdio.h>

extern UART_HandleTypeDef huart1;

int fputc(int ch, FILE *f)
{
    (void)f;
    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, HAL_MAX_DELAY);
    return ch;
}

static void Flash_Test_Erase(void)
{
    FLASH_EraseInitTypeDef erase;
    uint32_t page_error = 0;

    erase.TypeErase = FLASH_TYPEERASE_PAGES;
    erase.PageAddress = FLASH_TEST_ADDR;
    erase.NbPages = 1;

    HAL_FLASH_Unlock();

    if (HAL_FLASHEx_Erase(&erase, &page_error) == HAL_OK)
    {
        printf("ERASE OK\r\n");
    }
    else
    {
        printf("ERASE FAIL, page_error=%lu\r\n", page_error);
    }

    HAL_FLASH_Lock();
}

static void Flash_Test_Write(void)
{
    uint16_t data[FLASH_TEST_WORDS] =
    {
        0x1111, 0x2222, 0x3333, 0x4444,
        0x5555, 0x6666, 0x7777, 0x8888
    };
    uint32_t i;
    HAL_StatusTypeDef status = HAL_OK;

    HAL_FLASH_Unlock();

    for (i = 0; i < FLASH_TEST_WORDS; i++)
    {
        status = HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD,
                                   FLASH_TEST_ADDR + i * 2,
                                   data[i]);
        if (status != HAL_OK)
        {
            break;
        }
    }

    HAL_FLASH_Lock();

    if (status == HAL_OK)
    {
        printf("WRITE OK\r\n");
    }
    else
    {
        printf("WRITE FAIL at word %lu\r\n", i);
    }
}
static void Flash_Test_Read(void)
{
    uint32_t i;

    printf("READ:");

    for (i = 0; i < FLASH_TEST_WORDS; i++)
    {
        printf(" %04X", *(__IO uint16_t *)(FLASH_TEST_ADDR + i * 2));
    }

    printf("\r\n");
}

static uint8_t App_IsValid(uint32_t app_addr)
{
    uint32_t msp   = *(uint32_t *)app_addr;
    uint32_t reset = *(uint32_t *)(app_addr + 4);

    /* 1. 栈顶必须落在 SRAM 范围内，且 8 字节对齐 */
    if (msp < SRAM_START || msp > SRAM_END || (msp & 0x7U) != 0U)
    {
        return 0;
    }

    /* 2. 复位向量必须在 App 槽内，且 Thumb 位为 1 */
    if ((reset & 1U) == 0U ||
        reset < app_addr ||
        reset >= app_addr + APP_SLOT_SIZE)
    {
        return 0;
    }

    return 1;
}



typedef void (*pFunction)(void);
 
static void JumpToApp(uint32_t app_addr)
{
    uint32_t msp   = *(uint32_t *)app_addr;
    uint32_t reset = *(uint32_t *)(app_addr + 4);
    pFunction jump = (pFunction)reset;
 
    __disable_irq();                 // 1. 关中断总
    HAL_DeInit();                    // 2.  复位 HAL 和外 （可 但推荐）设 选
    SysTick->CTRL = 0;               // 3.   关 SysTick
    SysTick->LOAD = 0;
    SysTick->VAL  = 0;
    SCB->VTOR = app_addr;            // 4.  向量表搬到 App
    __set_MSP(msp);                  // 5. 设置主栈指针
    jump();                          // 6.  跳到 App   的 Reset_Handler
}


/* ================= 第 1 课：启动窗口 ================= */
/* 在 timeout_ms 内从 USART1 收到任意一个字节就返回 1，超时返回 0 */
static uint8_t Boot_WaitForStart(uint32_t timeout_ms)
{
    uint8_t ch;
    uint32_t t0 = HAL_GetTick();

    while ((HAL_GetTick() - t0) < timeout_ms)
    {
        if (HAL_UART_Receive(&huart1, &ch, 1, 1) == HAL_OK)
        {
            return 1;
        }
    }
    return 0;
}

/* 留在 Boot 模式：本课先只把收到的字节回显出来，方便确认串口活着 */
static void Boot_StayInBoot(void)
{
    uint8_t ch;

    printf("Stay in BOOT mode.\r\n");
    while (1)
    {
        if (HAL_UART_Receive(&huart1, &ch, 1, 10) == HAL_OK)
        {
            printf("RX: 0x%02X\r\n", ch);
        }
    }
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
   MX_GPIO_Init();
  MX_USART1_UART_Init();

  /* USER CODE BEGIN 2 */
  printf("\r\nBootloader Start\r\n");

  /* 窗口内收到字节 → 进升级模式 */
  if (Boot_WaitForStart(2500))
  {
      printf("Enter BOOT mode.\r\n");
      IAP_Run();                    /* 不会返回 */
  }

  /* 没人理我 → App 有效就跳 */
  if (App_IsValid(APP_ADDR))
  {
      printf("APP valid, jump...\r\n");
      HAL_Delay(20);
      JumpToApp(APP_ADDR);          /* 不会返回 */
  }

  /* App 无效 → 留在 Boot 等升级 */
  printf("APP invalid, stay in BOOT.\r\n");
  IAP_Run();
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
