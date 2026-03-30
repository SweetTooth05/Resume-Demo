"""
Enhanced Feature Engineering for Stock Prediction with Sentiment Analysis
"""

import pandas as pd
import numpy as np
import ta
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, f_classif
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from config import FEATURE_CONFIG, DATA_CONFIG, BASE_DIR

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Enhanced feature engineering with sentiment integration"""
    
    def __init__(self):
        self.scaler = RobustScaler()
        self.feature_selector = None
        self.selected_features = []
        self.feature_importance = {}
        
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        try:
            df = data.copy()
            
            # Ensure required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return df
            
            # Price-based features
            df = self._add_price_features(df)
            
            # Moving averages
            df = self._add_moving_averages(df)
            
            # Momentum indicators
            df = self._add_momentum_indicators(df)
            
            # Volatility indicators
            df = self._add_volatility_indicators(df)
            
            # Volume indicators
            df = self._add_volume_indicators(df)
            
            # Trend indicators
            df = self._add_trend_indicators(df)
            
            # Oscillator indicators
            df = self._add_oscillator_indicators(df)
            
            # Time-based features
            df = self._add_time_features(df)
            
            # Lagged features
            df = self._add_lagged_features(df)
            
            # Interaction features
            df = self._add_interaction_features(df)
            
            logger.info(f"Calculated {len(df.columns)} features")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return data
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        try:
            # Basic price changes
            df['Returns'] = df['Close'].pct_change()
            df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
            df['Price_Change'] = df['Close'] - df['Close'].shift(1)
            df['Price_Change_Pct'] = df['Price_Change'] / df['Close'].shift(1) * 100
            
            # Price ratios
            df['High_Low_Ratio'] = df['High'] / df['Low']
            df['Close_Open_Ratio'] = df['Close'] / df['Open']
            df['Body_Size'] = abs(df['Close'] - df['Open']) / df['Open']
            
            # Price levels
            df['Price_Position'] = (df['Close'] - df['Low']) / (df['High'] - df['Low'])
            
            # Gap analysis
            df['Gap'] = (df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)
            
            return df
        except Exception as e:
            logger.error(f"Error adding price features: {e}")
            return df
    
    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add moving average features"""
        try:
            periods = [5, 10, 20, 50, 100, 200]
            
            for period in periods:
                # Simple moving averages
                df[f'MA_{period}'] = df['Close'].rolling(window=period).mean()
                df[f'EMA_{period}'] = df['Close'].ewm(span=period).mean()
                
                # Price vs MA ratios
                df[f'Price_MA_{period}_Ratio'] = df['Close'] / df[f'MA_{period}']
                df[f'Price_EMA_{period}_Ratio'] = df['Close'] / df[f'EMA_{period}']
                
                # MA crossovers
                if period > 5:
                    df[f'MA_5_{period}_Crossover'] = (df['MA_5'] > df[f'MA_{period}']).astype(int)
                    df[f'EMA_5_{period}_Crossover'] = (df['EMA_5'] > df[f'EMA_{period}']).astype(int)
            
            return df
        except Exception as e:
            logger.error(f"Error adding moving averages: {e}")
            return df
    
    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        try:
            periods = [5, 10, 20, 50]
            
            for period in periods:
                # Momentum
                df[f'Momentum_{period}'] = df['Close'] / df['Close'].shift(period) - 1
                
                # Rate of Change
                df[f'ROC_{period}'] = ((df['Close'] - df['Close'].shift(period)) / df['Close'].shift(period)) * 100
                
                # Relative Strength Index
                if period >= 14:
                    df[f'RSI_{period}'] = ta.momentum.RSIIndicator(df['Close'], window=period).rsi()
            
            return df
        except Exception as e:
            logger.error(f"Error adding momentum indicators: {e}")
            return df
    
    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators"""
        try:
            periods = [5, 10, 20, 50]
            
            for period in periods:
                # Rolling volatility
                returns = df['Returns'].rolling(window=period)
                df[f'Volatility_{period}'] = returns.std()
                df[f'Volatility_Annualized_{period}'] = returns.std() * np.sqrt(252)
                
                # True Range and ATR
                if period >= 14:
                    df[f'ATR_{period}'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=period).average_true_range()
            
            return df
        except Exception as e:
            logger.error(f"Error adding volatility indicators: {e}")
            return df
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based indicators"""
        try:
            periods = [5, 20]
            
            for period in periods:
                # Volume moving averages
                df[f'Volume_MA_{period}'] = df['Volume'].rolling(window=period).mean()
                df[f'Volume_Ratio_{period}'] = df['Volume'] / df[f'Volume_MA_{period}']
                
                # On-Balance Volume
                if period == 20:
                    df['OBV'] = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
                    df['OBV_MA'] = df['OBV'].rolling(window=period).mean()
                    df['OBV_Ratio'] = df['OBV'] / df['OBV_MA']
            
            # Volume Price Trend
            df['VPT'] = (df['Volume'] * ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1))).cumsum()
            
            return df
        except Exception as e:
            logger.error(f"Error adding volume indicators: {e}")
            return df
    
    def _add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators"""
        try:
            # MACD
            macd = ta.trend.MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Histogram'] = macd.macd_diff()
            
            # Parabolic SAR
            df['PSAR'] = ta.trend.PSARIndicator(df['High'], df['Low'], df['Close']).psar()
            
            # ADX (Average Directional Index)
            df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()
            
            # Bollinger Bands
            for period in [10, 20, 50]:
                bb = ta.volatility.BollingerBands(df['Close'], window=period, window_dev=2)
                df[f'BB_Upper_{period}'] = bb.bollinger_hband()
                df[f'BB_Middle_{period}'] = bb.bollinger_mavg()
                df[f'BB_Lower_{period}'] = bb.bollinger_lband()
                df[f'BB_Position_{period}'] = (df['Close'] - df[f'BB_Lower_{period}']) / (df[f'BB_Upper_{period}'] - df[f'BB_Lower_{period}'])
            
            return df
        except Exception as e:
            logger.error(f"Error adding trend indicators: {e}")
            return df
    
    def _add_oscillator_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add oscillator indicators"""
        try:
            # Stochastic
            for period in [14, 21]:
                stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=period, smooth_window=3)
                df[f'Stoch_K_{period}'] = stoch.stoch()
                df[f'Stoch_D_{period}'] = stoch.stoch_signal()
            
            # Williams %R
            for period in [14, 21]:
                df[f'Williams_R_{period}'] = ta.momentum.WilliamsRIndicator(df['High'], df['Low'], df['Close'], lbp=period).williams_r()
            
            # CCI (Commodity Channel Index)
            for period in [14, 21]:
                df[f'CCI_{period}'] = ta.trend.CCIIndicator(df['High'], df['Low'], df['Close'], window=period).cci()
            
            # MFI (Money Flow Index)
            for period in [14, 21]:
                df[f'MFI_{period}'] = ta.volume.MFIIndicator(df['High'], df['Low'], df['Close'], df['Volume'], window=period).money_flow_index()
            
            return df
        except Exception as e:
            logger.error(f"Error adding oscillator indicators: {e}")
            return df
    
    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features with proper error handling"""
        try:
            if 'Date' in df.columns:
                # Convert to datetime, handling timezone-aware timestamps
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                
                # Remove timezone info if present
                if df['Date'].dt.tz is not None:
                    df['Date'] = df['Date'].dt.tz_localize(None)
                
                # Remove rows with invalid dates
                df = df.dropna(subset=['Date'])
                
                if len(df) > 0:
                    df['DayOfWeek'] = df['Date'].dt.dayofweek
                    df['Month'] = df['Date'].dt.month
                    df['Quarter'] = df['Date'].dt.quarter
                    df['Year'] = df['Date'].dt.year
                    df['DayOfYear'] = df['Date'].dt.dayofyear
                    
                    # Cyclical encoding
                    df['DayOfWeek_Sin'] = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
                    df['DayOfWeek_Cos'] = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
                    df['Month_Sin'] = np.sin(2 * np.pi * df['Month'] / 12)
                    df['Month_Cos'] = np.cos(2 * np.pi * df['Month'] / 12)
            
            return df
        except Exception as e:
            logger.error(f"Error adding time features: {e}")
            return df
    
    def _add_lagged_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add lagged features"""
        try:
            # Price lags
            for lag in [1, 2, 3, 5, 10]:
                df[f'Close_Lag_{lag}'] = df['Close'].shift(lag)
                df[f'Returns_Lag_{lag}'] = df['Returns'].shift(lag)
                df[f'Volume_Lag_{lag}'] = df['Volume'].shift(lag)
            
            return df
        except Exception as e:
            logger.error(f"Error adding lagged features: {e}")
            return df
    
    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add interaction features"""
        try:
            # Volume-Price interactions
            df['Volume_Price_Trend'] = df['Volume'] * df['Returns']
            df['Volume_Price_MA_Ratio'] = df['Volume_Ratio_20'] * df['Price_MA_20_Ratio']
            
            # Momentum-Volatility interactions
            df['Momentum_Volatility'] = df['Momentum_20'] * df['Volatility_20']
            
            # RSI-MACD interactions
            if 'RSI_14' in df.columns and 'MACD' in df.columns:
                df['RSI_MACD_Interaction'] = df['RSI_14'] * df['MACD']
            
            return df
        except Exception as e:
            logger.error(f"Error adding interaction features: {e}")
            return df
    
    def add_sentiment_features(self, df: pd.DataFrame, sentiment_data: Dict) -> pd.DataFrame:
        """Add sentiment features to the dataset"""
        try:
            if not sentiment_data:
                logger.warning("No sentiment data provided")
                return df
            
            # Add sentiment columns
            sentiment_features = [
                'news_sentiment', 'reddit_sentiment', 'social_sentiment', 'overall_sentiment'
            ]
            
            for feature in sentiment_features:
                if feature in sentiment_data:
                    df[f'Sentiment_{feature}'] = sentiment_data[feature]
                else:
                    df[f'Sentiment_{feature}'] = 0.0
            
            # Sentiment momentum
            if 'overall_sentiment' in sentiment_data:
                df['Sentiment_Momentum'] = sentiment_data['overall_sentiment'] * df['Returns']
                df['Sentiment_Volatility'] = sentiment_data['overall_sentiment'] * df['Volatility_20']
            
            logger.info("Added sentiment features")
            return df
            
        except Exception as e:
            logger.error(f"Error adding sentiment features: {e}")
            return df
    
    def prepare_features(self, df: pd.DataFrame, target_col: str = 'Target') -> Tuple[pd.DataFrame, List[str]]:
        """Prepare features for training with proper data validation"""
        try:
            logger.info("Preparing features for training...")
            
            # Make a copy to avoid modifying original data
            df_processed = df.copy()
            
            # Remove timestamp columns that shouldn't be used as features
            timestamp_cols = ['Date']
            for col in timestamp_cols:
                if col in df_processed.columns:
                    logger.warning(f"Removing timestamp columns: {timestamp_cols}")
                    df_processed = df_processed.drop(columns=[col])
            
            # Handle categorical columns
            categorical_cols = df_processed.select_dtypes(include=['object', 'category']).columns.tolist()
            if categorical_cols:
                logger.info(f"Encoding categorical columns: {categorical_cols}")
                for col in categorical_cols:
                    if col != target_col:
                        # Use label encoding for categorical variables
                        df_processed[col] = pd.Categorical(df_processed[col]).codes
            
            # Ensure target column exists
            if target_col not in df_processed.columns:
                logger.error(f"Target column '{target_col}' not found in data")
                return df_processed, []
            
            # Handle NaN values in features (but not target)
            feature_cols = [col for col in df_processed.columns if col != target_col]
            
            for col in feature_cols:
                if df_processed[col].isnull().any():
                    # For price/volume columns, use forward fill then backward fill
                    if any(keyword in col.lower() for keyword in ['open', 'high', 'low', 'close', 'volume']):
                        df_processed[col] = df_processed[col].fillna(method='ffill').fillna(method='bfill')
                    else:
                        # For technical indicators, use median
                        median_val = df_processed[col].median()
                        df_processed[col] = df_processed[col].fillna(median_val)
            
            # Remove any remaining rows with NaN values
            initial_rows = len(df_processed)
            df_processed = df_processed.dropna()
            final_rows = len(df_processed)
            
            if initial_rows != final_rows:
                logger.warning(f"Removed {initial_rows - final_rows} rows with NaN values")
            
            # Remove constant features
            constant_features = []
            for col in feature_cols:
                if col in df_processed.columns and df_processed[col].nunique() <= 1:
                    constant_features.append(col)
            
            if constant_features:
                logger.warning(f"Removing constant features: {constant_features}")
                df_processed = df_processed.drop(columns=constant_features)
            
            # Feature selection
            if len(feature_cols) > 100:  # Only select if we have many features
                df_processed, selected_features = self._select_features(df_processed, target_col, k=100)
                logger.info(f"Selected {len(selected_features)} features out of {len(feature_cols)}")
            else:
                selected_features = [col for col in df_processed.columns if col != target_col]
            
            # Final validation
            if len(df_processed) == 0:
                logger.error("No data remaining after processing!")
                return df_processed, []
            
            if target_col not in df_processed.columns:
                logger.error("Target column lost during processing!")
                return df_processed, []
            
            logger.info(f"Prepared {len(selected_features)} features")
            return df_processed, selected_features
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return df, []
    
    def _remove_correlated_features(self, df: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame:
        """Remove highly correlated features"""
        try:
            corr_matrix = df.corr().abs()
            upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            
            to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > threshold)]
            
            if to_drop:
                logger.info(f"Removing {len(to_drop)} highly correlated features")
                df = df.drop(columns=to_drop)
            
            return df
        except Exception as e:
            logger.error(f"Error removing correlated features: {e}")
            return df
    
    def _select_features(self, df: pd.DataFrame, target_col: str, k: int = 100) -> Tuple[pd.DataFrame, List[str]]:
        """Select top k features using statistical tests"""
        try:
            X = df.drop(columns=[target_col])
            y = df[target_col]
            
            # Handle non-numeric target
            if y.dtype == 'object':
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                y = le.fit_transform(y)
            
            # Feature selection
            self.feature_selector = SelectKBest(score_func=f_classif, k=min(k, len(X.columns)))
            X_selected = self.feature_selector.fit_transform(X, y)
            
            # Get selected feature names
            selected_features = X.columns[self.feature_selector.get_support()].tolist()
            
            # Create new dataframe with selected features
            df_selected = df[selected_features + [target_col]]
            
            logger.info(f"Selected {len(selected_features)} features out of {len(X.columns)}")
            return df_selected, selected_features
            
        except Exception as e:
            logger.error(f"Error in feature selection: {e}")
            return df, list(df.columns)
    
    def scale_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Scale features using robust scaling"""
        try:
            # Separate numeric and non-numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
            
            if len(numeric_cols) == 0:
                return df
            
            # Scale numeric features
            if fit:
                df_scaled = df.copy()
                df_scaled[numeric_cols] = self.scaler.fit_transform(df[numeric_cols])
            else:
                df_scaled = df.copy()
                df_scaled[numeric_cols] = self.scaler.transform(df[numeric_cols])
            
            logger.info(f"Scaled {len(numeric_cols)} features")
            return df_scaled
            
        except Exception as e:
            logger.error(f"Error scaling features: {e}")
            return df
    
    def get_feature_importance(self) -> Dict:
        """Get feature importance scores"""
        try:
            if self.feature_selector is not None:
                importance_scores = self.feature_selector.scores_
                feature_names = self.selected_features
                
                self.feature_importance = dict(zip(feature_names, importance_scores))
                
                # Sort by importance
                self.feature_importance = dict(
                    sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
                )
            
            return self.feature_importance
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}

def main():
    """Test feature engineering"""
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    sample_data = pd.DataFrame({
        'Date': dates,
        'Open': np.random.randn(252).cumsum() + 100,
        'High': np.random.randn(252).cumsum() + 102,
        'Low': np.random.randn(252).cumsum() + 98,
        'Close': np.random.randn(252).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 252)
    })
    
    # Initialize feature engineer
    fe = FeatureEngineer()
    
    # Calculate features
    df_with_features = fe.calculate_technical_indicators(sample_data)
    
    print(f"Original features: {len(sample_data.columns)}")
    print(f"Features after engineering: {len(df_with_features.columns)}")
    print(f"Feature names: {list(df_with_features.columns)}")

if __name__ == "__main__":
    main() 