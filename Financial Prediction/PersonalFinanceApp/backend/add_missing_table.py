#!/usr/bin/env python3
"""
Add missing table script
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_missing_table():
    """Add the missing top_stock_recommendations table"""
    
    # Set password for psycopg2
    os.environ['PGPASSWORD'] = 'postgres'
    
    # Database configuration
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/finance_app"
    
    try:
        logger.info("Connecting to PostgreSQL...")
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            logger.info("Connection successful!")
            
            # Check if top_stock_recommendations table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'top_stock_recommendations'
            """))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                logger.info("Creating top_stock_recommendations table...")
                
                # Create the table manually
                conn.execute(text("""
                    CREATE TABLE top_stock_recommendations (
                        id SERIAL PRIMARY KEY,
                        ticker VARCHAR(10) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        prediction VARCHAR(10) NOT NULL,
                        confidence FLOAT NOT NULL,
                        current_price FLOAT NOT NULL,
                        predicted_price FLOAT NOT NULL,
                        change FLOAT NOT NULL DEFAULT 0.0,
                        change_percent FLOAT NOT NULL DEFAULT 0.0,
                        rank INTEGER NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX ix_top_stock_recommendations_ticker ON top_stock_recommendations (ticker)"))
                conn.execute(text("CREATE INDEX ix_top_stock_recommendations_rank ON top_stock_recommendations (rank)"))
                
                conn.commit()
                logger.info("Table created successfully!")
                
                # Add sample data
                logger.info("Adding sample data...")
                
                sample_data = [
                    ("BHP.AX", "BHP Group Limited", "BUY", 0.92, 48.75, 52.50, 3.25, 7.14, 1),
                    ("CSL.AX", "CSL Limited", "BUY", 0.89, 245.80, 260.00, 5.20, 2.16, 2),
                    ("WES.AX", "Wesfarmers Limited", "BUY", 0.87, 52.40, 56.00, 1.80, 3.55, 3),
                    ("RIO.AX", "Rio Tinto Limited", "BUY", 0.85, 120.50, 128.00, 2.10, 4.20, 4),
                    ("CBA.AX", "Commonwealth Bank of Australia", "BUY", 0.83, 95.20, 98.50, 1.50, 1.65, 5),
                    ("ANZ.AX", "Australia and New Zealand Banking Group", "BUY", 0.81, 28.50, 29.85, 0.85, 3.08, 6),
                    ("NAB.AX", "National Australia Bank", "BUY", 0.79, 32.80, 34.50, 0.95, 2.98, 7),
                    ("WBC.AX", "Westpac Banking Corporation", "BUY", 0.77, 24.20, 25.50, 0.65, 2.76, 8),
                    ("MQG.AX", "Macquarie Group Limited", "BUY", 0.75, 185.30, 195.00, 3.20, 1.76, 9),
                    ("TLS.AX", "Telstra Group Limited", "BUY", 0.73, 4.15, 4.35, 0.05, 1.19, 10),
                    ("WOW.AX", "Woolworths Group Limited", "BUY", 0.71, 35.80, 37.20, 0.90, 2.51, 11),
                    ("COL.AX", "Coles Group Limited", "BUY", 0.69, 16.45, 17.10, 0.35, 2.13, 12),
                    ("TCL.AX", "Transurban Group", "BUY", 0.67, 13.20, 13.85, 0.25, 1.89, 13),
                    ("QBE.AX", "QBE Insurance Group Limited", "BUY", 0.65, 15.80, 16.45, 0.30, 1.90, 14),
                    ("IAG.AX", "Insurance Australia Group Limited", "BUY", 0.63, 5.95, 6.20, 0.15, 2.52, 15),
                    ("SGP.AX", "Stockland Corporation Limited", "BUY", 0.61, 4.25, 4.45, 0.10, 2.35, 16),
                    ("GMG.AX", "Goodman Group", "BUY", 0.59, 28.90, 30.15, 0.60, 2.08, 17),
                    ("REA.AX", "REA Group Limited", "BUY", 0.57, 165.40, 172.00, 2.80, 1.69, 18),
                    ("CAR.AX", "Carsales.com Limited", "BUY", 0.55, 32.15, 33.50, 0.65, 2.02, 19),
                    ("NCM.AX", "Newcrest Mining Limited", "BUY", 0.53, 28.75, 30.20, 0.85, 2.96, 20)
                ]
                
                for ticker, name, prediction, confidence, current_price, predicted_price, change, change_percent, rank in sample_data:
                    conn.execute(text("""
                        INSERT INTO top_stock_recommendations 
                        (ticker, name, prediction, confidence, current_price, predicted_price, change, change_percent, rank)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """), (ticker, name, prediction, confidence, current_price, predicted_price, change, change_percent, rank))
                
                conn.commit()
                logger.info("Sample data added successfully!")
                
            else:
                logger.info("Table top_stock_recommendations already exists")
        
        # Test the connection with our app
        logger.info("Testing app database connection...")
        from app.core.database import get_db
        from app.models.stock import TopStockRecommendation
        
        db = next(get_db())
        count = db.query(TopStockRecommendation).count()
        logger.info(f"Top recommendations in database: {count}")
        
        # Test portfolio endpoint
        logger.info("Testing portfolio endpoint...")
        from app.api.v1.endpoints.portfolio import get_portfolio
        from app.core.database import get_db
        
        portfolio_result = get_portfolio(next(get_db()))
        logger.info("Portfolio endpoint working!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    add_missing_table() 