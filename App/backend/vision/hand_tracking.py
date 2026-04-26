import mediapipe as mp
import cv2
import time
import logging

logger = logging.getLogger("HAND_TRACKER")


class HandTracker:
    def __init__(self, conf=0.7, smoothing_alpha=0.65):

        # ================= MEDIAPIPE =================
        self.mp_hands = mp.solutions.hands

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=conf,
            min_tracking_confidence=conf
        )

        # ================= SMOOTHING =================
        self.alpha = smoothing_alpha

        self.smooth_x = 0
        self.smooth_y = 0
        self.first_frame = True

        # ================= FPS =================
        self.last_time = time.time()
        self.fps = 0

        # ================= STATE =================
        self.last_gesture = None

        logger.info("HandTracker initialized")

    # ================= MAIN PROCESS =================
    def process(self, frame):

        if frame is None:
            return self._empty()

        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        data = self._empty()

        # ================= FPS CALC =================
        now = time.time()
        self.fps = 1 / max(now - self.last_time, 1e-6)
        self.last_time = now

        # ================= HAND DETECTION =================
        if results.multi_hand_landmarks:

            lm = results.multi_hand_landmarks[0].landmark

            # ================= STABLE CONTROL POINT =================
            # wrist + palm center hybrid
            cx = (lm[0].x + lm[9].x) / 2
            cy = (lm[0].y + lm[9].y) / 2

            raw_x = int(cx * w)
            raw_y = int(cy * h)

            # ================= SMOOTHING =================
            if self.first_frame:
                self.smooth_x = raw_x
                self.smooth_y = raw_y
                self.first_frame = False
            else:
                self.smooth_x = int(
                    self.alpha * self.smooth_x +
                    (1 - self.alpha) * raw_x
                )

                self.smooth_y = int(
                    self.alpha * self.smooth_y +
                    (1 - self.alpha) * raw_y
                )

            # ================= FINGER STATES =================
            fingers = self.get_fingers_state(lm)

            # ================= OUTPUT =================
            data.update({
                "found": True,
                "x": self.smooth_x,
                "y": self.smooth_y,
                "fps": int(self.fps),
                "fingers": fingers,
                "lmList": [[int(p.x * w), int(p.y * h)] for p in lm],
                "landmarks": [
                    {"x": p.x, "y": p.y} for p in lm
                ]
            })

            # ================= GESTURE ENGINE =================
            gesture = self.detect_gesture(fingers)

            data["gesture"] = gesture

            # log when gesture changes
            if gesture != self.last_gesture:
                logger.info(f"✋ Gesture: {gesture}")
                self.last_gesture = gesture

        else:
            # reset smoothing when hand lost
            self.first_frame = True
            self.last_gesture = None

        return data

    # ================= FINGERS STATE =================
    def get_fingers_state(self, lm):
        fingers = []
        if lm[4].x > lm[3].x: fingers.append(1)
        else: fingers.append(0)

        tip_ids = [8, 12, 16, 20]
        for tip in tip_ids:
            if lm[tip].y < lm[tip - 2].y: fingers.append(1)
            else: fingers.append(0)
        return fingers

    # ================= GESTURE ENGINE =================
    def detect_gesture(self, fingers):

        if fingers == [0, 0, 0, 0, 0]: return "fist"
        if fingers == [0, 1, 0, 0, 0]: return "point"
        if fingers == [0, 1, 1, 0, 0]: return "peace"
        if fingers == [1, 1, 1, 1, 1]: return "open"
        if fingers == [1, 0, 0, 0, 0]: return "thumbs_up"
        
        return "unknown"

    # ================= RESET STATE =================
    def reset(self):
        self.first_frame = True
        self.last_gesture = None

    # ================= EMPTY RESPONSE =================
    def _empty(self):
        return {
            "found": False,
            "x": 0,
            "y": 0,
            "fps": 0,
            "fingers": [0, 0, 0, 0, 0],
            "gesture": None,
            "lmList": [],
            "landmarks": []
        }