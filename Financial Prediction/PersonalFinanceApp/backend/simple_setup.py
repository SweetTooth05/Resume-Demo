#!/usr/bin/env python3
"""
Simple database setup script
"""

import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Simple database setup"""
    
    # Set password for psycopg2
    os.environ['PGPASSWORD'] = 'postgres'
    
    # Database configuration
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/finance_app"
    
    try:
        logger.info("Setting up PostgreSQL database...")
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            logger.info("✅ PostgreSQL connection successful!")
            
            # Drop all existing tables to start fresh
            logger.info("Dropping existing tables...")
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            for table in existing_tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            conn.commit()
            logger.info("✅ Existing tables dropped")
        
        # Import all models
        from app.core.database import Base
        from app.models.stock import StockHolding, StockPrediction, TopStockRecommendation, StockTransaction
        from app.models.financial import Income, Expense, Asset, Debt
        
        # Create all tables
        logger.info("Creating all tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully!")
        
        # Verify tables were created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"✅ Tables created: {tables}")
        
        # Create session and populate with sample data
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            logger.info("Adding sample data...")
            
            # Sample top stock recommendations
            top_recommendations = [
                TopStockRecommendation(
                    ticker="BHP.AX", name="BHP Group Limited", prediction="BUY", confidence=0.92,
                    current_price=48.75, predicted_price=52.50, change=3.25, change_percent=7.14, rank=1
                ),
                TopStockRecommendation(
                    ticker="CSL.AX", name="CSL Limited", prediction="BUY", confidence=0.89,
                    current_price=245.80, predicted_price=260.00, change=5.20, change_percent=2.16, rank=2
                ),
                TopStockRecommendation(
                    ticker="WES.AX", name="Wesfarmers Limited", prediction="BUY", confidence=0.87,
                    current_price=52.40, predicted_price=56.00, change=1.80, change_percent=3.55, rank=3
                ),
                TopStockRecommendation(
                    ticker="RIO.AX", name="Rio Tinto Limited", prediction="BUY", confidence=0.85,
                    current_price=120.50, predicted_price=128.00, change=2.10, change_percent=4.20, rank=4
                ),
                TopStockRecommendation(
                    ticker="CBA.AX", name="Commonwealth Bank of Australia", prediction="BUY", confidence=0.83,
                    current_price=95.20, predicted_price=98.50, change=1.50, change_percent=1.65, rank=5
                ),
                TopStockRecommendation(
                    ticker="ANZ.AX", name="Australia and New Zealand Banking Group", prediction="BUY", confidence=0.81,
                    current_price=28.50, predicted_price=29.85, change=0.85, change_percent=3.08, rank=6
                )
            ]
            
            # Add top recommendations
            for rec in top_recommendations:
                db.add(rec)
            
            # Sample stock predictions for search
            stock_predictions = [
                StockPrediction(ticker="BHP.AX", name="BHP Group Limited", prediction="BUY", confidence=0.92, current_price=48.75, predicted_price=52.50),
                StockPrediction(ticker="CSL.AX", name="CSL Limited", prediction="BUY", confidence=0.89, current_price=245.80, predicted_price=260.00),
                StockPrediction(ticker="CBA.AX", name="Commonwealth Bank of Australia", prediction="BUY", confidence=0.83, current_price=95.20, predicted_price=98.50),
                StockPrediction(ticker="ANZ.AX", name="Australia and New Zealand Banking Group", prediction="BUY", confidence=0.81, current_price=28.50, predicted_price=29.85),
                StockPrediction(ticker="TLS.AX", name="Telstra Group Limited", prediction="BUY", confidence=0.73, current_price=4.15, predicted_price=4.35),
                StockPrediction(ticker="WOW.AX", name="Woolworths Group Limited", prediction="BUY", confidence=0.71, current_price=35.80, predicted_price=37.20),
                StockPrediction(ticker="COL.AX", name="Coles Group Limited", prediction="BUY", confidence=0.69, current_price=16.45, predicted_price=17.10)
            ]
            
            # Add stock predictions
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
            logger.info("✅ Sample data added successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error adding sample data: {e}")
            db.rollback()
            raise
        finally:
            db.close()
        
        logger.info("🎉 Database setup completed successfully!")
        logger.info("You can now start the backend server with: uvicorn app.main:app --reload")
        
    except Exception as e:
        logger.error(f"❌ Error setting up database: {e}")
        raise

if __name__ == "__main__":
    setup_database() 