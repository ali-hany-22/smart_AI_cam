import cv2
import numpy as np
import time
import os
from config import ProjectConfig as config

class LiveMode:
    def __init__(self):
        self.current_zoom = 1.0
        self.target_zoom = 1.0
        self.smooth_factor = 0.08  

        # --- Recording & Media States ---
        self.is_recording = False
        self.video_writer = None
        self.last_action_time = 0
        
        os.makedirs(config.PHOTO_PATH, exist_ok=True)
        os.makedirs(config.VIDEO_PATH, exist_ok=True)

    def process(self, img, fingers, lmList):
        action_status = "LIVE READY"
        now = time.time()
        h, w, _ = img.shape

        if lmList:
            x4, y4 = lmList[4][0], lmList[4][1]
            x8, y8 = lmList[8][0], lmList[8][1]
            dist = np.linalg.norm(np.array([x4, y4]) - np.array([x8, y8]))

            if fingers[2] == 0 and fingers[3] == 0:
                self.target_zoom = np.interp(dist, [40, 250], [1.0, config.MAX_ZOOM])
                action_status = f"Zoom: {self.current_zoom:.1f}x"

            # fingers == [1, 0, 0, 0, 0]
            if fingers == [1, 0, 0, 0, 0] and (now - self.last_action_time > 2.0):
                temp_img = self._apply_zoom(img.copy(), self.current_zoom) if self.current_zoom > 1.01 else img
                filename = f"{config.PHOTO_PATH}/shot_{int(now)}.jpg"
                cv2.imwrite(filename, temp_img)
                self.last_action_time = now
                action_status = "Photo Captured!"

            # fingers == [0, 1, 1, 0, 0]
            if fingers == [0, 1, 1, 0, 0] and (now - self.last_action_time > 2.5):
                self.is_recording = not self.is_recording
                self.last_action_time = now
                
                if self.is_recording:
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    path = f"{config.VIDEO_PATH}/record_{int(now)}.avi"
                    self.video_writer = cv2.VideoWriter(path, fourcc, 20.0, (w, h))
                    action_status = "Recording Started"
                else:
                    if self.video_writer:
                        self.video_writer.release()
                        self.video_writer = None
                    action_status = "Recording Stopped"

        diff = self.target_zoom - self.current_zoom
        self.current_zoom += diff * self.smooth_factor

        if self.current_zoom > 1.01:
            img = self._apply_zoom(img, self.current_zoom)

        if self.is_recording and self.video_writer:
            self.video_writer.write(img)
            cv2.circle(img, (w - 40, 40), 10, (0, 0, 255), -1)
            cv2.putText(img, "REC", (w - 85, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            action_status = "RECORDING..."

        return img, action_status

    def _apply_zoom(self, img, zoom_factor):
        h, w = img.shape[:2]
        new_h, new_w = int(h / zoom_factor), int(w / zoom_factor)
        y1, x1 = (h - new_h) // 2, (w - new_w) // 2
        img_cropped = img[y1:y1+new_h, x1:x1+new_w]
        return cv2.resize(img_cropped, (w, h))