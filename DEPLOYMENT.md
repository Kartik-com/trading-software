# Production Deployment Guide

## Prerequisites

- Python 3.10+ installed
- Node.js 18+ installed  
- Telegram Bot Token and Chat ID
- Hosting accounts (Railway/Render for backend, Vercel for frontend)

## Part 1: Backend Deployment

### Option A: Railway (Recommended)

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Backend**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Navigate to backend
   cd backend
   
   # Initialize project
   railway init
   
   # Deploy
   railway up
   ```

3. **Set Environment Variables**
   - Go to Railway dashboard
   - Select your project
   - Go to Variables tab
   - Add:
     - `TELEGRAM_BOT_TOKEN=your_token`
     - `TELEGRAM_CHAT_ID=your_chat_id`
     - `CORS_ORIGINS=https://your-frontend-url.vercel.app`
     - `PORT=8000`

4. **Get Backend URL**
   - Railway will provide a URL like: `https://your-app.railway.app`
   - Save this for frontend configuration

### Option B: Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your repository
   - Select `backend` directory

3. **Configure Service**
   - **Name**: `crypto-trading-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

4. **Set Environment Variables**
   - Add the same variables as Railway

### Option C: DigitalOcean App Platform

1. **Create DigitalOcean Account**
   - Go to [digitalocean.com](https://digitalocean.com)

2. **Create New App**
   - Apps → Create App
   - Connect GitHub repository
   - Select `backend` directory

3. **Configure**
   - **Type**: Web Service
   - **Run Command**: `python main.py`
   - Add environment variables

## Part 2: Frontend Deployment

### Vercel (Recommended)

1. **Create Vercel Account**
   - Go to [vercel.com](https://vercel.com)
   - Sign up with GitHub

2. **Import Project**
   - Click "Add New" → "Project"
   - Import your repository
   - Select `frontend` directory as root

3. **Configure Build Settings**
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

4. **Set Environment Variable**
   - Go to Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app`

5. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete
   - Your app will be live at: `https://your-app.vercel.app`

### Alternative: Netlify

1. **Create Netlify Account**
   - Go to [netlify.com](https://netlify.com)

2. **Deploy**
   - Drag and drop the `frontend/.next` folder
   - Or connect GitHub repository

3. **Configure**
   - Set build command: `npm run build`
   - Set environment variable: `NEXT_PUBLIC_API_URL`

## Part 3: Post-Deployment Configuration

### Update CORS Origins

1. Go to your backend hosting platform
2. Update `CORS_ORIGINS` environment variable:
   ```
   CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
   ```
3. Restart the backend service

### Test the Deployment

1. **Backend Health Check**
   ```bash
   curl https://your-backend-url.railway.app/
   ```
   Should return JSON with status "running"

2. **Frontend Access**
   - Open `https://your-frontend.vercel.app`
   - Check if dashboard loads
   - Verify WebSocket connection shows "Live"

3. **Telegram Test**
   - Backend should send a test message on startup
   - Check your Telegram for the message

## Part 4: Monitoring & Maintenance

### Backend Logs

**Railway:**
```bash
railway logs
```

**Render:**
- Go to dashboard → Logs tab

**DigitalOcean:**
- Go to app → Runtime Logs

### Frontend Logs

**Vercel:**
- Go to project → Deployments → Click deployment → View Function Logs

### Common Issues

**Backend not starting:**
- Check Python version (must be 3.10+)
- Verify all environment variables are set
- Check logs for errors

**Frontend can't connect to backend:**
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS settings on backend
- Ensure backend is running

**No Telegram alerts:**
- Verify bot token and chat ID
- Check if bot is blocked
- Review backend logs for Telegram errors

**WebSocket not connecting:**
- Some hosting platforms don't support WebSockets
- Railway and Render support WebSockets by default
- Check firewall settings

## Part 5: Scaling & Performance

### Backend Scaling

**Railway:**
- Auto-scales based on usage
- Can set resource limits in dashboard

**Render:**
- Upgrade to paid plan for auto-scaling
- Set instance type in dashboard

### Frontend Scaling

**Vercel:**
- Automatically scales globally
- Uses CDN for static assets
- Serverless functions scale automatically

### Database (Optional)

If you want to persist signal history:

1. **Add PostgreSQL** (Railway/Render)
   - Add database service
   - Update backend to use database instead of in-memory storage

2. **Environment Variable**
   ```
   DATABASE_URL=postgresql://user:pass@host:port/db
   ```

## Part 6: Custom Domain (Optional)

### Frontend Custom Domain

**Vercel:**
1. Go to Settings → Domains
2. Add your domain
3. Update DNS records as instructed

### Backend Custom Domain

**Railway:**
1. Go to Settings → Domains
2. Add custom domain
3. Update DNS records

## Part 7: Security Checklist

- [ ] Environment variables are not committed to Git
- [ ] Telegram bot token is kept secret
- [ ] CORS is configured correctly
- [ ] HTTPS is enabled (automatic on Vercel/Railway)
- [ ] Rate limiting is in place (built into backend)
- [ ] No sensitive data in logs

## Part 8: Cost Estimates

### Free Tier Options

**Backend:**
- Railway: $5 free credit/month
- Render: 750 hours/month free
- DigitalOcean: $200 credit for 60 days

**Frontend:**
- Vercel: Unlimited for personal projects
- Netlify: 100GB bandwidth/month free

### Paid Plans (if needed)

**Backend:**
- Railway: ~$5-20/month
- Render: $7/month minimum
- DigitalOcean: $5/month minimum

**Frontend:**
- Vercel: Free for personal use
- Netlify: Free for personal use

## Part 9: Backup & Recovery

### Backup Signal History

If using in-memory storage, signals are lost on restart.

**Solution:**
1. Add database (PostgreSQL)
2. Or export signals to CSV periodically

### Backup Configuration

- Keep `.env.example` files updated
- Document any custom changes
- Use Git for version control

## Part 10: Updates & Maintenance

### Updating Backend

```bash
# Pull latest changes
git pull origin main

# Railway
railway up

# Render (auto-deploys from GitHub)
# Just push to main branch
```

### Updating Frontend

```bash
# Pull latest changes
git pull origin main

# Vercel (auto-deploys from GitHub)
# Just push to main branch
```

### Dependency Updates

**Backend:**
```bash
pip install --upgrade -r requirements.txt
```

**Frontend:**
```bash
npm update
npm audit fix
```

## Support

For deployment issues:
- Check hosting platform documentation
- Review application logs
- Verify environment variables
- Test locally first

---

**Remember:** Start with free tiers and upgrade only if needed. Most personal use cases will stay within free limits.
