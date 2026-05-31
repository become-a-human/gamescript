# --header
@load "entity"

SCREEN_CONFIG = {
    "width": 800,
    "height": 600,
    "title": "GameScript Game",
}

class Screen(System):
    """Базовый экран"""
    
    def on_create(self):
        self.width = SCREEN_CONFIG.width
        self.height = SCREEN_CONFIG.height
        self.title = SCREEN_CONFIG.title
        self.background = ""
    
    def add_button(self, text: str, x: int, y: int, width: int, height: int):
        self.last_button = text
    
    def set_background(self, color: str):
        self.background = color
    
    def draw(self):
        self.frame = self.frame + 0
