# Manual Setup Guide for WSL Testing

This guide will help you run the Personal Finance App directly in WSL without Docker for quick testing.

## Prerequisites

1. **WSL Ubuntu** (already installed)
2. **Python 3.11+** (already available in Ubuntu)
3. **Node.js 18+** (we'll install this)
4. **PostgreSQL** (we'll install this)

## Step 1: Install Dependencies

### Install Node.js and npm
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install nodejs -y
```

### Install PostgreSQL
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Install Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Setup Database

### Create database and user
```bash
sudo -u postgres psql
```

In the PostgreSQL prompt:
```sql
CREATE DATABASE personal_finance;
CREATE USER finance_user WITH PASSWORD 'finance_password';
GRANT ALL PRIVILEGES ON DATABASE personal_finance TO finance_user;
\q
```

## Step 3: Configure Environment

Create a `.env` file in the backend directory:
```bash
cd backend
cat > .env << EOF
DATABASE_URL=postgresql://finance_user:finance_password@localhost:5432/personal_finance
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
YAHOO_FINANCE_API_KEY=
MODEL_PATH=../FinanceApp/processed_finance_data/models/xgboost_stock_predictor.pkl
REDIS_URL=redis://localhost:6379
EOF
```

## Step 4: Setup Frontend

```bash
cd ../frontend
npm install
```

## Step 5: Run the Application

### Terminal 1: Start Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Start Frontend
```bash
cd frontend
npm start
```

## Step 6: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Troubleshooting

### If you get permission errors:
```bash
sudo chown -R $USER:$USER /mnt/c/Users/kevil/OneDrive/Documents/Fish\ Code/PersonalFinanceApp
```

### If PostgreSQL connection fails:
```bash
sudo systemctl status postgresql
sudo systemctl restart postgresql
```

### If npm install fails:
```bash
sudo apt-get install build-essential -y
```

## Quick Test

Once everything is running, you can test the stock predictor integration:

```bash
cd backend
python -c "
from app.ml.stock_predictor import stock_predictor
print('Model loaded successfully!')
print('Model info:', stock_predictor.get_model_info())
prediction = stock_predictor.predict_stock('BHP.AX')
print('BHP prediction:', prediction)
"
```

## Benefits of This Approach

1. **Faster setup** - No Docker build times
2. **Easier debugging** - Direct access to logs and processes
3. **Closer to production** - Similar to your Ubuntu server setup
4. **Immediate testing** - Can test individual components quickly

## Next Steps

Once you've confirmed everything works in WSL, you can:
1. Deploy the same setup to your Ubuntu server
2. Switch to Docker for production deployment
3. Add additional features and testing 