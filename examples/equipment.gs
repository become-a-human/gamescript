# ===== ЭКИПИРОВКА =====
EQUIPMENT_SLOTS = {
    "mainhand": str("none"),
    "offhand": str("none"),
    "head": str("none"),
    "body": str("none"),
}

class Equipment(System):
    """Система экипировки"""
    
    def on_create(self):
        self.attack_bonus = int(0)
        self.defense_bonus = int(0)
    
    def equip(self, item: str):
        if item == "sword":
            self.attack_bonus = int(8)
    
    def get_attack(self):
        return self.attack_bonus
