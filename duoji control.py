from machine import Pin, PWM, UART
import time

# 第一个舵机配置
servo_pin_1 = Pin(19)  # 控制第一个舵机的引脚
servo_1 = PWM(servo_pin_1, freq=50)

# 第二个舵机配置
servo_pin_2 = Pin(21)  # 控制第二个舵机的引脚
servo_2 = PWM(servo_pin_2, freq=50)

# 设置按钮引脚
button_left = Pin(5, Pin.IN, Pin.PULL_UP)  # 左转按钮
button_right = Pin(18, Pin.IN, Pin.PULL_UP)  # 右转按钮

# 初始化串口（用于接收指令）
uart = UART(2, baudrate=115200, tx=17, rx=16)

def angle_to_duty(angle):
    return int(40 + (angle * 75 / 180))  # duty范围：40~115

def set_servo_angle(servo, angle):
    servo.duty(angle_to_duty(angle))

try:
    current_angle_1 = 90   # 第一个舵机初始角度
    current_angle_2 = 0     # 第二个舵机初始角度
    step = 2                # 角度步长
    direction_1 = None      # 第一个舵机当前方向
    direction_2 = None      # 第二个舵机当前方向

    while True:
        if uart.any():
            data = uart.read()
            try:
                text = data.decode('utf-8').strip()
                if text == "left":
                    direction_1 = "serial_left"
                    print("收到指令：左转")
                elif text == "right":
                    direction_1 = "serial_right"
                    print("收到指令：右转")
                elif text == "up":
                    direction_2 = "serial_up"
                    print("收到指令：上转")
                elif text == "down":
                    direction_2 = "serial_down"
                    print("收到指令：下转")
                else:
                    print("未知指令:", text)
            except UnicodeError:
                print("解码失败，原始数据:", data)

        if not button_left.value():
            direction_1 = "button_left"
            print("按钮左转")
        elif not button_right.value():
            direction_1 = "button_right"
            print("按钮右转")

        if direction_1 in ["serial_right", "button_right"]:
            current_angle_1 = max(current_angle_1 - step, 0)
        elif direction_1 in ["serial_left", "button_left"]:
            current_angle_1 = min(current_angle_1 + step, 180)

        if direction_2 == "serial_up":
            current_angle_2 = min(current_angle_2 + step, 180)
        elif direction_2 == "serial_down":
            current_angle_2 = max(current_angle_2 - step, 0)

        set_servo_angle(servo_1, current_angle_1)
        set_servo_angle(servo_2, current_angle_2)

        direction_1 = None  # 重置方向
        direction_2 = None  # 重置方向

        time.sleep(0.1)

except KeyboardInterrupt:
    print("程序结束")
    servo_1.deinit()
    servo_2.deinit()