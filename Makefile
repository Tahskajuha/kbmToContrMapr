.PHONY: build install

build:
	.venv/bin/python -m nuitka --mode=onefile src/main.py --output-filename="main.bin"
	@echo "Built successfully! Install using:"
	@echo "		make install"

install:
	sudo install -Dm755 main.bin /usr/local/bin/kbmToContrMapr.bin
