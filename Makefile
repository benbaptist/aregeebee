# Makefile for Pico MicroPython firmware build

# Variables
BUILD_DIR = packaging
BIN_DIR = $(BUILD_DIR)/bin
BUILD_SCRIPT = $(BUILD_DIR)/build.py
PYTHON = python3

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
	$(PYTHON) $(BUILD_SCRIPT)
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
