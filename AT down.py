import network
import time
import urequests as requests
from ssd1306 import SSD1306_I2C  # 假设你已经安装了ssd1306库
from machine import Pin, I2C

# ===================== 配置部分 =====================
WIFI_SSID = "Redmi K50 Ultra"
WIFI_PASSWORD = "123456ab"

# OneNET 请求地址（查询设备属性）
URL = "https://iot-api.heclouds.com/thingmodel/query-device-property?product_id=Y8FD68G1xP&device_name=dev1"

# 签名 Authorization 头（从服务器或 Python 脚本中生成）
AUTHORIZATION = (
    "version=2018-10-31"
    "&res=products%2FY8FD68G1xP%2Fdevices%2Fdev1"
    "&et=2053320694"
    "&method=md5"
    "&sign=XEH5dtWsZaHTx7JQkrrX4A%3D%3D"
)

# 请求间隔（单位：秒）
INTERVAL = 10

i2c = I2C(scl=Pin(22), sda=Pin(23))
oled = SSD1306_I2C(128, 64, i2c)
# ===================================================

# 连接 WiFi 函数
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("WiFi connected:", wlan.ifconfig())

# 获取设备数据函数
def get_device_data():
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": AUTHORIZATION
    }

    try:
        response = requests.get(URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("获取成功！以下是设备属性：")
            water_temp = None
            customAmount = None
            for item in data.get("data", []):
                if item.get("identifier") == "customAmount":
                    customAmount = item.get("value", "无数据")
                if item.get("identifier") == "waterTemp":
                    water_temp = item.get("value", "无数据")
                    oled.font_load("GB2312-12.fon")
                    oled.fill(0)  # 清屏
                    oled.text("设定水温：{}°C".format(water_temp),0,0)
                    oled.text("设定水量：{}ml".format(customAmount),0,20)
                    oled.show()
        else:
            print("请求失败，状态码：", response.status_code)

    except Exception as e:
        print("错误：", e)

def display_on_oled(text,i,j):
    oled.font_load("GB2312-12.fon")
    #oled.fill(0)  # 清屏
    oled.text(text, i, j)  # 在(0,0)位置显示文本
    oled.show()

# 主程序逻辑
connect_wifi()

while True:
    get_device_data()
    time.sleep(INTERVAL)

