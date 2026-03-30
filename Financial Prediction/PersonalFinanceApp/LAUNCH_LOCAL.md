# 🚀 Local Launch Guide

This guide will help you launch the Personal Finance App locally for testing.

## 📋 Prerequisites

Before starting, ensure you have:

- **Docker & Docker Compose** installed
- **Python 3.11+** (for manual setup)
- **Node.js 18+** (for manual setup)
- **PostgreSQL** (for manual setup)
- **Your trained XGBoost model** in `../FinanceApp/processed_finance_data/models/xgboost_stock_predictor.pkl`

## 🐳 Option 1: Docker (Recommended)

### Quick Start with Docker

```bash
# 1. Navigate to the project directory
cd PersonalFinanceApp

# 2. Start all services
docker-compose up -d

# 3. Check if services are running
docker-compose ps

# 4. View logs if needed
docker-compose logs -f
```

### Access the Application

Once running, you can access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (PostgreSQL)

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (will delete database data)
docker-compose down -v
```

## 🛠️ Option 2: Manual Setup

### Step 1: Backend Setup

```bash
# 1. Navigate to backend directory
cd PersonalFinanceApp/backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
cp .env.example .env
# Edit .env with your database settings

# 6. Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Frontend Setup

```bash
# 1. Open a new terminal and navigate to frontend directory
cd PersonalFinanceApp/frontend

# 2. Install dependencies
npm install

# 3. Start the development server
npm start
```

### Step 3: Database Setup

```bash
# 1. Install PostgreSQL (if not already installed)
# On Ubuntu:
sudo apt install postgresql postgresql-contrib

# On macOS with Homebrew:
brew install postgresql

# On Windows: Download from https://www.postgresql.org/download/windows/

# 2. Start PostgreSQL service
# On Ubuntu:
sudo systemctl start postgresql

# On macOS:
brew services start postgresql

# 3. Create database and user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE finance_app;
CREATE USER finance_user WITH PASSWORD 'finance_password';
GRANT ALL PRIVILEGES ON DATABASE finance_app TO finance_user;
\q
```

## 🧪 Testing the Integration

### Test XGBoost Model Integration

```bash
# Run the integration test
cd PersonalFinanceApp
python test_integration.py
```

Expected output:
```
🧪 Testing XGBoost Model Integration
==================================================
1. Testing model loading...
   Model loaded: True
   Model type: XGBoost
   ✅ Model loaded successfully!

2. Testing stock prediction...
   Predicting BHP.AX...
   ✅ BHP.AX: BUY (confidence: 0.75)
      Current price: $45.20
   Predicting CBA.AX...
   ✅ CBA.AX: HOLD (confidence: 0.68)
      Current price: $98.45
   ...

🎉 Integration test completed!
```

### Test API Endpoints

```bash
# Test the API (replace with your actual token)
curl -X GET "http://localhost:8000/api/v1/stocks/model/info" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# Database
DATABASE_URL=postgresql://finance_user:finance_password@localhost/finance_app

# JWT Secret (change in production)
SECRET_KEY=your-super-secret-key-change-this

# Yahoo Finance API (optional)
YAHOO_FINANCE_API_KEY=your_api_key

# Redis (for background tasks)
REDIS_URL=redis://localhost:6379/0

# Stock Prediction Model Path
MODEL_PATH=../FinanceApp/processed_finance_data/models/xgboost_stock_predictor.pkl
```

### Model Path Configuration

The app automatically looks for your XGBoost model at:
```
PersonalFinanceApp/backend/../FinanceApp/processed_finance_data/models/xgboost_stock_predictor.pkl
```

Make sure this path is correct and the model file exists.

## 🐛 Troubleshooting

### Common Issues

1. **Model Not Loading**
   ```bash
   # Check if model file exists
   ls -la ../FinanceApp/processed_finance_data/models/
   
   # Check model path in .env
   cat backend/.env | grep MODEL_PATH
   ```

2. **Database Connection Error**
   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   
   # Test database connection
   psql -h localhost -U finance_user -d finance_app
   ```

3. **Docker Issues**
   ```bash
   # Rebuild containers
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   
   # Check container logs
   docker-compose logs backend
   ```

4. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   lsof -i :3000
   
   # Kill the process or change ports in docker-compose.yml
   ```

### Logs and Debugging

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# Database logs
docker-compose logs -f postgres
```

## 📊 Verifying Everything Works

### 1. Check Backend Health

Visit: http://localhost:8000/health

Expected response:
```json
{
  "status": "healthy",
  "message": "API is running"
}
```

### 2. Check API Documentation

Visit: http://localhost:8000/docs

You should see the Swagger UI with all available endpoints.

### 3. Test Stock Prediction

```bash
# Test a stock prediction (requires authentication)
curl -X GET "http://localhost:8000/api/v1/stocks/predict/BHP.AX" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Check Frontend

Visit: http://localhost:3000

You should see the React application loading.

## 🚀 Next Steps

Once everything is running locally:

1. **Test the API endpoints** using the Swagger UI
2. **Verify stock predictions** are working
3. **Test the frontend** components
4. **Add sample data** to test the full functionality
5. **Deploy to production** when ready

## 📞 Support

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify all prerequisites are installed
3. Ensure the model file path is correct
4. Check the troubleshooting section above
5. Create an issue in the repository

Happy testing! 🎉 