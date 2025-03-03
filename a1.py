import cv2
import numpy as np

def extend_line(p1, p2, length=2000):
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    norm = np.sqrt(dx**2 + dy**2)
    dx, dy = dx / norm, dy / norm
    return (int(x1 - dx * length), int(y1 - dy * length)), (int(x2 + dx * length), int(y2 + dy * length))

def reflect_line(p1, p2, bounds):
    x1, y1 = p1
    x2, y2 = p2
    rect_x, rect_y, rect_w, rect_h = bounds
    
    if x2 <= rect_x or x2 >= rect_x + rect_w:
        x2 = 2 * rect_x - x2 if x2 <= rect_x else 2 * (rect_x + rect_w) - x2
    if y2 <= rect_y or y2 >= rect_y + rect_h:
        y2 = 2 * rect_y - y2 if y2 <= rect_y else 2 * (rect_y + rect_h) - y2
    
    return (x1, y1), (x2, y2)

def detect_and_extend_lines(frame):
    global rect_x, rect_y, rect_w, rect_h
    roi = frame[rect_y:rect_y + rect_h, rect_x:rect_x + rect_w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=10)
    
    best_line = None
    if lines is not None:
        best_line = max(lines, key=lambda line: np.linalg.norm([line[0][2] - line[0][0], line[0][3] - line[0][1]]))
    
    if best_line is not None:
        x1, y1, x2, y2 = best_line[0]
        (x1_ext, y1_ext), (x2_ext, y2_ext) = extend_line((x1, y1), (x2, y2), length=2000)
        intersection, reflected = reflect_line((x1_ext, y1_ext), (x2_ext, y2_ext), (0, 0, rect_w, rect_h))
        
        if intersection and reflected:
            ix, iy = intersection
            rx, ry = reflected
            cv2.line(roi, (x1_ext, y1_ext), (ix, iy), (0, 255, 0), 2)
            cv2.line(roi, (ix, iy), (rx, ry), (255, 0, 0), 2)
        else:
            cv2.line(roi, (x1_ext, y1_ext), (x2_ext, y2_ext), (0, 255, 0), 2)
    
    cv2.rectangle(frame, (rect_x, rect_y), (rect_x + rect_w, rect_y + rect_h), (0, 0, 255), 2)
    return frame

cap = cv2.VideoCapture(0)
rect_x, rect_y, rect_w, rect_h = 100, 100, 400, 300

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = detect_and_extend_lines(frame)
    cv2.imshow('Bi-a Tracking', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
