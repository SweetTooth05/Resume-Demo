#!/usr/bin/env python3
"""
PostgreSQL database setup script
Creates database, user, and tables for the finance app
"""

import subprocess
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_postgres_database():
    """Setup PostgreSQL database and user"""
    
    # Database configuration
    DB_NAME = "finance_app"
    DB_USER = "postgres"
    DB_PASSWORD = "postgres"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    
    try:
        # Test connection to PostgreSQL
        logger.info("Testing PostgreSQL connection...")
        
        # Try to connect to default postgres database first
        test_engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres")
        
        with test_engine.connect() as conn:
            # Check if finance_app database exists
            result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'finance_app'"))
            db_exists = result.fetchone() is not None
            
            if not db_exists:
                logger.info("Creating finance_app database...")
                # Create the database
                conn.execute(text("COMMIT"))  # Close any open transaction
                conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
                logger.info("Database created successfully!")
            else:
                logger.info("Database finance_app already exists")
        
        # Now connect to the finance_app database
        engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        
        # Import and create tables
        from app.core.database import Base
        from app.models.stock import StockHolding, StockPrediction, TopStockRecommendation
        from app.models.financial import Income, Expense, Asset, Debt
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully!")
        
        # Create session and populate with sample data
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if data already exists
            existing_recommendations = db.query(TopStockRecommendation).count()
            if existing_recommendations > 0:
                logger.info("Database already contains data. Skipping initialization.")
                return
            
            logger.info("Populating database with sample data...")
            
            # Sample top stock recommendations
            top_recommendations = [
                TopStockRecommendation(
                    ticker="BHP.AX",
                    name="BHP Group Limited",
                    prediction="BUY",
                    confidence=0.92,
                    current_price=48.75,
                    predicted_price=52.50,
                    change=3.25,
                    change_percent=7.14,
                    rank=1
                ),
                TopStockRecommendation(
                    ticker="CSL.AX",
                    name="CSL Limited",
                    prediction="BUY",
                    confidence=0.89,
                    current_price=245.80,
                    predicted_price=260.00,
                    change=5.20,
                    change_percent=2.16,
                    rank=2
                ),
                TopStockRecommendation(
                    ticker="WES.AX",
                    name="Wesfarmers Limited",
                    prediction="BUY",
                    confidence=0.87,
                    current_price=52.40,
                    predicted_price=56.00,
                    change=1.80,
                    change_percent=3.55,
                    rank=3
                ),
                TopStockRecommendation(
                    ticker="RIO.AX",
                    name="Rio Tinto Limited",
                    prediction="BUY",
                    confidence=0.85,
                    current_price=120.50,
                    predicted_price=128.00,
                    change=2.10,
                    change_percent=4.20,
                    rank=4
                ),
                TopStockRecommendation(
                    ticker="CBA.AX",
                    name="Commonwealth Bank of Australia",
                    prediction="BUY",
                    confidence=0.83,
                    current_price=95.20,
                    predicted_price=98.50,
                    change=1.50,
                    change_percent=1.65,
                    rank=5
                ),
                TopStockRecommendation(
                    ticker="ANZ.AX",
                    name="Australia and New Zealand Banking Group",
                    prediction="BUY",
                    confidence=0.81,
                    current_price=28.50,
                    predicted_price=29.85,
                    change=0.85,
                    change_percent=3.08,
                    rank=6
                ),
                TopStockRecommendation(
                    ticker="NAB.AX",
                    name="National Australia Bank",
                    prediction="BUY",
                    confidence=0.79,
                    current_price=32.80,
                    predicted_price=34.50,
                    change=0.95,
                    change_percent=2.98,
                    rank=7
                ),
                TopStockRecommendation(
                    ticker="WBC.AX",
                    name="Westpac Banking Corporation",
                    prediction="BUY",
                    confidence=0.77,
                    current_price=24.20,
                    predicted_price=25.50,
                    change=0.65,
                    change_percent=2.76,
                    rank=8
                ),
                TopStockRecommendation(
                    ticker="MQG.AX",
                    name="Macquarie Group Limited",
                    prediction="BUY",
                    confidence=0.75,
                    current_price=185.30,
                    predicted_price=195.00,
                    change=3.20,
                    change_percent=1.76,
                    rank=9
                ),
                TopStockRecommendation(
                    ticker="TLS.AX",
                    name="Telstra Group Limited",
                    prediction="BUY",
                    confidence=0.73,
                    current_price=4.15,
                    predicted_price=4.35,
                    change=0.05,
                    change_percent=1.19,
                    rank=10
                ),
                TopStockRecommendation(
                    ticker="WOW.AX",
                    name="Woolworths Group Limited",
                    prediction="BUY",
                    confidence=0.71,
                    current_price=35.80,
                    predicted_price=37.20,
                    change=0.90,
                    change_percent=2.51,
                    rank=11
                ),
                TopStockRecommendation(
                    ticker="COL.AX",
                    name="Coles Group Limited",
                    prediction="BUY",
                    confidence=0.69,
                    current_price=16.45,
                    predicted_price=17.10,
                    change=0.35,
                    change_percent=2.13,
                    rank=12
                ),
                TopStockRecommendation(
                    ticker="TCL.AX",
                    name="Transurban Group",
                    prediction="BUY",
                    confidence=0.67,
                    current_price=13.20,
                    predicted_price=13.85,
                    change=0.25,
                    change_percent=1.89,
                    rank=13
                ),
                TopStockRecommendation(
                    ticker="QBE.AX",
                    name="QBE Insurance Group Limited",
                    prediction="BUY",
                    confidence=0.65,
                    current_price=15.80,
                    predicted_price=16.45,
                    change=0.30,
                    change_percent=1.90,
                    rank=14
                ),
                TopStockRecommendation(
                    ticker="IAG.AX",
                    name="Insurance Australia Group Limited",
                    prediction="BUY",
                    confidence=0.63,
                    current_price=5.95,
                    predicted_price=6.20,
                    change=0.15,
                    change_percent=2.52,
                    rank=15
                ),
                TopStockRecommendation(
                    ticker="SGP.AX",
                    name="Stockland Corporation Limited",
                    prediction="BUY",
                    confidence=0.61,
                    current_price=4.25,
                    predicted_price=4.45,
                    change=0.10,
                    change_percent=2.35,
                    rank=16
                ),
                TopStockRecommendation(
                    ticker="GMG.AX",
                    name="Goodman Group",
                    prediction="BUY",
                    confidence=0.59,
                    current_price=28.90,
                    predicted_price=30.15,
                    change=0.60,
                    change_percent=2.08,
                    rank=17
                ),
                TopStockRecommendation(
                    ticker="REA.AX",
                    name="REA Group Limited",
                    prediction="BUY",
                    confidence=0.57,
                    current_price=165.40,
                    predicted_price=172.00,
                    change=2.80,
                    change_percent=1.69,
                    rank=18
                ),
                TopStockRecommendation(
                    ticker="CAR.AX",
                    name="Carsales.com Limited",
                    prediction="BUY",
                    confidence=0.55,
                    current_price=32.15,
                    predicted_price=33.50,
                    change=0.65,
                    change_percent=2.02,
                    rank=19
                ),
                TopStockRecommendation(
                    ticker="NCM.AX",
                    name="Newcrest Mining Limited",
                    prediction="BUY",
                    confidence=0.53,
                    current_price=28.75,
                    predicted_price=30.20,
                    change=0.85,
                    change_percent=2.96,
                    rank=20
                )
            ]
            
            # Add top recommendations to database
            for rec in top_recommendations:
                db.add(rec)
            
            # Sample stock predictions for search functionality
            stock_predictions = [
                StockPrediction(
                    ticker="BHP.AX",
                    name="BHP Group Limited",
                    prediction="BUY",
                    confidence=0.92,
                    current_price=48.75,
                    predicted_price=52.50
                ),
                StockPrediction(
                    ticker="CSL.AX",
                    name="CSL Limited",
                    prediction="BUY",
                    confidence=0.89,
                    current_price=245.80,
                    predicted_price=260.00
                ),
                StockPrediction(
                    ticker="CBA.AX",
                    name="Commonwealth Bank of Australia",
                    prediction="BUY",
                    confidence=0.83,
                    current_price=95.20,
                    predicted_price=98.50
                ),
                StockPrediction(
                    ticker="ANZ.AX",
                    name="Australia and New Zealand Banking Group",
                    prediction="BUY",
                    confidence=0.81,
                    current_price=28.50,
                    predicted_price=29.85
                ),
                StockPrediction(
                    ticker="TLS.AX",
                    name="Telstra Group Limited",
                    prediction="BUY",
                    confidence=0.73,
                    current_price=4.15,
                    predicted_price=4.35
                ),
                StockPrediction(
                    ticker="WOW.AX",
                    name="Woolworths Group Limited",
                    prediction="BUY",
                    confidence=0.71,
                    current_price=35.80,
                    predicted_price=37.20
                ),
                StockPrediction(
                    ticker="COL.AX",
                    name="Coles Group Limited",
                    prediction="BUY",
                    confidence=0.69,
                    current_price=16.45,
                    predicted_price=17.10
                )
            ]
            
            # Add stock predictions to database
            for pred in stock_predictions:
                db.add(pred)
            
            # Sample financial data
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
            logger.info("Database initialization completed successfully!")
            
        except Exception as e:
            logger.error(f"Error populating database: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error setting up PostgreSQL database: {str(e)}")
        logger.error("Please ensure PostgreSQL is running and accessible")
        logger.error("You may need to:")
        logger.error("1. Start PostgreSQL service: sudo service postgresql start")
        logger.error("2. Set up PostgreSQL user: sudo -u postgres createuser --interactive")
        logger.error("3. Set password for postgres user: sudo -u postgres psql -c \"ALTER USER postgres PASSWORD 'postgres';\"")
        raise

if __name__ == "__main__":
    setup_postgres_database() 