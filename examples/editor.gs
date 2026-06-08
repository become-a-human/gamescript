@load "system"
@load "ncurses"

class Editor(System):
    """Консольный редактор кода"""
    
    def on_create(self):
        self.text = "Hello from GameScript Editor!"
        self.running = true
    
    def run(self):
        ncurses_init()
        while self.running:
            ncurses_clear()
            ncurses_print(1, 0, self.text)
            ncurses_status("GameScript Editor | Ctrl+Q:Quit")
            ncurses_refresh()
            ch = ncurses_getch()
            if ch == 17:
                self.running = false
        ncurses_end()
