# --header
@load "time"
@load "thread"

class Timer(System):
    def on_create(self):
        self.start_time = time()
        self.elapsed = 0
    
    def update(self):
        self.elapsed = time() - self.start_time
    
    def wait(self, ms: int):
        delay(ms)
