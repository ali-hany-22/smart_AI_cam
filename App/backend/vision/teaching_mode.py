import numpy as np
import time
import cv2
from config import ProjectConfig as config


class TeachingMode:
    def __init__(self, width=640, height=480):
        # ================= CANVAS =================
        self.width  = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), np.uint8)

        # ================= CONFIG SAFE DEFAULTS =================
        self.colors          = getattr(config, 'COLORS', [(255, 229, 0), (255, 0, 255), (0, 255, 0)])
        self.draw_thickness  = getattr(config, 'DRAW_THICKNESS', 8)
        self.eraser_thickness = getattr(config, 'ERASER_THICKNESS', 80)

        # ================= DRAW STATE =================
        self.px, self.py     = 0, 0
        self.color_index     = 0
        self.current_color   = self.colors[0]

        # ================= TEXT SYSTEM =================
        self.typed_text = ""
        self.text_pos   = [50, 400]
        self.drag_text  = False

        # ================= KEYBOARD =================
        self.keyboard_active = False
        self.is_arabic       = False   

        # ================= TIMING =================
        self.last_action_time = 0
        self.last_key_time    = 0

    # ================= Change Language =================
    def set_language(self, lang: str):

        self.is_arabic = (lang == "ar")
        self._reset_pen()

    # ================= MAIN PROCESS =================
    def process(self, img, data):
        if img.shape[0] != self.height or img.shape[1] != self.width:
            img = cv2.resize(img, (self.width, self.height))

        if not data or not data.get("found"):
            self._reset_pen()
            return self._draw_final(img), "IDLE"

        x, y    = data["x"], data["y"]
        fingers = data.get("fingers", [0, 0, 0, 0, 0])
        now     = time.time()
        action  = "TEACHING_IDLE"

        # ================= 1. TOGGLE KEYBOARD (OPEN HAND) =================
        if fingers == [1, 1, 1, 1, 1]:
            if now - self.last_action_time > 1.5:
                self.keyboard_active  = not self.keyboard_active
                self.last_action_time = now
                self._reset_pen()
                action = "TOGGLE_KEYBOARD"

        # ================= 2. KEYBOARD MODE =================
        if self.keyboard_active:
            action = "KEYBOARD_ACTIVE"

            if fingers == [0, 1, 0, 0, 0]:   
                key = self._get_key(x, y)
                if key and now - self.last_key_time > 0.8:
                    if key == "<":
                        self.typed_text = self.typed_text[:-1]
                    elif key == " ":
                        self.typed_text += " "
                    else:
                        self.typed_text += key
                    self.last_key_time = now
                    action = f"TYPE_{key}"

            dist = np.linalg.norm(np.array([x, y]) - np.array(self.text_pos))
            if dist < 60 and fingers == [1, 1, 0, 0, 0]:
                self.text_pos = [x, y]
                action = "MOVING_TEXT"

            self._reset_pen()

        # ================= 3. DRAWING LOGIC =================
        else:
            if fingers == [0, 1, 0, 0, 0]:             
                action = "DRAWING"
                if self.px == 0 and self.py == 0:
                    self.px, self.py = x, y
                cv2.line(self.canvas, (self.px, self.py), (x, y),
                         self.current_color, self.draw_thickness)
                self.px, self.py = x, y

            elif fingers == [0, 1, 1, 0, 0]:          
                action = "ERASING"
                cv2.circle(self.canvas, (x, y), self.eraser_thickness, (0, 0, 0), -1)
                self._reset_pen()

            elif fingers == [1, 1, 0, 0, 0]:          
                if now - self.last_action_time > 1.0:
                    self.color_index   = (self.color_index + 1) % len(self.colors)
                    self.current_color = self.colors[self.color_index]
                    self.last_action_time = now
                action = "COLOR_CHANGED"
                self._reset_pen()

            elif fingers == [0, 0, 0, 0, 0]:          
                if now - self.last_action_time > 2.0:
                    self.canvas     = np.zeros_like(self.canvas)
                    self.typed_text = ""
                    self.last_action_time = now
                    action = "CANVAS_CLEARED"
            else:
                self._reset_pen()

        return self._draw_final(img), action

    # ================= DRAW FINAL =================
    def _draw_final(self, img):
        img_gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(img_gray, 20, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, img_inv)
        img = cv2.bitwise_or(img, self.canvas)

        if self.keyboard_active:
            img = self._draw_keyboard_overlay(img)

        # رسم النص
        cv2.putText(img, self.typed_text,
                    (self.text_pos[0], self.text_pos[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

        # مؤشر اللون الحالي
        cv2.circle(img, (40, 40), 20, self.current_color, -1)
        cv2.putText(img, "PEN", (70, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # ✅ مؤشر اللغة
        lang_label = "AR" if self.is_arabic else "EN"
        cv2.putText(img, f"LANG:{lang_label}",
                    (self.width - 100, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 229, 255), 2)

        return img

    # ================= KEYBOARD OVERLAY =================
    def _draw_keyboard_overlay(self, img):
        keys = getattr(config, 'KEYS_AR' if self.is_arabic else 'KEYS_EN', [[]])
        if not keys or not keys[0]:
            return img

        overlay = img.copy()
        cv2.rectangle(overlay, (30, 150), (self.width - 30, 350), (30, 30, 30), -1)
        img = cv2.addWeighted(overlay, 0.5, img, 0.5, 0)

        for i, row in enumerate(keys):
            for j, key in enumerate(row):
                kw = (self.width - 100) // len(row)
                kh = 50
                kx = j * kw + 50
                ky = i * kh + 170
                cv2.rectangle(img, (kx, ky), (kx + kw - 5, ky + kh - 5), (100, 100, 100), 1)
                cv2.putText(img, key, (kx + 15, ky + 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return img

    # ================= GET KEY =================
    def _get_key(self, x, y):
        keys = getattr(config, 'KEYS_AR' if self.is_arabic else 'KEYS_EN', [[]])
        for i, row in enumerate(keys):
            for j, key in enumerate(row):
                kw = (self.width - 100) // len(row)
                kh = 50
                kx = j * kw + 50
                ky = i * kh + 170
                if kx < x < kx + kw and ky < y < ky + kh:
                    return key
        return None

    # ================= RESET PEN =================
    def _reset_pen(self):
        self.px, self.py = 0, 0