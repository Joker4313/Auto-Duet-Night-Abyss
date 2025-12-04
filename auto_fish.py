import cv2
import numpy as np
import mss
import pydirectinput
import time
import os

# ================= 核心配置区域 =================

# 1. 区域设置
GAME_ROI = {"left": 2160, "top": 520, "width": 35, "height": 530}
BITE_ROI = {"left": 2005, "top": 950, "width": 350, "height": 350}

# 【新增】空白区域点击坐标 (用于关闭结算)
EXIT_CLICK_POS = (1800, 1000) 

# 2. 颜色参数
RING_LOWER = np.array([6, 50, 180])
RING_UPPER = np.array([10, 69, 247])

BLUE_LOWER = np.array([110, 150, 80])
BLUE_UPPER = np.array([128, 255, 255])
FISH_LOWER = np.array([0, 0, 180])
FISH_UPPER = np.array([179, 15, 255])

# 3. 阈值设置
COLOR_PIXEL_THRESHOLD = 1000  
CONFIDENCE_THRESHOLD = 0.8  

# ==============================================================

# 【修改点 1】同时加载两个模板：Space 和 E
templates = {}

# 加载 Space 模板
if os.path.exists("cast_icon.png"):
    templates['SPACE'] = cv2.imread("cast_icon.png", 0)
    print("✅ 已加载 Space 抛竿模板")
else:
    print("❌ 未找到 cast_icon.png (Space)")

# 加载 E 模板
if os.path.exists("cast_icon_e.png"):
    templates['E'] = cv2.imread("cast_icon_e.png", 0)
    print("✅ 已加载 E 抛竿模板")
else:
    print("⚠️ 未找到 cast_icon_e.png，遇到E键情况将无法自动抛竿！")


def check_icon(sct, template):
    """
    通用模板匹配函数
    """
    if template is None:
        return 0
    
    # 全屏搜索 (主显示器)
    monitor = sct.monitors[1] 
    img = np.array(sct.grab(monitor))
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    return max_val


def is_game_active(sct):
    """检测是否已经在玩小游戏"""
    img = np.array(sct.grab(GAME_ROI))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    return cv2.countNonZero(mask) > 100


def check_bite_by_color(sct):
    """颜色光圈检测"""
    img_bgra = np.array(sct.grab(BITE_ROI))
    img_hsv = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
    img_hsv = cv2.cvtColor(img_hsv, cv2.COLOR_BGR2HSV)
    mask_ring = cv2.inRange(img_hsv, RING_LOWER, RING_UPPER)
    return cv2.countNonZero(mask_ring)


def get_center_y(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) < 10:
            return None
        x, y, w, h = cv2.boundingRect(c)
        return y + h // 2
    return None


def auto_fishing_bot():
    print("✅ 智能钓鱼机器人 (双键支持版) 已启动！")
    print("支持自动识别 'Space' 或 'E' 进行抛竿。")
    time.sleep(2)

    with mss.mss() as sct:
        state = "IDLE"
        no_fish_timer = 0
        is_holding_space = False

        while True:
            # ================= 状态 0: 寻找抛竿时机 (IDLE) =================
            if state == "IDLE":
                if is_game_active(sct):
                    print("⚠️ 游戏进行中，直接接管控鱼！")
                    state = "PLAYING"
                    continue

                # 【修改点 2】分别检测两个图标
                conf_space = check_icon(sct, templates.get('SPACE'))
                conf_e = check_icon(sct, templates.get('E'))

                # 优先判断 Space (通常 Space 是默认)
                if conf_space > CONFIDENCE_THRESHOLD:
                    print(f"👀 发现 Space 图标 (相似度: {conf_space:.2f}) -> 按 Space 抛竿")
                    time.sleep(0.5)
                    pydirectinput.press("space") # 动作：按 Space
                    time.sleep(2.5)
                    state = "WAITING"

                # 其次判断 E (特殊任务)
                elif conf_e > CONFIDENCE_THRESHOLD:
                    print(f"👀 发现 E 图标 (相似度: {conf_e:.2f}) -> 按 E 抛竿")
                    time.sleep(0.5)
                    pydirectinput.press("e")     # 动作：按 E
                    time.sleep(2.5)
                    state = "WAITING"
                
                else:
                    # 都没找到
                    pass

                time.sleep(0.5)

            # ================= 状态 1: 抛竿动作已合并到 IDLE 中 =================
            # 注意：上面的代码直接在 IDLE 里执行了 press 操作并跳到了 WAITING
            # 所以原来的 "CAST" 状态可以省略，或者保留结构但不进入

            # ================= 状态 2: 等待光圈 (WAITING) =================
            elif state == "WAITING":
                matched_pixels = check_bite_by_color(sct)

                if matched_pixels > COLOR_PIXEL_THRESHOLD:
                    print(f"⚡ 咬钩! (像素: {matched_pixels}) -> 提竿!")
                    pydirectinput.press("space") # 提竿通常还是 Space，如果这里也是 E，请修改
                    time.sleep(0.2)
                    state = "PLAYING"
                    no_fish_timer = time.time()
                    print(">>> 进入小游戏")

                time.sleep(0.05)

            # ================= 状态 3: 玩小游戏 (PLAYING) =================
            elif state == "PLAYING":
                game_img = np.array(sct.grab(GAME_ROI))
                hsv = cv2.cvtColor(game_img, cv2.COLOR_BGRA2BGR)
                hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)

                mask_bar = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
                mask_fish = cv2.inRange(hsv, FISH_LOWER, FISH_UPPER)

                bar_y = get_center_y(mask_bar)
                fish_y = get_center_y(mask_fish)

                if bar_y is not None and fish_y is not None:
                    no_fish_timer = time.time()
                    diff = fish_y - bar_y
                    tolerance = 20

                    if diff < -tolerance:
                        if not is_holding_space:
                            pydirectinput.keyDown("space")
                            is_holding_space = True
                    elif diff > tolerance:
                        if is_holding_space:
                            pydirectinput.keyUp("space")
                            is_holding_space = False
                    else:
                        if is_holding_space:
                            pydirectinput.keyUp("space")
                            is_holding_space = False
                else:
                    if is_holding_space:
                        pydirectinput.keyUp("space")
                        is_holding_space = False

                    if time.time() - no_fish_timer > 3.0:
                        print("🎉 钓鱼结束，准备退出结算...")
                        time.sleep(1) 
                        
                        # 点击退出结算
                        print(f"🖱️ 点击坐标 {EXIT_CLICK_POS}")
                        pydirectinput.moveTo(EXIT_CLICK_POS[0], EXIT_CLICK_POS[1])
                        time.sleep(0.2)
                        pydirectinput.click()
                        time.sleep(1.5)
                        
                        state = "IDLE"

            time.sleep(0.01)

if __name__ == "__main__":
    auto_fishing_bot()