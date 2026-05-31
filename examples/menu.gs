# --header
@load "screen"

class MainMenu(Screen):
    """Главное меню"""
    
    def on_create(self):
        self:set_background("dark")
        self:add_button("Новая игра", 300, 200, 200, 50)
        self:add_button("Загрузить", 300, 270, 200, 50)
        self:add_button("Выход", 300, 340, 200, 50)
    
    def draw(self):
        self.frame = self.frame + 1
