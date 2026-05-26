# ===== ОРУЖИЕ =====
SWORD = {
    "name": str("Стальной меч"),
    "type": str("weapon"),
    "slot": str("mainhand"),
    "attack_bonus": int(8),
    "speed_penalty": float(0.1),
    "price": int(50),
    "rarity": str("common"),
    "equipped": bool(false),
}

AXE = {
    "name": str("Боевой топор"),
    "type": str("weapon"),
    "slot": str("mainhand"),
    "attack_bonus": int(12),
    "speed_penalty": float(0.3),
    "price": int(80),
    "rarity": str("common"),
    "equipped": bool(false),
}

DAGGER = {
    "name": str("Кинжал"),
    "type": str("weapon"),
    "slot": str("offhand"),
    "attack_bonus": int(4),
    "speed_penalty": float(0.0),
    "price": int(30),
    "rarity": str("common"),
    "equipped": bool(false),
}

MAGIC_STAFF = {
    "name": str("Посох мага"),
    "type": str("weapon"),
    "slot": str("mainhand"),
    "attack_bonus": int(5),
    "magic_bonus": int(10),
    "speed_penalty": float(0.2),
    "price": int(120),
    "rarity": str("rare"),
    "equipped": bool(false),
}