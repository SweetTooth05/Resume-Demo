# PostgreSQL Setup Guide

This guide will help you set up PostgreSQL for the Personal Finance App.

## Prerequisites

- PostgreSQL installed on your system
- Python 3.8+ with required packages

## Quick Setup

### 1. Start PostgreSQL Service

```bash
# On Ubuntu/Debian
sudo service postgresql start

# On CentOS/RHEL
sudo systemctl start postgresql

# On macOS (if installed via Homebrew)
brew services start postgresql
```

### 2. Set PostgreSQL User Password

```bash
# Connect to PostgreSQL as postgres user
sudo -u postgres psql

# Set password for postgres user
ALTER USER postgres PASSWORD 'postgres';

# Exit PostgreSQL
\q
```

### 3. Initialize Database

```bash
# Navigate to backend directory
cd PersonalFinanceApp/backend

# Activate virtual environment
source venv/bin/activate

# Run PostgreSQL setup
python3 setup_postgres.py
```

## Manual Setup (Alternative)

If the automatic setup doesn't work, you can manually create the database:

### 1. Create Database

```bash
sudo -u postgres psql

# Create database
CREATE DATABASE finance_app;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE finance_app TO postgres;

# Exit
\q
```

### 2. Create Tables

```bash
# Run the initialization script
python3 setup_postgres.py
```

## Configuration

The app is configured to use:
- **Host**: localhost
- **Port**: 5432
- **Database**: finance_app
- **User**: postgres
- **Password**: postgres

You can override these settings by setting environment variables:

```bash
export DATABASE_URL="postgresql://username:password@host:port/database"
```

## Troubleshooting

### Connection Issues

1. **Check PostgreSQL is running**:
   ```bash
   sudo service postgresql status
   ```

2. **Check connection**:
   ```bash
   psql -h localhost -U postgres -d postgres
   ```

3. **Check database exists**:
   ```bash
   sudo -u postgres psql -c "\l"
   ```

### Permission Issues

1. **Fix PostgreSQL authentication**:
   Edit `/etc/postgresql/*/main/pg_hba.conf` and change:
   ```
   local   all             postgres                                peer
   ```
   to:
   ```
   local   all             postgres                                md5
   ```

2. **Restart PostgreSQL**:
   ```bash
   sudo service postgresql restart
   ```

### Port Issues

1. **Check if port 5432 is in use**:
   ```bash
   sudo netstat -tlnp | grep 5432
   ```

2. **Check PostgreSQL configuration**:
   ```bash
   sudo -u postgres psql -c "SHOW port;"
   ```

## Production Considerations

For production deployment:

1. **Use strong passwords**
2. **Enable SSL connections**
3. **Configure connection pooling**
4. **Set up proper backup strategies**
5. **Use environment variables for sensitive data**

## Database Schema

The app creates the following tables:

### Stock Tables
- `top_stock_recommendations` - Top 20 stock recommendations
- `stock_predictions` - All stock predictions for search
- `stock_holdings` - User portfolio holdings
- `stock_transactions` - Transaction history

### Financial Tables
- `incomes` - Income entries
- `expenses` - Expense entries
- `assets` - Asset entries
- `debts` - Debt entries

## Verification

After setup, you can verify the installation:

```bash
# Test database connection
python3 -c "
from app.core.database import get_db
from app.models.stock import TopStockRecommendation
db = next(get_db())
count = db.query(TopStockRecommendation).count()
print(f'Top recommendations in database: {count}')
"
```

Expected output: `Top recommendations in database: 20` 