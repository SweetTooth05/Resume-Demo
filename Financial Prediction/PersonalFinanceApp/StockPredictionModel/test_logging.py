#!/usr/bin/env python3
"""
Test script to verify logging configuration
"""

import logging
import os
from pathlib import Path

def test_logging():
    """Test different logging configurations"""
    
    # Test 1: Basic logging to file
    print("Testing basic logging...")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test_basic.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("This is a test message from basic logging")
    
    # Test 2: Check if retrain_model.log exists and is writable
    print("Checking retrain_model.log...")
    log_file = Path('retrain_model.log')
    if log_file.exists():
        print(f"retrain_model.log exists, size: {log_file.stat().st_size} bytes")
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("Test write to retrain_model.log\n")
            print("Successfully wrote to retrain_model.log")
        except Exception as e:
            print(f"Error writing to retrain_model.log: {e}")
    else:
        print("retrain_model.log does not exist")
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("Created retrain_model.log\n")
            print("Successfully created retrain_model.log")
        except Exception as e:
            print(f"Error creating retrain_model.log: {e}")
    
    # Test 3: Test the exact logging configuration from retrain_model_fixed.py
    print("Testing exact logging configuration from retrain_model_fixed.py...")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('retrain_model.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("This is a test message from retrain_model_fixed.py configuration")
    
    # Test 4: Check current working directory and file permissions
    print(f"Current working directory: {os.getcwd()}")
    print(f"Files in current directory: {list(Path('.').glob('*.log'))}")

if __name__ == "__main__":
    test_logging() 