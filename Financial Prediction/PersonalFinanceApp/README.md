# Personal Finance App

A modern, responsive personal finance management application with **real AI-powered stock predictions**, portfolio tracking, and financial analytics.

## Features

- **Dashboard**: Comprehensive financial overview with health score, charts, and analytics
- **Stock Portfolio**: Track stock holdings with **real XGBoost AI predictions** (62% accuracy)
- **Financial Management**: Manage income, expenses, assets, and debts
- **Real-time Data**: Live stock recommendations using actual trained machine learning model
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Material-UI (MUI)** for UI components
- **Recharts** for data visualization
- **Axios** for API communication
- **React Router** for navigation

### Backend
- **FastAPI** (Python) for REST API
- **SQLAlchemy** for database ORM
- **PostgreSQL** for production-grade data storage
- **Pydantic** for data validation

### Machine Learning
- **Real XGBoost Model** trained on ASX stock data
- **62% Prediction Accuracy** on test data
- **70+ Technical Indicators** (RSI, MACD, Bollinger Bands, etc.)
- **Real-time Yahoo Finance Data** integration
- **Feature Importance Analysis** from trained model

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PersonalFinanceApp
   ```

2. **Set up PostgreSQL**
   ```bash
   # Start PostgreSQL service
   sudo service postgresql start
   
   # Set password for postgres user
   sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
   ```

3. **Set up the Backend**
   ```bash
   cd backend
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   
   # Initialize database with real data
   python3 simple_setup.py
   python3 populate_real_data.py
   ```

4. **Set up the Frontend**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

1. **Start the Backend Server**
   ```bash
   cd backend
   # Activate virtual environment if not already activated
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the Frontend Development Server**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Real Data Integration

This application uses **real data** from your FinanceApp:

### Machine Learning Model
- **Trained XGBoost Model**: `FinanceApp/processed_finance_data/models/xgboost_stock_predictor.pkl`
- **Model Accuracy**: 62% on test data
- **Features**: 70+ technical indicators including RSI, MACD, Bollinger Bands, etc.
- **Training Data**: Real ASX stock data with comprehensive feature engineering

### Stock Data
- **ASX Companies**: Real ASX-listed companies from `FinanceApp/ASXListedCompanies.csv`
- **Live Data**: Real-time stock prices from Yahoo Finance
- **Predictions**: AI-powered predictions using the trained model
- **Technical Analysis**: Comprehensive technical indicators calculated in real-time

### Database
- **PostgreSQL**: Production-grade database for reliability
- **Real Predictions**: Actual model predictions stored in database
- **Performance**: Fast queries with proper indexing

## API Endpoints

### Health Check
- `GET /api/v1/health` - Check API status

### Dashboard
- `GET /api/v1/dashboard` - Get dashboard data
- `GET /api/v1/dashboard/financial-health` - Get financial health score
- `GET /api/v1/dashboard/expense-breakdown` - Get expense breakdown
- `GET /api/v1/dashboard/net-worth-history` - Get net worth history

### Financial Management
- `GET /api/v1/financial/summary` - Get financial summary
- `POST /api/v1/financial/{type}` - Add financial item (income/expense/asset/debt)
- `DELETE /api/v1/financial/{type}/{id}` - Delete financial item

### Stock Portfolio (Real AI Predictions)
- `GET /api/v1/stocks/recommendations` - Get top 20 AI-powered stock recommendations
- `GET /api/v1/stocks/search/{query}` - Search stocks with real predictions
- `GET /api/v1/stocks/predict/{ticker}` - Get real AI prediction for specific stock
- `GET /api/v1/portfolio` - Get user portfolio
- `POST /api/v1/portfolio/stocks` - Add stock to portfolio
- `DELETE /api/v1/portfolio/stocks/{id}` - Remove stock from portfolio

## Project Structure

```
PersonalFinanceApp/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── dashboard.py
│   │   │       │   ├── financial.py
│   │   │       │   ├── health.py
│   │   │       │   ├── portfolio.py
│   │   │       │   └── stocks.py
│   │   │       └── api.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── financial.py
│   │   │   └── stock.py
│   │   ├── schemas/
│   │   │   ├── financial.py
│   │   │   └── stock.py
│   │   ├── ml/
│   │   │   └── stock_predictor.py  # Real AI model integration
│   │   └── main.py
│   ├── requirements.txt
│   ├── simple_setup.py
│   ├── populate_real_data.py      # Real data population
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   └── ResponsiveWrapper.tsx
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Finances.tsx
│   │   │   └── Stocks.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Features in Detail

### Dashboard
- **Financial Health Score**: Calculated based on savings rate, debt-to-income ratio, and asset-to-debt ratio
- **Summary Cards**: Display total income, expenses, net worth, and monthly savings
- **Charts**: Expense breakdown and net worth growth over time
- **AI Stock Recommendations**: Top 6 BUY recommendations with real confidence scores

### Financial Management
- **Add/Remove Items**: Manage income, expenses, assets, and debts
- **Categorization**: Predefined categories for each financial type
- **Real-time Calculations**: Automatic calculation of totals and net worth
- **Local Storage Fallback**: Works offline with localStorage backup

### Stock Portfolio (Real AI)
- **Portfolio Tracking**: Add and manage stock holdings
- **Real AI Predictions**: XGBoost model with 62% accuracy
- **Live Data**: Real-time stock prices from Yahoo Finance
- **Search Functionality**: Search for stocks with real predictions
- **Performance Metrics**: Track gains/losses and portfolio value
- **Top 20 AI Recommendations**: Fast access to best stock picks

## Database Schema

### Stock Tables
- **top_stock_recommendations**: Top 20 AI-powered stock recommendations
- **stock_predictions**: All stock predictions for search functionality
- **stock_holdings**: User's portfolio holdings
- **stock_transactions**: Transaction history

### Financial Tables
- **incomes**: Income entries
- **expenses**: Expense entries
- **assets**: Asset entries
- **debts**: Debt entries

## Development

### Testing the API
```bash
cd PersonalFinanceApp
python test_api.py
```

### Database Management
```bash
cd backend
# Initialize database with real data
python3 simple_setup.py
python3 populate_real_data.py

# Reset database (delete and recreate)
python3 simple_setup.py
python3 populate_real_data.py
```

### Adding New Features
1. Create new endpoint in `backend/app/api/v1/endpoints/`
2. Add corresponding frontend service in `frontend/src/services/api.ts`
3. Create React component in `frontend/src/pages/` or `frontend/src/components/`
4. Update routing in `frontend/src/App.tsx`

### Styling
The app uses a custom Material-UI theme with:
- **Primary Color**: Tetraammine (#1029CC)
- **Secondary Color**: Solar Ash (#CC6123)
- **Neutral Palette**: Grays and whites for text and backgrounds

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running: `sudo service postgresql status`
   - Check connection: `psql -h localhost -U postgres -d postgres`

2. **AI Model Not Loading**
   - Check that `FinanceApp/processed_finance_data/models/xgboost_stock_predictor.pkl` exists
   - Verify ASX companies file: `FinanceApp/ASXListedCompanies.csv`

3. **API Endpoints Not Working**
   - Ensure the backend server is running on port 8000
   - Check the API documentation at http://localhost:8000/docs

4. **Frontend Not Loading**
   - Ensure Node.js and npm are installed
   - Run `npm install` in the frontend directory
   - Check that the backend is running

## Deployment

### Using Docker
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment
1. Build the frontend: `npm run build`
2. Set up a production server (nginx, Apache)
3. Configure environment variables
4. Run the backend with a production WSGI server

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue on GitHub or contact the development team. 
