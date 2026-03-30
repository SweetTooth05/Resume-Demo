#!/usr/bin/env python3
"""
Test script for XGBoost Stock Prediction Model
This script demonstrates the functionality with sample data and tests model accuracy
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import warnings
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns

# Suppress warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_sample_stock_data(n_days=500):
    """
    Create sample stock data for testing
    
    Args:
        n_days (int): Number of days of data to generate
        
    Returns:
        pd.DataFrame: Sample stock data
    """
    np.random.seed(42)
    
    # Generate price data first
    initial_price = 100.0
    returns = np.random.normal(0.001, 0.02, n_days)  # Daily returns
    prices = [initial_price]
    
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    # Generate dates to match the number of prices
    end_date = datetime.now()
    start_date = end_date - timedelta(days=len(prices)-1)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Create OHLCV data
    data = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(prices)),
        'Ticker': ['SAMPLE'] * len(prices),
        'Sector': ['Technology'] * len(prices)
    })
    
    # Ensure High >= Low
    data['High'] = data[['Open', 'Close', 'High']].max(axis=1)
    data['Low'] = data[['Open', 'Close', 'Low']].min(axis=1)
    
    return data

def calculate_technical_indicators(data):
    """
    Calculate technical indicators for the sample data
    
    Args:
        data (pd.DataFrame): Stock data
        
    Returns:
        pd.DataFrame: Data with technical indicators
    """
    df = data.copy()
    
    # Basic price features
    df['Returns'] = df['Close'].pct_change()
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['Price_Change'] = df['Close'] - df['Open']
    df['Price_Change_Pct'] = (df['Close'] - df['Open']) / df['Open']
    
    # Moving averages
    for window in [5, 10, 20, 50]:
        df[f'MA_{window}'] = df['Close'].rolling(window=window).mean()
        df[f'MA_Ratio_{window}'] = df['Close'] / df[f'MA_{window}']
    
    # Volatility
    for window in [5, 10, 20]:
        df[f'Volatility_{window}'] = df['Returns'].rolling(window=window).std()
    
    # RSI
    for period in [7, 14]:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df[f'RSI_{period}'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    
    # Volume indicators
    df['Volume_MA_5'] = df['Volume'].rolling(window=5).mean()
    df['Volume_Ratio_5'] = df['Volume'] / df['Volume_MA_5']
    
    # Momentum
    for period in [5, 10, 20]:
        df[f'Momentum_{period}'] = df['Close'] / df['Close'].shift(period) - 1
    
    return df

def prepare_features_for_training(data):
    """
    Prepare features for XGBoost training
    
    Args:
        data (pd.DataFrame): Data with technical indicators
        
    Returns:
        tuple: (X_features, y_target, feature_names)
    """
    # Define feature columns (exclude metadata and target)
    exclude_columns = ['Date', 'Ticker', 'Sector', 'Target', 'Future_Return']
    feature_columns = [col for col in data.columns if col not in exclude_columns]
    
    # Prepare features
    X = data[feature_columns].fillna(0)  # Fill NaN with 0 for simplicity
    y = data['Target']
    
    # Encode target
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    return X, y_encoded, feature_columns, label_encoder

def train_and_evaluate_model(X, y, feature_names, test_size=0.2, random_state=42):
    """
    Train XGBoost model and evaluate its performance
    
    Args:
        X (pd.DataFrame): Feature matrix
        y (np.array): Target labels
        feature_names (list): List of feature names
        test_size (float): Proportion of data for testing
        random_state (int): Random seed
        
    Returns:
        dict: Model performance metrics
    """
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # Initialize and train model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=random_state,
        eval_metric='mlogloss'
    )
    
    logging.info("Training XGBoost model...")
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    # Get class names
    class_names = ['HOLD', 'BUY', 'SELL']
    
    # Create confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    # Feature importance
    feature_importance = model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)
    
    # Store results
    results = {
        'accuracy': accuracy,
        'f1_score': f1,
        'confusion_matrix': cm,
        'classification_report': classification_report(y_test, y_pred, target_names=class_names),
        'feature_importance': feature_importance_df,
        'model': model,
        'X_test': X_test,
        'y_test': y_test,
        'y_pred': y_pred,
        'y_pred_proba': y_pred_proba,
        'class_names': class_names
    }
    
    return results

def create_target_variable(data, lookforward_days=30, threshold_pct=0.05):
    """
    Create target variable for buy/sell/hold prediction
    
    Args:
        data (pd.DataFrame): Stock data
        lookforward_days (int): Number of days to look forward
        threshold_pct (float): Percentage threshold for buy/sell signals
        
    Returns:
        pd.DataFrame: Data with target variable
    """
    df = data.copy()
    
    # Calculate future returns
    df['Future_Return'] = df['Close'].shift(-lookforward_days) / df['Close'] - 1
    
    # Create target variable
    def create_signal(future_return):
        if pd.isna(future_return):
            return np.nan
        elif future_return > threshold_pct:
            return 'BUY'
        elif future_return < -threshold_pct:
            return 'SELL'
        else:
            return 'HOLD'
    
    df['Target'] = df['Future_Return'].apply(create_signal)
    
    # Remove rows with NaN targets
    df = df.dropna(subset=['Target'])
    
    return df

def visualize_results(results):
    """
    Create visualizations for model performance
    
    Args:
        results (dict): Model evaluation results
    """
    # Set up the plotting style
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Confusion Matrix
    cm = results['confusion_matrix']
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
               xticklabels=results['class_names'], 
               yticklabels=results['class_names'], ax=axes[0,0])
    axes[0,0].set_title('Confusion Matrix')
    axes[0,0].set_xlabel('Predicted')
    axes[0,0].set_ylabel('Actual')
    
    # 2. Feature Importance (Top 10)
    top_features = results['feature_importance'].head(10)
    sns.barplot(data=top_features, x='importance', y='feature', ax=axes[0,1])
    axes[0,1].set_title('Top 10 Feature Importance')
    axes[0,1].set_xlabel('Importance')
    
    # 3. Class Distribution (Actual)
    actual_counts = pd.Series(results['y_test']).value_counts()
    axes[1,0].pie(actual_counts.values, labels=results['class_names'], autopct='%1.1f%%')
    axes[1,0].set_title('Actual Class Distribution (Test Set)')
    
    # 4. Prediction Distribution
    pred_counts = pd.Series(results['y_pred']).value_counts()
    axes[1,1].pie(pred_counts.values, labels=results['class_names'], autopct='%1.1f%%')
    axes[1,1].set_title('Prediction Distribution')
    
    plt.tight_layout()
    plt.savefig('model_accuracy_test_results.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info("Visualization saved as 'model_accuracy_test_results.png'")

def demonstrate_model_functionality():
    """
    Demonstrate the XGBoost model functionality with sample data
    """
    logging.info("=" * 60)
    logging.info("XGBOOST STOCK PREDICTION MODEL DEMONSTRATION")
    logging.info("=" * 60)
    
    # Create sample data
    logging.info("Creating sample stock data...")
    sample_data = create_sample_stock_data(n_days=500)
    logging.info(f"Created sample data with {len(sample_data)} records")
    
    # Calculate technical indicators
    logging.info("Calculating technical indicators...")
    data_with_indicators = calculate_technical_indicators(sample_data)
    logging.info(f"Added technical indicators. Shape: {data_with_indicators.shape}")
    
    # Create target variable
    logging.info("Creating target variable...")
    final_data = create_target_variable(data_with_indicators)
    logging.info(f"Final data shape: {final_data.shape}")
    
    # Show target distribution
    target_dist = final_data['Target'].value_counts()
    logging.info(f"Target distribution:\n{target_dist}")
    
    # Show feature columns
    feature_columns = [col for col in final_data.columns 
                      if col not in ['Date', 'Ticker', 'Sector', 'Target', 'Future_Return']]
    logging.info(f"Number of features: {len(feature_columns)}")
    logging.info(f"Feature columns: {feature_columns[:10]}...")  # Show first 10
    
    # Show sample of processed data
    logging.info("\nSample of processed data:")
    sample_cols = ['Date', 'Close', 'Returns', 'MA_20', 'RSI_14', 'MACD', 'Target']
    available_cols = [col for col in sample_cols if col in final_data.columns]
    print(final_data[available_cols].tail(10).to_string())
    
    # Demonstrate data splitting
    logging.info("\nDemonstrating data splitting...")
    train_size = int(len(final_data) * 0.7)
    val_size = int(len(final_data) * 0.15)
    
    train_data = final_data.iloc[:train_size]
    val_data = final_data.iloc[train_size:train_size + val_size]
    test_data = final_data.iloc[train_size + val_size:]
    
    logging.info(f"Train set: {len(train_data)} records")
    logging.info(f"Validation set: {len(val_data)} records")
    logging.info(f"Test set: {len(test_data)} records")
    
    # Show data quality metrics
    logging.info("\nData Quality Metrics:")
    logging.info(f"Missing values: {final_data.isnull().sum().sum()}")
    logging.info(f"Duplicate rows: {final_data.duplicated().sum()}")
    
    # Feature statistics
    numeric_features = final_data.select_dtypes(include=[np.number]).columns
    logging.info(f"Numeric features: {len(numeric_features)}")
    
    # ============================================================
    # MODEL ACCURACY TESTING
    # ============================================================
    logging.info("\n" + "=" * 60)
    logging.info("MODEL ACCURACY TESTING")
    logging.info("=" * 60)
    
    # Prepare features for training
    logging.info("Preparing features for model training...")
    X, y, feature_names, label_encoder = prepare_features_for_training(final_data)
    logging.info(f"Prepared {len(feature_names)} features for training")
    
    # Train and evaluate model
    logging.info("Training and evaluating XGBoost model...")
    results = train_and_evaluate_model(X, y, feature_names)
    
    # Display results
    logging.info("\n" + "=" * 60)
    logging.info("MODEL ACCURACY RESULTS")
    logging.info("=" * 60)
    logging.info(f"Overall Accuracy: {results['accuracy']:.4f} ({results['accuracy']*100:.2f}%)")
    logging.info(f"F1 Score: {results['f1_score']:.4f}")
    
    logging.info("\nClassification Report:")
    logging.info(results['classification_report'])
    
    logging.info("\nConfusion Matrix:")
    logging.info(results['confusion_matrix'])
    
    logging.info("\nTop 10 Most Important Features:")
    logging.info(results['feature_importance'].head(10).to_string())
    
    # Create visualizations
    logging.info("\nCreating visualizations...")
    visualize_results(results)
    
    # Performance assessment
    accuracy = results['accuracy']
    f1 = results['f1_score']
    
    logging.info("\n" + "=" * 60)
    logging.info("PERFORMANCE ASSESSMENT")
    logging.info("=" * 60)
    
    if accuracy >= 0.8:
        logging.info("EXCELLENT: Model accuracy is very high (>=80%)")
        logging.info("Ready for deployment!")
    elif accuracy >= 0.7:
        logging.info("GOOD: Model accuracy is good (70-80%)")
        logging.info("Consider fine-tuning before deployment")
    elif accuracy >= 0.6:
        logging.info("FAIR: Model accuracy is acceptable (60-70%)")
        logging.info("Needs improvement before deployment")
    else:
        logging.info("POOR: Model accuracy is below 60%")
        logging.info("Significant improvements needed before deployment")
    
    logging.info(f"\nRecommendation based on {accuracy*100:.1f}% accuracy:")
    if accuracy >= 0.75:
                    logging.info("Model is ready for deployment")
    elif accuracy >= 0.65:
                    logging.info("Model needs some tuning before deployment")
    else:
                    logging.info("Model needs significant improvements before deployment")
    
    logging.info("\n" + "=" * 60)
    logging.info("DEMONSTRATION COMPLETED")
    logging.info("=" * 60)
    logging.info("Accuracy testing completed!")
    logging.info("Check 'model_accuracy_test_results.png' for visualizations")
    logging.info("To train the full model, run: python FinanceModel.py")

if __name__ == "__main__":
    demonstrate_model_functionality() 