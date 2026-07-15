# GreenLoan System Architecture

## System Overview

GreenLoan is a **Django-based Loan Management System** designed to digitize the complete loan lifecycle. The system serves three main user roles with distinct workflows:

```
┌─────────────────────────────────────────────────────────┐
│                   GreenLoan Platform                      │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼─────┐        ┌────▼──────┐      ┌────▼─────────┐
    │ Customer  │        │  Loan     │      │   Admin      │
    │  Portal   │        │ Officer   │      │   Dashboard  │
    │           │        │  Review   │      │              │
    └────┬─────┘        └────┬──────┘      └────┬─────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                    ┌─────────▼────────────┐
                    │   Django Backend      │
                    │  (Python 3.10)        │
                    └─────────┬────────────┘
                              │
                    ┌─────────▼────────────┐
                    │  Database Layer       │
                    │  SQLite/PostgreSQL    │
                    └──────────────────────┘
```

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend Framework** | Django | 4.2.30 |
| **Runtime** | Python | 3.10 |
| **Frontend** | HTML5/CSS3/JavaScript | - |
| **CSS Framework** | Bootstrap 5 | - |
| **Database** | SQLite (dev), PostgreSQL (prod) | - |
| **Authentication** | Django Allauth + Google OAuth | 65.13.1 |
| **Server** | Gunicorn | 25.0.1 |
| **Static Files** | WhiteNoise | 6.11.0 |
| **API** | Django REST Framework | 3.16.1 |
| **ML/CV** | TensorFlow, OpenCV | 2.21.0, 4.13.0 |

## Project Structure

```
greenloan/                    # Root Django project
├── accounts/                 # User authentication & KYC
│   ├── models.py            # Custom User model with role-based access
│   ├── views.py             # Registration, login, KYC views
│   ├── forms.py             # User forms & validation
│   └── signals.py           # Email verification signals
│
├── loans/                    # Loan application & management
│   ├── models.py            # LoanTypes, Application, Document, ApprovedLoans, Repayment
│   ├── views.py             # Application workflow views
│   ├── serializers.py       # DRF serializers
│   └── urls.py              # Loan application routes
│
├── payments/                 # Payment & repayment processing
│   ├── models.py            # Payment transaction models
│   ├── views.py             # eSewa integration, payment processing
│   └── urls.py              # Payment routes
│
├── kyc/                      # Know Your Customer verification
│   ├── models.py            # KYC verification models
│   ├── views.py             # KYC self-verification views
│   └── urls.py              # KYC routes
│
├── core/                     # Shared utilities & middleware
│   ├── models.py            # Common models
│   ├── views.py             # Landing page, common views
│   └── utils.py             # Helper functions
│
├── greenloan/               # Main project configuration
│   ├── settings.py          # Django settings, apps config, middleware
│   ├── urls.py              # Main URL routing
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
│
├── templates/               # HTML templates
│   ├── accounts/            # Login, signup, KYC forms
│   ├── loans/               # Application forms & status pages
│   ├── dashboard/           # User & admin dashboards
│   └── base.html            # Base template
│
├── static/                  # Static files
│   ├── css/                 # SCSS & CSS styles
│   ├── js/                  # JavaScript files
│   └── images/              # Images & assets
│
├── media/                   # User-uploaded files
│   ├── kyc/                 # KYC documents
│   └── documents/           # Loan documents
│
├── manage.py                # Django CLI
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yaml      # Docker Compose setup
└── .env.example             # Environment variables template
```

## Data Models

### Core Models

#### User Model (Custom)
```python
User (accounts.models.User)
├── Authentication
│   ├── email (unique, used as username)
│   ├── password
│   └── email_verified
│
├── Profile
│   ├── first_name, last_name, full_name
│   ├── phone
│   ├── date_of_birth
│   ├── gender
│   ├── nationality
│   ├── occupation (individual, business_owner, student, self_employed, farmer)
│   └── monthly_income
│
├── Address
│   ├── permanent_address
│   ├── temporary_address
│   └── phone_verified
│
├── Identity
│   ├── citizenship_number
│   ├── national_id_number
│   ├── pan_number
│   └── KYC documents (front, back, passport)
│
├── Role & Status
│   ├── role (customer, admin, loan_officer, senior_officer)
│   ├── is_active
│   └── kyc_status (pending, submitted, verified, rejected)
│
└── KYC Verification
    ├── kyc_verified_at
    └── kyc_verified_by (foreign key to User)
```

#### Application Model
```python
Application (loans.models.Application)
├── Applicant Info
│   ├── applicant (ForeignKey → User)
│   ├── monthly_income
│   ├── citizenship_number
│   └── address
│
├── Loan Details
│   ├── loan_type (ForeignKey → LoanTypes)
│   ├── amount
│   ├── duration_months
│   └── purpose
│
├── Processing
│   ├── status (submitted → approved/rejected)
│   ├── officer (ForeignKey → User, assigned loan officer)
│   ├── status_history (JSON track all status changes)
│   └── comments (JSON, notes from officers)
│
└── Timestamps
    ├── created_at
    └── updated_at
```

#### LoanTypes Model
```python
LoanTypes
├── name (unique)
├── description
├── interest_rate
├── amount_limit
├── required_documents (JSON list)
└── is_active
```

#### ApprovedLoans Model
```python
ApprovedLoans
├── application (ForeignKey → Application)
├── principle
├── interest_rate
├── tenure_months
├── approved_by (ForeignKey → User)
├── approved_at
├── status (active, closed, defaulted)
└── repayments (reverse relation)
```

#### Repayment Model
```python
Repayment
├── loan (ForeignKey → ApprovedLoans)
├── due_date
├── paid_date
├── amount_due
├── amount_paid
└── status (pending, partial, paid, late)
```

#### Document Model
```python
Document
├── application (ForeignKey → Application)
├── document_type (citizenship, salary_slip, bank_statement, etc.)
├── file (FileField)
├── verification_status (pending, verified, rejected)
└── uploaded_at
```

#### CreditScore Model
```python
CreditScore
├── user (OneToOneField → User)
├── score (default: 300)
└── last_updated
```

## Request Flow

### Loan Application Workflow

```
1. User Registration & Email Verification
   └─→ accounts.views.register → send verification email → email verified

2. KYC Completion
   └─→ kyc.views.kyc_form → upload documents → kyc submitted

3. KYC Verification (Admin)
   └─→ admin dashboard → approve/reject KYC → kyc verified/rejected

4. Loan Application
   └─→ loans.views.apply_loan → select type → upload documents → status: submitted

5. Officer Review
   └─→ loan_officer dashboard → request info/verify documents → status: under_review

6. Admin Final Approval
   └─→ admin dashboard → approve/reject → status: approved/rejected

7. Repayment Processing
   └─→ payments.views.make_payment → eSewa integration → update repayment status
```

## Authentication & Authorization

### Authentication Methods
1. **Email & Password** - Django's default authentication
2. **Google OAuth** - django-allauth integration
3. **Role-Based Access Control (RBAC)**

### User Roles
| Role | Permissions |
|------|-------------|
| **Customer** | Apply for loan, upload documents, view own applications, make payments |
| **Loan Officer** | Review assigned applications, request information, verify documents |
| **Senior Officer** | Review all applications, recommend approval |
| **Admin** | Full system access, verify KYC, approve/reject loans, manage users |

## Payment Integration

### eSewa Integration
- Payment Gateway: eSewa (Nepal's payment platform)
- Endpoint: `https://rc-epay.esewa.com.np/api/epay/main/v2/form`
- Merchant Code: `EPAYTEST`
- Integration: payments.views handles payment initiation and verification

## Database Configuration

### Development
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
```

### Production
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "greenloan",
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": "5432",
    }
}
```

## Static Files & Media

### Static Files (CSS, JS, Images)
- Location: `static/`
- Served by: WhiteNoise middleware
- Storage: `CompressedManifestStaticFilesStorage`

### Media Files (Uploads)
- Location: `media/`
- KYC documents: `media/kyc/`
- Loan documents: `media/documents/`

## Security Features

1. **CSRF Protection** - Django middleware
2. **SQL Injection Prevention** - Django ORM
3. **XFrame Options** - Set to SAMEORIGIN
4. **CORS Headers** - Controlled via middleware
5. **Password Validation** - Minimum length enforced
6. **Email Verification** - Signal-based verification
7. **Document Storage** - Secure file uploads with validation

## Deployment

### Docker Setup
```dockerfile
FROM python:3.10
# Builds image with all dependencies
# Exposes port 8000
# Runs Django development server
```

### Environment Variables
```env
DEBUG=True/False
EMAIL_HOST_USER=example@gmail.com
EMAIL_HOST_PASSWORD=app_password
DATABASE_URL=postgresql://...
```

### Hosting Options
- **Development**: PythonAnywhere
- **Production**: Linux server with Gunicorn + Nginx

## Dependencies (Key)

| Category | Package | Purpose |
|----------|---------|---------|
| **Core** | Django 4.2.30 | Web framework |
| **Auth** | django-allauth | User authentication & OAuth |
| **API** | djangorestframework | REST API |
| **Frontend** | crispy-forms, bootstrap5 | Form rendering |
| **Storage** | whitenoise | Static file serving |
| **Database** | psycopg | PostgreSQL driver |
| **ML** | tensorflow, opencv | Facial recognition (KYC) |
| **Email** | SMTP (Gmail) | Email notifications |

## Performance Considerations

1. **Database Indexing** - Status, created_at, user_id fields indexed
2. **Query Optimization** - Use select_related for ForeignKeys
3. **Caching** - Consider Redis for session management
4. **Async Tasks** - Celery for email, document processing
5. **Static Files** - WhiteNoise compression enabled

## Monitoring & Logging

- Simple History: Track all model changes via `HistoricalRecords()`
- Status History: JSON field for application status tracking
- Email Logs: Transaction emails via Gmail SMTP
