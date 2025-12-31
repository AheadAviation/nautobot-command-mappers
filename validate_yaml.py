#!/usr/bin/env python3
"""Quick YAML validation script for command mapper files."""

import yaml
import sys
import os

def validate_yaml_file(filepath):
    """Validate a YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print(f"[OK] {os.path.basename(filepath)} is valid YAML")
        return True
    except yaml.YAMLError as e:
        print(f"[ERROR] {os.path.basename(filepath)} has YAML syntax errors:")
        print(f"  {e}")
        return False
    except FileNotFoundError:
        print(f"[ERROR] {filepath} not found")
        return False

if __name__ == '__main__':
    mapper_dir = os.path.join(os.path.dirname(__file__), 'onboarding_command_mappers')
    
    if not os.path.exists(mapper_dir):
        print(f"[ERROR] Directory not found: {mapper_dir}")
        sys.exit(1)
    
    print("Validating YAML files...")
    print()
    
    all_valid = True
    for filename in os.listdir(mapper_dir):
        if filename.endswith('.yml'):
            filepath = os.path.join(mapper_dir, filename)
            if not validate_yaml_file(filepath):
                all_valid = False
    
    print()
    if all_valid:
        print("[SUCCESS] All YAML files are valid")
        sys.exit(0)
    else:
        print("[ERROR] Some YAML files have errors")
        sys.exit(1)

