# Deployment Guide: Splitwise Clone

Follow these steps to deploy your production-ready Splitwise Clone using free-tier services.

---

## 1. Database: Supabase (Postgres)
1. Go to [Supabase](https://supabase.com/) and create a new project.
2. In **Project Settings > Database**, find your **Connection String**.
3. Choose the **URI** tab and copy the string (looks like `postgresql://postgres:[PASSWORD]@db.[ID].supabase.co:5432/postgres`).
4. **Note**: You will need this for the `DATABASE_URL` in Render.

---

## 2. Cache: Upstash (Redis)
1. Go to [Upstash](https://upstash.com/) and create a free account.
2. Click **Create Database**.
3. Scroll down to the **Node.js** or **Redis Connect** section.
4. Copy the **Redis URL** (looks like `redis://default:[PASSWORD]@...upstash.io:6379`).
5. **Note**: You will need this for the `REDIS_URL` in Render.

---

## 3. Backend: Render (FastAPI)
1. Go to [Render](https://render.com/) and create a new **Web Service**.
2. Connect your GitHub repository.
3. Choose **Docker** as the Runtime.
4. Add the following **Environment Variables**:
    - `DATABASE_URL`: (Your Supabase URI)
    - `REDIS_URL`: (Your Upstash URL)
    - `SECRET_KEY`: (A random string, e.g., `openssl rand -hex 32`)
    - `BACKEND_CORS_ORIGINS`: `["https://YOUR-VERCEL-DOMAIN.vercel.app"]`
5. Click **Deploy**.

---

## 4. Frontend: Vercel (Next.js)
1. Go to [Vercel](https://vercel.com/) and import your project.
2. Set the following **Environment Variable**:
    - `NEXT_PUBLIC_API_URL`: `https://YOUR-RENDER-APP.onrender.com/api/v1`
3. Click **Deploy**.

---

## 💡 Pro-Tips for Free Tiers
- **Graceful Redis**: If you don't provide `REDIS_URL`, the app will continue to work but will be slightly slower as it fetches balances directly from the DB.
- **Supabase SSL**: I have updated the code to automatically handle Supabase's SSL requirements (`?sslmode=require`).
- **Render Cold Starts**: Free Render instances spin down after inactivity. The first request might take ~30 seconds; I have added a loading state in the frontend to handle this gracefully.
