# ExpenseTracker - Modern Expense Tracking Application

## Overview
ExpenseTracker is a Django-based expense tracking application that helps users manage their personal finances effectively. The application provides features for tracking both expenses and income, setting budgets, managing financial goals, and generating detailed reports.

## Features

### 1. Expense Management
- Add, edit, and delete expenses
- Categorize expenses with custom categories
- Daily expense limit with email notifications
- Sort expenses by amount or date
- Search functionality
- Pagination support

### 2. Income Tracking
- Track multiple income sources
- Add, edit, and delete income records
- Sort and filter capabilities
- Detailed income summaries

### 3. Financial Goals
- Set and track savings goals
- Progress monitoring
- Email notifications on goal achievement
- Real-time progress updates

### 4. Reports & Analytics
- Generate comprehensive financial reports
- Export reports in multiple formats (PDF, CSV, XLSX)
- Date range filtering
- Summary statistics
- Income vs Expense analysis

### 5. User Preferences
- Customizable currency settings
- Configurable daily expense limits
- Personalized user profiles

### 6. Security
- User authentication required for all features
- Per-user data isolation
- Secure data handling
- API rate limiting
- JWT authentication for API endpoints

## Technical Stack

### Backend
- Django 5.1.1
- Django REST Framework 3.15.2
- SQLite (Development) / PostgreSQL (Production-ready)
- Celery for background tasks (email notifications, report generation)
- Redis for caching and task queue

### Frontend
- Bootstrap 5 for responsive design
- Chart.js for data visualization
- Vanilla JavaScript for interactivity
- Responsive templates for all device sizes

### API Endpoints
- RESTful API design
- JWT authentication
- Comprehensive documentation (Swagger/OpenAPI)
- Rate limiting and throttling

## Getting Started

### Prerequisites
- Python 3.8+
- Redis server (for background tasks)
- Node.js (for frontend assets, if needed)

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd Expensetracker
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Access the application at `http://127.0.0.1:8000/`

## Project Structure

```
expensetracker/
├── api/                 # REST API endpoints
├── authentication/      # User authentication and registration
├── expenses/           # Expense management
├── goals/              # Financial goals
├── report_generation/  # Report generation logic
├── static/            # Static files (CSS, JS, images)
├── templates/         # HTML templates
├── userincome/        # Income management
├── userpreferences/   # User settings and preferences
└── userprofile/       # User profile management
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
