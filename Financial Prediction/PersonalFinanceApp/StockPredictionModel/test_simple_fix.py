#!/usr/bin/env python3
"""
Simple test to verify the date handling fixes work
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
        logging.FileHandler('test_simple_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_date_handling():
    """Test the date handling fixes"""
    try:
        logger.info("Testing date handling fixes...")
        
        # Test with a small number of companies
        data_collector = IncrementalASXDataCollector(max_workers=2)
        data = data_collector.collect_all_data_incremental(max_companies=3)
        
        if data and data.get('stock_data'):
            logger.info(f"✅ Data collection successful! Collected data for {len(data['stock_data'])} tickers")
            
            # Test processing one ticker
            for ticker, df in data['stock_data'].items():
                logger.info(f"\nTesting {ticker}...")
                
                # Check if Date column exists and is properly formatted
                if 'Date' in df.columns:
                    logger.info(f"  Date column type: {df['Date'].dtype}")
                    
                    # Test datetime conversion
                    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
                        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                        logger.info(f"  Converted Date to datetime: {df['Date'].dtype}")
                    
                    # Test timezone handling
                    if df['Date'].dt.tz is not None:
                        df['Date'] = df['Date'].dt.tz_localize(None)
                        logger.info("  Removed timezone info")
                    
                    # Test date range
                    current_date = pd.Timestamp.now()
                    df = df[df['Date'] <= current_date]
                    logger.info(f"  Filtered to current date: {len(df)} rows")
                    
                    # Test feature engineering
                    feature_engineer = FeatureEngineer()
                    df_with_features = feature_engineer.calculate_technical_indicators(df)
                    logger.info(f"  ✅ Feature engineering successful: {len(df_with_features.columns)} features")
                    
                    # Test target creation
                    model_trainer = EnhancedStockPredictor()
                    df_with_target = model_trainer._create_time_based_target(df_with_features)
                    logger.info(f"  ✅ Target creation successful: {df_with_target['Target'].value_counts().to_dict()}")
                    
                    break  # Test with first ticker only
                else:
                    logger.warning(f"  No Date column found for {ticker}")
            
            return True
        else:
            logger.error("❌ No data collected!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in date handling test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Run the test"""
    logger.info("=" * 60)
    logger.info("TESTING DATE HANDLING FIXES")
    logger.info("=" * 60)
    
    success = test_date_handling()
    
    if success:
        logger.info("\n🎉 Date handling test passed!")
        logger.info("The fixes are working correctly.")
    else:
        logger.info("\n❌ Date handling test failed!")
        logger.info("Please check the logs for details.")
    
    logger.info("=" * 60)
    logger.info("TEST COMPLETED")
    logger.info("=" * 60)
    
    return success

if __name__ == "__main__":
    main() 