#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import logging
from pathlib import Path

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_imports.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test all required imports"""
    try:
        logger.info("Testing imports...")
        
        # Test basic imports
        import pandas as pd
        import numpy as np
        logger.info("✓ pandas and numpy imported successfully")
        
        # Test config
        from config import BASE_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, SCALERS_DIR, FEATURES_DIR
        logger.info("✓ config imported successfully")
        
        # Test data collector
        from incremental_data_collector import IncrementalASXDataCollector
        logger.info("✓ incremental_data_collector imported successfully")
        
        # Test feature engineering
        from feature_engineering import FeatureEngineer
        logger.info("✓ feature_engineering imported successfully")
        
        # Test enhanced model
        from enhanced_model import EnhancedStockPredictor
        logger.info("✓ enhanced_model imported successfully")
        
        # Test other required libraries
        import joblib
        import xgboost as xgb
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder
        logger.info("✓ sklearn and xgboost imported successfully")
        
        logger.info("All imports successful!")
        return True
        
    except Exception as e:
        logger.error(f"Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    try:
        logger.info("Testing basic functionality...")
        
        # Test config paths
        from config import BASE_DIR
        logger.info(f"Base directory: {BASE_DIR}")
        
        # Test data collector initialization
        from incremental_data_collector import IncrementalASXDataCollector
        collector = IncrementalASXDataCollector(max_workers=2)
        logger.info("✓ Data collector initialized successfully")
        
        # Test feature engineer initialization
        from feature_engineering import FeatureEngineer
        engineer = FeatureEngineer()
        logger.info("✓ Feature engineer initialized successfully")
        
        # Test model trainer initialization
        from enhanced_model import EnhancedStockPredictor
        trainer = EnhancedStockPredictor(transaction_fee=0.01)
        logger.info("✓ Model trainer initialized successfully")
        
        logger.info("All basic functionality tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Functionality test error: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("STARTING IMPORT AND FUNCTIONALITY TESTS")
    logger.info("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test functionality
        functionality_ok = test_basic_functionality()
        
        if functionality_ok:
            logger.info("All tests passed! Ready to run retraining.")
        else:
            logger.error("Functionality tests failed!")
    else:
        logger.error("Import tests failed!")
    
    logger.info("=" * 50)
    logger.info("TESTS COMPLETED")
    logger.info("=" * 50) 