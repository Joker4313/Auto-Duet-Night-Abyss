import cv2
import numpy as np
import mss
import pydirectinput
import time

# ================= 核心配置区域 =================

# 1. 监控区域 (保持你之前设置的)
MONITOR = {'left': 2160, 'top': 520, 'width': 35, 'height': 530}

# 2. 视觉识别参数 (使用你调试好的参数)
# 蓝条 (Catcher)
BLUE_LOWER = np.array([110, 150, 80])
BLUE_UPPER = np.array([128, 255, 255])

# 鱼 (Fish)
FISH_LOWER = np.array([0, 0, 180])
FISH_UPPER = np.array([179, 15, 255])

# 3. 游戏手感微调
THRESHOLD = 20 

# ==============================================

def get_center_y(mask):
    """ 计算掩膜中白色区域的中心 Y 坐标 """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        # 过滤过小的噪点 (例如小于10像素的误识别)
        if cv2.contourArea(c) < 10:
            return None
        x, y, w, h = cv2.boundingRect(c)
        return y + h // 2 
    return None

def auto_fisher():
    print("✅ 脚本已启动！")
    print("🛡️ 安全模式：只有同时看到蓝条和鱼时才会操作。")
    print("按 'Ctrl + C' 停止脚本。")
    time.sleep(2)

    with mss.mss() as sct:
        # 状态标记
        is_holding = False
        last_status = "IDLE" # 记录上一次状态，防止print刷屏

        while True:
            # 1. 极速截屏与图像处理
            img_bgra = np.array(sct.grab(MONITOR))
            img_hsv = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
            img_hsv = cv2.cvtColor(img_hsv, cv2.COLOR_BGR2HSV)

            # 2. 识别目标
            mask_bar = cv2.inRange(img_hsv, BLUE_LOWER, BLUE_UPPER)
            mask_fish = cv2.inRange(img_hsv, FISH_LOWER, FISH_UPPER)

            bar_y = get_center_y(mask_bar)
            fish_y = get_center_y(mask_fish)

            # ================= 核心状态监测 =================
            
            # 只有当两者都存在(不为None)时，才视为有效状态
            if bar_y is not None and fish_y is not None:
                
                # [状态更新] 如果之前是空闲，现在变成了钓鱼，打印提示
                if last_status == "IDLE":
                    print("🎣 监测到目标，开始自动控制...")
                    last_status = "FISHING"

                # --- 正常的PID控制逻辑 ---
                diff = fish_y - bar_y
                
                if diff < -THRESHOLD: # 鱼在上方，追！
                    if not is_holding:
                        pydirectinput.keyDown('space')
                        is_holding = True
                
                elif diff > THRESHOLD: # 鱼在下方，放！
                    if is_holding:
                        pydirectinput.keyUp('space')
                        is_holding = False
                
                else: # 重叠中，维持悬停
                    if is_holding:
                        pydirectinput.keyUp('space')
                        is_holding = False
                    # 可选：点按维持高度
                    # pydirectinput.press('space')

            else:
                # ================= 丢失目标 =================
                # 无论是鱼跑了，还是蓝条没了，统统视为异常/结束
                
                if is_holding:
                    # ⚠️ 紧急保险：只要丢失视野，必须立刻松开空格，防止卡死
                    pydirectinput.keyUp('space')
                    is_holding = False
                
                # [状态更新]
                if last_status == "FISHING":
                    print("💤 目标丢失 (钓鱼结束或中断)，等待中...")
                    last_status = "IDLE"

            # 极短休眠
            time.sleep(0.01)

if __name__ == "__main__":
    auto_fisher()