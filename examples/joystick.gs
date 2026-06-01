# --header
@load "system"

JOYSTICK_CONFIG = {
    "deadzone": 20,
    "max_distance": 120,
}

class Joystick(System):
    """Виртуальный джойстик"""
    
    def on_create(self):
        self.active = false
        self.direction_x = 0.0
        self.direction_y = 0.0
