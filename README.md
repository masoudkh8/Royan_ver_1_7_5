# 🌐 Flask Project with PostgreSQL

## 📋 Description
This project is a Flask-based web application that uses **PostgreSQL** as its database.

## ✅ Features
- Fully compatible with PostgreSQL
- No SQLite dependencies
- SQLAlchemy models for database management
- Migration support with Flask-Migrate
- User authentication with Flask-Login
- Email sending with Flask-Mail
- File upload support
- PWA (Progressive Web App)

## 🚀 Quick Setup

### 1. Install Prerequisites
```bash
pip install -r requirements.txt
```

### 2. Setup PostgreSQL Database
```bash
# Create database
sudo -u postgres psql -c "CREATE DATABASE ports_db;"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ports_db TO postgres;"
```

### 3. Configure `.env` File
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ports_db
SECRET_KEY=your-secret-key-here
```

### 4. Create Tables
```bash
python init_postgres_db.py
```

### 5. Load Port Data (Optional)
```bash
python load_ports_to_postgres.py
```

### 6. Run Application
```bash
python app.py
```

## 📚 Full Documentation
For complete guide, see `POSTGRES_GUIDE.md`.

## 🔧 Useful Scripts
- `init_postgres_db.py` - Create empty tables
- `load_ports_to_postgres.py` - Load port data
- `view_db.py` - View database

## 📦 Models
- User
- Port
- Order
- Magazine
- Notification
- Message
- DataProvider
- PremiumRequest

## 🛠 Technologies
- Flask 2.3.3
- SQLAlchemy 2.0.46
- PostgreSQL
- Flask-Migrate
- Flask-Login
- Flask-Mail

## 🛠️ Building Tailwind CSS for Offline Use

To build the Tailwind CSS file for offline use:

```bash
python build_tailwind.py
```

Or manually:

```bash
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify
```

This will compile all Tailwind classes used in your templates into a single `output.css` file that works without internet connection.
