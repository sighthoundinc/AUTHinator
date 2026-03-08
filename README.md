# 🔐 AUTHinator

> *"Behold! The AUTHinator! With this device, I shall control all authentication across the entire Tri-State Area's microservices! No user shall pass without my JWT tokens! Mwahahaha!"*
> 
> — Dr. Heinz Doofenshmirtz (probably)

**AUTHinator** is the authentication backbone of the Inator Platform. It's a Django-based microservice that provides JWT authentication, Single Sign-On (SSO), multi-factor authentication (MFA), service registry, and multi-tenant user management.

Every other -inator delegates authentication to AUTHinator. Services never store credentials — they validate JWT tokens and trust AUTHinator to be the source of truth.

## 🎯 What Does It Do?

```mermaid
graph TB
    subgraph "Your Microservices"
        RMA[📦 RMAinator]
        FULFIL[🚚 Fulfilinator]
        OTHER[🔧 YourService]
    end
    
    subgraph "AUTHinator"
        AUTH[🔐 JWT Auth]
        SSO[🌐 SSO Providers]
        MFA[🔑 MFA]
        USERS[👥 User Management]
        REGISTRY[📋 Service Registry]
    end
    
    USER[👤 End User]
    
    USER -->|Login| AUTH
    USER -->|Google/MS| SSO
    USER -->|2FA| MFA
    
    AUTH -->|JWT Token| USER
    
    USER -->|Request + JWT| RMA
    USER -->|Request + JWT| FULFIL
    USER -->|Request + JWT| OTHER
    
    RMA -->|Validate Token| AUTH
    FULFIL -->|Validate Token| AUTH
    OTHER -->|Validate Token| AUTH
    
    RMA -.->|Register| REGISTRY
    FULFIL -.->|Register| REGISTRY
    OTHER -.->|Register| REGISTRY
    
    style AUTH fill:#4a90d9,color:#fff
    style SSO fill:#27ae60,color:#fff
    style MFA fill:#e67e22,color:#fff
    style USERS fill:#9b59b6,color:#fff
    style REGISTRY fill:#3498db,color:#fff
```

### Features

- ✅ **JWT Authentication** — Secure access tokens with refresh flow
- ✅ **SSO Support** — Google, Microsoft, Auth0, Okta
- ✅ **Multi-Factor Authentication** — TOTP and WebAuthn/passkeys
- ✅ **Service Registry** — Central directory for your microservices
- ✅ **Multi-Tenancy** — Customer-scoped data with role-based access (ADMIN/USER)
- ✅ **User Approval Workflow** — Admin reviews before activation
- ✅ **Modern Frontend** — React + TypeScript + Tailwind CSS
- ✅ **Battle-Tested** — 86.94% test coverage with 79+ tests
- ✅ **Task Automation** — Taskfile for dev, test, deploy workflows

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

**Note**: If you're using the [Inator Platform](https://github.com/losomode/inator), the root `task setup` handles all of this automatically, including creating a default admin user and registering services.

### Demo Database

The Inator Platform provides a complete demo database with 12 users across 4 companies. See the [Demo Database Guide](https://github.com/losomode/inator/blob/main/docs/DEMO_DATABASE.md) for full details.

```bash
# From the platform root (inator/)
task setup:demodb        # Build demo databases
task demodb:activate     # Activate demo data
task setup:sso           # Configure OAuth providers (optional)
task restart:all         # Restart all services
```

**Demo users** (username/password):
- Platform admins: `admin/admin`, `alice.admin/admin`
- Company managers: `bob.manager/manager`, `frank.manager/manager`, etc.
- Company members: `carol.member/member`, `grace.member/member`, etc.

The demo database includes:
- 12 users with proper authentication credentials
- 4 companies (Acme, Globex, Initech, Wayne)
- 3 role levels (ADMIN=100, MANAGER=30, MEMBER=10)
- OAuth provider configuration support

### Using Taskfile (Recommended)

```bash
# Install all dependencies
task install

# Run backend development server
task backend:dev

# Run frontend development server (standalone mode)
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

**Important**: When running as part of the Inator Platform, the frontend is served from the unified SPA at `inator/frontend/`. The standalone frontend at `Authinator/frontend/` is only for development/testing of Authinator in isolation.

### Frontend Setup

```bash
cd frontend
npm install
npm start  # Starts on port 3001
```

### Troubleshooting Fresh Installs

If services fail to start, check:

```bash
# Verify .env exists
ls -la backend/.env

# Run migrations if database doesn't exist
cd backend && python manage.py migrate

# Check that dependencies installed correctly
ls -la .venv/                    # Backend venv should exist
ls -la frontend/node_modules/    # Frontend deps should exist

# View logs if running via platform orchestrator
tail -50 /path/to/logs/Authinator-backend.log
tail -50 /path/to/logs/Authinator-frontend.log
```

### Access

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** (standalone) | http://localhost:3001 | User login, registration, profile (dev only) |
| **Frontend** (platform) | http://localhost:8080 | Unified UI via Caddy gateway (recommended) |
| **Backend API** | http://localhost:8001 | REST API endpoints |
| **Admin Panel** | http://localhost:8001/admin | Django admin interface |

## 🌐 SSO Integration

```mermaid
sequenceDiagram
    participant User
    participant AUTHinator
    participant Google
    participant YourService

    User->>AUTHinator: Click "Login with Google"
    AUTHinator->>Google: Redirect to OAuth
    Google->>User: Login prompt
    User->>Google: Authenticate
    Google->>AUTHinator: Return with code
    AUTHinator->>Google: Exchange for user info
    AUTHinator->>AUTHinator: Create/link user
    AUTHinator->>User: Return JWT tokens
    User->>YourService: API request + JWT
    YourService->>AUTHinator: Validate token
    AUTHinator->>YourService: User info
    YourService->>User: Response
```

### Supported Providers

- **Google OAuth 2.0**
- **Microsoft Azure AD / Entra ID**
- **Auth0**
- **Okta**

### Setup Example: Google OAuth

1. **Create OAuth credentials** at [Google Cloud Console](https://console.cloud.google.com/)
2. **Set redirect URI**: `http://localhost:8001/accounts/google/login/callback/`
3. **Add to backend/.env**:
   ```bash
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-secret
   ```
4. **Configure in Django**:
   ```bash
   # From Authinator directory
   cd backend
   python manage.py setup_sso
   
   # OR from platform root (recommended)
   task setup:sso
   ```

### Setup Example: Microsoft

1. **Register app** at [Azure Portal](https://portal.azure.com/)
2. **Set redirect URI**: `http://localhost:8001/accounts/microsoft/login/callback/`
3. **Add to backend/.env**:
   ```bash
   MICROSOFT_CLIENT_ID=your-client-id
   MICROSOFT_CLIENT_SECRET=your-secret
   ```
4. **Configure in Django**:
   ```bash
   # From Authinator directory
   cd backend
   python manage.py setup_sso
   
   # OR from platform root (recommended)
   task setup:sso
   ```

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

## 🔌 Integrating Your Service

### Step 1: Register Your Service

Create a registration command in your service:

```python
# yourservice/management/commands/register_service.py
from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):
    help = 'Register with AUTHinator service registry'

    def handle(self, *args, **options):
        service_data = {
            'name': 'YourServiceinator',
            'description': 'Does amazing things',
            'base_url': 'http://localhost:8003',
            'api_prefix': '/api',
            'ui_url': 'http://localhost:3003',
            'icon': '🚀',
            'service_key': 'your-shared-secret',
        }
        
        response = requests.post(
            'http://localhost:8001/api/services/register/',
            json=service_data
        )
        
        if response.ok:
            self.stdout.write(self.style.SUCCESS('✅ Registered!'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {response.text}'))
```

Run it:
```bash
python manage.py register_service
```

### Step 2: Validate JWT Tokens

```python
# yourservice/authentication.py
import requests
from rest_framework import authentication, exceptions

class AUTHinatorAuthentication(authentication.BaseAuthentication):
    """Validate JWT tokens against AUTHinator."""
    
    AUTHINATOR_URL = 'http://localhost:8001'
    
    def authenticate(self, request):
        # Extract Bearer token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise exceptions.AuthenticationFailed('Invalid authorization header')
        
        token = parts[1]
        
        # Validate with AUTHinator
        try:
            response = requests.get(
                f'{self.AUTHINATOR_URL}/api/auth/me/',
                headers={'Authorization': f'Bearer {token}'},
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                # Return (user_data, token) tuple
                # DRF will set request.user = user_data
                return (user_data, token)
        except requests.RequestException:
            pass
        
        raise exceptions.AuthenticationFailed('Invalid or expired token')

# In your settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'yourservice.authentication.AUTHinatorAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Step 3: Enforce Permissions

```python
# Check user role from JWT
def your_view(request):
    user = request.user  # Dict from JWT
    
    if user.get('role') == 'ADMIN':
        # Full access
        pass
    elif user.get('role') == 'USER':
        # Customer-scoped access
        customer_id = user.get('customer_id')
        # Filter data by customer_id
        pass
```

## ⚛️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, Django 6.x, Django REST Framework |
| **Frontend** | TypeScript (strict), React 19, Vite, Tailwind CSS |
| **Gateway** | Caddy 2.x (in platform mode) |
| **Authentication** | JWT (simplejwt), django-allauth |
| **SSO** | Google OAuth, Microsoft Azure AD, Auth0, Okta |
| **MFA** | TOTP, WebAuthn/passkeys |
| **Testing** | pytest + coverage (86.94%), pytest-django |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **Task Runner** | [Taskfile](https://taskfile.dev/) |

## 📦 Deployment

### Docker Deployment (Recommended)

```bash
# Coming soon - Docker Compose setup
```

### Manual Deployment

#### Production Backend

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt gunicorn psycopg2-binary

# 2. Set environment variables (see below)
cp .env.example .env
# Edit .env with production values

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Start with gunicorn
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8001 \
  --workers 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

#### Production Frontend

```bash
cd frontend
npm install
npm run build
# Serve the dist/ directory with nginx or similar
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```bash
# Django Core
DEBUG=False                    # MUST be False in production
SECRET_KEY=your-secret-key-min-50-chars
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database (use PostgreSQL in production)
DATABASE_URL=postgresql://user:pass@localhost:5432/authinator

# CORS (your frontend domains)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Service Registry
SERVICE_REGISTRY_ENABLED=True
SERVICE_REGISTRATION_KEY=generate-a-secure-key

# SSO Providers (optional - leave empty to disable)
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

# Security (production only)
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
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

## 🔒 Security

### Production Checklist

**Before deploying to production:**

- [ ] **Set `DEBUG=False`** in `.env`
- [ ] **Generate strong `SECRET_KEY`** (50+ random characters)
- [ ] **Use PostgreSQL** instead of SQLite
- [ ] **Enable HTTPS** and set secure cookie flags:
  - `SESSION_COOKIE_SECURE=True`
  - `CSRF_COOKIE_SECURE=True`
  - `SECURE_SSL_REDIRECT=True`
- [ ] **Update SSO redirect URIs** to production domains
- [ ] **Set `ALLOWED_HOSTS`** to your actual domains
- [ ] **Configure CORS** for production frontend URLs
- [ ] **Use strong service registration key**
- [ ] **Implement rate limiting** on authentication endpoints
- [ ] **Regular security audits** and dependency updates
- [ ] **Backup strategy** for database

### Secrets Management

- ✅ **All secrets in `.env`** (gitignored)
- ✅ **`.env.example` template** provided
- ✅ **No hardcoded credentials** in code
- ✅ **SSO credentials encrypted** in database
- ✅ **Service keys validated** before registration


## 🐛 Troubleshooting

### 🌐 SSO Not Working?

**Symptom**: OAuth redirect fails or shows error

**Solutions**:
1. **Check redirect URI** — Must match EXACTLY (trailing slash matters!)
   - Dev: `http://localhost:8001/accounts/google/login/callback/`
   - Prod: `https://yourdomain.com/accounts/google/login/callback/`
2. **Verify credentials** in `backend/.env`
3. **Run setup**: `cd backend && python manage.py setup_sso`
4. **Clear cookies** and try again
5. **Check console** for CORS errors

### 🔐 Token Validation Failing?

**Symptom**: Services reject valid tokens

**Solutions**:
1. **Check token expiry** — Access tokens expire after 1 hour
2. **Use refresh endpoint**: `POST /api/auth/refresh/` with refresh token
3. **Verify AUTHinator URL** in service configuration
4. **Check CORS** if calling from browser
5. **Inspect JWT** at [jwt.io](https://jwt.io) to verify claims

### ❌ CORS Errors?

**Symptom**: Browser blocks requests

**Solutions**:
1. **Add origins** to `CORS_ALLOWED_ORIGINS` in `backend/.env`
2. **Restart backend** after changes
3. **Check protocol** — http vs https must match
4. **Verify port numbers** are correct

### 📦 Service Registration Fails?

**Symptom**: `register_service` returns 403/401

**Solutions**:
1. **Check service key** matches in both services
2. **Verify URL** is `http://localhost:8001/api/services/register/`
3. **Enable registry** — `SERVICE_REGISTRY_ENABLED=True`
4. **Check logs** in backend for detailed error

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

## 📜 API Documentation

Full API documentation available at:
- **Swagger UI**: `http://localhost:8001/api/docs/`
- **ReDoc**: `http://localhost:8001/api/redoc/`

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|----------|
| `/api/auth/login/` | POST | Username/password login |
| `/api/auth/refresh/` | POST | Refresh JWT token |
| `/api/auth/logout/` | POST | Blacklist refresh token |
| `/api/auth/me/` | GET | Get current user info |
| `/api/auth/register/` | POST | User registration |
| `/api/auth/sso-providers/` | GET | List enabled SSO providers |
| `/api/services/register/` | POST | Register service (requires key) |
| `/api/services/` | GET | List registered services |
| `/api/users/pending/` | GET | Pending user approvals (admin) |
| `/api/users/<id>/approve/` | POST | Approve user (admin) |
| `/api/users/<id>/reject/` | POST | Reject user (admin) |

## 📦 Repository

**GitHub**: [losomode/AUTHinator](https://github.com/losomode/AUTHinator)

## 📝 License

MIT — See [LICENSE](LICENSE) for details.

## 👥 Contributing

Part of the Inator Platform. See main platform docs for contributing guidelines.

## ❓ Support

- **Issues**: [GitHub Issues](https://github.com/losomode/AUTHinator/issues)
- **Platform Docs**: [Inator Platform](https://github.com/losomode/inator)
- **Discord**: Coming soon

---

*Built with ❤️ for the Inator Platform*
