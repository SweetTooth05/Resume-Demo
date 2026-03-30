#!/usr/bin/env python3
"""
Fixed Retraining Script for Stock Prediction Model
Addresses all identified issues:
1. Yahoo Finance session problems
2. Date handling issues
3. NaN value handling
4. Time-based splitting logic
"""

import pandas as pd
import numpy as np
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import glob
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

# Add the current directory to the path to import modules
sys.path.append(str(Path(__file__).parent))

from config import (
    BASE_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, 
    SCALERS_DIR, FEATURES_DIR, LOGGING_CONFIG
)
from incremental_data_collector import IncrementalASXDataCollector
from enhanced_model import EnhancedStockPredictor
from feature_engineering import FeatureEngineer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retrain_model_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixedModelRetrainer:
    """Fixed model retrainer with all issues resolved"""
    
    def __init__(self, max_companies: int = 50, use_gpu: bool = True):
        self.max_companies = max_companies
        self.use_gpu = use_gpu
        
        # Initialize components with optimized settings
        self.data_collector = IncrementalASXDataCollector(max_workers=5)  # Reduced for stability
        self.feature_engineer = FeatureEngineer()
        self.model_trainer = EnhancedStockPredictor(transaction_fee=0.01)
        
        # Performance tracking
        self.start_time = None
        self.performance_metrics = {}
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [MODELS_DIR, SCALERS_DIR, FEATURES_DIR, BASE_DIR / "backups"]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_backup_timestamp(self) -> str:
        """Get timestamp for backup naming"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def backup_existing_models(self) -> Optional[Path]:
        """Backup existing models"""
        try:
            timestamp = self._get_backup_timestamp()
            backup_dir = BASE_DIR / "backups" / f"models_backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup model files
            model_files = list(MODELS_DIR.glob("*.pkl")) + list(MODELS_DIR.glob("*.joblib"))
            for model_file in model_files:
                if model_file.exists():
                    shutil.copy2(model_file, backup_dir / model_file.name)
            
            # Backup scalers
            scaler_files = list(SCALERS_DIR.glob("*.pkl"))
            for scaler_file in scaler_files:
                if scaler_file.exists():
                    shutil.copy2(scaler_file, backup_dir / scaler_file.name)
            
            logger.info(f"Models backed up to: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Error backing up models: {e}")
            return None
    
    def update_data_incremental(self) -> Dict:
        """Update data incrementally with fixed session handling"""
        try:
            logger.info("Starting incremental data collection...")
            
            # Collect data with fixed session handling
            data = self.data_collector.collect_all_data_incremental(max_companies=self.max_companies)
            
            if not data or not data.get('stock_data'):
                logger.error("No data collected!")
                return {}
            
            logger.info(f"Collected data for {len(data['stock_data'])} tickers")
            return data
            
        except Exception as e:
            logger.error(f"Error updating data: {e}")
            return {}
    
    def clean_and_process_data(self, data: Dict) -> Dict[str, pd.DataFrame]:
        """Clean and process data with proper date handling"""
        try:
            logger.info("Cleaning and processing data...")
            
            processed_data = {}
            
            for ticker, stock_data in data['stock_data'].items():
                try:
                    logger.info(f"Processing {ticker}...")
                    
                    # Debug: Check data structure
                    logger.info(f"  {ticker} data shape: {stock_data.shape}")
                    logger.info(f"  {ticker} columns: {list(stock_data.columns)}")
                    
                    # Ensure Date column is properly formatted
                    if 'Date' in stock_data.columns:
                        # Check if Date is already datetime
                        if not pd.api.types.is_datetime64_any_dtype(stock_data['Date']):
                            # Convert string dates to datetime
                            stock_data['Date'] = pd.to_datetime(stock_data['Date'], errors='coerce')
                        
                        # Remove timezone info if present
                        if stock_data['Date'].dt.tz is not None:
                            stock_data['Date'] = stock_data['Date'].dt.tz_localize(None)
                        
                        # Remove rows with invalid dates
                        stock_data = stock_data.dropna(subset=['Date'])
                        
                        # Ensure dates are in reasonable range (not future dates)
                        current_date = datetime.now()
                        stock_data = stock_data[stock_data['Date'] <= current_date]
                        
                        logger.info(f"  {ticker} after date processing: {len(stock_data)} rows")
                    else:
                        # If no Date column, create one based on index
                        logger.warning(f"  {ticker} has no Date column, creating one")
                        stock_data['Date'] = pd.date_range(start='2020-01-01', periods=len(stock_data), freq='D')
                    
                    if len(stock_data) < 50:  # Minimum data requirement
                        logger.warning(f"Insufficient data for {ticker}: {len(stock_data)} rows")
                        continue
                    
                    # Calculate technical indicators
                    df_with_features = self.feature_engineer.calculate_technical_indicators(stock_data)
                    
                    # Create target variable
                    df_with_features = self.model_trainer._create_time_based_target(df_with_features)
                    
                    # Handle NaN values before feature preparation
                    df_with_features = self._handle_nan_values(df_with_features)
                    
                    # Prepare features
                    df_prepared, features = self.feature_engineer.prepare_features(df_with_features, target_col='Target')
                    
                    if len(df_prepared) > 0:
                        processed_data[ticker] = df_prepared
                        logger.info(f"Processed {ticker}: {len(df_prepared)} samples, {len(features)} features")
                    else:
                        logger.warning(f"No processed data for {ticker}")
                    
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(processed_data)} tickers")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error in data cleaning: {e}")
            return {}
    
    def _handle_nan_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle NaN values in the dataset"""
        try:
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            # Fill NaN values with appropriate methods
            for col in numeric_cols:
                if col == 'Target' or col == 'Target_Encoded':
                    continue
                
                # For price/volume columns, use forward fill then backward fill
                if any(keyword in col.lower() for keyword in ['open', 'high', 'low', 'close', 'volume']):
                    df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                else:
                    # For technical indicators, use median
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
            
            # Remove any remaining rows with NaN values
            df = df.dropna()
            
            logger.info(f"Handled NaN values. Remaining rows: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"Error handling NaN values: {e}")
            return df
    
    def engineer_features(self, cleaned_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Engineer features with proper error handling"""
        try:
            logger.info("Engineering features...")
            
            processed_data = {}
            
            for ticker, df in cleaned_data.items():
                try:
                    # Features are already engineered in clean_and_process_data
                    # Just ensure they're properly formatted
                    processed_data[ticker] = df
                    
                except Exception as e:
                    logger.error(f"Error engineering features for {ticker}: {e}")
                    continue
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error in feature engineering: {e}")
            return {}
    
    def prepare_training_data(self, processed_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Prepare training data with proper validation"""
        try:
            logger.info("Preparing training data...")
            
            # Validate data quality
            valid_data = {}
            for ticker, df in processed_data.items():
                if len(df) >= 50 and 'Target' in df.columns:
                    # Check for sufficient target distribution
                    target_counts = df['Target'].value_counts()
                    if len(target_counts) >= 2 and target_counts.min() >= 10:
                        valid_data[ticker] = df
                    else:
                        logger.warning(f"Insufficient target distribution for {ticker}")
                else:
                    logger.warning(f"Insufficient data for {ticker}")
            
            logger.info(f"Valid training data for {len(valid_data)} tickers")
            return valid_data
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return {}
    
    def retrain_model(self, training_data: Dict[str, pd.DataFrame]) -> bool:
        """Retrain model with fixed data handling"""
        try:
            logger.info("Starting model retraining...")
            
            if not training_data:
                logger.error("No training data available!")
                return False
            
            # Train models using the enhanced model trainer
            results = self.model_trainer.train_models(training_data)
            
            if results:
                logger.info("Model retraining completed successfully!")
                return True
            else:
                logger.error("Model retraining failed!")
                return False
                
        except Exception as e:
            logger.error(f"Error in model retraining: {e}")
            return False
    
    def validate_model(self) -> Dict:
        """Validate the retrained model"""
        try:
            logger.info("Validating model...")
            
            # Test prediction on a few stocks
            test_tickers = ['BHP', 'CBA', 'CSL']
            validation_results = {}
            
            for ticker in test_tickers:
                try:
                    prediction = self.model_trainer.predict_stock(ticker)
                    validation_results[ticker] = prediction
                except Exception as e:
                    logger.warning(f"Could not validate {ticker}: {e}")
            
            logger.info(f"Model validation completed for {len(validation_results)} tickers")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating model: {e}")
            return {}
    
    def run_full_retraining_pipeline(self) -> bool:
        """Run the complete retraining pipeline with all fixes"""
        try:
            self.start_time = datetime.now()
            logger.info("Starting full model retraining pipeline...")
            
            # Step 1: Backup existing models
            backup_dir = self.backup_existing_models()
            if not backup_dir:
                logger.warning("Could not backup existing models, but continuing...")
            
            # Step 2: Update data incrementally
            data = self.update_data_incremental()
            if not data:
                logger.error("Failed to update data")
                return False
            
            # Step 3: Clean and process data
            cleaned_data = self.clean_and_process_data(data)
            if not cleaned_data:
                logger.error("Failed to clean data")
                return False
            
            # Step 4: Engineer features
            processed_data = self.engineer_features(cleaned_data)
            if not processed_data:
                logger.error("Failed to engineer features")
                return False
            
            # Step 5: Prepare training data
            training_data = self.prepare_training_data(processed_data)
            if not training_data:
                logger.error("Failed to prepare training data")
                return False
            
            # Step 6: Retrain model
            retrain_success = self.retrain_model(training_data)
            if not retrain_success:
                logger.error("Failed to retrain model")
                return False
            
            # Step 7: Validate model
            validation_results = self.validate_model()
            if not validation_results:
                logger.warning("Model validation failed")
            
            # Calculate performance metrics
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            self.performance_metrics = {
                'duration_seconds': duration,
                'companies_processed': len(data.get('stock_data', {})),
                'success': True
            }
            
            logger.info("Full retraining pipeline completed successfully!")
            logger.info(f"Total duration: {duration:.2f} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Error in retraining pipeline: {e}")
            return False

def main():
    """Main function for model retraining"""
    try:
        logger.info("=" * 60)
        logger.info("STARTING FIXED MODEL RETRAINING PROCESS")
        logger.info("=" * 60)
        
        # Initialize retrainer with optimized settings
        retrainer = FixedModelRetrainer(max_companies=20, use_gpu=True)  # Reduced for testing
        
        # Run the full pipeline
        success = retrainer.run_full_retraining_pipeline()
        
        if success:
            logger.info("Model retraining completed successfully!")
            logger.info("The model has been updated with the latest data.")
            logger.info(f"Performance metrics: {retrainer.performance_metrics}")
        else:
            logger.error("Model retraining failed!")
            logger.error("Please check the logs for more details.")
        
        logger.info("=" * 60)
        logger.info("RETRAINING PROCESS COMPLETED")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return False

if __name__ == "__main__":
    main() 