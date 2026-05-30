# --header
@load "system"
# Виртуальный джойстик для мобильных игр

JOYSTICK_CONFIG = {
    "deadzone": 20,
    "max_distance": 120,
}

class Joystick(System):
    """Виртуальный джойстик"""
    
    def on_create(self):
        self.active = false
        self.base_x = 0
        self.base_y = 0
        self.current_x = 0
        self.current_y = 0
        self.direction_x = 0.0
        self.direction_y = 0.0
        self.magnitude = 0.0
    
    def on_touch_start(self, x: int, y: int):
        self.active = true
        self.base_x = x
        self.base_y = y
        self.current_x = x
        self.current_y = y
        self:update_direction()
    
    def on_touch_move(self, x: int, y: int):
        if self.active:
            self.current_x = x
            self.current_y = y
            self:update_direction()
    
    def on_touch_end(self):
        self.active = false
        self.direction_x = 0.0
        self.direction_y = 0.0
        self.magnitude = 0.0
    
    def update_direction(self):
        dx = self.current_x - self.base_x
        dy = self.current_y - self.base_y
        distance = dx * dx + dy * dy
        if distance < JOYSTICK_CONFIG.deadzone * JOYSTICK_CONFIG.deadzone:
            self.direction_x = 0.0
            self.direction_y = 0.0
            self.magnitude = 0.0
        else:
            self.magnitude = distance / (JOYSTICK_CONFIG.max_distance * JOYSTICK_CONFIG.max_distance)
            if self.magnitude > 1.0:
                self.magnitude = 1.0
