#!/usr/bin/env python3
"""
Test script to verify the fixes work correctly
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import sys

# Add the current directory to the path to import modules
sys.path.append(str(Path(__file__).parent))

from config import BASE_DIR, MODELS_DIR, SCALERS_DIR, FEATURES_DIR
from incremental_data_collector import IncrementalASXDataCollector
from enhanced_model import EnhancedStockPredictor
from feature_engineering import FeatureEngineer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_fixes.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_data_collection():
    """Test the fixed data collection"""
    try:
        logger.info("Testing data collection...")
        
        # Initialize data collector
        data_collector = IncrementalASXDataCollector(max_workers=2)
        
        # Test with a small number of companies
        data = data_collector.collect_all_data_incremental(max_companies=3)
        
        if data and data.get('stock_data'):
            logger.info(f"✅ Data collection successful! Collected data for {len(data['stock_data'])} tickers")
            
            # Check data quality
            for ticker, df in data['stock_data'].items():
                logger.info(f"  {ticker}: {len(df)} rows, columns: {list(df.columns)}")
                
                # Check for Date column
                if 'Date' in df.columns:
                    logger.info(f"    Date column type: {df['Date'].dtype}")
                else:
                    logger.warning(f"    No Date column found for {ticker}")
            
            return True
        else:
            logger.error("❌ Data collection failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in data collection test: {e}")
        return False

def test_feature_engineering():
    """Test the fixed feature engineering"""
    try:
        logger.info("Testing feature engineering...")
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        sample_data = pd.DataFrame({
            'Date': dates,
            'Open': np.random.uniform(10, 100, 100),
            'High': np.random.uniform(10, 100, 100),
            'Low': np.random.uniform(10, 100, 100),
            'Close': np.random.uniform(10, 100, 100),
            'Volume': np.random.uniform(1000, 10000, 100),
            'Ticker': ['TEST'] * 100
        })
        
        # Initialize feature engineer
        feature_engineer = FeatureEngineer()
        
        # Test technical indicators
        df_with_features = feature_engineer.calculate_technical_indicators(sample_data)
        logger.info(f"✅ Technical indicators calculated: {len(df_with_features.columns)} features")
        
        # Test feature preparation
        df_prepared, features = feature_engineer.prepare_features(df_with_features, target_col='Target')
        logger.info(f"✅ Feature preparation successful: {len(features)} features prepared")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in feature engineering test: {e}")
        return False

def test_model_splitting():
    """Test the fixed time-based splitting"""
    try:
        logger.info("Testing time-based splitting...")
        
        # Create sample data with proper dates
        dates = pd.date_range(start='2020-01-01', periods=500, freq='D')
        sample_data = {}
        
        for i in range(3):
            ticker = f'TEST{i}'
            df = pd.DataFrame({
                'Date': dates,
                'Open': np.random.uniform(10, 100, 500),
                'High': np.random.uniform(10, 100, 500),
                'Low': np.random.uniform(10, 100, 500),
                'Close': np.random.uniform(10, 100, 500),
                'Volume': np.random.uniform(1000, 10000, 500),
                'Target': np.random.choice(['BUY', 'SELL', 'HOLD'], 500)
            })
            sample_data[ticker] = df
        
        # Initialize model trainer
        model_trainer = EnhancedStockPredictor()
        
        # Test time-based splitting
        train_data, val_data, test_data = model_trainer.split_data_time_based(sample_data)
        
        logger.info(f"✅ Time-based splitting successful:")
        logger.info(f"  Train: {len(train_data)} samples")
        logger.info(f"  Val: {len(val_data)} samples")
        logger.info(f"  Test: {len(test_data)} samples")
        
        # Check date ranges
        if len(train_data) > 0:
            logger.info(f"  Train date range: {train_data['Date'].min()} to {train_data['Date'].max()}")
        if len(test_data) > 0:
            logger.info(f"  Test date range: {test_data['Date'].min()} to {test_data['Date'].max()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in model splitting test: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("TESTING FIXES")
    logger.info("=" * 60)
    
    tests = [
        ("Data Collection", test_data_collection),
        ("Feature Engineering", test_feature_engineering),
        ("Model Splitting", test_model_splitting)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        logger.info("\n🎉 All tests passed! The fixes are working correctly.")
    else:
        logger.info("\n⚠️ Some tests failed. Please check the logs for details.")
    
    return all_passed

if __name__ == "__main__":
    main() 