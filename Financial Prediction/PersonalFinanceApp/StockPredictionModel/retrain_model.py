"""
Optimized Retraining Script for Stock Prediction Model
Uses incremental data collection and retrains the model with updated data
"""

import pandas as pd
import numpy as np
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
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
        logging.FileHandler('retrain_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedModelRetrainer:
    """Optimized model retrainer with improved efficiency and error handling"""
    
    def __init__(self, max_companies: int = 50, use_gpu: bool = True):
        self.max_companies = max_companies
        self.use_gpu = use_gpu
        
        # Initialize components with optimized settings
        self.data_collector = IncrementalASXDataCollector(max_workers=10)  # Reduced workers for stability
        self.feature_engineer = FeatureEngineer()
        self.data_cleaner = None  # Lazy initialization
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
        """Backup existing models with optimized file operations"""
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
            
            # Backup feature importance
            feature_file = FEATURES_DIR / "feature_importance.csv"
            if feature_file.exists():
                shutil.copy2(feature_file, backup_dir / "feature_importance.csv")
            
            # Backup performance metrics
            performance_file = BASE_DIR / "processed_finance_data" / "model_performance.csv"
            if performance_file.exists():
                shutil.copy2(performance_file, backup_dir / "model_performance.csv")
            
            logger.info(f"Models backed up to: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Error backing up models: {e}")
            return None
    
    def update_data_incremental(self) -> Dict:
        """Update data using incremental collection with memory optimization"""
        try:
            logger.info("Starting incremental data update...")
            
            # Collect data incrementally
            data = self.data_collector.collect_all_data_incremental(max_companies=self.max_companies)
            
            if not data or not data.get('stock_data'):
                raise Exception("No stock data collected")
            
            logger.info(f"Data update completed. Collected data for {len(data['stock_data'])} tickers")
            return data
            
        except Exception as e:
            logger.error(f"Error updating data: {e}")
            return {}
    
    def clean_and_process_data(self, data: Dict) -> Dict[str, pd.DataFrame]:
        """Clean and process the updated data with optimized memory usage"""
        try:
            logger.info("Cleaning and processing data...")
            
            # Lazy initialize data cleaner
            if self.data_cleaner is None:
                from FinanceDataCleaning import ASXFinanceDataProcessor
                self.data_cleaner = ASXFinanceDataProcessor("ASXListedCompanies.csv")
            
            # Clean the data
            cleaned_data = {}
            
            for ticker, df in data['stock_data'].items():
                try:
                    cleaned_df = self.data_cleaner.process_financial_data(df)
                    if cleaned_df is not None and not cleaned_df.empty:
                        cleaned_data[ticker] = cleaned_df
                        logger.info(f"Cleaned data for {ticker}: {len(cleaned_df)} records")
                except Exception as e:
                    logger.warning(f"Error cleaning data for {ticker}: {e}")
                    continue
            
            # Clear memory
            del data
            gc.collect()
            
            logger.info(f"Data cleaning completed. Cleaned data for {len(cleaned_data)} tickers")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            return {}
    
    def engineer_features(self, cleaned_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Engineer features for the cleaned data with parallel processing"""
        try:
            logger.info("Engineering features...")
            
            # Process features for each ticker
            processed_data = {}
            
            def process_ticker_features(ticker_df_tuple):
                ticker, df = ticker_df_tuple
                try:
                    processed_df = self.feature_engineer.calculate_technical_indicators(df)
                    if processed_df is not None and not processed_df.empty:
                        return ticker, processed_df
                except Exception as e:
                    logger.warning(f"Error engineering features for {ticker}: {e}")
                return None
            
            # Use parallel processing for feature engineering
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(process_ticker_features, (ticker, df)) 
                          for ticker, df in cleaned_data.items()]
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        ticker, processed_df = result
                        processed_data[ticker] = processed_df
                        logger.info(f"Engineered features for {ticker}: {len(processed_df)} records")
            
            # Clear memory
            del cleaned_data
            gc.collect()
            
            logger.info(f"Feature engineering completed. Processed {len(processed_data)} tickers")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            return {}
    
    def prepare_training_data(self, processed_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Prepare data for training by splitting into train/validation/test sets"""
        try:
            logger.info("Preparing training data...")
            
            # Use the model trainer's data preparation method
            training_data = self.model_trainer.collect_and_prepare_data_from_dict(processed_data)
            
            # Clear memory
            del processed_data
            gc.collect()
            
            logger.info("Training data preparation completed")
            return training_data
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return {}
    
    def retrain_model(self, training_data: Dict[str, pd.DataFrame]) -> bool:
        """Retrain the model with updated data"""
        try:
            logger.info("Starting model retraining...")
            
            # Train the models
            results = self.model_trainer.train_models(training_data)
            
            if results and results.get('success', False):
                logger.info("Model retraining completed successfully!")
                return True
            else:
                logger.error("Model retraining failed!")
                return False
                
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
            return False
    
    def validate_model(self) -> Dict:
        """Validate the retrained model"""
        try:
            logger.info("Validating retrained model...")
            
            # Test the model on a few tickers
            test_tickers = ['WES', 'CBA', 'BHP', 'CSL', 'NAB']
            validation_results = {}
            
            for ticker in test_tickers:
                try:
                    prediction = self.model_trainer.predict_stock(ticker)
                    validation_results[ticker] = prediction
                    logger.info(f"Validation for {ticker}: {prediction.get('prediction', 'N/A')}")
                except Exception as e:
                    logger.warning(f"Validation failed for {ticker}: {e}")
                    continue
            
            logger.info("Model validation completed")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating model: {e}")
            return {}
    
    def run_full_retraining_pipeline(self) -> bool:
        """Run the complete retraining pipeline with performance tracking"""
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
        logger.info("STARTING MODEL RETRAINING PROCESS")
        logger.info("=" * 60)
        
        # Initialize retrainer with optimized settings
        retrainer = OptimizedModelRetrainer(max_companies=50, use_gpu=True)
        
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