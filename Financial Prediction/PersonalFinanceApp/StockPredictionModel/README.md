# XGBoost Stock Prediction System

A comprehensive machine learning system for predicting stock buy/sell/hold signals using XGBoost and advanced technical indicators.

## 🚀 Features

### Advanced Technical Indicators
- **Moving Averages**: 5, 10, 20, 50, 100, 200-day moving averages with price ratios
- **Volatility Metrics**: Rolling standard deviation with annualized calculations
- **RSI (Relative Strength Index)**: Multiple periods (7, 14, 21 days)
- **MACD**: Moving Average Convergence Divergence with signal line and histogram
- **Bollinger Bands**: Upper, lower, and position indicators for multiple periods
- **Volume Analysis**: Volume moving averages and ratios
- **Momentum Indicators**: Price momentum and rate of change calculations
- **Advanced Oscillators**: Stochastic, Williams %R, CCI, MFI
- **Trend Indicators**: Parabolic SAR, Average True Range (ATR)

### Target Variable Creation
- **Future Return Calculation**: 30-day forward-looking returns
- **Signal Classification**: BUY (>5% return), SELL (<-5% return), HOLD (between thresholds)
- **Customizable Thresholds**: Adjustable percentage thresholds for signal generation

### XGBoost Model Features
- **GPU Acceleration**: CUDA support for 10-50x faster training
- **Hyperparameter Tuning**: Grid search optimization for best parameters
- **Multi-class Classification**: BUY/SELL/HOLD prediction with confidence scores
- **Feature Importance Analysis**: Identify most predictive technical indicators
- **Comprehensive Evaluation**: Accuracy, F1-score, confusion matrix, classification reports
- **Model Persistence**: Save trained models for future use

## 📁 Project Structure

```
FinanceApp/
├── ASXListedCompanies.csv          # ASX company list with sectors
├── FinanceDataCleaning.py          # Enhanced data processing pipeline
├── FinanceModel.py                 # XGBoost model training and evaluation
├── test_model.py                   # Demonstration script with sample data
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── processed_finance_data/         # Output directory (created automatically)
    ├── raw_data/                   # Raw scraped data
    ├── processed_data/             # Data with technical indicators
    ├── train_data/                 # Training dataset
    ├── validation_data/            # Validation dataset
    ├── test_data/                  # Test dataset
    ├── scalers/                    # Data normalization scalers
    ├── models/                     # Trained XGBoost models
    └── features/                   # Feature importance analysis
```

## 🛠️ Installation

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up CUDA for GPU acceleration** (recommended for faster training):
   ```bash
   python setup_cuda.py
   ```
   
   This script will:
   - Check if CUDA is installed
   - Install XGBoost with GPU support
   - Verify GPU acceleration is working

4. **Verify installation**:
   ```bash
   python test_model.py
   ```

## 📊 Usage

### 1. Data Processing Pipeline

The enhanced `FinanceDataCleaning.py` processes ASX stock data with the following improvements:

```python
from FinanceDataCleaning import ASXFinanceDataProcessor

# Initialize processor
processor = ASXFinanceDataProcessor("ASXListedCompanies.csv", "processed_finance_data")

# Run the complete pipeline
processor.run_full_pipeline()
```

**Key Enhancements:**
- **Sector Information**: Includes GICS industry group classification
- **Enhanced Technical Indicators**: 50+ technical indicators for comprehensive analysis
- **Target Variable Creation**: Automatic BUY/SELL/HOLD signal generation
- **Data Normalization**: MinMaxScaler for feature scaling
- **Categorical Encoding**: Label encoding for sector and target variables

### 2. XGBoost Model Training

The `FinanceModel.py` provides a complete XGBoost training pipeline:

```python
from FinanceModel import XGBoostStockPredictor

# Initialize predictor
predictor = XGBoostStockPredictor("processed_finance_data")

# Run complete training pipeline
predictor.run_full_training_pipeline()
```

**Model Features:**
- **Hyperparameter Optimization**: Grid search for optimal parameters
- **Cross-validation**: 3-fold cross-validation during training
- **Feature Selection**: Automatic feature importance ranking
- **Model Evaluation**: Comprehensive performance metrics
- **Visualization**: Confusion matrix, feature importance plots

### 3. Single Stock Prediction

Make predictions for individual stocks:

```python
# Load trained model
predictor = XGBoostStockPredictor()
# (Model loading code would go here)

# Make prediction
result = predictor.predict_single_stock(stock_data)
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence_scores']}")
print(f"Recommendation: {result['recommendation']}")
```

## 🔧 Configuration

### Data Processing Parameters

In `FinanceDataCleaning.py`:
- `lookforward_days=30`: Days to look forward for target calculation
- `threshold_pct=0.05`: Percentage threshold for BUY/SELL signals
- `chunk_size=50`: Number of companies to process in each batch
- `delay_between_requests=1`: Rate limiting between API calls

### Model Training Parameters

In `FinanceModel.py`:
- **Hyperparameter Grid**: Customizable parameter search space
- **Cross-validation**: Adjustable CV folds
- **Scoring Metric**: F1-weighted score for multi-class evaluation

## 📈 Technical Indicators Included

### Price-Based Indicators
- Returns and log returns
- Price change and percentage change
- Moving averages (5, 10, 20, 50, 100, 200 days)
- Moving average ratios

### Volatility Indicators
- Rolling standard deviation
- Annualized volatility
- Average True Range (ATR)

### Momentum Indicators
- RSI (7, 14, 21 periods)
- MACD with signal line
- Rate of change (ROC)
- Price momentum

### Volume Indicators
- Volume moving averages
- Volume ratios
- Money Flow Index (MFI)

### Trend Indicators
- Bollinger Bands position
- Parabolic SAR
- Stochastic oscillator
- Williams %R
- Commodity Channel Index (CCI)

## 🎯 Model Performance

The XGBoost model provides:

- **Multi-class Classification**: BUY/SELL/HOLD predictions
- **Confidence Scores**: Probability estimates for each class
- **Feature Importance**: Ranking of most predictive indicators
- **Performance Metrics**: Accuracy, F1-score, precision, recall
- **Visualization**: Confusion matrix and feature importance plots

## 📋 Output Files

After running the pipeline, you'll find:

1. **Processed Data**: CSV files with technical indicators and targets
2. **Trained Model**: Pickle file with the best XGBoost model
3. **Feature Importance**: CSV ranking of most important features
4. **Performance Metrics**: Detailed evaluation results
5. **Visualizations**: PNG plots showing model performance
6. **Scalers**: Data normalization parameters

## ⚠️ Important Notes

### GPU Acceleration Benefits
- **10-50x faster training** with CUDA-enabled XGBoost
- **Automatic fallback** to CPU if GPU is not available
- **Memory efficient** GPU training for large datasets
- **Real-time detection** of CUDA availability

### Data Quality
- The system handles missing values by filling with median values
- Duplicate data points are automatically removed
- Rate limiting prevents API throttling

### Model Limitations
- Past performance doesn't guarantee future results
- Market conditions change, requiring model retraining
- Always use proper risk management strategies

### Dependencies
- Requires stable internet connection for data scraping
- XGBoost installation may require additional system dependencies
- Large datasets may require significant processing time
- CUDA Toolkit required for GPU acceleration (optional but recommended)

## 🚀 Quick Start

1. **Test the system**:
   ```bash
   python test_model.py
   ```

2. **Process ASX data**:
   ```bash
   python FinanceDataCleaning.py
   ```

3. **Train XGBoost model**:
   ```bash
   python FinanceModel.py
   ```

## 📞 Support

For issues or questions:
1. Check the log files for detailed error messages
2. Verify all dependencies are installed correctly
3. Ensure sufficient disk space for data processing
4. Check internet connection for data scraping

## 📄 License

This project is for educational and research purposes. Always conduct your own due diligence before making investment decisions.

---

**Disclaimer**: This system is for educational purposes only. Stock market predictions are inherently uncertain and past performance does not guarantee future results. Always consult with financial advisors and use proper risk management strategies. 