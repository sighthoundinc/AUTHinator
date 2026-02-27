# AUTHinator

🔐 **Centralized Authentication Service with SSO Support**

AUTHinator is a microservice authentication platform that provides JWT-based authentication, Single Sign-On (SSO), service registry, and user management for distributed systems.

## Features

- ✅ **Username/Password Authentication** with secure JWT tokens
- ✅ **SSO Support** - Google, Microsoft, Auth0, Okta
- ✅ **Multi-Factor Authentication (MFA)** - TOTP and WebAuthn support
- ✅ **Service Registry** - Central directory for microservices
- ✅ **Multi-Tenancy** - Customer isolation with role-based access
- ✅ **User Approval Workflow** - Admin approval for new users
- ✅ **Modern UI** - React + TypeScript frontend with Tailwind CSS
- ✅ **Comprehensive Testing** - 86.94% test coverage with 79+ tests
- ✅ **Task Automation** - Taskfile for common development tasks

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Task](https://taskfile.dev/) (optional but recommended)

### Backend Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cd backend
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start backend (port 8001)
python manage.py runserver 8001
```

### Using Taskfile (Recommended)

```bash
# Install all dependencies
task install

# Run backend development server
task backend:dev

# Run frontend development server
task frontend:dev

# Run tests with coverage
task test:coverage

# Run linting
task lint

# Run formatting
task fmt

# Run all checks (format, lint, test)
task check
```

### Frontend Setup

```bash
cd frontend
npm install
npm start  # Starts on port 3000
```

### Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin: http://localhost:8000/admin

## SSO Configuration

### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 Client ID
3. Add redirect URI: `http://localhost:8000/accounts/google/login/callback/`
4. Add credentials to `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-secret
   ```
5. Run: `python manage.py setup_sso`

### Microsoft OAuth
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register application
3. Add redirect URI: `http://localhost:8000/accounts/microsoft/login/callback/`
4. Add credentials to `.env`:
   ```
   MICROSOFT_CLIENT_ID=your-client-id
   MICROSOFT_CLIENT_SECRET=your-secret
   ```
5. Run: `python manage.py setup_sso`

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Username/password login
- `POST /api/auth/refresh/` - Refresh JWT token
- `GET /api/auth/me/` - Get current user
- `POST /api/auth/register/` - Register new user
- `GET /api/auth/sso-providers/` - List enabled SSO providers

### Service Registry
- `POST /api/services/register/` - Register a service (requires service_key)
- `GET /api/services/` - List services (requires auth)

### User Management
- `GET /api/users/pending/` - List pending approvals
- `POST /api/users/<id>/approve/` - Approve user
- `POST /api/users/<id>/reject/` - Reject user

## Registering a Microservice

Create a management command in your service:

```python
# yourservice/management/commands/register_service.py
from django.core.management.base import BaseCommand
from django.conf import settings
import requests

class Command(BaseCommand):
    help = 'Register service with AUTHinator'

    def handle(self, *args, **options):
        service_data = {
            'name': 'YourService',
            'description': 'Service description',
            'base_url': 'http://localhost:8003',
            'api_prefix': '/api',
            'ui_url': 'http://localhost:3003',
            'icon': '🚀',
            'service_key': settings.SERVICE_REGISTRATION_KEY,
        }
        
        response = requests.post(
            settings.SERVICE_REGISTRY_URL,
            json=service_data
        )
        
        if response.status_code in [200, 201]:
            self.stdout.write(self.style.SUCCESS('Service registered'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed: {response.text}'))
```

## Validating Tokens in Your Service

```python
# yourservice/authentication.py
import requests
from rest_framework import authentication, exceptions
from django.conf import settings

class AUTHinatorJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise exceptions.AuthenticationFailed('Invalid header')
        
        token = parts[1]
        
        try:
            response = requests.get(
                f'{settings.AUTHINATOR_API_URL}me/',
                headers={'Authorization': f'Bearer {token}'},
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                # Create a user object with the data
                return (user_data, token)
        except requests.RequestException:
            pass
            
        raise exceptions.AuthenticationFailed('Invalid token')

# In your settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'yourservice.authentication.AUTHinatorJWTAuthentication',
    ],
}
```

## Environment Variables

Required variables in `.env`:

```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002

# Service Registry
SERVICE_REGISTRY_ENABLED=True
SERVICE_REGISTRATION_KEY=your-service-key

# SSO (Optional - leave empty to disable)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_DOMAIN=
OKTA_CLIENT_ID=
OKTA_CLIENT_SECRET=
OKTA_BASE_URL=
```

## Testing

AUTHinator maintains **86.94% test coverage** (exceeds 85% requirement).

```bash
# Run tests with coverage
task test:coverage

# Or manually with pytest
cd backend
pytest --cov --cov-report=html

# View coverage report
open backend/htmlcov/index.html
```

### Test Suite
- **79 tests** covering authentication, SSO, user management, and services
- Comprehensive testing of:
  - JWT authentication flows
  - SSO adapters (Google, Microsoft, etc.)
  - Signal handlers for social login
  - User registration and approval workflows
  - Service registry
  - Customer and user models

## Project Structure

```
AUTHinator/
├── backend/               # Django backend
│   ├── auth_core/         # Authentication logic & SSO
│   │   ├── test_account_adapter.py
│   │   ├── test_adapters.py
│   │   ├── test_jwt_auth.py
│   │   ├── test_signals.py
│   │   └── test_views.py
│   ├── users/             # User & customer management
│   │   ├── test_models.py
│   │   └── test_registration.py
│   ├── services/          # Service registry
│   ├── mfa/               # Multi-factor authentication
│   ├── config/            # Django settings
│   ├── .env.example       # Example configuration
│   ├── requirements.txt   # Python dependencies
│   ├── pytest.ini         # Test configuration
│   └── manage.py
├── frontend/              # React TypeScript app
│   ├── src/
│   │   ├── pages/         # Login, ServiceDirectory
│   │   └── api/           # API client
│   └── public/
├── docs/                  # Documentation
├── Taskfile.yml           # Task automation
└── README.md
```

## Security

### Development
- SQLite database
- Debug mode enabled
- HTTP allowed

### Production Checklist
- [ ] `DEBUG=False`
- [ ] Strong `SECRET_KEY`
- [ ] PostgreSQL database
- [ ] HTTPS only
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] Production SSO redirect URIs
- [ ] Rate limiting on auth endpoints
- [ ] Regular security audits

### Secrets Management
- ✅ `.env` excluded from git
- ✅ `.env.example` provided without secrets
- ✅ No hardcoded credentials
- ✅ SSO credentials stored in database

## Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Troubleshooting

### SSO Issues
- Verify redirect URIs match exactly (trailing slash matters!)
- Check OAuth credentials in `.env`
- Run `python manage.py setup_sso` after updating credentials
- Clear browser cookies and try again

### Token Issues
- Tokens expire after 1 hour by default
- Use refresh endpoint to get new token
- Verify AUTHinator is accessible from your service

### CORS Issues
- Add your frontend URL to `CORS_ALLOWED_ORIGINS`
- Restart backend after changes

## Development

### Available Tasks

```bash
# Development servers
task backend:dev         # Start backend server (port 8001)
task frontend:dev        # Start frontend server (port 3000)

# Testing
task test                # Run backend tests
task test:coverage       # Run tests with coverage report
task frontend:test       # Run frontend tests

# Code quality
task fmt                 # Format code (black + prettier)
task lint                # Lint code (ruff + eslint)
task check               # Run all checks (fmt + lint + test)

# Database
task backend:migrate     # Run migrations
task backend:makemigrations  # Create migrations
task db:reset            # Reset database

# Other
task clean               # Clean cache files
task stats               # Show project statistics
```

### Manual Development

```bash
# Backend
cd backend
python manage.py makemigrations
python manage.py migrate
pytest                    # Run tests
ruff check .             # Lint
black .                  # Format

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build
```

## License

MIT

## Support

- GitHub Issues: [Report bugs or request features]
- Documentation: See inline code documentation
