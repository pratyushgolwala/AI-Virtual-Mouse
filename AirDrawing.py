import cv2
import numpy as np
import mediapipe as mp
from collections import deque
import time

last_click_time = 0
click_delay = 1.0  # 1 second cooldown

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.5)

# Canvas and webcam setup
screen_width, screen_height = 1280, 720
canvas = np.ones((screen_height, screen_width, 3), dtype=np.uint8) * 255
cap = cv2.VideoCapture(1)

# UI layout
button_width = 120
button_height = 60
buttons = ['Blue', 'Red', 'Pen', 'Redo', 'Undo', 'Eraser']  # Reordered
button_colors = [(255, 0, 0), (0, 0, 255), (0, 0, 0), (80, 80, 80), (50, 50, 50), (128, 128, 128)]  # Match new order

# Drawing state
draw_color = (0, 0, 0)
mode = 'DRAW'  # or 'UI'
undo_stack = deque(maxlen=20)
redo_stack = deque(maxlen=20)
prev_x, prev_y = None, None
finger_x, finger_y = None, None

# Load pen icon
pen_icon = cv2.imread("pen_icon.png", cv2.IMREAD_UNCHANGED)
pen_icon = cv2.resize(pen_icon, (30, 30))

def overlay_icon(background, icon, x, y):
    h, w = icon.shape[:2]
    if icon.shape[2] == 4:
        alpha_s = icon[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s
        for c in range(3):
            background[y:y+h, x:x+w, c] = (
                alpha_s * icon[:, :, c] + alpha_l * background[y:y+h, x:x+w, c]
            )
    else:
        background[y:y+h, x:x+w] = icon

def finger_up(hand_landmarks):
    fingers = []
    tips = [8, 12, 16, 20]
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

def draw_ui(frame):
    spacing = 30
    total_top_width = 3 * button_width + 2 * spacing
    start_x_top = (screen_width - total_top_width) // 2

    for i, (btn, color) in enumerate(zip(buttons[:3], button_colors[:3])):  # Top row
        x1 = start_x_top + i * (button_width + spacing)
        y1 = spacing
        x2 = x1 + button_width
        y2 = y1 + button_height
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        cv2.putText(frame, btn, (x1 + 15, y1 + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    total_bottom_width = 3 * button_width + 2 * spacing
    start_x_bottom = (screen_width - total_bottom_width) // 2

    for i, (btn, color) in enumerate(zip(buttons[3:], button_colors[3:])):  # Bottom row
        x1 = start_x_bottom + i * (button_width + spacing)
        y1 = screen_height - spacing - button_height
        x2 = x1 + button_width
        y2 = y1 + button_height
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        cv2.putText(frame, btn, (x1 + 15, y1 + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

def check_ui_click(x, y):
    spacing = 30
    total_top_width = 3 * button_width + 2 * spacing
    start_x_top = (screen_width - total_top_width) // 2

    for i, btn in enumerate(buttons[:3]):  # Top row
        x1 = start_x_top + i * (button_width + spacing)
        y1 = spacing
        x2 = x1 + button_width
        y2 = y1 + button_height
        if x1 <= x <= x2 and y1 <= y <= y2:
            return btn

    total_bottom_width = 3 * button_width + 2 * spacing
    start_x_bottom = (screen_width - total_bottom_width) // 2

    for i, btn in enumerate(buttons[3:]):  # Bottom row
        x1 = start_x_bottom + i * (button_width + spacing)
        y1 = screen_height - spacing - button_height
        x2 = x1 + button_width
        y2 = y1 + button_height
        if x1 <= x <= x2 and y1 <= y <= y2:
            return btn

    return None

while cap.isOpened():
    spacing = 30
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (screen_width, screen_height))
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    draw_ui(canvas)

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        h, w, _ = frame.shape

        # Get index fingertip
        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        x, y = int(index_tip.x * w), int(index_tip.y * h)
        finger_x, finger_y = x, y

        # Mode switching
        finger_state = finger_up(hand_landmarks)
        if all(f == 1 for f in finger_state):
            mode = 'UI'
        elif finger_state[0] == 1 and sum(finger_state[1:]) == 0:
            mode = 'DRAW'

        if mode == 'UI':
            selected = check_ui_click(x, y)
            current_time = time.time()

            if selected:
                # Draw green highlight around selected button
                if selected in buttons[:3]:
                    idx = buttons[:3].index(selected)
                    total_top_width = 3 * button_width + 2 * spacing
                    start_x = (screen_width - total_top_width) // 2
                    rect_x1 = start_x + idx * (button_width + spacing)
                    rect_y1 = spacing
                else:
                    idx = buttons[3:].index(selected)
                    total_bottom_width = 3 * button_width + 2 * spacing
                    start_x = (screen_width - total_bottom_width) // 2
                    rect_x1 = start_x + idx * (button_width + spacing)
                    rect_y1 = screen_height - spacing - button_height

                cv2.rectangle(canvas, (rect_x1, rect_y1), (rect_x1 + button_width, rect_y1 + button_height), (0, 255, 0), 3)

                # Accept click only after cooldown
                if current_time - last_click_time > click_delay:
                    last_click_time = current_time

                    if selected == 'Pen':
                        draw_color = (0, 0, 0)
                    elif selected == 'Red':
                        draw_color = (0, 0, 255)
                    elif selected == 'Blue':
                        draw_color = (255, 0, 0)
                    elif selected == 'Eraser':
                        draw_color = (255, 255, 255)
                    elif selected == 'Undo' and undo_stack:
                        redo_stack.append(canvas.copy())
                        canvas = undo_stack.pop()
                    elif selected == 'Redo' and redo_stack:
                        undo_stack.append(canvas.copy())
                        canvas = redo_stack.pop()

        elif mode == 'DRAW':
            if index_tip.y < middle_tip.y:  # Only draw if index is above middle
                if prev_x is not None and prev_y is not None:
                    undo_stack.append(canvas.copy())

                    # Increased thickness for eraser
                    line_thickness = 30 if draw_color == (255, 255, 255) else 4
                    cv2.line(canvas, (prev_x, prev_y), (x, y), draw_color, line_thickness)
                prev_x, prev_y = x, y
            else:
                prev_x, prev_y = None, None

    # Embed webcam preview on right side
    webcam_small = cv2.resize(frame, (200, 150))
    canvas[10:160, screen_width - 210:screen_width - 10] = webcam_small

    # Overlay pen icon
    display_frame = canvas.copy()
    if finger_x is not None and finger_y is not None:
        px = finger_x - pen_icon.shape[1] // 2
        py = finger_y - pen_icon.shape[0] // 2
        if 0 <= px < screen_width - 30 and 0 <= py < screen_height - 30:
            overlay_icon(display_frame, pen_icon, px, py)

    cv2.imshow("Air Drawing", display_frame)
    key = cv2.waitKey(1)
    if key == ord("c"):
        canvas = np.ones((screen_height, screen_width, 3), dtype=np.uint8) * 255
    elif key == 27:
        break

cap.release()
cv2.destroyAllWindows()
