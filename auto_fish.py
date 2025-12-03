import cv2
import mss
import numpy as np
import pyautogui
import time
import keyboard

# ================= 核心配置区 =================
pyautogui.PAUSE = 0 
GAME_REGION = {'left': 2160, 'top': 520, 'width': 35, 'height': 530}

# 颜色阈值 (保持宽松，靠几何规则来过滤)
LOWER_WHITE = np.array([0, 0, 150])    
UPPER_WHITE = np.array([180, 50, 255]) 
LOWER_BLUE = np.array([80, 40, 100])   
UPPER_BLUE = np.array([140, 255, 255])

# 控制参数
KEY_BIND = 'space'
DEAD_ZONE = 8        
Y_OFFSET = -15       
SLOW_ZONE = 80      

# ============================================

def get_positions(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    
    mask_w = cv2.inRange(hsv, LOWER_WHITE, UPPER_WHITE)
    mask_b = cv2.inRange(hsv, LOWER_BLUE, UPPER_BLUE)
    mask = cv2.bitwise_or(mask_w, mask_b)
    
    # 膨胀让物体连通
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    potential_fish = []
    potential_bar = []
    
    for c in contours:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        center_y = int(y + h / 2)
        
        # === 精准分类器 ===
        
        # 1. 识别滑块 (Bar)
        # 特征：宽大，面积 > 80，宽度 > 25 (接近满宽)
        if area > 80 and w > 25 and area < 400:
            potential_bar.append({'y': center_y, 'area': area})
            
        # 2. 识别鱼 (Fish)
        # 特征：小巧，面积 15-70，宽度 6-20
        # 还要排除太靠边缘的噪点 (x > 2 且 x+w < 33)
        elif 15 < area < 80 and 6 < w < 20:
             # 简单的居中检查：鱼应该在中间
             if x > 2 and (x + w) < 33:
                potential_fish.append({'y': center_y, 'area': area})

    # 如果没找到滑块或没找到鱼，就返回 None
    if not potential_bar or not potential_fish:
        return None

    # 如果找到了多个，取面积最大的那个最靠谱
    potential_bar.sort(key=lambda x: x['area'], reverse=True)
    potential_fish.sort(key=lambda x: x['area'], reverse=True)
    
    bar_y = potential_bar[0]['y']
    fish_y = potential_fish[0]['y']
    
    return fish_y, bar_y

def run_precision_fishing():
    print(">>> 精准过滤模式启动 <<<")
    print("已应用针对性过滤规则：")
    print(" - 滑块: Area>80, Width>25")
    print(" - 鱼: 15<Area<80, 6<Width<20")
    
    sct = mss.mss()
    is_active = False
    lost_counter = 0
    
    while True:
        if keyboard.is_pressed('q'):
            break

        img = np.array(sct.grab(GAME_REGION))
        res = get_positions(img)
        
        if res is None:
            if is_active:
                lost_counter += 1
                if lost_counter > 20:
                    print("\n[状态] 丢失目标，待机...")
                    is_active = False
                    pyautogui.mouseUp()
            continue
            
        lost_counter = 0
        if not is_active:
            print("\n[状态] 锁定目标！开始控制！")
            is_active = True
            
        fish_y, bar_y = res
        
        # 控制逻辑
        target_y = fish_y + Y_OFFSET
        diff = bar_y - target_y
        abs_diff = abs(diff)
        
        if abs_diff < DEAD_ZONE:
            pass
        elif diff > 0: # 框在下
            if abs_diff > SLOW_ZONE:
                pyautogui.keyDown(KEY_BIND)
                time.sleep(0.04) 
                pyautogui.keyUp(KEY_BIND)
            else:
                pyautogui.keyDown(KEY_BIND)
                time.sleep(0.01) 
                pyautogui.keyUp(KEY_BIND)
                time.sleep(0.01) 
        else: # 框在上
            pyautogui.keyUp(KEY_BIND)
            time.sleep(0.01)

if __name__ == "__main__":
    run_precision_fishing()