HERO = {
    "name": "Артур",
    "hp": 100,
}

class Main(System):
    def on_start(self):
        self.gold = 100
        print("Hello GameScript!")
    
    def on_update(self):
        self.gold = self.gold + 1