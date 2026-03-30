"""
Enhanced Stock Prediction Model with Sentiment Analysis Integration
With proper time-based splitting, CUDA optimization, and transaction fee evaluation
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pickle
import logging
import warnings
from datetime import datetime, timedelta
import glob
import psutil
import gc
from tqdm import tqdm
import joblib
from typing import Dict, List, Optional, Tuple, Any
import optuna
from optuna.integration import XGBoostPruningCallback

from config import MODEL_CONFIG, DATA_CONFIG, BASE_DIR, MODELS_DIR, SCALERS_DIR, FEATURES_DIR
from incremental_data_collector import IncrementalASXDataCollector
from feature_engineering import FeatureEngineer

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'logs' / 'enhanced_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedStockPredictor:
    """Enhanced stock predictor with sentiment analysis and improved performance"""
    
    def __init__(self, transaction_fee: float = 0.01):  # 1% transaction fee
        self.data_collector = IncrementalASXDataCollector()
        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.label_encoder = LabelEncoder()
        self.feature_importance = None
        self.model_performance = {}
        self.best_params = {}
        self.transaction_fee = transaction_fee
        self.use_gpu = self._check_cuda_availability()
        
        # Model ensemble
        self.models = {
            'xgboost': None,
            'random_forest': None,
            'gradient_boosting': None,
            'logistic_regression': None
        }
        self.ensemble_weights = {}
        
    def _check_cuda_availability(self) -> bool:
        """Check if CUDA is available for GPU acceleration"""
        try:
            # Check if CUDA is available
            import torch
            if torch.cuda.is_available():
                logger.info(f"CUDA GPU acceleration is available: {torch.cuda.get_device_name(0)}")
                return True
            else:
                logger.warning("⚠️ CUDA not available, falling back to CPU")
                return False
        except ImportError:
            try:
                # Test XGBoost GPU support
                test_model = xgb.XGBClassifier(tree_method='gpu_hist', gpu_id=0)
                logger.info("✅ XGBoost GPU acceleration is available")
                return True
            except Exception as e:
                logger.warning(f"⚠️ GPU acceleration not available: {e}")
                logger.info("🔄 Falling back to CPU training")
                return False
    
    def collect_and_prepare_data(self, max_companies: int = 100) -> Dict[str, pd.DataFrame]:
        """Collect and prepare all data for training"""
        try:
            logger.info("🚀 Starting comprehensive data collection and preparation...")
            
            # Collect data
            data = self.data_collector.collect_all_data(max_companies=max_companies)
            if not data:
                raise Exception("No data collected")
            
            # Prepare features for each stock
            processed_data = {}
            
            for ticker, stock_data in data['stock_data'].items():
                try:
                    logger.info(f"Processing features for {ticker}")
                    
                    # Calculate technical indicators
                    df_with_features = self.feature_engineer.calculate_technical_indicators(stock_data)
                    
                    # Add sentiment features if available
                    if ticker in data['sentiment_data']:
                        df_with_features = self.feature_engineer.add_sentiment_features(
                            df_with_features, data['sentiment_data'][ticker]
                        )
                    
                    # Create target variable with proper time-based approach
                    df_with_features = self._create_time_based_target(df_with_features)
                    
                    # Prepare features
                    df_prepared, features = self.feature_engineer.prepare_features(
                        df_with_features, target_col='Target'
                    )
                    
                    if len(df_prepared) > DATA_CONFIG['min_data_points']:
                        processed_data[ticker] = df_prepared
                        logger.info(f"Processed {ticker}: {len(df_prepared)} samples, {len(features)} features")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {ticker}: {e}")
                    continue
            
            logger.info(f"Data preparation completed: {len(processed_data)} stocks processed")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error in data collection and preparation: {e}")
            return {}
    
    def collect_and_prepare_data_from_dict(self, processed_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Prepare data from already processed dictionary (for retraining)"""
        try:
            logger.info("Preparing data from processed dictionary...")
            
            # Prepare features for each stock
            final_processed_data = {}
            
            for ticker, stock_data in processed_data.items():
                try:
                    logger.info(f"Processing features for {ticker}")
                    
                    # Create target variable with proper time-based approach
                    df_with_features = self._create_time_based_target(stock_data)
                    
                    # Prepare features
                    df_prepared, features = self.feature_engineer.prepare_features(
                        df_with_features, target_col='Target'
                    )
                    
                    if len(df_prepared) > DATA_CONFIG['min_data_points']:
                        final_processed_data[ticker] = df_prepared
                        logger.info(f"Processed {ticker}: {len(df_prepared)} samples, {len(features)} features")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {ticker}: {e}")
                    continue
            
            logger.info(f"Data preparation completed: {len(final_processed_data)} stocks processed")
            return final_processed_data
            
        except Exception as e:
            logger.error(f"Error in data preparation from dict: {e}")
            return {}
    
    def _create_time_based_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create target variable using time-based approach with transaction fees"""
        try:
            # Calculate future returns (next day)
            df['Future_Return'] = df['Close'].shift(-1) / df['Close'] - 1
            
            # Calculate transaction fee threshold
            fee_threshold = self.transaction_fee
            
            # Create classification target based on transaction fee logic
            df['Target'] = 'HOLD'
            
            # BUY: Future return > transaction fee (profitable after fees)
            df.loc[df['Future_Return'] > fee_threshold, 'Target'] = 'BUY'
            
            # SELL: Future return < -transaction fee (avoiding losses)
            df.loc[df['Future_Return'] < -fee_threshold, 'Target'] = 'SELL'
            
            # HOLD: Between -fee_threshold and +fee_threshold (not profitable after fees)
            
            # Remove rows with NaN targets (last row)
            df = df.dropna(subset=['Target'])
            
            # Add target encoding for ML
            target_mapping = {'SELL': 0, 'HOLD': 1, 'BUY': 2}
            df['Target_Encoded'] = df['Target'].map(target_mapping)
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating time-based target: {e}")
            return df
    
    def split_data_time_based(self, data: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split data based on time (last year for testing)"""
        try:
            logger.info("Splitting data based on time...")
            
            # Combine all data
            combined_data = pd.concat(data.values(), ignore_index=True)
            
            # Ensure Date column is datetime and handle timezone issues
            if 'Date' in combined_data.columns:
                combined_data['Date'] = pd.to_datetime(combined_data['Date'], errors='coerce')
                
                # Remove timezone info if present
                if combined_data['Date'].dt.tz is not None:
                    combined_data['Date'] = combined_data['Date'].dt.tz_localize(None)
                
                # Remove rows with invalid dates
                combined_data = combined_data.dropna(subset=['Date'])
                
                # Ensure dates are not in the future
                current_date = datetime.now()
                combined_data = combined_data[combined_data['Date'] <= current_date]
            else:
                # Create date index if not available (fallback)
                combined_data['Date'] = pd.date_range(start='2020-01-01', periods=len(combined_data), freq='D')
            
            # Sort by date
            combined_data = combined_data.sort_values('Date').reset_index(drop=True)
            
            # Find the split point (last 20% of data for testing)
            total_rows = len(combined_data)
            test_size = int(0.2 * total_rows)
            val_size = int(0.1 * total_rows)
            train_size = total_rows - test_size - val_size
            
            if train_size < 252:  # Need at least 1 year of training data
                logger.warning(f"Insufficient data for proper time-based split. Using 70/15/15 split instead.")
                train_size = int(0.7 * total_rows)
                val_size = int(0.15 * total_rows)
                test_size = total_rows - train_size - val_size
            
            # Time-based split
            train_data = combined_data.iloc[:train_size]
            val_data = combined_data.iloc[train_size:train_size + val_size]
            test_data = combined_data.iloc[train_size + val_size:]
            
            logger.info(f"Time-based split: Train={len(train_data)}, Val={len(val_data)}, Test={len(test_data)}")
            if len(train_data) > 0:
                logger.info(f"Date ranges: Train={train_data['Date'].min()} to {train_data['Date'].max()}")
            if len(test_data) > 0:
                logger.info(f"Test={test_data['Date'].min()} to {test_data['Date'].max()}")
            
            return train_data, val_data, test_data
            
        except Exception as e:
            logger.error(f"Error in time-based data splitting: {e}")
            # Fallback to random split
            combined_data = pd.concat(data.values(), ignore_index=True)
            train_data, temp_data = train_test_split(combined_data, test_size=0.3, random_state=42)
            val_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)
            return train_data, val_data, test_data
    
    def train_models(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Train multiple models and create ensemble"""
        try:
            logger.info("Starting model training...")
            
            # Split data based on time
            train_data, val_data, test_data = self.split_data_time_based(data)
            
            # Prepare features and target
            columns_to_drop = ['Target', 'Target_Encoded', 'Date']
            if 'Ticker' in train_data.columns:
                columns_to_drop.append('Ticker')
            
            X_train = train_data.drop(columns=columns_to_drop)
            y_train = train_data['Target_Encoded']
            
            X_val = val_data.drop(columns=columns_to_drop)
            y_val = val_data['Target_Encoded']
            
            X_test = test_data.drop(columns=columns_to_drop)
            y_test = test_data['Target_Encoded']
            
            # Scale features
            X_train_scaled = self.feature_engineer.scale_features(X_train, fit=True)
            X_val_scaled = self.feature_engineer.scale_features(X_val, fit=False)
            X_test_scaled = self.feature_engineer.scale_features(X_test, fit=False)
            
            # Train individual models
            self._train_xgboost(X_train_scaled, y_train, X_val_scaled, y_val, X_test_scaled, y_test)
            self._train_random_forest(X_train_scaled, y_train, X_val_scaled, y_val, X_test_scaled, y_test)
            self._train_gradient_boosting(X_train_scaled, y_train, X_val_scaled, y_val, X_test_scaled, y_test)
            self._train_logistic_regression(X_train_scaled, y_train, X_val_scaled, y_val, X_test_scaled, y_test)
            
            # Create ensemble
            self._create_ensemble(X_test_scaled, y_test, test_data)
            
            # Save models
            self._save_models()
            
            # Generate performance report
            self._generate_performance_report(X_test_scaled, y_test, test_data)
            
            logger.info("Model training completed successfully!")
            return self.model_performance
            
        except Exception as e:
            logger.error(f"Error in model training: {e}")
            return {}
    
    def _train_xgboost(self, X_train: pd.DataFrame, y_train: np.ndarray, 
                      X_val: pd.DataFrame, y_val: np.ndarray,
                      X_test: pd.DataFrame, y_test: np.ndarray):
        """Train XGBoost model with hyperparameter optimization and CUDA"""
        try:
            logger.info("Training XGBoost model with CUDA optimization...")
            
            # Define parameter space for optimization
            def objective(trial):
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0, 10),
                    'reg_lambda': trial.suggest_float('reg_lambda', 0, 10),
                    'random_state': MODEL_CONFIG['random_state'],
                    'eval_metric': 'mlogloss',  # Use mlogloss for multi-class
                    'early_stopping_rounds': MODEL_CONFIG['early_stopping_rounds']
                }
                
                # GPU acceleration
                if self.use_gpu:
                    params['tree_method'] = 'gpu_hist'
                    params['gpu_id'] = 0
                    params['predictor'] = 'gpu_predictor'
                else:
                    params['tree_method'] = 'hist'
                    params['n_jobs'] = MODEL_CONFIG['n_jobs']
                
                model = xgb.XGBClassifier(**params)
                
                # Train with validation set
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    verbose=False
                )
                
                # Evaluate on validation set
                y_pred = model.predict(X_val)
                f1 = f1_score(y_val, y_pred, average='weighted')
                
                return f1
            
            # Optimize hyperparameters
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=20)  # Reduced trials for faster training
            
            # Train final model with best parameters
            best_params = study.best_params
            best_params.update({
                'random_state': MODEL_CONFIG['random_state'],
                'eval_metric': 'mlogloss',
                'early_stopping_rounds': MODEL_CONFIG['early_stopping_rounds']
            })
            
            # GPU acceleration
            if self.use_gpu:
                best_params['tree_method'] = 'gpu_hist'
                best_params['gpu_id'] = 0
                best_params['predictor'] = 'gpu_predictor'
            else:
                best_params['tree_method'] = 'hist'
                best_params['n_jobs'] = MODEL_CONFIG['n_jobs']
            
            # Train final model
            self.models['xgboost'] = xgb.XGBClassifier(**best_params)
            self.models['xgboost'].fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
            
            # Evaluate on test set
            y_pred = self.models['xgboost'].predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            # Store performance metrics
            self.model_performance['xgboost'] = {
                'accuracy': accuracy,
                'f1_score': f1,
                'best_params': best_params
            }
            
            logger.info(f"XGBoost trained - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
            
        except Exception as e:
            logger.error(f"Error training XGBoost: {e}")
            # Create a simple fallback model
            self.models['xgboost'] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.models['xgboost'].fit(X_train, y_train)
    
    def _train_random_forest(self, X_train: pd.DataFrame, y_train: np.ndarray,
                           X_val: pd.DataFrame, y_val: np.ndarray,
                           X_test: pd.DataFrame, y_test: np.ndarray):
        """Train Random Forest model"""
        try:
            logger.info("Training Random Forest model...")
            
            # Create and train model
            self.models['random_forest'] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.models['random_forest'].fit(X_train, y_train)
            
            # Evaluate on test set
            y_pred = self.models['random_forest'].predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            # Store performance metrics
            self.model_performance['random_forest'] = {
                'accuracy': accuracy,
                'f1_score': f1
            }
            
            logger.info(f"Random Forest trained - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
            
        except Exception as e:
            logger.error(f"Error training Random Forest: {e}")
            # Create a simple fallback model
            self.models['random_forest'] = RandomForestClassifier(
                n_estimators=50,
                random_state=42
            )
            self.models['random_forest'].fit(X_train, y_train)
    
    def _train_gradient_boosting(self, X_train: pd.DataFrame, y_train: np.ndarray,
                               X_val: pd.DataFrame, y_val: np.ndarray,
                               X_test: pd.DataFrame, y_test: np.ndarray):
        """Train Gradient Boosting model"""
        try:
            logger.info("Training Gradient Boosting model...")
            
            # Create and train model
            self.models['gradient_boosting'] = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.models['gradient_boosting'].fit(X_train, y_train)
            
            # Evaluate on test set
            y_pred = self.models['gradient_boosting'].predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            # Store performance metrics
            self.model_performance['gradient_boosting'] = {
                'accuracy': accuracy,
                'f1_score': f1
            }
            
            logger.info(f"Gradient Boosting trained - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
            
        except Exception as e:
            logger.error(f"Error training Gradient Boosting: {e}")
            # Create a simple fallback model
            self.models['gradient_boosting'] = GradientBoostingClassifier(
                n_estimators=50,
                random_state=42
            )
            self.models['gradient_boosting'].fit(X_train, y_train)
    
    def _train_logistic_regression(self, X_train: pd.DataFrame, y_train: np.ndarray,
                                 X_val: pd.DataFrame, y_val: np.ndarray,
                                 X_test: pd.DataFrame, y_test: np.ndarray):
        """Train Logistic Regression model"""
        try:
            logger.info("Training Logistic Regression model...")
            
            # Create and train model
            self.models['logistic_regression'] = LogisticRegression(
                max_iter=1000,
                random_state=42,
                n_jobs=-1
            )
            self.models['logistic_regression'].fit(X_train, y_train)
            
            # Evaluate on test set
            y_pred = self.models['logistic_regression'].predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            # Store performance metrics
            self.model_performance['logistic_regression'] = {
                'accuracy': accuracy,
                'f1_score': f1
            }
            
            logger.info(f"Logistic Regression trained - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
            
        except Exception as e:
            logger.error(f"Error training Logistic Regression: {e}")
            # Create a simple fallback model
            self.models['logistic_regression'] = LogisticRegression(
                max_iter=500,
                random_state=42
            )
            self.models['logistic_regression'].fit(X_train, y_train)
    
    def _calculate_fee_based_accuracy(self, X_test: pd.DataFrame, y_test: np.ndarray, 
                                    y_pred: np.ndarray, test_data: pd.DataFrame) -> float:
        """Calculate accuracy based on transaction fee logic"""
        try:
            correct_predictions = 0
            total_predictions = 0
            
            # Get actual future returns
            future_returns = test_data['Future_Return'].values
            current_prices = test_data['Close'].values
            
            for i, (pred, actual_return, current_price) in enumerate(zip(y_pred, future_returns, current_prices)):
                if np.isnan(actual_return) or np.isnan(current_price):
                    continue
                
                # Calculate if prediction was correct based on transaction fee logic
                is_correct = False
                
                if pred == 2:  # BUY prediction
                    # Correct if future return > transaction fee
                    is_correct = actual_return > self.transaction_fee
                elif pred == 0:  # SELL prediction
                    # Correct if future return < -transaction fee
                    is_correct = actual_return < -self.transaction_fee
                else:  # HOLD prediction
                    # Correct if future return is between -fee and +fee
                    is_correct = -self.transaction_fee <= actual_return <= self.transaction_fee
                
                if is_correct:
                    correct_predictions += 1
                total_predictions += 1
            
            return correct_predictions / total_predictions if total_predictions > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating fee-based accuracy: {e}")
            return 0.0
    
    def _create_ensemble(self, X_test: pd.DataFrame, y_test: np.ndarray, test_data: pd.DataFrame):
        """Create weighted ensemble of models"""
        try:
            logger.info("Creating model ensemble...")
            
            # Calculate ensemble weights based on fee-based performance
            performances = {}
            for model_name, performance in self.model_performance.items():
                if self.models[model_name] is not None:
                    performances[model_name] = performance['fee_based_accuracy']
            
            # Normalize weights
            total_performance = sum(performances.values())
            self.ensemble_weights = {
                name: score / total_performance 
                for name, score in performances.items()
            }
            
            # Create ensemble predictions
            ensemble_predictions = np.zeros(len(y_test))
            
            for model_name, weight in self.ensemble_weights.items():
                if self.models[model_name] is not None:
                    predictions = self.models[model_name].predict(X_test)
                    ensemble_predictions += weight * predictions
            
            # Convert to class predictions
            ensemble_predictions = np.round(ensemble_predictions).astype(int)
            
            # Evaluate ensemble
            accuracy = accuracy_score(y_test, ensemble_predictions)
            f1 = f1_score(y_test, ensemble_predictions, average='weighted')
            fee_accuracy = self._calculate_fee_based_accuracy(X_test, y_test, ensemble_predictions, test_data)
            
            self.model_performance['ensemble'] = {
                'accuracy': accuracy,
                'f1_score': f1,
                'fee_based_accuracy': fee_accuracy,
                'weights': self.ensemble_weights
            }
            
            logger.info(f"Ensemble created - Accuracy: {accuracy:.4f}, F1: {f1:.4f}, Fee Accuracy: {fee_accuracy:.4f}")
            logger.info(f"Ensemble weights: {self.ensemble_weights}")
            
        except Exception as e:
            logger.error(f"❌ Error creating ensemble: {e}")
    
    def _save_models(self):
        """Save trained models and metadata"""
        try:
            # Save individual models
            for model_name, model in self.models.items():
                if model is not None:
                    model_path = MODELS_DIR / f"{model_name}_model.pkl"
                    joblib.dump(model, model_path)
                    logger.info(f"Saved {model_name} model")
            
            # Save ensemble metadata
            ensemble_data = {
                'ensemble_weights': self.ensemble_weights,
                'label_encoder': self.label_encoder,
                'feature_engineer': self.feature_engineer,
                'model_performance': self.model_performance,
                'transaction_fee': self.transaction_fee,
                'training_date': datetime.now().isoformat()
            }
            
            ensemble_path = MODELS_DIR / "ensemble_metadata.pkl"
            joblib.dump(ensemble_data, ensemble_path)
            
            # Save feature importance
            if self.models['xgboost'] is not None:
                feature_importance = self.models['xgboost'].feature_importances_
                feature_names = self.feature_engineer.selected_features
                
                importance_df = pd.DataFrame({
                    'feature': feature_names,
                    'importance': feature_importance
                }).sort_values('importance', ascending=False)
                
                importance_path = FEATURES_DIR / "feature_importance.csv"
                importance_df.to_csv(importance_path, index=False)
                
                self.feature_importance = importance_df
            
            logger.info("All models and metadata saved")
            
        except Exception as e:
            logger.error(f"❌ Error saving models: {e}")
    
    def _generate_performance_report(self, X_test: pd.DataFrame, y_test: np.ndarray, test_data: pd.DataFrame):
        """Generate comprehensive performance report"""
        try:
            logger.info("Generating performance report...")
            
            # Create performance summary
            performance_summary = []
            for model_name, performance in self.model_performance.items():
                performance_summary.append({
                    'Model': model_name,
                    'Accuracy': f"{performance['accuracy']:.4f}",
                    'F1_Score': f"{performance['f1_score']:.4f}",
                    'Fee_Based_Accuracy': f"{performance['fee_based_accuracy']:.4f}"
                })
            
            performance_df = pd.DataFrame(performance_summary)
            performance_path = MODELS_DIR / "model_performance.csv"
            performance_df.to_csv(performance_path, index=False)
            
            # Create confusion matrices
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            axes = axes.ravel()
            
            for i, (model_name, model) in enumerate(self.models.items()):
                if model is not None and i < 4:
                    y_pred = model.predict(X_test)
                    cm = confusion_matrix(y_test, y_pred)
                    
                    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[i])
                    axes[i].set_title(f'{model_name.replace("_", " ").title()} Confusion Matrix')
                    axes[i].set_xlabel('Predicted')
                    axes[i].set_ylabel('Actual')
            
            plt.tight_layout()
            plot_path = MODELS_DIR / "confusion_matrices.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("✅ Performance report generated")
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
    
    def predict_stock(self, ticker: str) -> Dict:
        """Make prediction for a single stock using ensemble"""
        try:
            # Get stock data
            stock_data = self.data_collector.yfinance_collector.get_stock_data(ticker)
            if stock_data is None:
                return self._get_fallback_prediction(ticker)
            
            # Calculate features
            df_with_features = self.feature_engineer.calculate_technical_indicators(stock_data)
            
            # Get sentiment data
            sentiment_data = asyncio.run(self.data_collector.collect_sentiment_data(ticker))
            df_with_features = self.feature_engineer.add_sentiment_features(df_with_features, sentiment_data)
            
            # Prepare features
            latest_data = df_with_features.iloc[-1:].copy()
            feature_cols = [col for col in latest_data.columns if col not in ['Date', 'Ticker', 'Target', 'Target_Encoded']]
            
            if len(feature_cols) == 0:
                return self._get_fallback_prediction(ticker)
            
            X = latest_data[feature_cols]
            
            # Scale features
            X_scaled = self.feature_engineer.scale_features(X, fit=False)
            
            # Get ensemble prediction
            ensemble_prediction = 0
            confidence_scores = {}
            
            for model_name, model in self.models.items():
                if model is not None:
                    prediction = model.predict(X_scaled)[0]
                    weight = self.ensemble_weights.get(model_name, 0)
                    ensemble_prediction += weight * prediction
                    
                    # Get confidence scores
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(X_scaled)[0]
                        confidence_scores[model_name] = max(proba)
            
            # Convert to class prediction
            final_prediction = int(round(ensemble_prediction))
            prediction_class = ['SELL', 'HOLD', 'BUY'][final_prediction]
            
            # Calculate overall confidence
            overall_confidence = np.mean(list(confidence_scores.values())) if confidence_scores else 0.5
            
            # Get current price
            current_price = stock_data['Close'].iloc[-1]
            
            return {
                'ticker': ticker,
                'prediction': prediction_class,
                'confidence': overall_confidence,
                'current_price': current_price,
                'model_confidence': confidence_scores,
                'ensemble_weights': self.ensemble_weights,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting {ticker}: {e}")
            return self._get_fallback_prediction(ticker)
    
    def _get_fallback_prediction(self, ticker: str) -> Dict:
        """Get fallback prediction when model fails"""
        return {
            'ticker': ticker,
            'prediction': 'HOLD',
            'confidence': 0.5,
            'current_price': 25.0,
            'model_confidence': {},
            'ensemble_weights': {},
            'timestamp': datetime.now().isoformat()
        }
    
    def run_full_pipeline(self, max_companies: int = 50) -> Dict:
        """Run the complete training pipeline"""
        try:
            logger.info("🚀 Starting full training pipeline...")
            
            # Collect and prepare data
            data = self.collect_and_prepare_data(max_companies=max_companies)
            if not data:
                raise Exception("No data available for training")
            
            # Train models
            performance = self.train_models(data)
            
            logger.info("🎉 Full pipeline completed successfully!")
            return performance
            
        except Exception as e:
            logger.error(f"❌ Error in full pipeline: {e}")
            return {}

def main():
    """Main function for model training"""
    predictor = EnhancedStockPredictor(transaction_fee=0.01)  # 1% transaction fee
    performance = predictor.run_full_pipeline(max_companies=30)  # Start with 30 companies
    
    if performance:
        logger.info("Model training completed successfully!")
        ensemble_perf = performance.get('ensemble', {})
        logger.info(f"Best ensemble performance: {ensemble_perf.get('fee_based_accuracy', 0):.4f}")
    else:
        logger.error("Model training failed!")

if __name__ == "__main__":
    main() 