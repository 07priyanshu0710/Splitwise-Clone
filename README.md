# Splitwise Clone Backend

A production-grade, fully featured Splitwise clone backend built using Clean Architecture principles, leveraging modern Python standards. It is tailored to provide lightning fast responses to resolving complex mathematical shared debts iteratively using native PostgreSQL computations.

## Technologies Used
* **Framework:** FastAPI (Python 3.11)
* **Database:** PostgreSQL & Redis
* **ORM:** SQLAlchemy 2.0
* **Migrations:** Alembic
* **Authentication:** JWT (JSON Web Tokens) with `bcrypt` secure hashing
* **Deployment & CI:** Docker & Github Actions (`pytest`)

## Features Implemented
1. **User Auth**: Secure User Registration, Session Login, & JWT token mechanisms.
2. **Groups Maintenance**: Assemble groups of users natively securely guarded with group validation perimeters.
3. **Advanced Expense Parsing**: Dynamically compute expenses based upon 4 formats efficiently:
    - **EQUAL**: Divides amount accurately resolving pennies math implicitly.
    - **UNEQUAL**: Strict individual exact quantity splits.
    - **PERCENTAGE**: Scales sum across percentages ensuring it perfectly captures total quantity.
    - **SHARES**: Dynamically evaluates splits based on total share proportions (e.g., 2 shares over 5 total = 40% owed quantity).
4. **Iterative Debt Reduction**: Real-time cached Ledger Balance computation mathematically canceling out opposing user debts seamlessly.
5. **Settlements**: Native playback logic recording payback traces between friends seamlessly neutralizing cached debt ledgers effortlessly.
6. **Robust Test Parquet**: End-to-end Python native `pytest` Integration execution safely masking test DB deployments.

## Free Production Deployment (Supabase + Render)

Our setup is specifically tuned referencing top tier production configuration (combining `Gunicorn` handling scaling multiple concurrent CPU threading natively bridging via `uvicorn.workers.UvicornWorker`).

**1. Database (Supabase)**
- Navigate to Supabase and create a fresh organization.
- Fetch your **Database URL**.
- **Crucial**: Free tier databases natively enforce PostgreSQL connection maxes. Use the **Session Mode** URI ending in port `6543` provided inside your Supavisor connection dashboard to safely proxy dynamic traffic threads!

**2. Web Environment (Render)**
- Bind this Git repository directly.
- Ensure the Render **Environment** is set to `Docker`.
- Set Environment Variables:
  - `DATABASE_URL` = `<your-supabase-connection-string>`
- Render handles extracting the internal native Dockerfile configuring CPU variables globally.

## Running Locally

### 1. Spin up Databases via Docker
Configure local dependencies safely bypassing local binary installations.
```bash
docker compose up -d
```

### 2. Prepare Virtual Environment
Install required components correctly matching standard environments.
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Establish Postgres Data
Update schemas recursively mapping core definitions.
```bash
alembic upgrade head
```

### 4. Boot Dev Web Server
Server runs on port `:8000` via Uvicorn native loader.
```bash
uvicorn app.main:app --reload
```

## Running Tests
Run tests mapped over `splitwise_test` local ephemeral database.
```bash
pytest tests/ -v
```

## Interactive API Docs (Swagger)
Explore and execute natively via FastAPI's UI safely.
Available locally via: `http://localhost:8000/docs`
