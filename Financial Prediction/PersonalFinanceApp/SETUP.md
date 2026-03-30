# Personal Finance App Setup Guide

This guide will help you set up and run the Personal Finance App with AI-powered stock predictions.

## 🚀 Quick Start (Docker)

The easiest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone <your-repo-url>
cd PersonalFinanceApp

# Start all services
docker-compose up -d

# Check if services are running
docker-compose ps
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🛠️ Manual Setup

### Prerequisites

- **Node.js 18+** and **npm**
- **Python 3.11+** and **pip**
- **PostgreSQL 15+**
- **Redis 7+**

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database and API keys

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

## 📊 Database Setup

### PostgreSQL Configuration

```sql
-- Create database
CREATE DATABASE finance_app;

-- Create user
CREATE USER finance_user WITH PASSWORD 'finance_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE finance_app TO finance_user;
```

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql://finance_user:finance_password@localhost/finance_app

# JWT Secret (change in production)
SECRET_KEY=your-super-secret-key-change-this

# Yahoo Finance API (optional)
YAHOO_FINANCE_API_KEY=your_api_key

# Redis
REDIS_URL=redis://localhost:6379/0

# Stock Prediction Model Path
MODEL_PATH=../FinanceApp/processed_finance_data/models/xgboost_stock_predictor.pkl
```

## 🔧 Configuration

### Backend Configuration

The backend uses the following configuration files:

- `app/core/config.py` - Main configuration settings
- `.env` - Environment variables
- `alembic.ini` - Database migration configuration

### Frontend Configuration

The frontend configuration is in:

- `package.json` - Dependencies and scripts
- `src/config/api.ts` - API endpoint configuration
- `public/index.html` - HTML template

## 📈 Stock Prediction Integration

The app integrates with your existing XGBoost model:

1. **Model Path**: Points to your existing model in `../FinanceApp/`
2. **Data Updates**: Automatically fetches new stock data
3. **Predictions**: Runs daily predictions for all ASX stocks
4. **Recommendations**: Provides buy/sell/hold signals

### Model Integration Steps

1. Ensure your XGBoost model is trained and saved
2. Update the `MODEL_PATH` in `.env`
3. The backend will automatically load the model on startup
4. Background tasks will update predictions daily

## 🔒 Security Features

### Authentication

- JWT-based authentication
- Password hashing with bcrypt
- Session management
- Role-based access control

### Data Protection

- Input validation with Pydantic
- SQL injection prevention
- CORS protection
- Rate limiting

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

### E2E Tests

```bash
npm run test:e2e
```

## 📦 Production Deployment

### Docker Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Ubuntu Server Setup

```bash
# Install Docker
sudo apt update
sudo apt install docker.io docker-compose

# Clone repository
git clone <your-repo-url>
cd PersonalFinanceApp

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in .env
   - Ensure database and user exist

2. **Model Loading Error**
   - Verify MODEL_PATH points to correct file
   - Check model file permissions
   - Ensure all dependencies are installed

3. **Frontend Build Error**
   - Clear node_modules and reinstall
   - Check Node.js version (18+)
   - Verify all dependencies in package.json

4. **Docker Issues**
   - Check Docker and Docker Compose versions
   - Clear Docker cache: `docker system prune`
   - Rebuild images: `docker-compose build --no-cache`

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check the logs for error messages
4. Create an issue in the repository

## 📄 License

This project is licensed under the MIT License. 