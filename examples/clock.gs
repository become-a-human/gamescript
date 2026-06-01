# --header
@load "time"

class Timer(System):
    def on_create(self):
        self.start_time = 0
        self.elapsed = 0
    
    def update(self):
        self.elapsed = self.elapsed + 1
