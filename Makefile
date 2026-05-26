.PHONY: install test test-lexer test-parser test-compiler compile clean

# Установка
install:
	pip install -e .

# Все тесты
test:
	@echo "=== Лексер ==="
	python tests/test_lexer.py
	@echo ""
	@echo "=== Парсер ==="
	python tests/test_parser.py
	@echo ""
	@echo "=== Компилятор ==="
	python tests/test_compiler.py
	@echo ""
	@echo "✓ Все тесты пройдены!"

# Тесты по отдельности
test-lexer:
	python tests/test_lexer.py

test-parser:
	python tests/test_parser.py

test-compiler:
	python tests/test_compiler.py

# Компиляция примеров
compile:
	@mkdir -p examples/generated
	python -m gamescript.compiler examples/hero.gs examples/generated/hero.h
	python -m gamescript.compiler examples/weapons.gs examples/generated/weapons.h
	python -m gamescript.compiler examples/enemies.gs examples/generated/enemies.h
	python -m gamescript.compiler examples/inventory.gs examples/generated/inventory.h
	python -m gamescript.compiler examples/equipment.gs examples/generated/equipment.h
	python -m gamescript.compiler examples/mainfile.gs examples/generated/mainfile.cpp
	@echo "✓ Все примеры скомпилированы в examples/generated/"

# Очистка
clean:
	rm -rf examples/generated/
	rm -rf *.egg-info
	@echo "✓ Очищено"