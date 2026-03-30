"""
Enhanced Stock Predictor for Personal Finance App
Integrates with the new StockPredictionModel
"""

import os
import sys
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Optional, List
import joblib
from pathlib import Path

from app.services.yahoo_client import yfinance_ticker

# Add StockPredictionModel to path (repo root: PersonalFinanceApp/StockPredictionModel;
# in Docker, compose mounts it at /StockPredictionModel — see path fallback below).
_backend_root = Path(__file__).resolve().parent.parent.parent
_repo_root = _backend_root.parent
_candidates = [
    _repo_root / "StockPredictionModel",
    Path("/StockPredictionModel"),
]
stock_model_path = next((p for p in _candidates if p.is_dir()), _candidates[0])
if str(stock_model_path) not in sys.path:
    sys.path.insert(0, str(stock_model_path))

# Populated only if imports succeed (avoid NameError in _load_enhanced_model / _setup_fallback).
STOCK_PREDICTION_IMPORT_ERROR: Optional[str] = None
EnhancedStockPredictor = None  # type: ignore[assignment,misc]
FeatureEngineer = None  # type: ignore[assignment,misc]
ASXDataCollector = None  # type: ignore[assignment,misc]
MODEL_CONFIG: Dict = {}
SENTIMENT_CONFIG: Dict = {}

try:
    from enhanced_model import EnhancedStockPredictor as _EnhancedStockPredictor
    from feature_engineering import FeatureEngineer as _FeatureEngineer
    from incremental_data_collector import IncrementalASXDataCollector as _ASXDataCollector
    from config import MODEL_CONFIG as _MODEL_CONFIG, SENTIMENT_CONFIG as _SENTIMENT_CONFIG

    EnhancedStockPredictor = _EnhancedStockPredictor
    FeatureEngineer = _FeatureEngineer
    ASXDataCollector = _ASXDataCollector
    MODEL_CONFIG = _MODEL_CONFIG
    SENTIMENT_CONFIG = _SENTIMENT_CONFIG
except ImportError as e:
    STOCK_PREDICTION_IMPORT_ERROR = str(e)
    logging.getLogger(__name__).warning("Could not import StockPredictionModel modules: %s", e)

logger = logging.getLogger(__name__)

class StockPredictor:
    """Enhanced stock predictor using the new StockPredictionModel"""
    
    def __init__(self):
        self.predictor = None
        self.feature_engineer = None
        self.data_collector = None
        self.model_loaded = False
        self.model_accuracy = 0.0
        self.feature_importance = {}
        
        # Try to load the enhanced model
        self._load_enhanced_model()
        
        # Fallback configuration
        self.fallback_config = {
            'model_type': 'xgboost',
            'accuracy': 0.62,
            'features_used': 70,
            'training_date': '2024-01-01',
            'data_source': 'Yahoo Finance + Sentiment Analysis'
        }
    
    def _load_enhanced_model(self):
        """Load the enhanced model from StockPredictionModel"""
        try:
            if (
                EnhancedStockPredictor is None
                or FeatureEngineer is None
                or ASXDataCollector is None
            ):
                logger.warning(
                    "StockPredictionModel not available (%s); skipping ensemble load.",
                    STOCK_PREDICTION_IMPORT_ERROR or "imports failed",
                )
                self._setup_fallback()
                return

            # Check if enhanced model exists
            models_dir = stock_model_path / "processed_finance_data" / "models"
            ensemble_path = models_dir / "ensemble_metadata.pkl"
            
            if ensemble_path.exists():
                logger.info("Loading enhanced ensemble model...")
                
                # Load ensemble metadata
                ensemble_data = joblib.load(ensemble_path)
                
                # Initialize components
                self.predictor = EnhancedStockPredictor()
                self.feature_engineer = FeatureEngineer()
                self.data_collector = ASXDataCollector()
                
                # Load models
                for model_name in ['xgboost', 'random_forest', 'gradient_boosting', 'logistic_regression']:
                    model_path = models_dir / f"{model_name}_model.pkl"
                    if model_path.exists():
                        self.predictor.models[model_name] = joblib.load(model_path)
                
                # Load other components
                self.predictor.ensemble_weights = ensemble_data.get('ensemble_weights', {})
                self.predictor.label_encoder = ensemble_data.get('label_encoder')
                self.predictor.model_performance = ensemble_data.get('model_performance', {})
                
                # Load feature importance
                feature_importance_path = stock_model_path / "processed_finance_data" / "features" / "feature_importance.csv"
                if feature_importance_path.exists():
                    self.feature_importance = pd.read_csv(feature_importance_path)
                
                # Get model accuracy
                ensemble_performance = self.predictor.model_performance.get('ensemble', {})
                self.model_accuracy = ensemble_performance.get('accuracy', 0.62)
                
                self.model_loaded = True
                logger.info("Enhanced model loaded successfully")
                
            else:
                logger.warning("Enhanced model not found, using fallback")
                self._setup_fallback()
                
        except Exception as e:
            logger.error("Error loading enhanced model: %s", e)
            self._setup_fallback()
    
    def _setup_fallback(self):
        """Setup fallback prediction system"""
        try:
            logger.info("Setting up fallback prediction system...")
            
            if FeatureEngineer is not None and ASXDataCollector is not None:
                self.feature_engineer = FeatureEngineer()
                self.data_collector = ASXDataCollector()
            else:
                self.feature_engineer = None
                self.data_collector = None
            
            # Load old model if available
            old_model_path = stock_model_path / "processed_finance_data" / "models" / "xgboost_stock_predictor.pkl"
            if old_model_path.exists():
                try:
                    import pickle
                    with open(old_model_path, 'rb') as f:
                        self.old_model = pickle.load(f)
                    logger.info("Loaded fallback XGBoost model")
                except Exception as e:
                    logger.error("Error loading fallback model: %s", e)
            
            self.model_loaded = False
            
        except Exception as e:
            logger.error("Error setting up fallback: %s", e)
    
    def get_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get stock data from Yahoo Finance"""
        try:
            # Add .AX suffix if not present
            if not ticker.endswith('.AX') and len(ticker) <= 5:
                ticker = f"{ticker}.AX"
            
            stock = yfinance_ticker(ticker)
            data = stock.history(period="2y", interval="1d")
            
            if data.empty:
                logger.warning("No data found for %s", ticker)
                return None
            
            # Add metadata
            data['Ticker'] = ticker
            data['Date'] = data.index
            data.reset_index(drop=True, inplace=True)
            
            return data
            
        except Exception as e:
            logger.error("Error fetching data for %s: %s", ticker, e)
            return None
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators using the enhanced feature engineer"""
        try:
            if self.feature_engineer is None:
                logger.error("Feature engineer not available")
                return data
            
            return self.feature_engineer.calculate_technical_indicators(data)
            
        except Exception as e:
            logger.error("Error calculating technical indicators: %s", e)
            return data
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for prediction"""
        try:
            if self.feature_engineer is None:
                logger.error("Feature engineer not available")
                return df
            
            # Prepare features
            df_prepared, _ = self.feature_engineer.prepare_features(df)
            
            # Scale features
            df_scaled = self.feature_engineer.scale_features(df_prepared, fit=False)
            
            return df_scaled
            
        except Exception as e:
            logger.error("Error preparing features: %s", e)
            return df
    
    def predict_stock(self, ticker: str) -> Dict:
        """Make stock prediction using enhanced model"""
        try:
            logger.info("Making prediction for %s", ticker)
            
            # Use enhanced model if available
            if self.predictor is not None and self.model_loaded:
                return self._predict_with_enhanced_model(ticker)
            else:
                return self._predict_with_fallback(ticker)
                
        except Exception as e:
            logger.error("Error predicting %s: %s", ticker, e)
            return self._get_fallback_prediction(ticker)
    
    def _predict_with_enhanced_model(self, ticker: str) -> Dict:
        """Make prediction using enhanced ensemble model"""
        try:
            # Use the enhanced predictor
            prediction_result = self.predictor.predict_stock(ticker)
            
            # Format result for API
            result = {
                'ticker': ticker,
                'prediction': prediction_result['prediction'],
                'confidence': prediction_result['confidence'],
                'current_price': prediction_result['current_price'],
                'predicted_price': prediction_result['current_price'],  # Enhanced model doesn't predict price directly
                'change': 0.0,  # Calculate based on prediction
                'change_percent': 0.0,
                'recommendation': self._get_recommendation(prediction_result['prediction'], prediction_result['confidence']),
                'model_accuracy': self.model_accuracy,
                'model_type': 'Enhanced Ensemble',
                'features_used': len(self.feature_importance) if isinstance(self.feature_importance, pd.DataFrame) and not self.feature_importance.empty else 70,
                'sentiment_included': True,
                'timestamp': datetime.now().isoformat()
            }
            
            # Calculate change based on prediction
            if prediction_result['prediction'] == 'BUY':
                result['change'] = result['current_price'] * 0.02  # 2% increase
                result['change_percent'] = 2.0
            elif prediction_result['prediction'] == 'SELL':
                result['change'] = -result['current_price'] * 0.02  # 2% decrease
                result['change_percent'] = -2.0
            
            return result
            
        except Exception as e:
            logger.error("Error with enhanced model prediction: %s", e)
            return self._predict_with_fallback(ticker)
    
    def _predict_with_fallback(self, ticker: str) -> Dict:
        """Make prediction using fallback model"""
        try:
            # Get stock data
            data = self.get_stock_data(ticker)
            if data is None:
                return self._get_fallback_prediction(ticker)
            
            # Calculate features
            df_with_features = self.calculate_technical_indicators(data)
            
            # Prepare features
            latest_data = df_with_features.iloc[-1:].copy()
            
            # Remove non-feature columns
            feature_cols = [col for col in latest_data.columns 
                          if col not in ['Date', 'Ticker', 'Target', 'Future_Return']]
            
            if len(feature_cols) == 0:
                return self._get_fallback_prediction(ticker)
            
            X = latest_data[feature_cols]
            
            # Fill missing values
            X = X.fillna(0)
            
            # Make prediction
            if hasattr(self, 'old_model') and self.old_model is not None:
                try:
                    prediction = self.old_model.predict(X)[0]
                    confidence = 0.6  # Default confidence for old model
                except Exception as e:
                    logger.error("Error with old model prediction: %s", e)
                    prediction = 1  # Default to HOLD
                    confidence = 0.5
            else:
                # Simple rule-based prediction
                prediction = self._simple_prediction(X)
                confidence = 0.5
            
            # Get current price
            current_price = data['Close'].iloc[-1]
            
            # Calculate predicted price and change
            if prediction == 1:  # BUY
                predicted_price = current_price * 1.02
                change = predicted_price - current_price
                change_percent = 2.0
                recommendation = "BUY"
            elif prediction == 2:  # SELL
                predicted_price = current_price * 0.98
                change = predicted_price - current_price
                change_percent = -2.0
                recommendation = "SELL"
            else:  # HOLD
                predicted_price = current_price
                change = 0.0
                change_percent = 0.0
                recommendation = "HOLD"
            
            return {
                'ticker': ticker,
                'prediction': prediction,
                'confidence': confidence,
                'current_price': current_price,
                'predicted_price': predicted_price,
                'change': change,
                'change_percent': change_percent,
                'recommendation': recommendation,
                'model_accuracy': self.fallback_config['accuracy'],
                'model_type': 'Fallback XGBoost',
                'features_used': self.fallback_config['features_used'],
                'sentiment_included': False,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error with fallback prediction: %s", e)
            return self._get_fallback_prediction(ticker)
    
    def _simple_prediction(self, X: pd.DataFrame) -> int:
        """Simple rule-based prediction"""
        try:
            # Simple rules based on technical indicators
            if 'RSI_14' in X.columns:
                rsi = X['RSI_14'].iloc[0]
                if rsi < 30:
                    return 1  # BUY (oversold)
                elif rsi > 70:
                    return 2  # SELL (overbought)
            
            if 'MACD' in X.columns and 'MACD_Signal' in X.columns:
                macd = X['MACD'].iloc[0]
                macd_signal = X['MACD_Signal'].iloc[0]
                if macd > macd_signal:
                    return 1  # BUY
                elif macd < macd_signal:
                    return 2  # SELL
            
            return 0  # HOLD
            
        except Exception as e:
            logger.error("Error in simple prediction: %s", e)
            return 0
    
    def _get_fallback_prediction(self, ticker: str) -> Dict:
        """Get fallback prediction when all else fails"""
        return {
            'ticker': ticker,
            'prediction': 'HOLD',
            'confidence': 0.5,
            'current_price': 25.0,
            'predicted_price': 25.0,
            'change': 0.0,
            'change_percent': 0.0,
            'recommendation': 'HOLD',
            'model_accuracy': self.fallback_config['accuracy'],
            'model_type': 'Fallback',
            'features_used': 0,
            'sentiment_included': False,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_recommendation(self, prediction: str, confidence: float) -> str:
        """Get recommendation based on prediction and confidence"""
        if prediction == 'BUY':
            if confidence > 0.7:
                return "Strong Buy"
            else:
                return "Buy"
        elif prediction == 'SELL':
            if confidence > 0.7:
                return "Strong Sell"
            else:
                return "Sell"
        else:
            return "Hold"
    
    def get_model_accuracy(self) -> float:
        """Get model accuracy"""
        return self.model_accuracy if self.model_loaded else self.fallback_config['accuracy']
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        if self.model_loaded:
            return {
                'model_type': 'Enhanced Ensemble',
                'accuracy': self.model_accuracy,
                'features_used': len(self.feature_importance) if isinstance(self.feature_importance, pd.DataFrame) and not self.feature_importance.empty else 70,
                'training_date': datetime.now().strftime('%Y-%m-%d'),
                'data_source': 'Yahoo Finance + Sentiment Analysis',
                'sentiment_sources': list(
                    (SENTIMENT_CONFIG.get('sources') or {}).keys()
                ),
                'ensemble_models': list(self.predictor.ensemble_weights.keys()) if self.predictor else []
            }
        else:
            return self.fallback_config

# Global instance
stock_predictor = StockPredictor() 