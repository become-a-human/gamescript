# --header
@load "system"
# ===== ИНВЕНТАРЬ =====
INVENTORY_CONFIG = {
    "max_slots": 20,
    "allow_stack": true,
    "max_stack": 99,
}

class Inventory(System):
    """Система инвентаря"""
    
    def on_create(self):
        self.gold = 0
    
    def add_gold(self, amount: int):
        self.gold = self.gold + amount
    
    def remove_gold(self, amount: int):
        self.gold = self.gold - amount
