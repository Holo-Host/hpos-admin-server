# 
# Test and build hpos-admin-server
# 

SHELL	= bash

# nix-test, nix-build, ... TODO: unimplemented
nix-%:
	nix-shell --pure --run "make $*"

# Internal targets; assumes a nix-shell environment
.PHONY: all build test test-unit test-serve 
all: build

build:
	@echo "Building hpos-admin-server Python3 package"
	python3 setup.py build

install: build
	@echo "Installing hpos-admin-server Python3 package"
	python3 setup.py install

test: test-unit
	@echo "Testing complete"

test-unit:
	@echo "Testing: unit tests"

test-server:
	@echo "Testing: local hpos-admin-server (hit ^C to terminate)"
	python3 -m admin_webpy -dvv -C test
