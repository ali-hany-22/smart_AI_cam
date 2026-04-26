import cv2
import threading
import time
import logging

logger = logging.getLogger("CAMERA")


class CameraHandler:
    def __init__(self, index=0, width=640, height=480, fps=25):

        # CONFIG
        self.index  = index
        self.width  = width
        self.height = height
        self.fps    = fps

        # STATE
        self.cap          = None
        self.latest_frame = None
        self.running      = True
        self.lock         = threading.Lock()

        # RECONNECT
        self.retry_delay     = 2
        self.max_retry_delay = 10

        # START
        self._open_camera()

        self.thread = threading.Thread(
            target=self._capture_loop,
            daemon=True
        )
        self.thread.start()
        logger.info(f"Camera thread started (index={self.index})")

    # ================= OPEN CAMERA =================
    def _open_camera(self):
        device = f"/dev/video{self.index}"
        logger.info(f"Opening camera {device}...")

        cap = cv2.VideoCapture(device, cv2.CAP_V4L2)

        if not cap.isOpened():
            logger.error(f"Cannot open {device}")
            return False

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Warm up
        frame = None
        for _ in range(10):
            ret, frame = cap.read()
            if ret and frame is not None:
                break
            time.sleep(0.05)

        if frame is None:
            logger.error("Camera warm-up failed")
            cap.release()
            return False

        self.cap         = cap
        self.retry_delay = 2
        logger.info(f"Camera ready: {device}")
        return True

    # ================= RELEASE =================
    def _release_camera(self):
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
                logger.info("Camera released")
        except Exception as e:
            logger.error(f"Release error: {e}")

    # ================= LOOP =================
    def _capture_loop(self):
        frame_interval = 1.0 / self.fps

        while self.running:
            start_time = time.time()

            if self.cap is None or not self.cap.isOpened():
                logger.warning(f"Camera lost, retry in {self.retry_delay}s")
                time.sleep(self.retry_delay)
                success          = self._open_camera()
                self.retry_delay = min(self.retry_delay * 1.5, self.max_retry_delay)
                if not success:
                    continue

            ret, frame = self.cap.read()

            if not ret or frame is None:
                logger.warning("Frame read failed")
                self._release_camera()
                continue

            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (self.width, self.height))

            with self.lock:
                self.latest_frame = frame

            elapsed = time.time() - start_time
            time.sleep(max(0, frame_interval - elapsed))

    # ================= GET FRAME =================
    def get_frame(self):
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None

    # ================= SWITCH CAMERA =================
    def switch_camera(self, new_index):

        if new_index == self.index and self.cap and self.cap.isOpened():
            logger.info(f"Camera {new_index} already active")
            return

        logger.info(f"Switching camera: {self.index} → {new_index}")

        with self.lock:
            self._release_camera()
            self.index       = new_index
            self.retry_delay = 2

        success = self._open_camera()

        if success:
            logger.info(f"Switched to camera {new_index}")
        else:
            logger.error(f"Failed to switch to camera {new_index}")
            self.index = 0
            self._open_camera()

    # ================= SETTINGS =================
    def update_fps(self, fps):
        self.fps = max(1, int(fps))

    def update_resolution(self, width, height):
        self.width  = width
        self.height = height
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # ================= STOP =================
    def stop(self):
        logger.info("Stopping camera...")
        self.running = False
        self._release_camera()
        if hasattr(self, "thread"):
            self.thread.join(timeout=2)
        logger.info("Camera stopped cleanly")
