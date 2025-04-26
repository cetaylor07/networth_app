from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date
from pydantic import BaseModel
from database import get_db, Account, BalanceHistory, NetWorthHistory

app = FastAPI()

# --- Pydantic models ---
class AccountCreate(BaseModel):
    account_name: str
    account_type:str

class BalanceUpdate(BaseModel):
    date: date
    balance: float

# --- API Endpoints ---

@app.post("/add-account/")
def add_account(account: AccountCreate, db: Session = Depends(get_db)):
    existing_account = db.query(Account).filter(Account.account_name == account.account_name).first()
    if existing_account:
        return {"message": "Account already exists!"}
    new_account = Account(account_name=account.account_name, account_type=account.account_type)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return {"message": "Account added successfully!"}

@app.post("/update-balance/{account_name}")
def update_balance(account_name: str, balance_update: BalanceUpdate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_name == account_name).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    new_balance = BalanceHistory(account_id=account.id, date=balance_update.date, balance=balance_update.balance)
    db.add(new_balance)
    db.commit()
    return {"message": "Balance updated successfully!"}

@app.get("/accounts/")
def get_accounts(db: Session = Depends(get_db)):
    accounts = db.query(Account).all()
    account_list = []
    for account in accounts:
        # Get the most recent balance
        latest_balance = (
            db.query(BalanceHistory)
            .filter(BalanceHistory.account_id == account.id)
            .order_by(BalanceHistory.date.desc())
            .first()
        )
        
        account_list.append({
            "account_name": account.account_name,
            "account_type": account.account_type,
            "balance": latest_balance.balance if latest_balance else 0.0  # Default to 0 if no balance history
        })

    return account_list

@app.get("/balances/{account_name}")
def get_balances(account_name: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_name == account_name).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    balances = db.query(BalanceHistory).filter(BalanceHistory.account_id == account.id).all()
    return [{"date": bal.date, "balance": bal.balance} for bal in balances]

@app.get("/net-worth/")
def get_net_worth(db: Session = Depends(get_db)):
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
    return {"net_worth": net_worth or 0}

@app.get("/net-worth-history/")
def get_net_worth_history(db: Session = Depends(get_db)):
    history = db.query(NetWorthHistory).all()
    return [{"date": h.date, "total_net_worth": h.total_net_worth} for h in history]

@app.delete("/delete-account/{account_name}")
def delete_account(account_name: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_name == account_name).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account deleted successfully!"}

