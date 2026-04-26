import time

class GestureControl:
    def __init__(self):
        self.gesture_map = {
            "point": "teaching",     
            "peace": "live",         
            "thumbs_up": "security", 
            "open": "gesture"        
        }
        
        self.last_gesture = None
        self.last_emitted_mode = None
        self.start_time = 0
        self.required_duration = 1.5 

    def get_new_mode(self, current_gesture, current_mode):

        current_gesture = str(current_gesture).lower() if current_gesture else None

        if not current_gesture or current_gesture in ["none", "unknown", "fist"]:
            self.last_gesture = None
            self.start_time = 0
            return None

        if current_gesture == self.last_gesture:
            elapsed = time.time() - self.start_time
            
            if elapsed >= self.required_duration:
                target_mode = self.gesture_map.get(current_gesture)
                
                if target_mode and target_mode != current_mode:
                    self.last_emitted_mode = target_mode
                    self.start_time = time.time() + 1000  
                    return target_mode
        else:
            self.last_gesture = current_gesture
            self.start_time = time.time()
            
        return None

    def reset_history(self):
        self.last_gesture = None
        self.last_emitted_mode = None
        self.start_time = 0