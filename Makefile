# Makefile for Pico MicroPython firmware build

# Variables
BUILD_DIR = build
BIN_DIR = $(BUILD_DIR)/bin
BUILD_SCRIPT = $(BUILD_DIR)/build.py
PYTHON = python3
VERSION ?= # Can be overridden: make build VERSION=1.2.3

# Default target
.PHONY: all
all: build

# Create bin directory if it doesn't exist
$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Build the firmware bundle
.PHONY: build
build: $(BIN_DIR)
	@echo "Building firmware bundle..."
	$(if $(VERSION),$(PYTHON) $(BUILD_SCRIPT) --version $(VERSION),$(PYTHON) $(BUILD_SCRIPT))
	@echo "Build complete! Output in $(BIN_DIR)/"

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(BIN_DIR)
	@echo "Clean complete!"

# Show build info
.PHONY: info
info:
	@echo "Pico MicroPython Firmware Build System"
	@echo "======================================"
	@echo "Build directory: $(BUILD_DIR)"
	@echo "Output directory: $(BIN_DIR)"
	@echo "Build script: $(BUILD_SCRIPT)"
	@echo "Python: $(PYTHON)"
	@echo ""
	@echo "Available targets:"
	@echo "  build  - Build the firmware bundle (default)"
	@echo "  clean  - Clean build artifacts"
	@echo "  info   - Show this information"
	@echo "  help   - Show this information"
	@echo "  version - Show version of last build"
	@echo ""
	@echo "Version examples:"
	@echo "  make build VERSION=1.2.3"
	@echo "  make build VERSION=2.0.0-beta"

# Help target (alias for info)
.PHONY: help
help: info

# Check if version.json exists and show version info
.PHONY: version
version:
	@if [ -f "$(BIN_DIR)/version.json" ]; then \
		echo "Last build version info:"; \
		cat $(BIN_DIR)/version.json; \
	else \
		echo "No version.json found. Run 'make build' first."; \
	fi
