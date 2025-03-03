import cv2
import numpy as np
import json
import os

# Đường dẫn lưu trạng thái khung
config_path = "config.json"

import cv2
import numpy as np
import json
import os

# Đường dẫn lưu trạng thái khung
config_path = "config.json"

def load_config():
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {"rect_x": 100, "rect_y": 100, "rect_w": 300, "rect_h": 200}

def save_config():
    with open(config_path, "w") as f:
        json.dump({"rect_x": rect_x, "rect_y": rect_y, "rect_w": rect_w, "rect_h": rect_h}, f)

config = load_config()
rect_x, rect_y, rect_w, rect_h = config["rect_x"], config["rect_y"], config["rect_w"], config["rect_h"]

is_dragging = False
is_resizing = False
corner_threshold = 10
corner_selected = None
start_x, start_y = 0, 0

def extend_line(p1, p2, length=1000):
    """ Kéo dài đường thẳng từ p1 đến p2 thêm một khoảng length """
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    norm = np.sqrt(dx**2 + dy**2)
    dx, dy = dx / norm, dy / norm  # Chuẩn hóa
    x2_ext, y2_ext = int(x2 + dx * length), int(y2 + dy * length)
    x1_ext, y1_ext = int(x1 - dx * length), int(y1 - dy * length)
    return (x1_ext, y1_ext), (x2_ext, y2_ext)

def reflect_line(p1, p2, boundary):
    """ Phản xạ đường thẳng khi chạm biên """
    x1, y1 = p1
    x2, y2 = p2
    bx1, by1, bx2, by2 = boundary

    # Tính toán góc của đường thẳng
    angle = np.arctan2(y2 - y1, x2 - x1)

    # Tìm giao điểm của đường thẳng và biên
    intersection = None
    if x2 < bx1 or x2 > bx2:
        x_intersect = bx1 if x2 < bx1 else bx2
        y_intersect = y1 + np.tan(angle) * (x_intersect - x1)
        if by1 <= y_intersect <= by2:
            intersection = (x_intersect, int(y_intersect))
            normal_angle = np.pi / 2  # Biên dọc
    elif y2 < by1 or y2 > by2:
        y_intersect = by1 if y2 < by1 else by2
        x_intersect = x1 + (y_intersect - y1) / np.tan(angle)
        if bx1 <= x_intersect <= bx2:
            intersection = (int(x_intersect), y_intersect)
            normal_angle = 0  # Biên ngang

    if intersection:
        # Tính toán góc phản xạ
        reflection_angle = 2 * normal_angle - angle

        # Tính toán điểm phản xạ
        length = 1000  # Độ dài đường phản xạ
        x3 = intersection[0] + length * np.cos(reflection_angle)
        y3 = intersection[1] + length * np.sin(reflection_angle)
        return intersection, (int(x3), int(y3))
    return None, None

def detect_and_extend_lines(frame):
    global rect_x, rect_y, rect_w, rect_h
    roi = frame[rect_y:rect_y + rect_h, rect_x:rect_x + rect_w] # Lấy ROI
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=10)

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            (x1_ext, y1_ext), (x2_ext, y2_ext) = extend_line((x1, y1), (x2, y2), length=2000)
            intersection, reflected = reflect_line((x1_ext, y1_ext), (x2_ext, y2_ext), (0, 0, rect_w, rect_h))
            if intersection and reflected:
                ix, iy = intersection
                rx, ry = reflected
                cv2.line(roi, (x1_ext, y1_ext), (ix, iy), (0, 255, 0), 2)
                cv2.line(roi, (ix, iy), (rx, ry), (0, 255, 0), 2)
            else:
                cv2.line(roi, (x1_ext, y1_ext), (x2_ext, y2_ext), (0, 255, 0), 2)

    cv2.rectangle(frame, (rect_x, rect_y), (rect_x + rect_w, rect_y + rect_h), (0, 0, 255), 2) # Vẽ khung chữ nhật
    return frame

def mouse_callback(event, x, y, flags, param):
    global rect_x, rect_y, rect_w, rect_h, is_dragging, is_resizing, corner_selected, start_x, start_y

    if event == cv2.EVENT_LBUTTONDOWN:
        if abs(x - rect_x) < corner_threshold and abs(y - rect_y) < corner_threshold:
            is_resizing = True
            corner_selected = "top_left"
        elif abs(x - (rect_x + rect_w)) < corner_threshold and abs(y - rect_y) < corner_threshold:
            is_resizing = True
            corner_selected = "top_right"
        elif abs(x - rect_x) < corner_threshold and abs(y - (rect_y + rect_h)) < corner_threshold:
            is_resizing = True
            corner_selected = "bottom_left"
        elif abs(x - (rect_x + rect_w)) < corner_threshold and abs(y - (rect_y + rect_h)) < corner_threshold:
            is_resizing = True
            corner_selected = "bottom_right"
        elif rect_x <= x <= rect_x + rect_w and rect_y <= y <= rect_y + rect_h:
            is_dragging = True
            start_x, start_y = x - rect_x, y - rect_y
        else:
            is_dragging = False
            is_resizing = False
            corner_selected = None
    elif event == cv2.EVENT_LBUTTONUP:
        is_dragging = False
        is_resizing = False
        corner_selected = None
        save_config()
    elif event == cv2.EVENT_MOUSEMOVE:
        if is_dragging:
            rect_x, rect_y = x - start_x, y - start_y
        elif is_resizing:
            if corner_selected == "top_left":
                rect_w += rect_x - x
                rect_h += rect_y - y
                rect_x, rect_y = x, y
            elif corner_selected == "top_right":
                rect_w = x - rect_x
                rect_h += rect_y - y
                rect_y = y
            elif corner_selected == "bottom_left":
                rect_w += rect_x - x
                rect_h = y - rect_y
                rect_x = x

def main():
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('Extended Lines')
    cv2.setMouseCallback('Extended Lines', mouse_callback)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        processed_frame = detect_and_extend_lines(frame)
        cv2.imshow('Extended Lines', processed_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()