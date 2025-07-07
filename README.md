# H.E.L.P Backend (Kincash)

A robust Django REST Framework backend for a peer-to-peer loan management system. This application enables users to create, manage, and track loans between individuals, with features for EMI scheduling, payment tracking, and real-time notifications.

## Features

- **User Management**
  - Registration and authentication with JWT
  - Profile management
  - OTP verification for secure operations

- **Loan Management**
  - Create loans between users
  - Accept/reject loan requests
  - Automatic EMI schedule generation
  - Support for monthly and weekly repayment cycles

- **Payment Tracking**
  - Record and track EMI payments
  - Late fee calculation for overdue payments
  - Payment history and transaction ledger

- **Real-time Notifications**
  - WebSocket integration for instant updates
  - Email and SMS notifications
  - Customizable notification preferences

## Tech Stack

- **Framework**: Django 4.x + Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Task Queue**: Celery + Redis
- **WebSockets**: Django Channels
- **Documentation**: drf-spectacular (OpenAPI)
- **Testing**: pytest, factory_boy
- **CI/CD**: GitHub Actions

## Project Structure

```
kincashBackend/
├── apps/
│   ├── users/              # User management
│   ├── loans/              # Loan and payment management
│   │   ├── views/
│   │   │   ├── loan_views.py
│   │   │   └── payments_views.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── services.py
│   ├── notifications/      # Notification system
│   └── tests/              # Integration tests
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── utils/                  # Utility functions
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── .github/workflows/      # CI/CD configuration
├── Dockerfile
├── docker-compose.yml
└── manage.py
```

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/kincashBackend.git
   cd kincashBackend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements/dev.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Using Docker

For a containerized setup:

```bash
docker-compose up -d
```

This will start the Django app, PostgreSQL, Redis, Celery worker, and Celery beat scheduler.

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI Schema: http://localhost:8000/api/schema/

## Testing

Run the test suite:

```bash
pytest
```

For coverage report:

```bash
pytest --cov=apps
```

## Deployment

The project includes CI/CD workflows for GitHub Actions that:

1. Run linting and tests
2. Build Docker image
3. Deploy to production (when merged to main)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
