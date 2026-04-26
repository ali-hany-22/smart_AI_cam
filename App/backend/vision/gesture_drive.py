import cv2
import serial
from config import ProjectConfig as config


class GestureDriveMode:
    def __init__(self):
        self.serial_enabled = False
        try:
            self.ser = serial.Serial(config.SERIAL_PORT, config.BAUD_RATE, timeout=0.1)
            self.serial_enabled = True
            print(f"Pan-Tilt Mode: Connected to ESP32")
        except:
            print("ESP32 not detected.")

        self.last_cmd = ""

    def process(self, img, fingers, lmList):
        action_status = "PAN-TILT READY"
        h, w, _ = img.shape
        center_x = w // 2
        center_y = h // 2

        if lmList:
            hand_x = lmList[9][0]
            hand_y = lmList[9][1]

            # ================= Drawing Deadzone =================
            cv2.line(img,
                     (center_x - config.DEADZONE_X, 0),
                     (center_x - config.DEADZONE_X, h),
                     (0, 255, 255), 1)
            cv2.line(img,
                     (center_x + config.DEADZONE_X, 0),
                     (center_x + config.DEADZONE_X, h),
                     (0, 255, 255), 1)

            cv2.line(img,
                     (0,  center_y - config.DEADZONE_Y),
                     (w,  center_y - config.DEADZONE_Y),
                     (255, 165, 0), 1)
            cv2.line(img,
                     (0,  center_y + config.DEADZONE_Y),
                     (w,  center_y + config.DEADZONE_Y),
                     (255, 165, 0), 1)

            # ================= Command Calculation =================
            cmd = self._get_command(hand_x, hand_y, center_x, center_y)

            if cmd != self.last_cmd:
                self._send(cmd)
                self.last_cmd = cmd

            # ================= Drawing =================
            cv2.circle(img, (hand_x, hand_y), 10, (0, 255, 0), -1)
            cv2.line(img, (center_x, center_y), (hand_x, hand_y), (0, 255, 0), 1)

            action_status = f"CMD: {cmd}" if cmd != config.CMD_STOP else "CENTER STABLE"

        return img, action_status

    # ================= (Pan + Tilt) =================
    def _get_command(self, hand_x, hand_y, center_x, center_y):
        dx = hand_x - center_x
        dy = hand_y - center_y

        outside_x = abs(dx) > config.DEADZONE_X
        outside_y = abs(dy) > config.DEADZONE_Y

        if outside_x and outside_y:
            if abs(dx) >= abs(dy):
                return config.CMD_RIGHT if dx > 0 else config.CMD_LEFT
            else:
                return config.CMD_DOWN if dy > 0 else config.CMD_UP

        if outside_x:
            return config.CMD_RIGHT if dx > 0 else config.CMD_LEFT

        if outside_y:
            return config.CMD_DOWN if dy > 0 else config.CMD_UP

        return config.CMD_STOP

    # ================= SEND TO ESP32 =================
    def _send(self, cmd):
        if self.serial_enabled and self.ser:
            try:
                self.ser.write(f"{cmd}\n".encode())
            except Exception as e:
                print(f"⚠️ Serial error: {e}")
                self.serial_enabled = False