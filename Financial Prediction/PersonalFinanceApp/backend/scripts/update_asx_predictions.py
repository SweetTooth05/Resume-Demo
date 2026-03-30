#!/usr/bin/env python3
"""
ASX Stock Prediction Update Script

This script fetches data for all ASX-listed stocks, makes predictions using the trained XGBoost model,
and stores the results in the database. Designed to be run weekly via cron job.

Usage:
    python update_asx_predictions.py

Requirements:
    - Trained XGBoost model at ../FinanceApp/processed_finance_data/models/xgboost_stock_predictor.pkl
    - Database connection configured in .env
    - yfinance, pandas, numpy, xgboost installed
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.stock import StockPrediction
from app.ml.stock_predictor import StockPredictor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('asx_predictions_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ASXPredictionUpdater:
    def __init__(self):
        self.stock_predictor = StockPredictor()
        self.db = SessionLocal()
        
        # ASX stock list - major stocks with good liquidity
        self.asx_stocks = [
            # Banks
            'CBA.AX', 'ANZ.AX', 'NAB.AX', 'WBC.AX', 'MQG.AX',
            # Mining
            'BHP.AX', 'RIO.AX', 'FMG.AX', 'NCM.AX', 'NEM.AX',
            # Healthcare
            'CSL.AX', 'RMD.AX', 'COH.AX', 'SHL.AX', 'PLS.AX',
            # Consumer
            'WES.AX', 'WOW.AX', 'COL.AX', 'WSA.AX', 'JBH.AX',
            # Technology
            'WTC.AX', 'XRO.AX', 'WSP.AX', 'NXT.AX', 'REA.AX',
            # Energy
            'WDS.AX', 'STO.AX', 'ORG.AX', 'AGL.AX', 'APA.AX',
            # Industrials
            'TCL.AX', 'QUB.AX', 'BAP.AX', 'ALU.AX', 'TWE.AX',
            # Real Estate
            'GMG.AX', 'SCG.AX', 'VCX.AX', 'DMP.AX', 'GPT.AX',
            # Telecommunications
            'TLS.AX', 'TPG.AX', 'NEC.AX', 'VOC.AX', 'TNE.AX',
            # Utilities
            'AWC.AX', 'APA.AX', 'DUET.AX', 'SPK.AX', 'SKI.AX',
            # Additional major stocks
            'AMP.AX', 'ASX.AX', 'BKL.AX', 'BXB.AX', 'CAR.AX',
            'CPU.AX', 'DOW.AX', 'EVN.AX', 'FPH.AX', 'GMA.AX',
            'GUD.AX', 'HVN.AX', 'IEL.AX', 'IPL.AX', 'IRE.AX',
            'IVC.AX', 'LIC.AX', 'MIN.AX', 'MPL.AX', 'MSB.AX',
            'NAN.AX', 'NVT.AX', 'ORA.AX', 'ORI.AX', 'PMV.AX',
            'PPT.AX', 'PRU.AX', 'QAN.AX', 'RHC.AX', 'RRL.AX',
            'S32.AX', 'SGP.AX', 'SUN.AX', 'TAH.AX', 'TLS.AX',
            'TPG.AX', 'TWE.AX', 'URW.AX', 'VEA.AX', 'VOC.AX',
            'WSA.AX', 'WSP.AX', 'XRO.AX', 'YAL.AX', 'ZIM.AX'
        ]
        
        # Additional ASX stocks (expanded list)
        self.additional_asx_stocks = [
            '14D.AX', '1AD.AX', '1AE.AX', '1AI.AX', '1CG.AX',
            '1MC.AX', '1TT.AX', '29M.AX', '360.AX', '3DA.AX',
            '3DP.AX', '3PL.AX', '4DS.AX', '4DX.AX', '5EA.AX',
            '5GG.AX', '5GN.AX', '88E.AX', '8CO.AX', '8IH.AX',
            'A11.AX', 'A1G.AX', 'A1M.AX', 'A1N.AX', 'A2M.AX',
            'A3D.AX', 'A4N.AX', 'A8G.AX', 'AAC.AX', 'AAI.AX',
            'AAJ.AX', 'AAL.AX', 'AAM.AX', 'AAP.AX', 'AAR.AX',
            'AAU.AX', 'ABB.AX', 'ABE.AX', 'ABG.AX', 'ABV.AX',
            'ABX.AX', 'ABY.AX', 'ACE.AX', 'ACF.AX', 'ACL.AX',
            'ACM.AX', 'ACP.AX', 'ACQ.AX', 'ACR.AX', 'ACS.AX',
            'ACU.AX', 'ACW.AX', 'AD1.AX', 'AD8.AX', 'ADC.AX',
            'ADD.AX', 'ADG.AX', 'ADH.AX', 'ADN.AX', 'ADO.AX',
            'ADR.AX', 'ADS.AX', 'ADT.AX', 'ADV.AX', 'ADX.AX',
            'ADY.AX', 'AEE.AX', 'AEF.AX', 'AEI.AX', 'AER.AX',
            'AEV.AX', 'AFA.AX', 'AFG.AX', 'AFI.AX', 'AFL.AX',
            'AFP.AX', 'AGC.AX', 'AGD.AX', 'AGE.AX', 'AGH.AX',
            'AGI.AX', 'AGL.AX', 'AGN.AX', 'AGR.AX', 'AGY.AX',
            'AHC.AX', 'AHF.AX', 'AHI.AX', 'AHK.AX', 'AHL.AX',
            'AHN.AX', 'AHX.AX', 'AI1.AX', 'AIA.AX', 'AII.AX',
            'AIM.AX', 'AIQ.AX', 'AIS.AX', 'AIV.AX', 'AIZ.AX',
            'AJL.AX', 'AJX.AX', 'AKA.AX', 'AKG.AX', 'AKM.AX',
            'AKN.AX', 'AKO.AX', 'AKP.AX', 'AL3.AX', 'ALA.AX',
            'ALB.AX', 'ALC.AX', 'ALD.AX', 'ALI.AX', 'ALK.AX',
            'ALL.AX', 'ALM.AX', 'ALQ.AX', 'ALR.AX', 'ALV.AX',
            'ALX.AX', 'ALY.AX', 'AM5.AX', 'AM7.AX', 'AMA.AX',
            'AMC.AX', 'AMD.AX', 'AMH.AX', 'AMI.AX', 'AMN.AX',
            'AMO.AX', 'AMP.AX', 'AMS.AX', 'AMX.AX', 'AN1.AX',
            'ANG.AX', 'ANN.AX', 'ANO.AX', 'ANR.AX', 'ANX.AX',
            'ANZ.AX', 'AO1.AX', 'AOA.AX', 'AOF.AX', 'AOH.AX',
            'AON.AX', 'AOV.AX', 'APA.AX', 'APC.AX', 'APE.AX',
            'APL.AX', 'APW.AX', 'APX.AX', 'APZ.AX', 'AQC.AX',
            'AQD.AX', 'AQI.AX', 'AQN.AX', 'AQX.AX', 'AQZ.AX',
            'AR1.AX', 'AR3.AX', 'AR9.AX', 'ARA.AX', 'ARB.AX',
            'ARC.AX', 'ARD.AX', 'ARF.AX', 'ARG.AX', 'ARI.AX',
            'ARL.AX', 'ARN.AX', 'ARR.AX', 'ART.AX', 'ARU.AX',
            'ARV.AX', 'ARX.AX', 'AS1.AX', 'AS2.AX', 'ASB.AX',
            'ASE.AX', 'ASG.AX', 'ASH.AX', 'ASK.AX', 'ASL.AX',
            'ASM.AX', 'ASN.AX', 'ASP.AX', 'ASQ.AX', 'ASR.AX',
            'ASV.AX', 'ASX.AX', 'AT1.AX', 'ATA.AX', 'ATC.AX',
            'ATG.AX', 'ATH.AX', 'ATM.AX', 'ATP.AX', 'ATR.AX',
            'ATS.AX', 'ATV.AX', 'ATX.AX', 'AU1.AX', 'AUA.AX',
            'AUB.AX', 'AUC.AX', 'AUE.AX', 'AUG.AX', 'AUH.AX',
            'AUI.AX', 'AUK.AX', 'AUN.AX', 'AUQ.AX', 'AUR.AX',
            'AUZ.AX', 'AV1.AX', 'AVA.AX', 'AVD.AX', 'AVE.AX',
            'AVG.AX', 'AVH.AX', 'AVJ.AX', 'AVL.AX', 'AVM.AX',
            'AVR.AX', 'AVW.AX', 'AW1.AX', 'AWJ.AX', 'AX1.AX',
            'AX8.AX', 'AXE.AX', 'AXI.AX', 'AXL.AX', 'AXN.AX',
            'AXP.AX', 'AYA.AX', 'AYI.AX', 'AYM.AX', 'AYT.AX',
            'AZ9.AX', 'AZI.AX', 'AZJ.AX', 'AZL.AX', 'AZY.AX',
            'B4P.AX', 'BAP.AX', 'BAS.AX', 'BB1.AX', 'BBC.AX',
            'BBL.AX', 'BBN.AX', 'BBT.AX', 'BC8.AX', 'BCA.AX',
            'BCB.AX', 'BCC.AX', 'BCI.AX', 'BCK.AX', 'BCM.AX',
            'BCN.AX', 'BCT.AX', 'BDG.AX', 'BDM.AX', 'BDT.AX',
            'BDX.AX', 'BEL.AX', 'BEN.AX', 'BEO.AX', 'BET.AX',
            'BEZ.AX', 'BFC.AX', 'BFG.AX', 'BFL.AX', 'BGA.AX',
            'BGD.AX', 'BGE.AX', 'BGL.AX'
        ]
        
        # Combine all stocks
        self.all_asx_stocks = list(set(self.asx_stocks + self.additional_asx_stocks))

    def fetch_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Fetch stock data from Yahoo Finance"""
        try:
            logger.info(f"Fetching data for {ticker}")
            stock = yf.Ticker(ticker)
            
            # Get historical data for the last 2 years
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)
            
            data = stock.history(start=start_date, end=end_date)
            
            if data.empty or len(data) < 50:  # Need at least 50 days of data
                logger.warning(f"Insufficient data for {ticker}")
                return None
                
            # Ensure required columns exist
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_columns):
                logger.warning(f"Missing required columns for {ticker}")
                return None
                
            # Add Dividends and Stock Splits if missing
            if 'Dividends' not in data.columns:
                data['Dividends'] = 0
            if 'Stock Splits' not in data.columns:
                data['Stock Splits'] = 0
                
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None

    def make_prediction(self, ticker: str, data: pd.DataFrame) -> Optional[Dict]:
        """Make prediction for a single stock"""
        try:
            prediction_result = self.stock_predictor.predict_stock(ticker)
            
            if prediction_result and 'prediction' in prediction_result:
                return {
                    'ticker': ticker,
                    'prediction': prediction_result['prediction'],
                    'confidence': prediction_result['confidence'],
                    'current_price': prediction_result.get('current_price', 0),
                    'predicted_price': prediction_result.get('predicted_price', 0),
                    'timestamp': datetime.now()
                }
            else:
                logger.warning(f"No prediction result for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error making prediction for {ticker}: {str(e)}")
            return None

    def save_prediction_to_db(self, prediction_data: Dict):
        """Save prediction to database"""
        try:
            # Check if prediction already exists
            existing = self.db.query(StockPrediction).filter(
                StockPrediction.ticker == prediction_data['ticker']
            ).first()
            
            if existing:
                # Update existing prediction
                existing.prediction = prediction_data['prediction']
                existing.confidence = prediction_data['confidence']
                existing.current_price = prediction_data['current_price']
                existing.predicted_price = prediction_data['predicted_price']
                existing.updated_at = datetime.now()
            else:
                # Create new prediction
                new_prediction = StockPrediction(
                    ticker=prediction_data['ticker'],
                    prediction=prediction_data['prediction'],
                    confidence=prediction_data['confidence'],
                    current_price=prediction_data['current_price'],
                    predicted_price=prediction_data['predicted_price']
                )
                self.db.add(new_prediction)
            
            self.db.commit()
            logger.info(f"Saved prediction for {prediction_data['ticker']}")
            
        except Exception as e:
            logger.error(f"Error saving prediction for {prediction_data['ticker']}: {str(e)}")
            self.db.rollback()

    def update_all_predictions(self):
        """Update predictions for all ASX stocks"""
        logger.info(f"Starting prediction update for {len(self.all_asx_stocks)} ASX stocks")
        
        successful_predictions = 0
        failed_predictions = 0
        
        for i, ticker in enumerate(self.all_asx_stocks, 1):
            try:
                logger.info(f"Processing {i}/{len(self.all_asx_stocks)}: {ticker}")
                
                # Fetch data
                data = self.fetch_stock_data(ticker)
                if data is None:
                    failed_predictions += 1
                    continue
                
                # Make prediction
                prediction = self.make_prediction(ticker, data)
                if prediction is None:
                    failed_predictions += 1
                    continue
                
                # Save to database
                self.save_prediction_to_db(prediction)
                successful_predictions += 1
                
                # Add small delay to avoid rate limiting
                import time
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {str(e)}")
                failed_predictions += 1
                continue
        
        logger.info(f"Prediction update completed. Successful: {successful_predictions}, Failed: {failed_predictions}")
        return successful_predictions, failed_predictions

    def cleanup_old_predictions(self, days_old: int = 30):
        """Remove predictions older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = self.db.query(StockPrediction).filter(
                StockPrediction.updated_at < cutoff_date
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} old predictions")
            
        except Exception as e:
            logger.error(f"Error cleaning up old predictions: {str(e)}")
            self.db.rollback()

    def run(self):
        """Main execution method"""
        try:
            logger.info("Starting ASX prediction update process")
            
            # Update all predictions
            successful, failed = self.update_all_predictions()
            
            # Clean up old predictions
            self.cleanup_old_predictions()
            
            logger.info(f"ASX prediction update completed successfully")
            logger.info(f"Summary: {successful} successful, {failed} failed")
            
            return successful, failed
            
        except Exception as e:
            logger.error(f"Error in prediction update process: {str(e)}")
            return 0, len(self.all_asx_stocks)
        finally:
            self.db.close()

def main():
    """Main function"""
    updater = ASXPredictionUpdater()
    successful, failed = updater.run()
    
    # Exit with appropriate code
    if failed == 0:
        sys.exit(0)
    elif successful > 0:
        sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # Complete failure

if __name__ == "__main__":
    main() 