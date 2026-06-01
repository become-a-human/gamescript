# --header
@load "random"

class LootSystem(System):
    def get_drop(self, luck: int):
        roll = random() * 100
        if roll < luck:
            self.drop = "rare"
        elif roll < luck * 2:
            self.drop = "uncommon"
        else:
            self.drop = "common"
