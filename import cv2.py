import cv2
import numpy as np
import serial
import time
import threading
from tensorflow.keras.models import load_model

# 加载预训练的情绪识别模型
try:
    emotion_model = load_model('c:/Users/yu/Desktop/face_classification-master/models/ck+_emotion_recognition_model_experiment_1.h5', compile=False)
    emotion_recognition_available = True
except Exception as e:
    print(f"无法加载情绪识别模型: {str(e)}")
    emotion_recognition_available = False

# 定义情绪标签
emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral', 'Contempt']

# 初始化串口连接
try:
    ser = serial.Serial('COM21', 115200)
    print("串口已连接")
except Exception as e:
    print("无法连接串口:", str(e))
    exit()

# 打开摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("无法打开摄像头，请检查索引号或设备连接")
    exit()
else:
    print("摄像头已打开")

# 加载人脸检测器
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
if face_cascade.empty():
    print("未能加载人脸检测器，请检查路径是否正确")
    exit()
else:
    print("人脸检测器加载成功")

# 全局变量
global_str = "Hello, World!"
global_j = 0  # 坐姿时间计数器
k = 0         # 离开时间计数器

# 发送命令到串口
def send_command(command):
    try:
        ser.write((command + '\n').encode())  # 添加换行符确保接收端识别
    except Exception as e:
        print("串口发送失败:", str(e))

# 情绪识别函数
def detect_emotion(face_roi):
    if not emotion_recognition_available:
        return "N/A"
        
    face_roi = cv2.resize(face_roi, (48, 48))  # 调整大小以匹配模型输入（CK+ 使用 48x48）
    face_roi = face_roi.astype("float") / 255.0  # 归一化
    face_roi = np.expand_dims(face_roi, axis=-1)  # 增加通道维度
    face_roi = np.expand_dims(face_roi, axis=0)   # 增加批次维度

    preds = emotion_model.predict(face_roi)[0]
    emotion_label = emotion_labels[np.argmax(preds)]
    return emotion_label

# 定时任务：记录坐姿时间并提醒休息
def my_function():
    global global_j, k

    if global_str == "no face":
        k += 1
        if k > 60:  # 如果1分钟没检测到人脸，清零计时
            global_j = 0
            k = 0
    else:
        global_j += 1
        k = 0
        print(f"已连续使用电脑: {global_j} 秒")
        if global_j > 300:  # 连续使用5分钟提示休息
            print("建议休息一下！")
            send_command("rest")
            # global_j = 0  # 可选：重置计时

    # 重新启动定时器（每秒执行一次）
    timer = threading.Timer(1.0, my_function)
    timer.start()

# 启动定时器
timer = threading.Timer(1.0, my_function)
timer.start()

# 主循环：读取摄像头帧并处理
while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取帧，请检查摄像头是否断开")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) > 0:
        x, y, w, h = faces[0]
        center_x = x + w // 2
        center_y = y + h // 2
        
        # 控制逻辑：左转 / 右转 / 居中
        if center_x < 200:
            send_command('left')
            #print('向左转')
            global_str = "left"
            time.sleep(0.1)
        elif center_x > 440:
            send_command('right')
            #print('向右转')
            global_str = "right"
            time.sleep(0.1)
        elif center_y < 180:
            send_command('up')
            #print('向上转')
            global_str = "up"
            time.sleep(0.1)
        elif center_y > 300:
            send_command('down')
            #print('向下转')
            global_str = "down"
            time.sleep(0.1)    
        elif 200 <= center_x <= 440 and 180 <= center_y <= 300 and global_str != "center":
            send_command('center')
            #print('居中')
            global_str = "center"
            time.sleep(0.1)

        # 情绪识别
        face_roi = gray[y:y+h, x:x+w]
        emotion_label = detect_emotion(face_roi)
        
        # 绘制人脸矩形框和情绪标签
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(frame, emotion_label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    else:
        global_str = "no face"

    # 显示图像
    cv2.imshow('Integrated System', frame)

    # 按 q 键退出程序
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

# 清理资源
timer.cancel()
cap.release()
ser.close()
cv2.destroyAllWindows()
print("程序已结束")