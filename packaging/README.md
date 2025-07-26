# Build System Documentation

This directory contains the build system for the AreGeeBee Pico MicroPython firmware.

## Overview

The build system creates a JSON bundle containing all the necessary files for OTA (Over-The-Air) updates. The bundle includes:

- All Python source files
- Version information with build metadata
- File hashes for integrity checking
- Git commit information (if available)

## Files

- `build.py` - Python build script that processes source files and creates the bundle
- `../Makefile` - Make targets for easy building
- `bin/` - Output directory (created when building, ignored by git)

## Usage

### Building

From the project root directory:

```bash
# Build the firmware bundle
make build

# Or build with default target
make
```

### Other Commands

```bash
# Clean build artifacts
make clean

# Show build information
make info

# Show version of last build
make version

# Show help
make help
```

## Output Files

The build process creates two files in `build/bin/`:

1. **`firmware_bundle.json`** - Complete firmware bundle containing:
   - Version metadata
   - All source files with content, hashes, and metadata
   
2. **`version.json`** - Standalone version information file

## Bundle Structure

### version.json
```json
{
  "build_time": "2025-07-26T11:43:58.140251",
  "bundle_hash": "8298a07f...",
  "file_count": 9,
  "total_size": 72150,
  "git_commit": "f82670f8...",
  "git_branch": "main",
  "version": "1.0.0"
}
```

### firmware_bundle.json
```json
{
  "version": { /* same as version.json */ },
  "files": {
    "main.py": {
      "content": "import time\nfrom config_manager...",
      "type": "text",
      "hash": "8ded8c21...",
      "size": 7190
    },
    /* ... more files ... */
  }
}
```

## Included Files

The build system automatically includes:

### Individual Files:
- `main.py` - Main application entry point
- `config_manager.py` - Configuration management
- `wifi_manager.py` - WiFi connectivity
- `udp_server.py` - UDP server for LED data
- `mqtt_client.py` - MQTT client for Home Assistant
- `led_controller.py` - LED strip controller
- `neopixel.py` - NeoPixel/WS2812B driver

### Directories:
- `umqtt/` - MQTT library files

## Excluded Files

The following are automatically excluded:
- `__pycache__/` directories
- `.pyc` files
- `.git/` directory
- `.vscode/` directory
- `.DS_Store` files
- `clients/` directory (example files)
- Documentation files (`README.md`, `TODO.md`)
- Build system files

## Configuration

You can modify the included/excluded files by editing the `FirmwareBundler` class in `build.py`:

- `include_files` - List of individual files to include
- `include_dirs` - List of directories to include recursively
- `exclude_patterns` - List of patterns to exclude

## Git Integration

The build system automatically captures git information:
- Current commit hash
- Current branch name
- Build timestamp

This information is included in the version metadata for tracking and debugging.

## Future Usage

This bundle format is designed for:
- **OTA Updates** - The JSON bundle can be easily transmitted and parsed
- **Version Control** - Hash verification ensures integrity
- **Rollback Support** - Version information enables rollback functionality
- **Device Management** - Build metadata helps with device tracking

## Build Script Details

The `build.py` script:
1. Scans for all specified source files
2. Reads file contents (text or binary with base64 encoding)
3. Calculates SHA256 hashes for each file
4. Collects git metadata
5. Creates a comprehensive bundle with version information
6. Outputs both individual version file and complete bundle

The script is designed to be robust and handles various edge cases like binary files, missing git repository, and file read errors.
