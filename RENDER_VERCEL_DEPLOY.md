# Deployment Guide: Backend (Render) + Frontend (Vercel)

## Prerequisites

1. **GitHub Repository** - Your code must be on GitHub
2. **Render Account** - Sign up at [render.com](https://render.com) (free tier available)
3. **Vercel Account** - Sign up at [vercel.com](https://vercel.com) (free tier available)

---

## Part 1: Deploy Backend to Render

### Step 1: Push Code to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/ttc-delay-risk.git
git branch -M main
git push -u origin main
```

**⚠️ Important:** Your model file (265MB) exceeds GitHub's 100MB limit. Options:
- **Option A:** Use Git LFS (recommended)
  ```bash
  brew install git-lfs
  git lfs install
  git lfs track "*.pkl"
  git add .gitattributes model/delay_risk_model_latest.pkl
  git commit -m "Add model with Git LFS"
  git push
  ```
- **Option B:** Exclude model from git, upload separately to Render

### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account (if not already connected)
4. Select your repository: `ttc-delay-risk`

### Step 3: Configure Backend Settings

Fill in the following:

- **Name:** `ttc-delay-api` (or your preferred name)
- **Environment:** `Python 3`
- **Region:** Choose closest to you (e.g., `Oregon (US West)`)
- **Branch:** `main`
- **Root Directory:** Leave empty (root of repo)
- **Build Command:** 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```bash
  uvicorn api.main:app --host 0.0.0.0 --port $PORT
  ```

### Step 4: Environment Variables (Optional)

Click **"Advanced"** → **"Environment Variables"**:
- No variables needed for basic setup (CORS allows all origins)

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will start building and deploying
3. Wait for deployment to complete (5-10 minutes)
4. **Copy your backend URL** (e.g., `https://ttc-delay-api.onrender.com`)

### Step 6: Test Backend

```bash
# Health check
curl https://YOUR-BACKEND-URL.onrender.com/health

# Should return: {"status":"healthy","model_loaded":true}
```

**⚠️ Note:** Render free tier services sleep after 15 minutes of inactivity. First request may take 30-60 seconds to wake up.

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Update Frontend API URL

Before deploying, update the frontend to use your Render backend URL:

1. **Option A: Use Environment Variable (Recommended)**

   Create `web/.env.production`:
   ```bash
   VITE_API_URL=https://YOUR-BACKEND-URL.onrender.com
   ```

2. **Option B: Update client.ts directly**

   Edit `web/src/api/client.ts`:
   ```typescript
   const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://YOUR-BACKEND-URL.onrender.com';
   ```

### Step 2: Build Frontend Locally (Test)

```bash
cd web
npm install
npm run build
```

Verify `web/dist` folder was created successfully.

### Step 3: Deploy to Vercel

#### Method A: Vercel Dashboard (Easiest)

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository: `ttc-delay-risk`
4. Configure project:
   - **Framework Preset:** Vite
   - **Root Directory:** `web` (IMPORTANT!)
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

5. **Environment Variables:**
   - Click **"Environment Variables"**
   - Add: `VITE_API_URL` = `https://YOUR-BACKEND-URL.onrender.com`
   - Select: **Production**, **Preview**, **Development**

6. Click **"Deploy"**
7. Wait for deployment (2-3 minutes)
8. **Copy your frontend URL** (e.g., `https://ttc-delay-risk.vercel.app`)

#### Method B: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd web
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? ttc-delay-risk
# - Directory? ./
# - Override settings? No
```

### Step 4: Update CORS in Backend (If Needed)

If you get CORS errors, update `api/config.py`:

```python
# Update CORS_ORIGINS with your Vercel URL
CORS_ORIGINS = [
    "https://your-frontend.vercel.app",
    "http://localhost:3000"  # For local dev
]
```

Then redeploy backend on Render.

---

## Part 3: Verify Deployment

### Test Frontend
1. Open your Vercel URL: `https://your-frontend.vercel.app`
2. Check connection status (should show "Connected")
3. Make a test prediction

### Test Backend Directly
```bash
# Health check
curl https://YOUR-BACKEND.onrender.com/health

# Prediction test
curl -X POST https://YOUR-BACKEND.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "route": "1",
    "location": "Finch Station",
    "hour": 8,
    "day_of_week": 1,
    "mode": "subway"
  }'
```

---

## Troubleshooting

### Backend Issues

**Problem: Model file too large (265MB)**
- **Solution:** Use Git LFS or exclude from git and upload separately
- Render has a 500MB limit, so 265MB should be fine if uploaded correctly

**Problem: Build fails**
- Check `requirements.txt` has all dependencies
- Check Render logs for specific error
- Verify Python version matches `runtime.txt`

**Problem: Service sleeps (free tier)**
- First request after 15 min inactivity takes 30-60s
- Consider upgrading to paid tier for always-on service
- Or use a cron job to ping your service every 10 minutes

**Problem: CORS errors**
- Update `api/config.py` with your Vercel URL
- Redeploy backend

### Frontend Issues

**Problem: Can't connect to backend**
- Verify `VITE_API_URL` environment variable is set in Vercel
- Check backend URL is correct (no trailing slash)
- Check backend is awake (make a request to `/health` first)

**Problem: Build fails**
- Check `web/package.json` has all dependencies
- Check Vercel logs for specific error
- Verify `Root Directory` is set to `web` in Vercel settings

**Problem: Environment variable not working**
- Variables must start with `VITE_` to be exposed to frontend
- Redeploy after adding/changing environment variables
- Check Vercel dashboard → Settings → Environment Variables

---

## Quick Reference

### Backend URL (Render)
```
https://YOUR-SERVICE-NAME.onrender.com
```

### Frontend URL (Vercel)
```
https://YOUR-PROJECT-NAME.vercel.app
```

### Important Files
- `requirements.txt` - Python dependencies
- `Procfile` - Render start command (optional, can specify in dashboard)
- `runtime.txt` - Python version
- `web/package.json` - Frontend dependencies
- `web/vite.config.ts` - Vite configuration

### Environment Variables

**Render (Backend):**
- None required for basic setup

**Vercel (Frontend):**
- `VITE_API_URL` - Your Render backend URL

---

## Next Steps

1. ✅ Backend deployed to Render
2. ✅ Frontend deployed to Vercel
3. ✅ Test both services
4. 🎉 Share your app!

### Optional Improvements

- Add custom domain to Vercel
- Set up monitoring/analytics
- Add error tracking (Sentry)
- Set up CI/CD for automatic deployments

