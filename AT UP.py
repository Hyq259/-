import network
import time
import json
from simple import MQTTClient

# WiFi 配置
WIFI_SSID = "Redmi K50 Ultra"
WIFI_PASSWORD = "123456ab"

# OneNET 平台配置
PRODUCT_ID = "Y8FD68G1xP"
DEVICE_NAME = "dev1"
SERVER = "mqtts.heclouds.com"
PORT = 1883  # 或 8883（加密）
CLIENT_ID = DEVICE_NAME
USERNAME = PRODUCT_ID
PASSWORD = "version=2018-10-31&res=products%2FY8FD68G1xP%2Fdevices%2Fdev1&et=2053320694&method=md5&sign=XEH5dtWsZaHTx7JQkrrX4A%3D%3D"

# 物模型定义
WATER_TEMP_MODEL = "waterTemp"
CUSTOM_AMOUNT_MODEL = "customAmount"  # 新增自定义水量属性名


# 连接 WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            pass
    print("WiFi connected:", wlan.ifconfig())


# MQTT 回调函数
def sub_cb(topic, msg):
    print("Received message on topic {}: {}".format(topic.decode(), msg.decode()))
    try:
        data = json.loads(msg.decode())
        
        if isinstance(data, dict):  # 确保 data 是字典
            if "msg" in data and isinstance(data["msg"], dict):  # 确保 msg 是字典
                if "waterTemp" in data["msg"]:
                    print("Water temperature update:", data["msg"]["waterTemp"])
                if "customAmount" in data["msg"]:
                    print("Custom amount update:", data["msg"]["customAmount"])
            elif "code" in data and "msg" in data:
                print("Error from server: code={}, msg={}".format(data["code"], data["msg"]))
        else:
            print("Unexpected data format:", data)
            
    except Exception as e:
        print("Error processing message:", e)


# 生成 OneJSON 格式的数据点（支持多个参数）
def generate_onejson_multi_data_point(data_dict):
    timestamp = time.localtime()
    iso_time = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
        timestamp[0], timestamp[1], timestamp[2],
        timestamp[3], timestamp[4], timestamp[5]
    )
    
    return {
        "id": "123",
        "version": "1.0",
        "sys": {
            "ack": 0
        },
        "params": {
            key: {
                "value": value,
                "time": iso_time
            } for key, value in data_dict.items()
        }
    }


# 主函数
def main():
    # 连接 WiFi
    connect_wifi()
    
    # 创建 MQTT 客户端
    client = MQTTClient(
        client_id=CLIENT_ID,
        server=SERVER,
        port=PORT,
        user=USERNAME,
        password=PASSWORD,
        keepalive=60
    )
    
    # 设置回调函数
    client.set_callback(sub_cb)
    
    try:
        # 连接 MQTT 服务器
        print("Connecting to OneNET MQTT...")
        client.connect()
        print("Connected to OneNET MQTT")
        
        # 订阅主题
        topic_sub = "$sys/{}/{}/thing/property/post/reply".format(PRODUCT_ID, DEVICE_NAME)
        client.subscribe(topic_sub)
        print("Subscribed to {}".format(topic_sub))
        
        # 主循环
        counter = 0
        while True:
            # 检查消息
            client.check_msg()
            
            # 每10秒发布一次数据
            if counter % 10 == 0:
                # 生成模拟数据
                water_temp = 80.0 
                custom_amount = 200   # 示例：水量范围 200~690ml
                
                # 构建多参数数据
                data_dict = {
                    WATER_TEMP_MODEL: water_temp,
                    CUSTOM_AMOUNT_MODEL: custom_amount
                }
                
                # 创建 OneJSON 数据
                data = generate_onejson_multi_data_point(data_dict)
                json_data = json.dumps(data)
                
                # 发布主题
                topic_pub = "$sys/{}/{}/thing/property/post".format(PRODUCT_ID, DEVICE_NAME)
                client.publish(topic_pub, json_data)
                print("Published to {}: {}".format(topic_pub, json_data))
            
            counter += 1
            time.sleep(1)
            
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()
        print("Disconnected from MQTT")


if __name__ == "__main__":
    main()