# --header
@load "system"
# ===== ЭКИПИРОВКА =====
EQUIPMENT_SLOTS = {
    "mainhand": None,
    "offhand": None,
    "head": None,
    "body": None,
}

class Equipment(System):
    """Система экипировки"""
    
    def on_create(self):
        self.attack_bonus = 0
        self.defense_bonus = 0
    
    def equip(self, item: str):
        if item == "sword":
            self.attack_bonus = 8
    
    def get_attack(self):
        return self.attack_bonus
