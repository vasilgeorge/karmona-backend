# 🌙 Karmona Backend API

AI-powered karma reflection API that blends astrology and daily journaling.

## 🎯 Features

- **User Onboarding**: Birth chart calculation (Sun/Moon signs)
- **Daily Reflections**: AI-generated karma readings via AWS Bedrock
- **Astrology Integration**: Real-time horoscopes and planetary context
- **History Tracking**: View past reflections and karma scores
- **Share Cards**: Generate beautiful reflection images

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **Python 3.12** - Latest stable Python
- **uv** - Lightning-fast package manager
- **AWS Bedrock** - Claude AI for reflections
- **Supabase** - PostgreSQL database & auth
- **pyswisseph** - Swiss Ephemeris for astrology
- **Aztro API** - Daily horoscopes

## 📦 Project Structure

```
karmona-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Settings & configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check
│   │   ├── onboarding.py    # User registration
│   │   ├── reflection.py    # Reflection generation
│   │   └── history.py       # User history
│   └── services/
│       ├── __init__.py
│       ├── supabase_service.py    # Database operations
│       ├── astrology_service.py   # Astrology calculations
│       └── bedrock_service.py     # AI reflection generation
├── pyproject.toml           # Dependencies
├── Dockerfile               # Container definition
├── railway.toml             # Railway deployment config
├── .env.example             # Example environment variables
└── README.md                # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) installed
- AWS account with Bedrock access
- Supabase project

### 2. Installation

```bash
# Clone the repository
git clone <your-repo>
cd karmona-backend

# Install dependencies with uv
uv sync

# Copy environment file
cp .env.example .env
# Edit .env with your credentials
```

### 3. Configure Environment

Edit `.env` with your credentials:

```env
# AWS Bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_key
SUPABASE_ANON_KEY=your_key

# CORS (add your frontend URL)
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com
```

### 4. Set Up Database

Run the SQL schema in your Supabase project:

```sql
-- See database/schema.sql
```

### 5. Run Development Server

```bash
# Using uv
uv run uvicorn app.main:app --reload --port 8000

# Or with Python directly
python -m uvicorn app.main:app --reload --port 8000
```

API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### Health Check

```http
GET /health
```

### Onboarding

```http
POST /api/v1/onboarding
Content-Type: application/json

{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "birthdate": "1995-08-15",
  "birth_time": "14:30",
  "birth_place": "New York, NY"
}
```

### Generate Reflection

```http
POST /api/v1/reflection/generate
Content-Type: application/json

{
  "user_id": "uuid",
  "mood": "good",
  "actions": ["meditated", "helped", "worked"],
  "note": "Had a productive day"
}
```

### Get History

```http
GET /api/v1/history/{user_id}?limit=7
```

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t karmona-backend .
```

### Run Container

```bash
docker run -p 8000:8000 --env-file .env karmona-backend
```

## 🚂 Railway Deployment

1. Create a new Railway project
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy!

Railway will automatically:
- Detect the Dockerfile
- Build the image
- Deploy to a public URL

## 🧪 Testing

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests (coming soon)
uv run pytest

# Linting
uv run ruff check app/

# Formatting
uv run black app/

# Type checking
uv run mypy app/
```

## 📊 Database Schema

See `database/schema.sql` for the complete schema.

**Tables:**
- `users` - User profiles with astrology data
- `daily_reports` - Daily karma reflections
- `waitlist_emails` - Email waitlist (shared with frontend)

## 🔒 Security Notes

- Use environment variables for all secrets
- Never commit `.env` file
- Use service role key for backend operations
- Validate all user inputs
- Enable RLS (Row Level Security) in Supabase for production

## 🛠️ Development

### Add New Dependencies

```bash
# Add a package
uv add package-name

# Add dev dependency
uv add --dev package-name
```

### Code Style

- Python 3.12+ syntax
- Type hints everywhere
- Black formatting (line length: 100)
- Ruff linting
- Docstrings for all public functions

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_REGION` | AWS region for Bedrock | Yes |
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes |
| `BEDROCK_MODEL_ID` | Bedrock model ID | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service key | Yes |
| `ALLOWED_ORIGINS` | CORS allowed origins | Yes |
| `DEBUG` | Enable debug mode | No (default: false) |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

MIT

## 🌟 Acknowledgments

- AWS Bedrock for AI capabilities
- Supabase for database & auth
- Aztro API for horoscope data
- Swiss Ephemeris for astrology calculations

---

Built with ❤️ for Karmona
