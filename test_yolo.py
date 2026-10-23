from ultralytics import YOLO
import cv2

model = YOLO("best.pt")
# 读取你这张截图
img = cv2.imread("test.jpg")
results = model(img, device='cpu', conf=0.1) # 👈 注意：把置信度降到极低 0.1，看看能不能憋出框来

for box in results[0].boxes:
    cls_id = int(box.cls[0])
    conf = float(box.conf[0])
    print(f"识别到: {model.names[cls_id]}, 置信度: {conf:.3f}")

# 保存带框的图
results[0].save("test_result.jpg")
# 这个是测试yolo识别的代码