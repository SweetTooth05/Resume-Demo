"""
Incremental Data Collector for ASX Stock Data
Checks existing data and only fetches new data from yfinance
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import re
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
import random
import socket
from fake_useragent import UserAgent
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from tqdm import tqdm

from config import (
    ASX_DATA_SOURCES, DATA_CONFIG,
    DATABASE_CONFIG, LOGGING_CONFIG, BASE_DIR, RAW_DATA_DIR,
)
from yahoo_http import build_yahoo_session, proxies_configured

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG["file"]),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IPRotator:
    """
    Legacy: fetches public proxy lists (often unreliable).

    Yahoo/yfinance traffic uses ``yahoo_http`` with ``YAHOO_HTTP_PROXIES`` or
    ``HTTPS_PROXY`` for rotation instead — see PersonalFinanceApp docs.
    """

    def __init__(self):
        self.proxy_list = []
        self.current_proxy_index = 0
        self.user_agent = UserAgent()
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxy list from various sources"""
        try:
            # Free proxy sources (for development - use paid proxies in production)
            proxy_sources = [
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
            ]
            
            for source in proxy_sources:
                try:
                    response = requests.get(source, timeout=10)
                    if response.status_code == 200:
                        proxies = response.text.strip().split('\n')
                        self.proxy_list.extend([f"http://{proxy}" for proxy in proxies if proxy])
                except Exception as e:
                    logger.warning(f"Failed to load proxies from {source}: {e}")
            
            # Add local proxies for development
            self.proxy_list.extend([
                None,  # Direct connection
                "http://127.0.0.1:8080",
                "http://127.0.0.1:3128"
            ])
            
            logger.info(f"Loaded {len(self.proxy_list)} proxies")
            
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
            self.proxy_list = [None]  # Fallback to direct connection
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy from rotation"""
        if not self.proxy_list:
            return None
        
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy
    
    def get_random_user_agent(self) -> str:
        """Get random user agent"""
        try:
            return self.user_agent.random
        except:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

class ThreadSafeYFinance:
    """Thread-safe yfinance wrapper with rate limiting; optional proxy rotation via env."""

    def __init__(self, max_workers: int = 10, request_delay: float = 0.5):
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.sessions = Queue()
        self.lock = threading.Lock()
        self._initialize_sessions()

    def _initialize_sessions(self) -> None:
        """Session pool only when not using proxies (rotating sessions need a fresh client per request)."""
        if proxies_configured():
            return
        for _ in range(self.max_workers):
            self.sessions.put(build_yahoo_session())
    
    def _get_session(self):
        """Get session from pool"""
        return self.sessions.get()

    def _return_session(self, session) -> None:
        """Return session to pool"""
        self.sessions.put(session)
    
    def _rate_limit(self):
        """Rate limiting to avoid API restrictions"""
        time.sleep(self.request_delay)
    
    def get_stock_data_incremental(self, ticker: str, start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get stock data with incremental updates"""
        try:
            self._rate_limit()

            # Add .AX suffix if not present
            if not ticker.endswith('.AX') and len(ticker) <= 5:
                ticker = f"{ticker}.AX"

            if proxies_configured():
                session = build_yahoo_session()
                try:
                    stock = yf.Ticker(ticker, session=session)
                    if start_date:
                        data = stock.history(start=start_date, interval="1d")
                    else:
                        data = stock.history(period="2y", interval="1d")
                finally:
                    try:
                        session.close()
                    except Exception:
                        pass
            else:
                session = self._get_session()
                try:
                    stock = yf.Ticker(ticker, session=session)
                    if start_date:
                        data = stock.history(start=start_date, interval="1d")
                    else:
                        data = stock.history(period="2y", interval="1d")
                finally:
                    self._return_session(session)

            if data.empty:
                logger.warning(f"No data found for {ticker}")
                return None

            data["Ticker"] = ticker
            data["Date"] = data.index
            data.reset_index(drop=True, inplace=True)

            return data

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None

    def get_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Alias used by ``EnhancedStockPredictor.predict_stock``."""
        return self.get_stock_data_incremental(ticker)

class IncrementalASXDataCollector:
    """Incremental ASX data collector that checks existing data and only fetches new data"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.yfinance_collector = ThreadSafeYFinance(max_workers=max_workers)
        self.db_engine = None
        self.setup_database()
        
    def setup_database(self):
        """Setup database connection"""
        try:
            db_url = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
            self.db_engine = create_engine(db_url, pool_size=DATABASE_CONFIG['pool_size'], max_overflow=DATABASE_CONFIG['max_overflow'])
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.db_engine = None
    
    def get_existing_data_info(self) -> Dict[str, str]:
        """Get information about existing data files and their last dates"""
        existing_data = {}
        
        try:
            # Check raw data directory
            if RAW_DATA_DIR.exists():
                for file_path in RAW_DATA_DIR.glob("*_raw.csv"):
                    ticker = file_path.stem.replace("_raw", "")
                    
                    try:
                        # Read the last few lines to get the most recent date
                        df = pd.read_csv(file_path)
                        if not df.empty and 'Date' in df.columns:
                            # Convert date column to datetime
                            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                            # Remove timezone info if present
                            if df['Date'].dt.tz is not None:
                                df['Date'] = df['Date'].dt.tz_localize(None)
                            last_date = df['Date'].max()
                            if pd.notna(last_date):
                                existing_data[ticker] = last_date.strftime('%Y-%m-%d')
                                logger.info(f"Found existing data for {ticker}: last date {last_date.strftime('%Y-%m-%d')}")
                    except Exception as e:
                        logger.warning(f"Error reading existing data for {ticker}: {e}")
                        continue
            
            logger.info(f"Found {len(existing_data)} existing data files")
            return existing_data
            
        except Exception as e:
            logger.error(f"Error checking existing data: {e}")
            return {}
    
    def download_asx_companies(self) -> pd.DataFrame:
        """Download latest ASX companies list"""
        try:
            logger.info("📥 Downloading ASX companies list...")
            
            # Try to use existing ASX companies file
            asx_file = BASE_DIR / "ASXListedCompanies.csv"
            if asx_file.exists():
                logger.info("Using existing ASX companies file")
                df = pd.read_csv(asx_file)
                return df
            
            # If not available, try to download
            try:
                response = requests.get(ASX_DATA_SOURCES["primary"])
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for CSV download link
                    csv_links = soup.find_all('a', href=re.compile(r'\.csv'))
                    if csv_links:
                        csv_url = csv_links[0]['href']
                        if not csv_url.startswith('http'):
                            csv_url = ASX_DATA_SOURCES["primary"] + csv_url
                        
                        logger.info(f"Found CSV link: {csv_url}")
                        csv_response = requests.get(csv_url)
                        if csv_response.status_code == 200:
                            df = pd.read_csv(csv_response.content)
                            logger.info(f"Downloaded {len(df)} companies from primary source")
                            return df
            except Exception as e:
                logger.warning(f"Primary source failed: {e}")
            
            # Fallback to backup source
            logger.info("Trying backup source...")
            response = requests.get(ASX_DATA_SOURCES["backup"])
            if response.status_code == 200:
                # Parse HTML table
                soup = BeautifulSoup(response.content, 'html.parser')
                tables = soup.find_all('table')
                
                for table in tables:
                    try:
                        df = pd.read_html(str(table))[0]
                        if len(df.columns) > 2:  # Basic validation
                            logger.info(f"Downloaded {len(df)} companies from backup source")
                            return df
                    except Exception as e:
                        continue
            
            # If all else fails, create a basic list from existing data
            logger.warning("Could not download ASX companies, using existing data files")
            existing_files = list(RAW_DATA_DIR.glob("*_raw.csv"))
            tickers = [f.stem.replace("_raw", "") for f in existing_files]
            df = pd.DataFrame({'Code': tickers})
            return df
            
        except Exception as e:
            logger.error(f"Error downloading ASX companies: {e}")
            return pd.DataFrame()
    
    def collect_stock_data_incremental(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        """Collect stock data with incremental updates"""
        logger.info(f"Starting incremental data collection for {len(tickers)} tickers...")
        
        # Get existing data info
        existing_data = self.get_existing_data_info()
        
        def fetch_single_stock(ticker: str) -> Tuple[str, Optional[pd.DataFrame]]:
            try:
                # Check if we have existing data for this ticker
                if ticker in existing_data:
                    last_date = existing_data[ticker]
                    logger.info(f"Fetching incremental data for {ticker} from {last_date}")
                    
                    # Add one day to avoid duplicate data
                    start_date = (pd.to_datetime(last_date) + timedelta(days=1)).strftime('%Y-%m-%d')
                    data = self.yfinance_collector.get_stock_data_incremental(ticker, start_date=start_date)
                    
                    if data is not None and not data.empty:
                        # Load existing data and append new data
                        existing_file = RAW_DATA_DIR / f"{ticker}_raw.csv"
                        if existing_file.exists():
                            existing_df = pd.read_csv(existing_file)
                            # Ensure Date column is properly formatted
                            if 'Date' in existing_df.columns:
                                existing_df['Date'] = pd.to_datetime(existing_df['Date'])
                            if 'Date' in data.columns:
                                data['Date'] = pd.to_datetime(data['Date'])
                            
                            combined_df = pd.concat([existing_df, data], ignore_index=True)
                            combined_df = combined_df.drop_duplicates(subset=['Date'], keep='last')
                            combined_df = combined_df.sort_values('Date')
                            
                            # Save updated data
                            combined_df.to_csv(existing_file, index=False)
                            logger.info(f"Updated {ticker} with {len(data)} new records")
                            return ticker, combined_df
                        else:
                            # Save new data
                            data.to_csv(existing_file, index=False)
                            logger.info(f"Created new file for {ticker} with {len(data)} records")
                            return ticker, data
                    else:
                        logger.info(f"No new data available for {ticker}")
                        # Return existing data
                        existing_file = RAW_DATA_DIR / f"{ticker}_raw.csv"
                        if existing_file.exists():
                            existing_df = pd.read_csv(existing_file)
                            # Ensure Date column is properly formatted
                            if 'Date' in existing_df.columns:
                                existing_df['Date'] = pd.to_datetime(existing_df['Date'])
                            return ticker, existing_df
                        return ticker, None
                else:
                    # No existing data, fetch full dataset
                    logger.info(f"🆕 Fetching full dataset for {ticker}")
                    data = self.yfinance_collector.get_stock_data_incremental(ticker)
                    
                    if data is not None and not data.empty:
                        # Save new data
                        output_file = RAW_DATA_DIR / f"{ticker}_raw.csv"
                        data.to_csv(output_file, index=False)
                        logger.info(f"Created new file for {ticker} with {len(data)} records")
                        return ticker, data
                    else:
                        logger.warning(f"No data available for {ticker}")
                        return ticker, None
                        
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
                return ticker, None
        
        # Use ThreadPoolExecutor for parallel processing
        stock_data = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {executor.submit(fetch_single_stock, ticker): ticker for ticker in tickers}
            
            for future in tqdm(as_completed(future_to_ticker), total=len(tickers), desc="Collecting stock data"):
                ticker = future_to_ticker[future]
                try:
                    ticker_name, data = future.result()
                    if data is not None:
                        stock_data[ticker_name] = data
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")
        
        logger.info(f"Incremental data collection completed! Collected data for {len(stock_data)} tickers")
        return stock_data
    
    def collect_all_data_incremental(self, max_companies: int = 100) -> Dict:
        """Collect all data with incremental updates"""
        try:
            logger.info("Starting incremental data collection...")
            
            # Download ASX companies
            companies_df = self.download_asx_companies()
            if companies_df.empty:
                raise Exception("No ASX companies data available")
            
            # Limit companies for processing
            if len(companies_df) > max_companies:
                companies_df = companies_df.head(max_companies)
                logger.info(f"Limited to top {max_companies} companies")
            
            # Get ticker column
            ticker_col = None
            for col in ['Code', 'Ticker', 'Symbol', 'ASX code']:
                if col in companies_df.columns:
                    ticker_col = col
                    break
            
            if not ticker_col:
                raise Exception("No ticker column found in ASX data")
            
            # Collect stock data using incremental updates
            tickers = companies_df[ticker_col].dropna().tolist()
            stock_data = self.collect_stock_data_incremental(tickers)
            
            logger.info(f"Incremental data collection completed!")
            logger.info(f"   - Companies processed: {len(companies_df)}")
            logger.info(f"   - Stock data collected: {len(stock_data)}")
            
            return {
                'companies': companies_df,
                'stock_data': stock_data
            }
            
        except Exception as e:
            logger.error(f"Error in incremental data collection: {e}")
            return {}

def main():
    """Main function for incremental data collection"""
    collector = IncrementalASXDataCollector(max_workers=15)  # Use 15 threads for better performance
    data = collector.collect_all_data_incremental(max_companies=50)  # Start with 50 companies
    
    if data:
        logger.info("Incremental data collection completed successfully!")
    else:
        logger.error("Incremental data collection failed!")

if __name__ == "__main__":
    main() 