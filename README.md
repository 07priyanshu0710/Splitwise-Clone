# Splitwise Clone

A production-grade, high-performance expense-splitting application with **Clean Architecture** (FastAPI) and a **Neo-brutalist** frontend (Next.js), featuring Redis-backed balance caching and robust cloud resilience.

**Live Demo:**
- 🌐 Frontend: [splitwise-clone-dusky.vercel.app](https://splitwise-clone-dusky.vercel.app)
- ⚡ API: [splitwise-clone-96iy.onrender.com](https://splitwise-clone-96iy.onrender.com)
- 📖 API Docs: [Swagger UI](https://splitwise-clone-96iy.onrender.com/docs)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11) |
| Frontend | Next.js 16 (React) |
| Database | PostgreSQL (Supabase) |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Auth | JWT + bcrypt |
| Backend Hosting | Render (Docker) |
| Frontend Hosting | Vercel |
| Server | Gunicorn + Uvicorn Workers |

## Features

- **User Authentication** — Register (with optional mobile number), login, JWT-based session management
- **Groups** — Create groups, add members by email or mobile number, role-based membership (admin/member)
- **Expense Splitting** — 4 split types:
  - **Equal** — Auto-divides with penny-accurate remainder handling
  - **Unequal** — Exact per-user amounts with sum validation
  - **Percentage** — Percentage-based with automatic rounding correction
  - **Shares** — Proportional split based on share ratios
- **Real-Time Balances** — High-performance bidirectional debt ledger with **Redis Read-Through caching** and automatic offset cancellation.
- **Fail-Safe Resilience** — Architectural "Circuit Breaker" handles intermittent Redis or Database downtime gracefully.
- **Settlements** — Record payments between users, automatically Reducing outstanding balances across all cached layers.
- **Monthly Reports** — Professional aggregated spending analytics.

## Architecture

```
├── app/
│   ├── api/v1/endpoints/     # Route handlers
│   ├── core/                 # Config, security, JWT
│   ├── db/                   # SQLAlchemy base, session, migrations
│   ├── models/               # ORM models
│   ├── repositories/         # Data access layer
│   ├── schemas/              # Pydantic request/response models
│   └── services/             # Business logic layer
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages (App Router)
│       └── lib/              # API client with JWT handling
├── Dockerfile                # Multi-stage production build
├── gunicorn_conf.py          # Production WSGI config
└── render.yaml               # Render deployment spec
```

## Production Deployment

### Backend (Render)

1. Connect your GitHub repository to Render
2. Set **Environment** to `Docker`
3. Add environment variables:
   - `DATABASE_URL` — Supabase connection string (Session Mode, port `6543`)
   - `SECRET_KEY` — Random 32+ character string for JWT signing
4. Deploy — Alembic migrations run automatically on boot

### Frontend (Vercel)

1. Import the repository on Vercel
2. Set **Root Directory** to `frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://splitwise-clone-96iy.onrender.com/api/v1`
4. Deploy

## Local Development

### Prerequisites
- Python 3.11+, Node.js 18+, Docker

### Backend
```bash
docker compose up -d                    # Start PostgreSQL
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                    # Apply migrations
uvicorn app.main:app --reload           # Start on :8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                             # Start on :3000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login (returns JWT) |
| GET | `/api/v1/users/me` | Get current user profile |
| PUT | `/api/v1/users/me` | Update profile |
| GET | `/api/v1/groups/` | List user's groups |
| POST | `/api/v1/groups/` | Create a group |
| GET | `/api/v1/groups/{id}` | Get group with members |
| POST | `/api/v1/groups/{id}/members` | Add member by email/mobile |
| POST | `/api/v1/expenses/` | Create an expense with splits |
| GET | `/api/v1/expenses/group/{id}` | List group expenses |
| GET | `/api/v1/balances/me` | Get all user balances |
| GET | `/api/v1/balances/group/{id}` | Get group balances |
| POST | `/api/v1/settlements/` | Record a settlement payment |
| GET | `/api/v1/reports/monthly-summary` | Monthly spending summary |

## License

MIT
