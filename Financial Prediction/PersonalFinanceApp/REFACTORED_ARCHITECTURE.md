# Personal Finance App - Refactored Architecture

## Overview

This document describes the comprehensive refactoring of the Personal Finance App to integrate the enhanced StockPredictionModel with sentiment analysis, improved data collection, and a more efficient architecture.

## Key Improvements

### 1. Enhanced Data Collection
- **Updated ASX Data Source**: Now uses the latest ASX data from [asxlistedcompanies.com](https://www.asxlistedcompanies.com/)
- **Real-time Data**: Live stock data from Yahoo Finance with automatic updates
- **Sentiment Analysis**: Integration with Australian news sources, Reddit, and social media
- **Async Processing**: Concurrent data collection for improved performance

### 2. Advanced Feature Engineering
- **70+ Technical Indicators**: Comprehensive technical analysis including RSI, MACD, Bollinger Bands, etc.
- **Sentiment Features**: News sentiment, social media sentiment, and Reddit sentiment
- **Time-based Features**: Cyclical encoding for temporal patterns
- **Interaction Features**: Cross-indicator interactions for better predictions

### 3. Ensemble Machine Learning Model
- **Multiple Models**: XGBoost, Random Forest, Gradient Boosting, Logistic Regression
- **Hyperparameter Optimization**: Automated tuning using Optuna
- **GPU Acceleration**: CUDA support for faster training
- **Ensemble Weighting**: Performance-based model combination

### 4. Improved Architecture
- **Modular Design**: Separated concerns with dedicated modules
- **Error Handling**: Comprehensive error handling and fallback mechanisms
- **Logging**: Detailed logging for monitoring and debugging
- **Configuration Management**: Centralized configuration system

## Directory Structure

```
PersonalFinanceApp/
├── backend/
│   ├── app/
│   │   ├── ml/
│   │   │   └── stock_predictor.py          # Enhanced predictor integration
│   │   ├── models/
│   │   ├── api/
│   │   └── core/
│   ├── simple_setup.py                     # Database setup
│   └── populate_enhanced_data.py           # Enhanced data population
├── StockPredictionModel/                   # NEW: Enhanced ML system
│   ├── config.py                           # Centralized configuration
│   ├── data_collector.py                   # Enhanced data collection
│   ├── feature_engineering.py              # Advanced feature engineering
│   ├── enhanced_model.py                   # Ensemble ML model
│   ├── requirements.txt                    # Updated dependencies
│   ├── processed_finance_data/             # Model outputs
│   └── logs/                               # Logging directory
└── frontend/                               # React frontend (unchanged)
```

## New Components

### 1. StockPredictionModel/
The new enhanced ML system with the following modules:

#### `config.py`
- Centralized configuration management
- ASX data sources configuration
- Model hyperparameters
- Sentiment analysis sources
- Database and API settings

#### `data_collector.py`
- **ASXDataCollector**: Downloads latest ASX company data
- **Sentiment Collection**: Async sentiment analysis from multiple sources
- **Real-time Data**: Live stock data from Yahoo Finance
- **Database Integration**: Direct PostgreSQL integration

#### `feature_engineering.py`
- **FeatureEngineer**: Comprehensive technical indicator calculation
- **70+ Indicators**: RSI, MACD, Bollinger Bands, Stochastic, etc.
- **Sentiment Integration**: News and social media sentiment features
- **Feature Selection**: Automated feature selection and correlation removal
- **Scaling**: Robust scaling for ML models

#### `enhanced_model.py`
- **EnhancedStockPredictor**: Main prediction engine
- **Ensemble Models**: XGBoost, Random Forest, Gradient Boosting, Logistic Regression
- **Hyperparameter Optimization**: Optuna-based automated tuning
- **GPU Support**: CUDA acceleration for faster training
- **Model Persistence**: Save/load trained models and metadata

### 2. Enhanced Backend Integration

#### `backend/app/ml/stock_predictor.py`
- **Enhanced Integration**: Uses the new StockPredictionModel
- **Fallback System**: Graceful degradation when enhanced model unavailable
- **Real-time Predictions**: Live predictions with sentiment analysis
- **Performance Monitoring**: Model accuracy tracking

#### `backend/populate_enhanced_data.py`
- **Enhanced Data Population**: Uses the new ML system
- **Real Predictions**: AI-powered stock predictions
- **Sentiment Integration**: Includes sentiment data in predictions
- **Performance Metrics**: Detailed performance reporting

## Sentiment Analysis Sources

### Australian News Sources
- Australian Financial Review (AFR)
- Sydney Morning Herald Business
- The Australian Business
- News.com.au Finance

### Social Media
- Reddit: r/ausfinance, r/ASX_Bets, r/AusStocks
- Twitter: ASX-related discussions
- LinkedIn: Australian Securities Exchange

### Keywords
- ASX, Australian stocks, Aussie market
- Australian shares, ASX 200
- Australian Securities Exchange

## Technical Indicators

### Price-based Features
- Returns, Log Returns, Price Changes
- High/Low ratios, Body size, Gap analysis
- Price position within daily range

### Moving Averages
- Simple and Exponential MAs (5, 10, 20, 50, 100, 200)
- Price vs MA ratios
- MA crossovers

### Momentum Indicators
- RSI (7, 14, 21)
- Momentum (5, 10, 20, 50)
- Rate of Change (ROC)

### Volatility Indicators
- Rolling volatility (5, 10, 20, 50)
- Annualized volatility
- ATR (Average True Range)

### Volume Indicators
- Volume moving averages
- Volume ratios
- On-Balance Volume (OBV)
- Volume Price Trend (VPT)

### Trend Indicators
- MACD (12, 26, 9)
- Parabolic SAR
- ADX (Average Directional Index)
- Bollinger Bands (10, 20, 50)

### Oscillator Indicators
- Stochastic (14, 21)
- Williams %R (14, 21)
- CCI (Commodity Channel Index)
- MFI (Money Flow Index)

### Time Features
- Day of week, Month, Quarter, Year
- Cyclical encoding (sin/cos)
- Day of year

### Interaction Features
- Volume-Price interactions
- Momentum-Volatility interactions
- RSI-MACD interactions

## Model Architecture

### Ensemble Approach
1. **XGBoost**: Primary model with GPU acceleration
2. **Random Forest**: Robust baseline model
3. **Gradient Boosting**: Sequential learning model
4. **Logistic Regression**: Linear model for interpretability

### Hyperparameter Optimization
- **Optuna**: Automated hyperparameter tuning
- **Cross-validation**: 5-fold stratified CV
- **Early stopping**: Prevent overfitting
- **GPU acceleration**: CUDA support for XGBoost

### Feature Selection
- **Statistical tests**: F-test for feature importance
- **Correlation removal**: Remove highly correlated features
- **Threshold-based**: Minimum importance threshold
- **Top-k selection**: Select top k features

## Performance Improvements

### Data Collection
- **Async processing**: Concurrent data collection
- **Rate limiting**: Respectful API usage
- **Caching**: Reduce redundant requests
- **Error handling**: Robust error recovery

### Model Training
- **GPU acceleration**: 10x faster training with CUDA
- **Parallel processing**: Multi-core feature engineering
- **Memory optimization**: Efficient data handling
- **Early stopping**: Prevent overfitting

### Prediction Pipeline
- **Real-time predictions**: Live stock predictions
- **Sentiment integration**: Market sentiment analysis
- **Confidence scoring**: Prediction confidence metrics
- **Fallback system**: Graceful degradation

## Setup Instructions

### 1. Install Dependencies
```bash
cd PersonalFinanceApp/StockPredictionModel
pip install -r requirements.txt
```

### 2. Setup Database
```bash
cd PersonalFinanceApp/backend
python3 simple_setup.py
```

### 3. Train Enhanced Model (Optional)
```bash
cd PersonalFinanceApp/StockPredictionModel
python3 enhanced_model.py
```

### 4. Populate Database
```bash
cd PersonalFinanceApp/backend
python3 populate_enhanced_data.py
```

### 5. Start Backend
```bash
cd PersonalFinanceApp/backend
uvicorn app.main:app --reload
```

### 6. Start Frontend
```bash
cd PersonalFinanceApp/frontend
npm run dev
```

## Configuration

### Environment Variables
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=finance_app
DB_USER=postgres
DB_PASSWORD=postgres

# API Keys (for production)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
TWITTER_API_KEY=your_twitter_api_key
```

### Model Configuration
- **Training data**: 2 years of historical data
- **Update frequency**: 6 hours for sentiment data
- **Minimum data points**: 252 (1 year)
- **Feature threshold**: 0.01 minimum importance

## Monitoring and Logging

### Log Files
- `StockPredictionModel/logs/stock_prediction.log`
- `StockPredictionModel/logs/enhanced_model.log`
- `backend/logs/app.log`

### Performance Metrics
- Model accuracy tracking
- Prediction confidence scores
- Feature importance analysis
- Training time monitoring

### Error Handling
- Comprehensive error logging
- Fallback mechanisms
- Graceful degradation
- Recovery procedures

## Future Enhancements

### Planned Improvements
1. **Advanced Sentiment Analysis**: BERT-based sentiment models
2. **News API Integration**: Real-time news sentiment
3. **Alternative Data**: Social media trends, economic indicators
4. **Deep Learning**: LSTM/Transformer models for time series
5. **Portfolio Optimization**: Risk-adjusted portfolio recommendations

### Scalability
1. **Microservices**: Separate services for data collection, ML, API
2. **Message Queues**: Async processing with Redis/RabbitMQ
3. **Containerization**: Docker deployment
4. **Cloud Integration**: AWS/Azure deployment
5. **Real-time Streaming**: Kafka for real-time data

## Troubleshooting

### Common Issues
1. **CUDA not available**: Falls back to CPU training
2. **ASX data unavailable**: Uses backup sources
3. **Model loading failed**: Uses fallback predictions
4. **Database connection**: Check PostgreSQL service

### Performance Tuning
1. **GPU memory**: Adjust batch sizes for GPU training
2. **Database connections**: Optimize connection pooling
3. **Feature selection**: Reduce feature count for faster training
4. **Caching**: Enable prediction caching

## Conclusion

The refactored architecture provides a robust, scalable, and efficient system for stock prediction with sentiment analysis. The modular design allows for easy maintenance and future enhancements while providing significant performance improvements over the previous system. 