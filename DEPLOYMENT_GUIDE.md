# Deployment Guide: Render & Vercel

Follow these steps to deploy your trading software to the cloud.

## 1. Backend Deployment (Render)

1.  **Create a New Web Service**: Log in to [Render](https://render.com/) and create a new "Web Service".
2.  **Connect Repo**: Connect your GitHub repository.
3.  **Configure Service**:
    *   **Runtime**: `Docker`
    *   **Region**: Choose the one closest to you.
    *   **Plan**: Free or Starter.
4.  **Environment Variables**:
    *   `PORT`: `8000`
    *   `EXCHANGE`: `binance`
    *   `CORS_ORIGINS`: `*` (or your Vercel URL later).
    *   `TELEGRAM_BOT_TOKEN`: (Your Token)
    *   `TELEGRAM_CHAT_ID`: (Your Chat ID)
5.  **Persistence (Crucial)**:
    *   Go to **Advanced** -> **Add Disk**.
    *   **Mount Path**: `/app` (or specifically for the data folder if you move it).
    *   *Note: On the Free Plan, disks aren't available. The `signals.json` will persist during the session but might reset on server sleep. For long-term cataloging, consider the Starter plan with a Disk.*

## 2. Frontend Deployment (Vercel)

1.  **Create a New Project**: Log in to [Vercel](https://vercel.com/) and "Add New" -> "Project".
2.  **Connect Repo**: Import your GitHub repository.
3.  **Root Directory**: Set to `frontend`.
4.  **Environment Variables**:
    *   `NEXT_PUBLIC_API_URL`: Use your Render URL (e.g., `https://your-app.onrender.com`).
5.  **Deploy**: Click Deploy.

## 3. Post-Deployment Verification
- Open your Vercel URL.
- Check if the "Realtime Clock" is ticking (this confirms connectivity to Render).
- Your trade signal "Catalog" will start populating and stay saved in `signals.json`.

> [!TIP]
> **Old Messages**: The `signals.json` file now ensures that old signals are reloaded every time the server starts, creating a "Proper Catalog" as you requested.
