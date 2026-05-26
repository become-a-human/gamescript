# ===== ИНВЕНТАРЬ =====
INVENTORY_CONFIG = {
    "max_slots": int(20),
    "allow_stack": bool(true),
    "max_stack": int(99),
}

class Inventory(System):
    """Система инвентаря"""
    
    def on_create(self):
        self.gold = int(0)
    
    def add_gold(self, amount: int):
        self.gold = self.gold + amount
    
    def remove_gold(self, amount: int):
        self.gold = self.gold - amount
