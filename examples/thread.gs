# --header
@load "thread"

class Task(System):
    def wait(self, ms: int):
        thread_sleep(ms)
    
    def run_async(self):
        self.callback = fn():
            self:wait(1000)
            self.done = true
