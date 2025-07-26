#!/usr/bin/env python3
"""
Build script for Pico MicroPython firmware bundle
Creates a JSON package containing all necessary files for OTA updates
"""

import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

class FirmwareBundler:
    def __init__(self, source_dir, output_dir):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Files to include in the bundle
        self.include_files = [
            'main.py',
            'config_manager.py',
            'wifi_manager.py',
            'udp_server.py',
            'mqtt_client.py',
            'led_controller.py',
            'neopixel.py'
        ]
        
        # Directories to include recursively
        self.include_dirs = [
            'umqtt'
        ]
        
        # Files to exclude (patterns)
        self.exclude_patterns = [
            '__pycache__',
            '.pyc',
            '.git',
            '.vscode',
            '.DS_Store',
            'clients',
            'README.md',
            'TODO.md',
            '.gitignore',
            '.micropico',
            'build'
        ]
    
    def should_exclude(self, file_path):
        """Check if a file should be excluded from the bundle"""
        path_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False
    
    def read_file_content(self, file_path):
        """Read file content as text or binary"""
        try:
            # Try to read as text first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read(), 'text'
        except UnicodeDecodeError:
            # If it fails, read as binary and encode as base64
            import base64
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('ascii')
                return content, 'binary'
    
    def calculate_file_hash(self, content):
        """Calculate SHA256 hash of file content"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def collect_files(self):
        """Collect all files to be included in the bundle"""
        files = {}
        
        # Add individual files
        for file_name in self.include_files:
            file_path = self.source_dir / file_name
            if file_path.exists() and not self.should_exclude(file_path):
                content, content_type = self.read_file_content(file_path)
                files[file_name] = {
                    'content': content,
                    'type': content_type,
                    'hash': self.calculate_file_hash(content if content_type == 'text' else content.encode()),
                    'size': len(content)
                }
                print(f"Added file: {file_name}")
        
        # Add directories recursively
        for dir_name in self.include_dirs:
            dir_path = self.source_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                for root, dirs, filenames in os.walk(dir_path):
                    # Filter out excluded directories
                    dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
                    
                    for filename in filenames:
                        file_path = Path(root) / filename
                        if not self.should_exclude(file_path):
                            # Create relative path from source directory
                            relative_path = file_path.relative_to(self.source_dir)
                            content, content_type = self.read_file_content(file_path)
                            files[str(relative_path)] = {
                                'content': content,
                                'type': content_type,
                                'hash': self.calculate_file_hash(content if content_type == 'text' else content.encode()),
                                'size': len(content)
                            }
                            print(f"Added file: {relative_path}")
        
        return files
    
    def create_version_info(self, files):
        """Create version information"""
        # Calculate overall bundle hash
        all_hashes = [file_info['hash'] for file_info in files.values()]
        all_hashes.sort()  # Sort for consistent hash
        bundle_hash = hashlib.sha256(''.join(all_hashes).encode()).hexdigest()
        
        # Get git info if available
        git_commit = self.get_git_commit()
        git_branch = self.get_git_branch()
        
        version_info = {
            'build_time': datetime.now().isoformat(),
            'bundle_hash': bundle_hash,
            'file_count': len(files),
            'total_size': sum(file_info['size'] for file_info in files.values()),
            'git_commit': git_commit,
            'git_branch': git_branch,
            'version': '1.0.0'  # You can modify this or make it configurable
        }
        
        return version_info
    
    def get_git_commit(self):
        """Get current git commit hash"""
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  cwd=self.source_dir, 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def get_git_branch(self):
        """Get current git branch"""
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                  cwd=self.source_dir, 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def build(self):
        """Build the firmware bundle"""
        print(f"Building firmware bundle from {self.source_dir}")
        print(f"Output directory: {self.output_dir}")
        
        # Collect all files
        files = self.collect_files()
        
        if not files:
            print("No files found to bundle!")
            return False
        
        # Create version info
        version_info = self.create_version_info(files)
        
        # Create the bundle
        bundle = {
            'version': version_info,
            'files': files
        }
        
        # Write version.json
        version_file = self.output_dir / 'version.json'
        with open(version_file, 'w') as f:
            json.dump(version_info, f, indent=2)
        print(f"Created version file: {version_file}")
        
        # Write the main bundle
        bundle_file = self.output_dir / 'firmware_bundle.json'
        with open(bundle_file, 'w') as f:
            json.dump(bundle, f, indent=2)
        
        print(f"Created firmware bundle: {bundle_file}")
        print(f"Bundle contains {len(files)} files")
        print(f"Total size: {version_info['total_size']} bytes")
        print(f"Bundle hash: {version_info['bundle_hash']}")
        
        return True

def main():
    if len(sys.argv) > 1:
        source_dir = sys.argv[1]
    else:
        # Default to parent directory of build script
        source_dir = Path(__file__).parent.parent
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = Path(__file__).parent / 'bin'
    
    bundler = FirmwareBundler(source_dir, output_dir)
    success = bundler.build()
    
    if not success:
        sys.exit(1)
    
    print("Build completed successfully!")

if __name__ == '__main__':
    main()
