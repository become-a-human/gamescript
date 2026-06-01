# --header

class Collision(System):
    def check_aabb(self, x1: int, y1: int, w1: int, h1: int, x2: int, y2: int, w2: int, h2: int):
        if x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2:
            self.collides = true
        else:
            self.collides = false
