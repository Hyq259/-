from machine import Pin, PWM, Timer
import onewire, ds18x20
import time

dat = Pin(4)
relay_pin = Pin(2, Pin.OUT) #即热管继电器
shuibeng_pin = Pin(15,Pin.OUT) #水泵控制
in3 = Pin(26, Pin.OUT) # 推杆B IN3
in4 = Pin(25, Pin.OUT) # 推杆B IN4
enb = PWM(Pin(33), freq=1000, duty=0) # 推杆B ENB, 频率设为1kHz
ds_sensor = ds18x20.DS18X20(onewire.OneWire(dat))
roms = ds_sensor.scan()
print('发现设备:', roms)

relay_pin.value(1)
shuibeng_pin.value(0)

if not roms:
    print("⚠️ 没有找到 DS18B20！请检查接线和上拉电阻！")
# 设置按键引脚（用于触发序列）
button_trigger = Pin(13, Pin.IN, Pin.PULL_UP)  # 触发按钮

# ===== 步进电机控制引脚 =====
PUL = Pin(21, Pin.OUT)   # 脉冲信号
DIR = Pin(19, Pin.OUT)   # 方向控制
ENA = Pin(18, Pin.OUT)   # 使能控制

# ===== 常量设置 =====
Pulse = 800            # 每圈脉冲数
FREQ_US = 50           # 控制速度（越小越快，但不能太小避免丢步）

def motor_stop(in1_pin, in2_pin, pwm_pin):
    in1_pin.value(0)
    in2_pin.value(0)
    pwm_pin.duty(0)

def motor_forward(in1_pin, in2_pin, pwm_pin, speed=1023):  # 默认全速
    in1_pin.value(0)
    in2_pin.value(1)
    pwm_pin.duty(speed)
    
def motor_forwar(in1_pin, in2_pin, pwm_pin, speed=1023):  # 默认全速
    in1_pin.value(1)
    in2_pin.value(0)
    pwm_pin.duty(speed)
    
def Freq(freq_us):
    PUL.value(0)
    time.sleep_us(freq_us)
    PUL.value(1)
    time.sleep_us(freq_us)

def run_motor(direction, duration_ms):
    DIR.value(direction)  # 设置方向（0: 正转, 1: 反转）
    ENA.value(0)          # 使能电机
    
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
        Freq(FREQ_US)
    
    ENA.value(1)  # 禁用电机



def temperature_monitor(timer):
    if shuibeng_pin.value() == 1:  # 只有当启动引脚为高电平时才执行温度检测
        ds_sensor.convert_temp()
        time.sleep_ms(750)  # 等待转换完成

        for rom in roms:
            temp = ds_sensor.read_temp(rom)
            print("🌡️ 当前温度: {:.2f} °C".format(temp))

            # 控制继电器逻辑
            if temp > 85.0:
                relay_pin.value(1)  # 开启继电器
                print("🔥 温度高于85°C，继电器开启")
            elif temp < 80.0:
                relay_pin.value(0)  # 关闭继电器
                print("❄️ 温度低于80°C，继电器关闭")
            else:
                print("🌡️ 温度在80~85°C之间，保持继电器状态不变")
    else:
        print("🛑 Pin 15 不是高电平，跳过本次温度检测")

# 设置定时器每1秒触发一次温度监测
temp_timer = Timer(-1)
temp_timer.init(period=1000, mode=Timer.PERIODIC, callback=temperature_monitor)

print("⏳ 程序已启动，等待Pin 15 高电平信号...")

try:
    while True:
            print("触发序列开始：推杆B正转 -> 步进电机正转")
            time.sleep(1)
            motor_forward(in3, in4, enb)
            print("推杆B正转")
            time.sleep(1.5)  # 等待3秒
            motor_stop(in3, in4, enb)
            time.sleep(2)
            # 步进电机正转3秒
            run_motor(0, 5700)  # 0 表示正转, 持续3000毫秒
            print("步进电机正转结束")
            relay_pin.value(1)
            time.sleep_ms(2000)
            shuibeng_pin.value(1)
            time.sleep_ms(18000)
            shuibeng_pin.value(0)
            relay_pin.value(1)
            motor_forwar(in3, in4, enb)
            # 推杆B正转3秒
            time.sleep(3)
            # 等待按键释放
            #while button_trigger.value() == 0:
            #    time.sleep_ms(10)
        
            time.sleep_ms(3000)
            run_motor(1, 5700)
            time.sleep_ms(100000)

except KeyboardInterrupt:
    print("手动中断程序...")
finally:
    temp_timer.deinit()  # 确保停止定时器
    relay_pin.value(1)
    shuibeng_pin.value(0)
    print("🔌 程序结束，继电器已关闭。")
            
if __name__ == "__main__":
    main()