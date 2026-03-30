#!/usr/bin/env python3
"""
Fix database tables script
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    """Fix database tables"""
    
    # Set password for psycopg2
    os.environ['PGPASSWORD'] = 'postgres'
    
    # Database configuration
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/finance_app"
    
    try:
        logger.info("Connecting to PostgreSQL...")
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            logger.info("Connection successful!")
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            logger.info(f"Existing tables: {tables}")
            
            if not tables:
                logger.info("No tables found. Creating tables...")
                
                # Import and create tables
                from app.core.database import Base
                from app.models.stock import StockHolding, StockPrediction, TopStockRecommendation
                from app.models.financial import Income, Expense, Asset, Debt
                
                Base.metadata.create_all(bind=engine)
                logger.info("Tables created successfully!")
                
                # Populate with sample data
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                db = SessionLocal()
                
                try:
                    logger.info("Adding sample data...")
                    
                    # Add a simple test record
                    test_rec = TopStockRecommendation(
                        ticker="TEST.AX",
                        name="Test Company",
                        prediction="BUY",
                        confidence=0.95,
                        current_price=10.00,
                        predicted_price=11.00,
                        change=1.00,
                        change_percent=10.00,
                        rank=1
                    )
                    db.add(test_rec)
                    db.commit()
                    logger.info("Sample data added successfully!")
                    
                except Exception as e:
                    logger.error(f"Error adding sample data: {e}")
                    db.rollback()
                finally:
                    db.close()
            else:
                logger.info("Tables already exist")
        
        # Test the connection with our app
        logger.info("Testing app database connection...")
        from app.core.database import get_db
        from app.models.stock import TopStockRecommendation
        
        db = next(get_db())
        count = db.query(TopStockRecommendation).count()
        logger.info(f"Top recommendations in database: {count}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    fix_database() 