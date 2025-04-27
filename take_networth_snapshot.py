import sys
import logging
from datetime import date
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./logs/net_worth_snapshot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("net_worth_snapshot")

# Import your database models
# This assumes your models are defined in database.py
try:
    from database import Base, Account, BalanceHistory, NetWorthHistory
except ImportError:
    logger.error("Could not import database models. Make sure 'database.py' is in the same directory or in your Python path.")
    sys.exit(1)

# Database connection - adjust this to match your actual database configuration
DB_URL = "sqlite:///./networth.db" 

def get_db_session():
    """Create and return a new database session."""
    try:
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        sys.exit(1)

def get_net_worth(db):
    """Calculate current net worth based on latest account balances."""
    try:
        # For each account, get the latest balance entry
        latest_balances = (
            db.query(BalanceHistory.account_id, func.max(BalanceHistory.date).label("latest_date"))
            .group_by(BalanceHistory.account_id)
            .subquery()
        )
        
        net_worth = (
            db.query(func.sum(BalanceHistory.balance))
            .join(
                latest_balances,
                (BalanceHistory.account_id == latest_balances.c.account_id) &
                (BalanceHistory.date == latest_balances.c.latest_date)
            )
            .scalar()
        )
        
        return net_worth or 0
    except Exception as e:
        logger.error(f"Error calculating net worth: {str(e)}")
        return 0

def take_snapshot():
    """Take a snapshot of current net worth and store it in the database."""
    db = get_db_session()
    
    try:
        today = date.today()
        logger.info(f"Taking net worth snapshot for {today}")
        
        # Check if we already have an entry for today
        existing_entry = db.query(NetWorthHistory).filter(NetWorthHistory.date == today).first()
        
        if existing_entry:
            logger.info(f"Snapshot for {today} already exists with value {existing_entry.total_net_worth}")
            return
        
        # Calculate current net worth
        net_worth = get_net_worth(db)
        
        # Create new history entry
        new_entry = NetWorthHistory(date=today, total_net_worth=net_worth)
        db.add(new_entry)
        db.commit()
        
        logger.info(f"Successfully recorded net worth snapshot: {net_worth}")
    except Exception as e:
        logger.error(f"Error recording snapshot: {str(e)}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main function to run the snapshot."""
    logger.info("Starting net worth snapshot process")
    take_snapshot()
    logger.info("Snapshot process completed")

if __name__ == "__main__":
    main()