import cv2
import numpy as np
import mss
import time
import pydirectinput

# ================= 基础工具函数 =================
def find_image_on_screen(template_path, threshold=0.7):
    template = cv2.imread(template_path)
    if template is None: return None
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        screen_img = np.array(screenshot)
        screen_img = cv2.cvtColor(screen_img, cv2.COLOR_BGRA2BGR)
    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        h, w = template.shape[:2]
        return (max_loc[0] + w // 2, max_loc[1] + h // 2)
    return None

# ================= 蓝量检测 =================
mp_locked_rect = None 
def lock_mp_location(template_path="mp_bar.png"):
    global mp_locked_rect
    template = cv2.imread(template_path)
    if template is None: return False
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        screen_img = np.array(screenshot)
        screen_img = cv2.cvtColor(screen_img, cv2.COLOR_BGRA2BGR)
    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.7:
        x, y = max_loc
        h, w = template.shape[:2]
        mp_locked_rect = {"top": y, "left": x, "width": w, "height": h}
        return True
    return False

def check_mp_percentage():
    global mp_locked_rect
    if mp_locked_rect is None: return 100
    with mss.mss() as sct:
        screenshot = sct.grab(mp_locked_rect)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([140, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        col_counts = np.sum(mask > 0, axis=0)
        h = mp_locked_rect["height"]
        w = mp_locked_rect["width"]
        valid_cols = np.where(col_counts > (h * 0.5))[0]
        if len(valid_cols) > 0:
            return (valid_cols[-1] / w) * 100
    return 100

# ================= 蓝条消失检测 =================
def is_mp_gone():
    global mp_locked_rect
    if mp_locked_rect is None:
        return True 
    with mss.mss() as sct:
        screenshot = sct.grab(mp_locked_rect)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([140, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        blue_pixels = cv2.countNonZero(mask)
        if blue_pixels < 10:
            return True
    return False

def is_screen_black(threshold=30):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        region = {"top": monitor["height"]//2 - 100, "left": monitor["width"]//2 - 100, "width": 200, "height": 200}
        screenshot = sct.grab(region)
        img = np.array(screenshot)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return np.mean(gray) < threshold

def click_at(pos):
    if not pos: return
    x, y = pos
    pydirectinput.moveTo(x, y)
    time.sleep(0.1)
    pydirectinput.mouseDown(button='left')
    time.sleep(0.05)
    pydirectinput.mouseUp(button='left')

def use_fabao():
    print("  🛑 释放法宝并开启 P 保护...")
    pydirectinput.keyUp('a')
    pydirectinput.keyUp('d')
    time.sleep(0.15) 
    pydirectinput.press('h')
    time.sleep(0.1)
    pydirectinput.press('h')
    pydirectinput.press('p')
    time.sleep(0.8) 

# ================= 通关退出逻辑（只点一次） =================
def exit_dungeon():
    print("🚪 通关！按 M 键打开设置...")
    pydirectinput.keyUp('a')
    pydirectinput.keyUp('d')
    time.sleep(0.5)
    
    pydirectinput.press('m')
    time.sleep(1.5) 
    
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        return_x = int(monitor["width"] * 0.5)
        return_y = int(monitor["height"] * 0.35)
        
        print(f"  🎯 精准点击【返回地图】坐标: ({return_x}, {return_y})")
        click_at((return_x, return_y))
        # 删除了第二次点击，只点一次
    time.sleep(2)

# ================= 死亡处理逻辑（只点一次） =================
def handle_death():
    print("💀 确认死亡！紧急刹车！")
    pydirectinput.keyUp('d')
    pydirectinput.keyUp('a')
    pydirectinput.keyUp('l')
    pydirectinput.keyUp('j')
    
    # 延长等待时间到 1 秒，确保弹窗完全出来
    time.sleep(1.0) 
    
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        width = monitor["width"]
        height = monitor["height"]
        
        return_x = int(width * 0.535)
        return_y = int(height * 0.54)
        
        print(f"  🎯 精准点击【返回地图】坐标: ({return_x}, {return_y})")
        click_at((return_x, return_y))
        # 删除了第二次点击，只点一次
        
    time.sleep(2.5) # 等待地图加载完毕
    print("  ✅ 已返回大地图，准备重新开始。")

# ================= 主控逻辑 =================
print("请在 1 秒内切换到游戏...")
time.sleep(1)

current_state = "MAP"
pydirectinput.keyUp('d')
pydirectinput.keyUp('a')

last_mp_check = 0
mp_cd_time = 0
black_count = 0 

try:
    while True:
        if current_state == "MAP":
            print("[状态] 寻找金蟾宝宫...")
            pos = find_image_on_screen("jinchang.png", threshold=0.7)
            if pos:
                print("找到副本，点击进入！")
                click_at(pos)
                print("等待进图加载（4.5秒）...")
                time.sleep(4.5)
                pydirectinput.press('o')
                lock_mp_location()
                black_count = 0 
                current_state = "RUNNING"
            # else:
            #     time.sleep(2)
            #     print("  🔄 没看到地图，尝试盲点中间清理弹窗...")
            #     with mss.mss() as sct:
            #         monitor = sct.monitors[1]
            #         click_at((monitor["width"]//2, monitor["height"]//2))
            # time.sleep(0.5)

        elif current_state == "RUNNING":
            print("[状态] 向右狂奔中...")
            pydirectinput.press('d') 
            time.sleep(0.05)
            pydirectinput.keyDown('d') 
            
            run_start = time.time()
            while time.time() - run_start < 2.5:
                pydirectinput.press('u') 
                current_time = time.time()
                
                if current_time > last_mp_check and current_time > mp_cd_time:
                    mp = check_mp_percentage()
                    if mp < 40: 
                        use_fabao() 
                        pydirectinput.keyDown('d') 
                        mp_cd_time = time.time() + 8 
                    last_mp_check = time.time() + 1 
                
                if is_screen_black() or is_mp_gone():
                    pydirectinput.keyUp('d')
                    current_state = "SCAN_MODE"
                    break
                time.sleep(0.01) 
                
            if current_state != "SCAN_MODE":
                pydirectinput.keyUp('d')
                current_state = "CORNER_FIGHT"

        elif current_state == "CORNER_FIGHT":
            print("[状态] 墙角狂暴输出中...")
            pydirectinput.keyDown('a')
            time.sleep(0.1) 
            
            fight_start = time.time()
            while time.time() - fight_start < 3.5:
                pydirectinput.press('l')
                pydirectinput.press('j')
                current_time = time.time()
                
                if current_time > last_mp_check and current_time > mp_cd_time:
                    mp = check_mp_percentage()
                    if mp < 40: 
                        use_fabao() 
                        pydirectinput.keyDown('a') 
                        mp_cd_time = time.time() + 8 
                    last_mp_check = time.time() + 1 
                
                if is_screen_black() or is_mp_gone():
                    pydirectinput.keyUp('a')
                    current_state = "SCAN_MODE"
                    break
                time.sleep(0.01) 
                
            if current_state != "SCAN_MODE":
                pydirectinput.keyUp('a')
                current_state = "RUNNING"

        elif current_state == "SCAN_MODE":
            print("🌑 发现疑似黑屏/UI消失，开启雷达扫描（0.3秒/次）...")
            missing_count = 0
            is_transition = False
            
            for i in range(3):
                time.sleep(0.3)
                if not is_mp_gone():
                    print("  🔆 蓝条恢复，判定为转场！")
                    is_transition = True
                    break
                else:
                    missing_count += 1
                    print(f"  🌑 第 {missing_count} 次未检测到蓝条...")
            
            if is_transition:
                black_count += 1
                print(f"  ✅ 转场成功，通关黑屏次数 +1 (当前 {black_count})")
                if black_count >= 4:
                    print("🏁 第 4 次黑屏结束，准备通关退出！")
                    current_state = "EXIT"
                else:
                    current_state = "RUNNING"
            else:
                current_state = "DEAD"

        elif current_state == "DEAD":
            handle_death()
            black_count = 0 
            current_state = "MAP"

        elif current_state == "EXIT":
            exit_dungeon()
            current_state = "MAP"

except KeyboardInterrupt:
    print("\n[停止] 用户终止脚本。")
finally:
    pydirectinput.keyUp('d')
    pydirectinput.keyUp('a')
    pydirectinput.keyUp('u')
    pydirectinput.keyUp('l')
    pydirectinput.keyUp('j')