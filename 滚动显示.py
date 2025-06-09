from machine import Pin, I2C, Timer
import ssd1306
import time

# 初始化I2C和OLED
i2c = I2C(scl=Pin(22), sda=Pin(23))  # 根据你的连接修改引脚号
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

counter = 0
temp = 60.0
b1 = 1
def update_display(timer):
    global counter
    global temp
    global b1
    oled.font_load("GB2312-12.fon")
    oled.fill(0)  # 清除屏幕内容
    oled.text("当前出水水温：{:.1f}°C".format(temp),0,0)
    oled.text("当前出水水量：{}ml".format(counter), 0, 20)  # 显示计数
    if counter < 200:
        counter += 1
        temp += b1 * 0.2
        oled.show()
    else:
        oled.text("茶香四溢，静待君品", 0, 40)
        oled.show()
    if temp > 75 or temp < 60:
        b1 = -b1
    
# 创建一个周期性定时器，每秒调用一次update_display函数
timer = Timer(0)
timer.init(period=10, mode=Timer.PERIODIC, callback=update_display)
    