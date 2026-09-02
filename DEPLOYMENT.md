# Deployment Guide: Splitwise Clone

Follow these steps to deploy your production-ready Splitwise Clone using free-tier services.

---

## 1. Database: Neon (Postgres)
1. Go to [Neon](https://neon.tech/) and create a new project.
2. Click **Connect** and disable connection pooling.
3. Copy the direct connection string (it starts with `postgresql://` and contains `neon.tech`).
4. **Note**: You will need this for the `DATABASE_URL` in Render.

---

## 2. Backend: Render (FastAPI)
1. Go to [Render](https://render.com/) and create a new **Web Service**.
2. Connect your GitHub repository.
3. Choose **Docker** as the Runtime.
4. Add the following **Environment Variables**:
    - `DATABASE_URL`: (Your direct Neon URI)
    - `SECRET_KEY`: (A random string, e.g., `openssl rand -hex 32`)
    - `BACKEND_CORS_ORIGINS`: `["https://YOUR-VERCEL-DOMAIN.vercel.app"]`
5. Click **Deploy**.

---

## 3. Frontend: Vercel (Next.js)
1. Go to [Vercel](https://vercel.com/) and import your project.
2. Set the following **Environment Variable**:
    - `NEXT_PUBLIC_API_URL`: `https://YOUR-RENDER-APP.onrender.com/api/v1`
3. Click **Deploy**.

---

## 💡 Pro-Tips for Free Tiers
- **Neon SSL**: Keep the SSL parameters included in Neon's generated connection string.
- **Render Cold Starts**: Free Render instances spin down after inactivity. The first request might take ~30 seconds; I have added a loading state in the frontend to handle this gracefully.
