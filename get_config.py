import cv2
import numpy as np
import mss

# ================= 配置区域 =================
# 【关键】请在这里填入你要调试的区域坐标
# 1. 调试“蓝条/鱼”时，填入中间长条的坐标
# 2. 调试“光圈”时，填入右下角图标的坐标
MONITOR = {"left": 2005, "top": 950, "width": 350, "height": 350}
# ===========================================


def nothing(x):
    pass


def run_hsv_tuner():
    win_ctrl = "Controls"
    win_view = "Preview (Left:Original Right:Filter)"

    cv2.namedWindow(win_ctrl)
    cv2.resizeWindow(win_ctrl, 400, 300)
    cv2.namedWindow(win_view)

    # ==========================================
    # 【新增】设置窗口置顶 (Always on Top)
    # 1 表示置顶，0 表示取消
    # ==========================================
    try:
        cv2.setWindowProperty(win_ctrl, cv2.WND_PROP_TOPMOST, 1)
        cv2.setWindowProperty(win_view, cv2.WND_PROP_TOPMOST, 1)
    except:
        print("⚠️ 当前 OpenCV 版本不支持置顶属性，窗口可能无法保持最前。")

    # 创建6个滑动条
    cv2.createTrackbar("H Min", win_ctrl, 0, 179, nothing)
    cv2.createTrackbar("H Max", win_ctrl, 179, 179, nothing)
    cv2.createTrackbar("S Min", win_ctrl, 0, 255, nothing)
    cv2.createTrackbar("S Max", win_ctrl, 255, 255, nothing)
    cv2.createTrackbar("V Min", win_ctrl, 0, 255, nothing)
    cv2.createTrackbar("V Max", win_ctrl, 255, 255, nothing)

    print(f"✅ 调试器启动！监控区域: {MONITOR}")
    print(f"👉 目标：调节滑条，让你的【目标物体】变白，【背景】变黑。")
    print(f"⌨️  按 's' 保存参数，按 'q' 退出。")

    with mss.mss() as sct:
        while True:
            try:
                # 截屏
                img_bgra = np.array(sct.grab(MONITOR), dtype=np.uint8)
            except:
                print("❌ 坐标错误，请检查 MONITOR 配置")
                break

            # 转换颜色
            img_bgr = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

            # 检查窗口是否关闭
            if cv2.getWindowProperty(win_ctrl, cv2.WND_PROP_VISIBLE) < 1:
                break

            # 读取滑条
            h_min = cv2.getTrackbarPos("H Min", win_ctrl)
            h_max = cv2.getTrackbarPos("H Max", win_ctrl)
            s_min = cv2.getTrackbarPos("S Min", win_ctrl)
            s_max = cv2.getTrackbarPos("S Max", win_ctrl)
            v_min = cv2.getTrackbarPos("V Min", win_ctrl)
            v_max = cv2.getTrackbarPos("V Max", win_ctrl)

            # 生成掩膜 (黑白图)
            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(hsv, lower, upper)

            # 生成预览 (原图 + 掩膜)
            mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            preview = np.hstack((img_bgr, mask_3ch))

            cv2.imshow(win_view, preview)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("s"):
                print(f"\n====== ✂️ 请复制以下代码 ======")
                print(f"LOWER = np.array([{h_min}, {s_min}, {v_min}])")
                print(f"UPPER = np.array([{h_max}, {s_max}, {v_max}])")
                print(f"==============================\n")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_hsv_tuner()
