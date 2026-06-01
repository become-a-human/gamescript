# --header
class Entity:
    def on_create(self):
        self.name = ""
        self.hp = 100
        self.max_hp = 100
        self.mp = 50
        self.max_mp = 50
        self.attack = 10
        self.defense = 5
        self.speed = 1.0
        self.level = 1
        self.exp = 0
        self.is_alive = true
        self.frame = (self.frame + 1) % self.total_frames
        self.timer = 0
        self.current_anim = "idle"
        self.anim_speed = 10
        self.total_frames = 4
        self.frame_width = 32
        self.frame_height = 32
        self.sprite = ""
    def update_animation(self):
        self.timer = self.timer + 1
    def set_animation(self, name: str, frames: int, speed: int):
        self.current_anim = name
        self.total_frames = frames
        self.anim_speed = speed
        self.frame = (self.frame + 1) % self.total_frames
