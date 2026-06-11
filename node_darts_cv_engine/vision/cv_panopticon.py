import cv2
import numpy as np
import pytesseract
import time
import os
import json
import logging
from dataclasses import dataclass, asdict

# Set up logging for Panopticon
logging.basicConfig(level=logging.INFO, format='%(asctime)s | PANOPTICON | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# To run headless on Proxmox, we use Xvfb wrapper for the container
display_env = os.environ.get('DISPLAY', ':99')

@dataclass
class DartsTelemetry:
    player_a_score: int
    player_b_score: int
    momentum_shift: str
    timestamp: float

class PanopticonCore:
    def __init__(self, use_screen=True, video_source=0):
        self.use_screen = use_screen
        self.video_source = video_source
        self.cap = None

        if self.use_screen:
            try:
                import mss
                self.sct = mss.mss()
                # On headless Xvfb, this captures the single unified display buffer
                self.monitor = self.sct.monitors[1]
                logger.info("Attached to Headless Xvfb Screen Capture Buffer.")
            except ImportError:
                logger.error("mss library missing. Install via pip.")
                raise
        
        # Ensure Tesseract can find the binary (in Docker it will be at /usr/bin/tesseract)
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

    def start_vision_loop(self):
        logger.info("Initializing Relativistic Vision Search...")
        
        # Example Bounding boxes for score overlays (would be calibrated based on the broadcast feed)
        SCORE_BOX_A = (100, 100, 300, 200) # (x1, y1, x2, y2)
        SCORE_BOX_B = (100, 250, 300, 350)
        
        previous_score_a = 0
        previous_score_b = 0

        while True:
            start_time = time.time()
            if self.use_screen:
                img = self.sct.grab(self.monitor)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            else:
                ret, frame = self.cap.read()
                if not ret:
                    continue
            
            # --- VISION PROCESSING ---
            # Extract ROI
            roi_a = frame[SCORE_BOX_A[1]:SCORE_BOX_A[3], SCORE_BOX_A[0]:SCORE_BOX_A[2]]
            roi_b = frame[SCORE_BOX_B[1]:SCORE_BOX_B[3], SCORE_BOX_B[0]:SCORE_BOX_B[2]]
            
            # Process for OCR (grayscale, threshold)
            gray_a = cv2.cvtColor(roi_a, cv2.COLOR_BGR2GRAY)
            thresh_a = cv2.threshold(gray_a, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            
            gray_b = cv2.cvtColor(roi_b, cv2.COLOR_BGR2GRAY)
            thresh_b = cv2.threshold(gray_b, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            
            # Fast OCR - configure psd block size to look only for digits
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
            text_a = pytesseract.image_to_string(thresh_a, config=custom_config).strip()
            text_b = pytesseract.image_to_string(thresh_b, config=custom_config).strip()
            
            # Relativistic Arbitrage Logic: Detect state changes instantly
            try:
                score_a = int(text_a) if text_a else previous_score_a
                score_b = int(text_b) if text_b else previous_score_b
            except ValueError:
                continue

            momentum_shift = "NONE"
            if score_a != previous_score_a:
                momentum_shift = "PLAYER_A_POINT"
                previous_score_a = score_a
            elif score_b != previous_score_b:
                momentum_shift = "PLAYER_B_POINT"
                previous_score_b = score_b

            if momentum_shift != "NONE":
                latency = time.time() - start_time
                logger.info(f"[{latency*1000:.2f}ms] SCORE DETECTED. {score_a} - {score_b} | Shift: {momentum_shift}")
                
                # Emit to IPC/Pipe for the Inference Core
                telemetry = DartsTelemetry(score_a, score_b, momentum_shift, time.time())
                self._dispatch_to_inference(telemetry)
                
            # Run at approx 30 frames per second limit to not blow CPU
            time.sleep(1.0/30.0)

    def _dispatch_to_inference(self, telemetry: DartsTelemetry):
        # Writes directly to a fast named pipe or UNIX socket read by darts_inference.py
        pipe_path = "/tmp/darts_cv_telemetry.pipe"
        if os.path.exists(pipe_path):
            try:
                with open(pipe_path, 'w') as p:
                    p.write(json.dumps(asdict(telemetry)) + '\n')
            except Exception as e:
                logger.debug(f"Pipe write failed: {e}")

if __name__ == "__main__":
    logger.info("Igniting LiteSpeed Panopticon Vision Core...")
    panopticon = PanopticonCore()
    panopticon.start_vision_loop()
