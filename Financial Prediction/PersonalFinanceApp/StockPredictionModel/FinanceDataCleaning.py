import yfinance as yf
import pandas as pd

from yahoo_http import build_yahoo_session
import numpy as np
import seaborn as sns
import os
import time
import warnings
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import logging
from sklearn.ensemble import RandomForestClassifier
import pickle
import threading
import queue
import requests
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Suppress warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('finance_scraping.log'),
        logging.StreamHandler()
    ]
)

class ASXFinanceDataProcessor:
    def __init__(self, csv_file_path, output_base_dir="processed_data", max_workers=10, use_proxies=True):

        self.csv_file_path = csv_file_path
        self.output_base_dir = output_base_dir
        self.scaler = MinMaxScaler()
        self.label_encoder = LabelEncoder()
        
        # Threading parameters
        self.max_workers = max_workers
        self.use_proxies = use_proxies
        self.proxy_list = self.load_proxy_list() if use_proxies else []
        self.proxy_lock = Lock()
        
        # Create output directories
        self.create_output_directories()
        
        # Rate limiting parameters (per thread)
        self.delay_between_requests = 0.5  # Reduced delay since we're using multiple threads
        self.max_retries = 3
        
        # Load sector information
        self.sector_info = self.load_sector_info()
        
        # Thread-safe counters
        self.successful_companies = []
        self.failed_companies = []
        self.counters_lock = Lock()
    
    def load_proxy_list(self):
        """Load list of free proxies for IP rotation"""
        try:
            # Free proxy list - you can replace with your own proxy service
            proxy_urls = [
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
                "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt"
            ]
            
            proxies = []
            for url in proxy_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        proxy_lines = response.text.strip().split('\n')
                        for line in proxy_lines:
                            if ':' in line and line.strip():
                                proxies.append(line.strip())
                except:
                    continue
            
            # Add some common free proxies as fallback
            fallback_proxies = [
                "127.0.0.1:8080",
                "127.0.0.1:3128",
                "127.0.0.1:1080"
            ]
            proxies.extend(fallback_proxies)
            
            logging.info(f"Loaded {len(proxies)} proxies for IP rotation")
            return proxies
        except Exception as e:
            logging.warning(f"Failed to load proxies: {e}")
            return []
    
    def get_random_proxy(self):
        """Get a random proxy from the list"""
        with self.proxy_lock:
            if self.proxy_list:
                return random.choice(self.proxy_list)
            return None
        
    def create_output_directories(self):
        """Create the necessary output directories"""
        directories = [
            self.output_base_dir,
            f"{self.output_base_dir}/raw_data",
            f"{self.output_base_dir}/processed_data",
            f"{self.output_base_dir}/train_data",
            f"{self.output_base_dir}/test_data",
            f"{self.output_base_dir}/validation_data",
            f"{self.output_base_dir}/scalers",
            f"{self.output_base_dir}/models",
            f"{self.output_base_dir}/features"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Created directory: {directory}")
    
    def load_sector_info(self):
        """Load sector information from CSV"""
        try:
            df = pd.read_csv(self.csv_file_path)
            sector_dict = dict(zip(df['ASX code'], df['GICS industry group']))
            logging.info(f"Loaded sector information for {len(sector_dict)} companies")
            return sector_dict
        except Exception as e:
            logging.error(f"Error loading sector info: {e}")
            return {}
    
    def load_asx_companies(self):
        try:
            df = pd.read_csv(self.csv_file_path)
            # Extract ASX codes from the 'ASX code' column
            asx_codes = df['ASX code'].dropna().tolist()
            logging.info(f"Loaded {len(asx_codes)} ASX companies from CSV")
            return asx_codes
        except Exception as e:
            logging.error(f"Error loading ASX companies: {e}")
            return []
    
    def scrape_financial_data(self, ticker, start_date="2020-01-01", end_date=None, thread_id=None):
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        for attempt in range(self.max_retries):
            try:
                # Add .AX suffix for ASX companies
                full_ticker = f"{ticker}.AX"
                
                # Configure proxy if available
                proxy = None
                if self.use_proxies and self.proxy_list:
                    proxy = self.get_random_proxy()
                    if proxy:
                        proxy_dict = {
                            'http': f'http://{proxy}',
                            'https': f'http://{proxy}'
                        }
                    else:
                        proxy_dict = None
                else:
                    proxy_dict = None

                if proxy_dict:
                    session = requests.Session()
                    session.proxies.update(proxy_dict)
                else:
                    session = build_yahoo_session()

                stock = yf.Ticker(full_ticker, session=session)
                data = stock.history(start=start_date, end=end_date)
                
                if data.empty:
                    logging.warning(f"[Thread {thread_id}] No data found for {full_ticker}")
                    return None
                
                # Add ticker column for identification
                data['Ticker'] = ticker
                data['Date'] = data.index
                
                # Add sector information
                data['Sector'] = self.sector_info.get(ticker, 'Unknown')
                
                logging.info(f"[Thread {thread_id}] Successfully scraped data for {full_ticker}: {len(data)} records")
                return data
                
            except Exception as e:
                logging.warning(f"[Thread {thread_id}] Attempt {attempt + 1} failed for {ticker}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_requests * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    logging.error(f"[Thread {thread_id}] All attempts failed for {ticker}")
                    return None
        
        return None
    
    def create_target_variable(self, data, lookforward_days=30, threshold_pct=0.05):
        """
        Create target variable for buy/sell/hold prediction
        
        Args:
            data (pd.DataFrame): Stock data
            lookforward_days (int): Number of days to look forward
            threshold_pct (float): Percentage threshold for buy/sell signals
            
        Returns:
            pd.DataFrame: Data with target variable
        """
        try:
            data = data.copy()
            
            # Calculate future returns
            data['Future_Return'] = data['Close'].shift(-lookforward_days) / data['Close'] - 1
            
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
            
            data['Target'] = data['Future_Return'].apply(create_signal)
            
            # Remove rows with NaN targets (last few days)
            data = data.dropna(subset=['Target'])
            
            logging.info(f"Created target variable with distribution: {data['Target'].value_counts().to_dict()}")
            return data
            
        except Exception as e:
            logging.error(f"Error creating target variable: {e}")
            return data
    
    def process_financial_data(self, data):
        """
        Process and clean financial data with enhanced features for XGBoost
        
        Args:
            data (pd.DataFrame): Raw financial data
            
        Returns:
            pd.DataFrame: Processed data
        """
        if data is None or data.empty:
            return None
        
        try:
            # Create a copy to avoid modifying original data
            processed_data = data.copy()
            
            # Basic price features
            processed_data['Returns'] = processed_data['Close'].pct_change()
            processed_data['Log_Returns'] = np.log(processed_data['Close'] / processed_data['Close'].shift(1))
            processed_data['Price_Change'] = processed_data['Close'] - processed_data['Open']
            processed_data['Price_Change_Pct'] = (processed_data['Close'] - processed_data['Open']) / processed_data['Open']
            
            # Moving averages
            for window in [5, 10, 20, 50, 100, 200]:
                processed_data[f'MA_{window}'] = processed_data['Close'].rolling(window=window).mean()
                processed_data[f'MA_Ratio_{window}'] = processed_data['Close'] / processed_data[f'MA_{window}']
            
            # Volatility features
            for window in [5, 10, 20, 50]:
                processed_data[f'Volatility_{window}'] = processed_data['Returns'].rolling(window=window).std()
                processed_data[f'Volatility_Annualized_{window}'] = processed_data[f'Volatility_{window}'] * np.sqrt(252)
            
            # RSI with multiple periods
            for period in [7, 14, 21]:
                delta = processed_data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                processed_data[f'RSI_{period}'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = processed_data['Close'].ewm(span=12).mean()
            exp2 = processed_data['Close'].ewm(span=26).mean()
            processed_data['MACD'] = exp1 - exp2
            processed_data['MACD_Signal'] = processed_data['MACD'].ewm(span=9).mean()
            processed_data['MACD_Histogram'] = processed_data['MACD'] - processed_data['MACD_Signal']
            
            # Bollinger Bands
            for window in [10, 20, 50]:
                bb_middle = processed_data['Close'].rolling(window=window).mean()
                bb_std = processed_data['Close'].rolling(window=window).std()
                processed_data[f'BB_Upper_{window}'] = bb_middle + (bb_std * 2)
                processed_data[f'BB_Lower_{window}'] = bb_middle - (bb_std * 2)
                processed_data[f'BB_Position_{window}'] = (processed_data['Close'] - bb_middle) / (bb_std * 2)
            
            # Volume indicators
            processed_data['Volume_MA_5'] = processed_data['Volume'].rolling(window=5).mean()
            processed_data['Volume_MA_20'] = processed_data['Volume'].rolling(window=20).mean()
            processed_data['Volume_Ratio_5'] = processed_data['Volume'] / processed_data['Volume_MA_5']
            processed_data['Volume_Ratio_20'] = processed_data['Volume'] / processed_data['Volume_MA_20']
            
            # Price momentum
            for period in [5, 10, 20, 50]:
                processed_data[f'Momentum_{period}'] = processed_data['Close'] / processed_data['Close'].shift(period) - 1
            
            # Rate of change
            for period in [5, 10, 20, 50]:
                processed_data[f'ROC_{period}'] = (processed_data['Close'] - processed_data['Close'].shift(period)) / processed_data['Close'].shift(period)
            
            # Stochastic oscillator
            for period in [14, 21]:
                low_min = processed_data['Low'].rolling(window=period).min()
                high_max = processed_data['High'].rolling(window=period).max()
                processed_data[f'Stoch_K_{period}'] = 100 * (processed_data['Close'] - low_min) / (high_max - low_min)
                processed_data[f'Stoch_D_{period}'] = processed_data[f'Stoch_K_{period}'].rolling(window=3).mean()
            
            # Williams %R
            for period in [14, 21]:
                low_min = processed_data['Low'].rolling(window=period).min()
                high_max = processed_data['High'].rolling(window=period).max()
                processed_data[f'Williams_R_{period}'] = -100 * (high_max - processed_data['Close']) / (high_max - low_min)
            
            # Average True Range (ATR)
            for period in [14, 21]:
                high_low = processed_data['High'] - processed_data['Low']
                high_close = np.abs(processed_data['High'] - processed_data['Close'].shift())
                low_close = np.abs(processed_data['Low'] - processed_data['Close'].shift())
                true_range = np.maximum(high_low, np.maximum(high_close, low_close))
                processed_data[f'ATR_{period}'] = true_range.rolling(window=period).mean()
            
            # Commodity Channel Index (CCI)
            for period in [14, 21]:
                typical_price = (processed_data['High'] + processed_data['Low'] + processed_data['Close']) / 3
                sma_tp = typical_price.rolling(window=period).mean()
                mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
                processed_data[f'CCI_{period}'] = (typical_price - sma_tp) / (0.015 * mad)
            
            # Money Flow Index (MFI)
            for period in [14, 21]:
                typical_price = (processed_data['High'] + processed_data['Low'] + processed_data['Close']) / 3
                money_flow = typical_price * processed_data['Volume']
                
                positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=period).sum()
                negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=period).sum()
                
                money_ratio = positive_flow / negative_flow
                processed_data[f'MFI_{period}'] = 100 - (100 / (1 + money_ratio))
            
            # Parabolic SAR
            processed_data['PSAR'] = self.calculate_psar(processed_data)
            
            # Create target variable
            processed_data = self.create_target_variable(processed_data)
            
            # Remove rows with NaN values (from rolling calculations)
            processed_data = processed_data.dropna()
            
            logging.info(f"Processed data shape: {processed_data.shape}")
            return processed_data
            
        except Exception as e:
            logging.error(f"Error processing data: {e}")
            return None
    
    def calculate_psar(self, data, acceleration=0.02, maximum=0.2):
        """Calculate Parabolic SAR"""
        try:
            high = data['High'].values
            low = data['Low'].values
            close = data['Close'].values
            
            psar = np.zeros(len(data))
            af = acceleration
            ep = high[0]
            long = True
            
            for i in range(1, len(data)):
                if long:
                    psar[i] = psar[i-1] + af * (ep - psar[i-1])
                    if low[i] < psar[i]:
                        long = False
                        psar[i] = ep
                        ep = low[i]
                        af = acceleration
                    else:
                        if high[i] > ep:
                            ep = high[i]
                            af = min(af + acceleration, maximum)
                else:
                    psar[i] = psar[i-1] + af * (ep - psar[i-1])
                    if high[i] > psar[i]:
                        long = True
                        psar[i] = ep
                        ep = high[i]
                        af = acceleration
                    else:
                        if low[i] < ep:
                            ep = low[i]
                            af = min(af + acceleration, maximum)
            
            return psar
        except Exception as e:
            logging.error(f"Error calculating PSAR: {e}")
            return np.zeros(len(data))
    
    def normalize_data(self, data, ticker):
        """
        Normalize the data using MinMaxScaler
        
        Args:
            data (pd.DataFrame): Processed data
            ticker (str): Stock ticker for identification
            
        Returns:
            tuple: (normalized_data, scaler)
        """
        if data is None or data.empty:
            return None, None
        
        try:
            # Select numerical columns for normalization (exclude target and categorical)
            exclude_columns = ['Ticker', 'Date', 'Sector', 'Target', 'Future_Return']
            numerical_columns = [col for col in data.columns if col not in exclude_columns and data[col].dtype in ['float64', 'int64']]
            
            if not numerical_columns:
                logging.warning(f"No numerical columns found for {ticker}")
                return data, None
            
            # Create a copy for normalization
            normalized_data = data.copy()
            
            # Fit scaler and transform data
            scaler = MinMaxScaler()
            normalized_data[numerical_columns] = scaler.fit_transform(data[numerical_columns])
            
            # Save scaler
            scaler_path = f"{self.output_base_dir}/scalers/{ticker}_scaler.pkl"
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            logging.info(f"Normalized data for {ticker}")
            return normalized_data, scaler
            
        except Exception as e:
            logging.error(f"Error normalizing data for {ticker}: {e}")
            return data, None
    
    def encode_categorical_features(self, data):
        """Encode categorical features"""
        try:
            data = data.copy()
            
            # Encode sector
            if 'Sector' in data.columns:
                data['Sector_Encoded'] = self.label_encoder.fit_transform(data['Sector'])
            
            # Encode target
            if 'Target' in data.columns:
                data['Target_Encoded'] = self.label_encoder.fit_transform(data['Target'])
            
            return data
        except Exception as e:
            logging.error(f"Error encoding categorical features: {e}")
            return data
    
    def split_data(self, data, ticker, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """
        Split data into train, validation, and test sets
        
        Args:
            data (pd.DataFrame): Processed data
            ticker (str): Stock ticker for identification
            train_ratio (float): Proportion for training data
            val_ratio (float): Proportion for validation data
            test_ratio (float): Proportion for test data
            
        Returns:
            tuple: (train_data, val_data, test_data)
        """
        if data is None or data.empty:
            return None, None, None
        
        try:
            # Ensure ratios sum to 1
            total_ratio = train_ratio + val_ratio + test_ratio
            if abs(total_ratio - 1.0) > 0.01:
                logging.warning(f"Ratios don't sum to 1, normalizing: {total_ratio}")
                train_ratio /= total_ratio
                val_ratio /= total_ratio
                test_ratio /= total_ratio
            
            # Calculate split indices
            n_samples = len(data)
            train_end = int(n_samples * train_ratio)
            val_end = train_end + int(n_samples * val_ratio)
            
            # Split the data
            train_data = data.iloc[:train_end]
            val_data = data.iloc[train_end:val_end]
            test_data = data.iloc[val_end:]
            
            logging.info(f"Split data for {ticker}: Train={len(train_data)}, Val={len(val_data)}, Test={len(test_data)}")
            return train_data, val_data, test_data
            
        except Exception as e:
            logging.error(f"Error splitting data for {ticker}: {e}")
            return None, None, None
    
    def save_data(self, data, ticker, data_type):
        """
        Save data to appropriate directory
        
        Args:
            data (pd.DataFrame): Data to save
            ticker (str): Stock ticker for identification
            data_type (str): Type of data (raw, processed, train, val, test)
        """
        if data is None or data.empty:
            return
        
        try:
            # Determine file path based on data type
            if data_type == "raw":
                file_path = f"{self.output_base_dir}/raw_data/{ticker}_raw.csv"
            elif data_type == "processed":
                file_path = f"{self.output_base_dir}/processed_data/{ticker}_processed.csv"
            elif data_type == "train":
                file_path = f"{self.output_base_dir}/train_data/{ticker}_train.csv"
            elif data_type == "val":
                file_path = f"{self.output_base_dir}/validation_data/{ticker}_val.csv"
            elif data_type == "test":
                file_path = f"{self.output_base_dir}/test_data/{ticker}_test.csv"
            else:
                logging.error(f"Unknown data type: {data_type}")
                return
            
            # Save to CSV
            data.to_csv(file_path, index=False)
            logging.info(f"Saved {data_type} data for {ticker}: {file_path}")
            
        except Exception as e:
            logging.error(f"Error saving {data_type} data for {ticker}: {e}")
    
    def process_single_company(self, ticker, thread_id):
        """
        Process a single company (thread-safe)
        
        Args:
            ticker (str): Company ticker to process
            thread_id (int): Thread identifier for logging
        """
        try:
            logging.info(f"[Thread {thread_id}] Processing {ticker}")
            
            # Scrape financial data
            raw_data = self.scrape_financial_data(ticker, thread_id=thread_id)
            if raw_data is not None:
                # Save raw data
                self.save_data(raw_data, ticker, "raw")
                
                # Process data
                processed_data = self.process_financial_data(raw_data)
                if processed_data is not None:
                    # Encode categorical features
                    processed_data = self.encode_categorical_features(processed_data)
                    
                    # Save processed data
                    self.save_data(processed_data, ticker, "processed")
                    
                    # Normalize data
                    normalized_data, scaler = self.normalize_data(processed_data, ticker)
                    if normalized_data is not None:
                        # Split data
                        train_data, val_data, test_data = self.split_data(normalized_data, ticker)
                        
                        # Save split data
                        self.save_data(train_data, ticker, "train")
                        self.save_data(val_data, ticker, "val")
                        self.save_data(test_data, ticker, "test")
                        
                        with self.counters_lock:
                            self.successful_companies.append(ticker)
                        logging.info(f"[Thread {thread_id}] Successfully processed {ticker}")
                        return True
                    else:
                        with self.counters_lock:
                            self.failed_companies.append(ticker)
                        logging.warning(f"[Thread {thread_id}] Failed to normalize data for {ticker}")
                else:
                    with self.counters_lock:
                        self.failed_companies.append(ticker)
                    logging.warning(f"[Thread {thread_id}] Failed to process data for {ticker}")
            else:
                with self.counters_lock:
                    self.failed_companies.append(ticker)
                logging.warning(f"[Thread {thread_id}] Failed to scrape data for {ticker}")
                
        except Exception as e:
            with self.counters_lock:
                self.failed_companies.append(ticker)
            logging.error(f"[Thread {thread_id}] Unexpected error processing {ticker}: {e}")
        
        return False
    
    def run_full_pipeline(self):
        """
        Run the complete data processing pipeline with multi-threading
        """
        logging.info("Starting ASX Finance Data Processing Pipeline with Multi-Threading")
        logging.info(f"Using {self.max_workers} threads with {'proxy rotation' if self.use_proxies else 'no proxy rotation'}")
        
        # Load ASX companies
        asx_codes = self.load_asx_companies()
        if not asx_codes:
            logging.error("No ASX codes loaded. Exiting.")
            return
        
        logging.info(f"Processing {len(asx_codes)} companies with {self.max_workers} threads")
        
        # Reset counters
        self.successful_companies = []
        self.failed_companies = []
        
        # Process companies using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self.process_single_company, ticker, i % self.max_workers): ticker 
                for i, ticker in enumerate(asx_codes)
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                completed += 1
                
                try:
                    success = future.result()
                    if completed % 10 == 0:  # Log progress every 10 companies
                        logging.info(f"Progress: {completed}/{len(asx_codes)} companies processed")
                except Exception as e:
                    logging.error(f"Exception occurred while processing {ticker}: {e}")
                    with self.counters_lock:
                        self.failed_companies.append(ticker)
        
        # Summary
        logging.info("=" * 50)
        logging.info("PIPELINE COMPLETED")
        logging.info("=" * 50)
        logging.info(f"Total companies processed: {len(asx_codes)}")
        logging.info(f"Successful: {len(self.successful_companies)}")
        logging.info(f"Failed: {len(self.failed_companies)}")
        logging.info(f"Success rate: {len(self.successful_companies)/len(asx_codes)*100:.2f}%")
        
        if self.failed_companies:
            logging.info("Failed companies:")
            for company in self.failed_companies:
                logging.info(f"  - {company}")
        
        # Save summary to file
        summary_data = {
            'Total_Companies': len(asx_codes),
            'Successful': len(self.successful_companies),
            'Failed': len(self.failed_companies),
            'Success_Rate': len(self.successful_companies)/len(asx_codes)*100,
            'Successful_Companies': self.successful_companies,
            'Failed_Companies': self.failed_companies,
            'Threads_Used': self.max_workers,
            'Proxy_Rotation': self.use_proxies
        }
        
        summary_df = pd.DataFrame([summary_data])
        summary_df.to_csv(f"{self.output_base_dir}/processing_summary.csv", index=False)
        logging.info(f"Summary saved to {self.output_base_dir}/processing_summary.csv")

def main():
    """
    Main function to run the ASX Finance Data Processing Pipeline
    """
    # Configuration
    csv_file_path = "ASXListedCompanies.csv"  # Update path as needed
    output_directory = "processed_finance_data"
    
    # Threading configuration
    max_workers = 10  # Number of concurrent threads
    use_proxies = True  # Enable proxy rotation for IP diversity
    
    # Initialize processor with threading
    processor = ASXFinanceDataProcessor(
        csv_file_path, 
        output_directory,
        max_workers=max_workers,
        use_proxies=use_proxies
    )
    
    # Run the full pipeline
    processor.run_full_pipeline()

if __name__ == "__main__":
    main()
