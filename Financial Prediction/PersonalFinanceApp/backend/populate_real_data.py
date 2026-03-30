#!/usr/bin/env python3
"""
Populate database with real stock predictions using actual ASX data
"""

import os
import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
import yfinance as yf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_real_data():
    """Populate database with real stock predictions"""
    
    # Set password for psycopg2
    os.environ['PGPASSWORD'] = 'postgres'
    
    # Database configuration
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/finance_app"
    
    try:
        logger.info("Connecting to PostgreSQL...")
        engine = create_engine(DATABASE_URL)
        
        # Import models
        from app.core.database import Base
        from app.models.stock import StockHolding, StockPrediction, TopStockRecommendation
        from app.models.financial import Income, Expense, Asset, Debt
        
        # Import the real stock predictor
        from app.ml.stock_predictor import stock_predictor
        
        # Load ASX companies list
        asx_file = os.path.join(
            os.path.dirname(__file__), 
            '../../../FinanceApp/ASXListedCompanies.csv'
        )
        
        if os.path.exists(asx_file):
            logger.info("Loading ASX companies list...")
            asx_companies = pd.read_csv(asx_file)
            logger.info(f"Loaded {len(asx_companies)} ASX companies")
        else:
            logger.warning("ASX companies file not found, using default list")
            # Default ASX companies if file not found
            default_companies = [
                "BHP.AX", "CSL.AX", "WES.AX", "RIO.AX", "CBA.AX", "ANZ.AX", "NAB.AX", 
                "WBC.AX", "MQG.AX", "TLS.AX", "WOW.AX", "COL.AX", "TCL.AX", "QBE.AX", 
                "IAG.AX", "SGP.AX", "GMG.AX", "REA.AX", "CAR.AX", "NCM.AX"
            ]
            asx_companies = pd.DataFrame({
                'ASX code': [code.replace('.AX', '') for code in default_companies],
                'Company name': [f"{code.replace('.AX', '')} Company" for code in default_companies]
            })
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            logger.info("Starting real stock predictions...")
            
            # Get top 20 companies by market cap or use first 20
            top_companies = asx_companies.head(20)
            
            top_recommendations = []
            stock_predictions = []
            
            for idx, row in top_companies.iterrows():
                ticker = f"{row['ASX code']}.AX"
                company_name = row['Company name']
                
                logger.info(f"Processing {ticker} - {company_name}")
                
                try:
                    # Get real prediction using the trained model
                    prediction_result = stock_predictor.predict_stock(ticker)
                    
                    if prediction_result:
                        # Create top recommendation
                        top_rec = TopStockRecommendation(
                            ticker=ticker,
                            name=company_name,
                            prediction=prediction_result['prediction'],
                            confidence=prediction_result['confidence'],
                            current_price=prediction_result['current_price'],
                            predicted_price=prediction_result['predicted_price'],
                            change=prediction_result['change'],
                            change_percent=prediction_result['change_percent'],
                            rank=idx + 1
                        )
                        top_recommendations.append(top_rec)
                        
                        # Create stock prediction for search
                        stock_pred = StockPrediction(
                            ticker=ticker,
                            name=company_name,
                            prediction=prediction_result['prediction'],
                            confidence=prediction_result['confidence'],
                            current_price=prediction_result['current_price'],
                            predicted_price=prediction_result['predicted_price']
                        )
                        stock_predictions.append(stock_pred)
                        
                        logger.info(f"✅ {ticker}: {prediction_result['prediction']} (confidence: {prediction_result['confidence']:.2f})")
                    else:
                        logger.warning(f"⚠️ No prediction available for {ticker}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {ticker}: {e}")
                    continue
            
            # Clear existing data
            logger.info("Clearing existing data...")
            db.query(TopStockRecommendation).delete()
            db.query(StockPrediction).delete()
            db.commit()
            
            # Add real predictions to database
            logger.info(f"Adding {len(top_recommendations)} top recommendations...")
            for rec in top_recommendations:
                db.add(rec)
            
            logger.info(f"Adding {len(stock_predictions)} stock predictions...")
            for pred in stock_predictions:
                db.add(pred)
            
            # Add sample financial data
            logger.info("Adding sample financial data...")
            sample_income = Income(name="Salary", amount=5000, category="Salary")
            sample_expense = Expense(name="Rent", amount=1500, category="Housing")
            sample_asset = Asset(name="Savings Account", amount=10000, category="Cash")
            sample_debt = Debt(name="Credit Card", amount=2000, category="Credit Card")
            
            db.add(sample_income)
            db.add(sample_expense)
            db.add(sample_asset)
            db.add(sample_debt)
            
            # Commit all changes
            db.commit()
            logger.info("✅ Real data populated successfully!")
            
            # Show summary
            logger.info("📊 Summary:")
            logger.info(f"   - Top recommendations: {len(top_recommendations)}")
            logger.info(f"   - Stock predictions: {len(stock_predictions)}")
            logger.info(f"   - Model accuracy: {stock_predictor.get_model_accuracy():.2%}")
            
        except Exception as e:
            logger.error(f"❌ Error populating data: {e}")
            db.rollback()
            raise
        finally:
            db.close()
        
        logger.info("🎉 Database populated with real data!")
        logger.info("You can now start the backend server with: uvicorn app.main:app --reload")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    populate_real_data() 