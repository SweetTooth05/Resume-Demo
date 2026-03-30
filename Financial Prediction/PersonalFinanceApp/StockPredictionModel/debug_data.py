#!/usr/bin/env python3
"""
Debug script to check what data is being collected
"""

import pandas as pd
import logging
from pathlib import Path
import sys

# Add the current directory to the path to import modules
sys.path.append(str(Path(__file__).parent))

from incremental_data_collector import IncrementalASXDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def debug_data_collection():
    """Debug the data collection process"""
    try:
        logger.info("Starting data collection debug...")
        
        # Initialize data collector
        data_collector = IncrementalASXDataCollector(max_workers=2)
        
        # Test with a small number of companies
        data = data_collector.collect_all_data_incremental(max_companies=5)
        
        if data and data.get('stock_data'):
            logger.info(f"Collected data for {len(data['stock_data'])} tickers")
            
            for ticker, df in data['stock_data'].items():
                logger.info(f"\n=== {ticker} ===")
                logger.info(f"Shape: {df.shape}")
                logger.info(f"Columns: {list(df.columns)}")
                logger.info(f"Data types: {df.dtypes.to_dict()}")
                
                if 'Date' in df.columns:
                    logger.info(f"Date column type: {df['Date'].dtype}")
                    logger.info(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
                    logger.info(f"Sample dates: {df['Date'].head().tolist()}")
                else:
                    logger.warning("No Date column found!")
                
                if 'Close' in df.columns:
                    logger.info(f"Close price range: {df['Close'].min():.2f} to {df['Close'].max():.2f}")
                else:
                    logger.warning("No Close column found!")
                
                # Show first few rows
                logger.info(f"First 3 rows:")
                logger.info(df.head(3).to_string())
                
        else:
            logger.error("No data collected!")
            
    except Exception as e:
        logger.error(f"Error in debug: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    debug_data_collection() 