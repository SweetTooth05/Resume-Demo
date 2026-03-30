#!/usr/bin/env python3
"""
Diagnostic script to identify training issues
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
        logging.FileHandler('diagnose_training.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def diagnose_data_issues():
    """Diagnose data quality issues"""
    try:
        logger.info("=" * 60)
        logger.info("DIAGNOSING TRAINING DATA ISSUES")
        logger.info("=" * 60)
        
        # Initialize components
        data_collector = IncrementalASXDataCollector(max_workers=4)
        feature_engineer = FeatureEngineer()
        model_trainer = EnhancedStockPredictor(transaction_fee=0.01)
        
        # Collect a small sample of data
        logger.info("Collecting sample data...")
        data = data_collector.collect_all_data_incremental(max_companies=5)
        
        if not data or not data.get('stock_data'):
            logger.error("No data collected!")
            return
        
        logger.info(f"Collected data for {len(data['stock_data'])} tickers")
        
        # Process the data
        logger.info("Processing data...")
        processed_data = {}
        
        for ticker, stock_data in data['stock_data'].items():
            try:
                logger.info(f"Processing {ticker}...")
                
                # Calculate technical indicators
                df_with_features = feature_engineer.calculate_technical_indicators(stock_data)
                
                # Create target variable
                df_with_features = model_trainer._create_time_based_target(df_with_features)
                
                # Prepare features
                df_prepared, features = feature_engineer.prepare_features(df_with_features, target_col='Target')
                
                processed_data[ticker] = df_prepared
                logger.info(f"Processed {ticker}: {len(df_prepared)} samples, {len(features)} features")
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
        
        if not processed_data:
            logger.error("No data processed successfully!")
            return
        
        # Analyze the data
        logger.info("Analyzing data quality...")
        
        # Combine all data
        combined_data = pd.concat(processed_data.values(), ignore_index=True)
        logger.info(f"Combined data shape: {combined_data.shape}")
        
        # Check for NaN values
        nan_counts = combined_data.isnull().sum()
        logger.info(f"NaN counts:\n{nan_counts[nan_counts > 0]}")
        
        # Check target distribution
        if 'Target' in combined_data.columns:
            target_dist = combined_data['Target'].value_counts()
            logger.info(f"Target distribution:\n{target_dist}")
            
            # Check if target is too imbalanced
            if len(target_dist) < 2:
                logger.error("Target has only one class! This will cause perfect accuracy.")
            elif target_dist.min() / target_dist.max() < 0.1:
                logger.warning("Target is highly imbalanced!")
        
        # Check feature distributions
        numeric_cols = combined_data.select_dtypes(include=[np.number]).columns
        logger.info(f"Number of numeric features: {len(numeric_cols)}")
        
        # Check for constant features
        constant_features = []
        for col in numeric_cols:
            if col != 'Target' and combined_data[col].nunique() <= 1:
                constant_features.append(col)
        
        if constant_features:
            logger.warning(f"Constant features found: {constant_features}")
        
        # Check for infinite values
        inf_counts = np.isinf(combined_data[numeric_cols]).sum()
        logger.info(f"Infinite value counts:\n{inf_counts[inf_counts > 0]}")
        
        # Test data splitting
        logger.info("Testing data splitting...")
        try:
            train_data, val_data, test_data = model_trainer.split_data_time_based(processed_data)
            
            logger.info(f"Split results:")
            logger.info(f"  Train: {len(train_data)} samples")
            logger.info(f"  Val: {len(val_data)} samples")
            logger.info(f"  Test: {len(test_data)} samples")
            
            # Check if splits have the target
            for split_name, split_data in [("Train", train_data), ("Val", val_data), ("Test", test_data)]:
                if 'Target' in split_data.columns:
                    target_dist = split_data['Target'].value_counts()
                    logger.info(f"  {split_name} target distribution: {dict(target_dist)}")
                else:
                    logger.error(f"  {split_name} data missing Target column!")
            
        except Exception as e:
            logger.error(f"Error in data splitting: {e}")
        
        # Test feature scaling
        logger.info("Testing feature scaling...")
        try:
            columns_to_drop = ['Target', 'Target_Encoded', 'Date']
            if 'Ticker' in train_data.columns:
                columns_to_drop.append('Ticker')
            
            X_train = train_data.drop(columns=columns_to_drop)
            y_train = train_data['Target_Encoded'] if 'Target_Encoded' in train_data.columns else train_data['Target']
            
            logger.info(f"X_train shape: {X_train.shape}")
            logger.info(f"y_train shape: {y_train.shape}")
            
            # Check for NaN in features
            nan_in_features = X_train.isnull().sum().sum()
            logger.info(f"NaN values in features: {nan_in_features}")
            
            if nan_in_features > 0:
                logger.error("Features contain NaN values! This will cause training to fail.")
            
            # Scale features
            X_train_scaled = feature_engineer.scale_features(X_train, fit=True)
            logger.info(f"Scaling completed. Shape: {X_train_scaled.shape}")
            
            # Check for NaN after scaling
            nan_after_scaling = X_train_scaled.isnull().sum().sum()
            logger.info(f"NaN values after scaling: {nan_after_scaling}")
            
        except Exception as e:
            logger.error(f"Error in feature scaling: {e}")
        
        logger.info("=" * 60)
        logger.info("DIAGNOSIS COMPLETED")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in diagnosis: {e}")

if __name__ == "__main__":
    diagnose_data_issues() 