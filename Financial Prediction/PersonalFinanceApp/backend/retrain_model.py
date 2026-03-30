#!/usr/bin/env python3
"""
Model Retraining Script for Personal Finance App Backend
Comprehensive pipeline for retraining the entire model system
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import json
import shutil

# Add StockPredictionModel to path
stock_model_path = Path(__file__).parent.parent / "StockPredictionModel"
sys.path.append(str(stock_model_path))

try:
    from enhanced_model import EnhancedStockPredictor
    from data_collector import ASXDataCollector
    from config import MODEL_CONFIG, DATA_CONFIG, BASE_DIR
except ImportError as e:
    logging.error(f"Could not import StockPredictionModel modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retrain_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ModelRetrainer:
    """Comprehensive model retraining system"""
    
    def __init__(self, config: dict = None):
        self.config = config or {
            'max_companies': 100,
            'transaction_fee': 0.01,
            'backup_models': True,
            'validate_models': True,
            'update_database': True,
            'cleanup_old_models': True
        }
        self.backup_dir = None
        self.retrain_start_time = None
        
    def run_full_retraining_pipeline(self) -> bool:
        """Run the complete retraining pipeline"""
        try:
            self.retrain_start_time = datetime.now()
            logger.info("🚀 Starting full model retraining pipeline...")
            logger.info(f"Configuration: {self.config}")
            
            # Step 1: Backup existing models
            if self.config['backup_models']:
                self._backup_existing_models()
            
            # Step 2: Clean up old data
            if self.config['cleanup_old_models']:
                self._cleanup_old_data()
            
            # Step 3: Collect fresh data
            logger.info("📊 Step 3: Collecting fresh data...")
            data_collector = ASXDataCollector(max_workers=15)
            data = data_collector.collect_all_data(max_companies=self.config['max_companies'])
            
            if not data:
                logger.error("❌ Failed to collect data")
                return False
            
            # Step 4: Train new models
            logger.info("🤖 Step 4: Training new models...")
            predictor = EnhancedStockPredictor(transaction_fee=self.config['transaction_fee'])
            performance = predictor.run_full_pipeline(max_companies=self.config['max_companies'])
            
            if not performance:
                logger.error("❌ Failed to train models")
                return False
            
            # Step 5: Validate new models
            if self.config['validate_models']:
                logger.info("✅ Step 5: Validating new models...")
                if not self._validate_new_models(performance):
                    logger.error("❌ Model validation failed")
                    return False
            
            # Step 6: Update database
            if self.config['update_database']:
                logger.info("🗄️ Step 6: Updating database...")
                self._update_database_with_new_predictions()
            
            # Step 7: Generate retraining report
            self._generate_retraining_report(performance)
            
            # Step 8: Cleanup
            self._cleanup_after_retraining()
            
            retrain_duration = datetime.now() - self.retrain_start_time
            logger.info(f"🎉 Full retraining pipeline completed successfully!")
            logger.info(f"⏱️ Total duration: {retrain_duration}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in retraining pipeline: {e}")
            self._rollback_on_failure()
            return False
    
    def _backup_existing_models(self):
        """Backup existing models before retraining"""
        try:
            logger.info("💾 Backing up existing models...")
            
            # Create backup directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = BASE_DIR / "backups" / f"models_backup_{timestamp}"
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup model files
            models_dir = BASE_DIR / "processed_finance_data" / "models"
            if models_dir.exists():
                for model_file in models_dir.glob("*.pkl"):
                    backup_path = self.backup_dir / model_file.name
                    shutil.copy2(model_file, backup_path)
                    logger.info(f"Backed up: {model_file.name}")
            
            # Backup feature importance
            features_dir = BASE_DIR / "processed_finance_data" / "features"
            if features_dir.exists():
                for feature_file in features_dir.glob("*.csv"):
                    backup_path = self.backup_dir / feature_file.name
                    shutil.copy2(feature_file, backup_path)
                    logger.info(f"Backed up: {feature_file.name}")
            
            logger.info(f"✅ Models backed up to: {self.backup_dir}")
            
        except Exception as e:
            logger.error(f"❌ Error backing up models: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old data and temporary files"""
        try:
            logger.info("🧹 Cleaning up old data...")
            
            # Clean up old logs
            logs_dir = BASE_DIR / "logs"
            if logs_dir.exists():
                for log_file in logs_dir.glob("*.log"):
                    if log_file.stat().st_mtime < (datetime.now() - timedelta(days=7)).timestamp():
                        log_file.unlink()
                        logger.info(f"Cleaned up old log: {log_file.name}")
            
            # Clean up temporary files
            temp_patterns = ["*.tmp", "*.temp", "*.cache"]
            for pattern in temp_patterns:
                for temp_file in BASE_DIR.rglob(pattern):
                    temp_file.unlink()
                    logger.info(f"Cleaned up temp file: {temp_file}")
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    def _validate_new_models(self, performance: dict) -> bool:
        """Validate new models against performance thresholds"""
        try:
            logger.info("🔍 Validating new models...")
            
            # Check ensemble performance
            ensemble_perf = performance.get('ensemble', {})
            fee_accuracy = ensemble_perf.get('fee_based_accuracy', 0)
            f1_score = ensemble_perf.get('f1_score', 0)
            
            # Performance thresholds
            min_fee_accuracy = 0.55  # 55% fee-based accuracy
            min_f1_score = 0.50      # 50% F1 score
            
            logger.info(f"Model Performance:")
            logger.info(f"  - Fee-based accuracy: {fee_accuracy:.4f} (min: {min_fee_accuracy})")
            logger.info(f"  - F1 score: {f1_score:.4f} (min: {min_f1_score})")
            
            # Check if models meet thresholds
            if fee_accuracy < min_fee_accuracy:
                logger.warning(f"⚠️ Fee-based accuracy below threshold: {fee_accuracy:.4f} < {min_fee_accuracy}")
                return False
            
            if f1_score < min_f1_score:
                logger.warning(f"⚠️ F1 score below threshold: {f1_score:.4f} < {min_f1_score}")
                return False
            
            # Check individual model performance
            for model_name, model_perf in performance.items():
                if model_name != 'ensemble':
                    model_fee_acc = model_perf.get('fee_based_accuracy', 0)
                    if model_fee_acc < 0.45:  # Individual models should have at least 45% accuracy
                        logger.warning(f"⚠️ {model_name} accuracy below threshold: {model_fee_acc:.4f}")
            
            logger.info("✅ Model validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating models: {e}")
            return False
    
    def _update_database_with_new_predictions(self):
        """Update database with new predictions"""
        try:
            logger.info("🗄️ Updating database with new predictions...")
            
            # Run the enhanced data population script
            populate_script = Path(__file__).parent / "populate_enhanced_data.py"
            if populate_script.exists():
                result = subprocess.run([
                    sys.executable, str(populate_script)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ Database updated successfully")
                else:
                    logger.error(f"❌ Database update failed: {result.stderr}")
                    return False
            else:
                logger.warning("⚠️ populate_enhanced_data.py not found, skipping database update")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating database: {e}")
            return False
    
    def _generate_retraining_report(self, performance: dict):
        """Generate comprehensive retraining report"""
        try:
            logger.info("📊 Generating retraining report...")
            
            # Create report directory
            reports_dir = BASE_DIR / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            # Generate report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"retraining_report_{timestamp}.json"
            
            report_data = {
                'retraining_info': {
                    'start_time': self.retrain_start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'duration_minutes': (datetime.now() - self.retrain_start_time).total_seconds() / 60,
                    'configuration': self.config
                },
                'model_performance': performance,
                'backup_location': str(self.backup_dir) if self.backup_dir else None,
                'status': 'success'
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"✅ Retraining report saved to: {report_file}")
            
            # Print summary
            self._print_retraining_summary(performance)
            
        except Exception as e:
            logger.error(f"❌ Error generating retraining report: {e}")
    
    def _print_retraining_summary(self, performance: dict):
        """Print retraining summary"""
        try:
            logger.info("=" * 60)
            logger.info("🎉 RETRAINING SUMMARY")
            logger.info("=" * 60)
            
            ensemble_perf = performance.get('ensemble', {})
            logger.info(f"Ensemble Performance:")
            logger.info(f"  - Fee-based accuracy: {ensemble_perf.get('fee_based_accuracy', 0):.4f}")
            logger.info(f"  - F1 score: {ensemble_perf.get('f1_score', 0):.4f}")
            logger.info(f"  - Standard accuracy: {ensemble_perf.get('accuracy', 0):.4f}")
            
            logger.info(f"\nIndividual Models:")
            for model_name, model_perf in performance.items():
                if model_name != 'ensemble':
                    logger.info(f"  - {model_name}: {model_perf.get('fee_based_accuracy', 0):.4f} fee accuracy")
            
            logger.info(f"\nConfiguration:")
            logger.info(f"  - Companies processed: {self.config['max_companies']}")
            logger.info(f"  - Transaction fee: {self.config['transaction_fee']:.2%}")
            logger.info(f"  - Backup created: {self.config['backup_models']}")
            logger.info(f"  - Database updated: {self.config['update_database']}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Error printing summary: {e}")
    
    def _cleanup_after_retraining(self):
        """Cleanup after successful retraining"""
        try:
            logger.info("🧹 Cleaning up after retraining...")
            
            # Remove old backups (keep only last 3)
            backups_dir = BASE_DIR / "backups"
            if backups_dir.exists():
                backup_dirs = sorted([d for d in backups_dir.iterdir() if d.is_dir()], 
                                   key=lambda x: x.stat().st_mtime, reverse=True)
                
                for old_backup in backup_dirs[3:]:  # Keep only last 3 backups
                    shutil.rmtree(old_backup)
                    logger.info(f"Removed old backup: {old_backup.name}")
            
            # Clean up temporary files
            for temp_file in BASE_DIR.rglob("*.tmp"):
                temp_file.unlink()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    def _rollback_on_failure(self):
        """Rollback to previous models on failure"""
        try:
            if self.backup_dir and self.backup_dir.exists():
                logger.info("🔄 Rolling back to previous models...")
                
                models_dir = BASE_DIR / "processed_finance_data" / "models"
                models_dir.mkdir(parents=True, exist_ok=True)
                
                # Restore backed up models
                for backup_file in self.backup_dir.glob("*.pkl"):
                    restore_path = models_dir / backup_file.name
                    shutil.copy2(backup_file, restore_path)
                    logger.info(f"Restored: {backup_file.name}")
                
                logger.info("✅ Rollback completed")
            else:
                logger.warning("⚠️ No backup available for rollback")
                
        except Exception as e:
            logger.error(f"❌ Error during rollback: {e}")

def main():
    """Main function for retraining"""
    parser = argparse.ArgumentParser(description='Retrain the stock prediction model')
    parser.add_argument('--max-companies', type=int, default=100, 
                       help='Maximum number of companies to process')
    parser.add_argument('--transaction-fee', type=float, default=0.01,
                       help='Transaction fee for accuracy calculation')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backing up existing models')
    parser.add_argument('--no-validation', action='store_true',
                       help='Skip model validation')
    parser.add_argument('--no-database-update', action='store_true',
                       help='Skip database update')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup of old data')
    
    args = parser.parse_args()
    
    # Create configuration
    config = {
        'max_companies': args.max_companies,
        'transaction_fee': args.transaction_fee,
        'backup_models': not args.no_backup,
        'validate_models': not args.no_validation,
        'update_database': not args.no_database_update,
        'cleanup_old_models': not args.no_cleanup
    }
    
    # Run retraining
    retrainer = ModelRetrainer(config)
    success = retrainer.run_full_retraining_pipeline()
    
    if success:
        logger.info("🎉 Model retraining completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Model retraining failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 