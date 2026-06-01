# --header
@load "math"

class Calculator(System):
    def distance(self, x1: int, y1: int, x2: int, y2: int):
        dx = x2 - x1
        dy = y2 - y1
        self.result = sqrt(dx * dx + dy * dy)
    
    def angle(self, x: int, y: int):
        self.result = sin(x) + cos(y)
