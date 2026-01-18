# Deployment Guide

This guide covers multiple deployment options for the TTC Delay Risk Predictor.

## Option 1: Railway (Recommended - Easiest)

Railway can deploy both backend and frontend together.

### Backend Deployment

1. **Sign up** at [railway.app](https://railway.app)

2. **Create new project** → "Deploy from GitHub repo"

3. **Configure**:
   - Root directory: `/` (root of repo)
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

4. **Set environment variables** (if needed):
   - `PORT`: Railway sets this automatically

5. **Deploy** → Railway will detect the `Procfile` and deploy

### Frontend Deployment (Separate Service)

1. **Create new service** in same Railway project

2. **Configure**:
   - Root directory: `/web`
   - Build command: `npm install && npm run build`
   - Start command: `npx serve -s dist -l $PORT`

3. **Set environment variable**:
   - `VITE_API_URL`: Your backend URL (e.g., `https://your-backend.railway.app`)

4. **Update frontend API URL**:
   ```typescript
   // web/src/api/client.ts
   const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
   ```

## Option 2: Render

### Backend Deployment

1. **Sign up** at [render.com](https://render.com)

2. **New** → "Web Service" → Connect GitHub repo

3. **Configure**:
   - Name: `ttc-delay-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

4. **Deploy**

### Frontend Deployment

1. **New** → "Static Site" → Connect GitHub repo

2. **Configure**:
   - Root directory: `web`
   - Build command: `npm install && npm run build`
   - Publish directory: `web/dist`

3. **Set environment variable**:
   - `VITE_API_URL`: Your backend URL

## Option 3: Vercel (Frontend) + Railway/Render (Backend)

### Frontend on Vercel

1. **Sign up** at [vercel.com](https://vercel.com)

2. **Import project** from GitHub

3. **Configure**:
   - Framework Preset: Vite
   - Root directory: `web`
   - Build command: `npm run build`
   - Output directory: `dist`

4. **Set environment variable**:
   - `VITE_API_URL`: Your backend URL

### Backend on Railway/Render

Follow Option 1 or 2 for backend deployment.

## Option 4: Docker Deployment

### Build Docker Image

```bash
docker build -t ttc-delay-risk .
```

### Run Locally

```bash
docker run -p 8000:8000 ttc-delay-risk
```

### Deploy to Docker Hub / Cloud Run / ECS

1. **Build and tag**:
   ```bash
   docker build -t yourusername/ttc-delay-risk:latest .
   ```

2. **Push to Docker Hub**:
   ```bash
   docker push yourusername/ttc-delay-risk:latest
   ```

3. **Deploy** to:
   - Google Cloud Run
   - AWS ECS/Fargate
   - Azure Container Instances
   - DigitalOcean App Platform

## Pre-Deployment Checklist

- [ ] Update `web/src/api/client.ts` with production API URL
- [ ] Ensure `model/delay_risk_model_latest.pkl` is committed (or uploaded separately)
- [ ] Ensure `data/features/features.csv` exists (needed for feature stats)
- [ ] Ensure `data/gtfs/` files exist (needed for station data)
- [ ] Test locally: `./api/start.sh` and `cd web && npm run dev`
- [ ] Build frontend: `cd web && npm run build`
- [ ] Check `.gitignore` doesn't exclude necessary files

## Environment Variables

### Backend
- `PORT`: Server port (usually set by platform)
- `CORS_ORIGINS`: Comma-separated list of allowed origins (optional)

### Frontend
- `VITE_API_URL`: Backend API URL (required for production)

## File Size Considerations

The model file (`delay_risk_model_latest.pkl`) is ~600MB. Some platforms have file size limits:

- **Railway**: 500MB limit (may need to upload model separately)
- **Render**: 500MB limit
- **Heroku**: 500MB limit
- **Vercel**: 100MB limit (frontend only)

### Solutions for Large Model Files:

1. **Use external storage** (S3, Google Cloud Storage):
   - Upload model to cloud storage
   - Download on startup in `api/dependencies.py`

2. **Git LFS** (Git Large File Storage):
   ```bash
   git lfs install
   git lfs track "*.pkl"
   git add .gitattributes
   git add model/delay_risk_model_latest.pkl
   ```

3. **Split deployment**:
   - Deploy code to platform
   - Upload model file separately via platform's file system or storage

## Quick Deploy Commands

### Railway (CLI)
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### Render (CLI)
```bash
npm i -g render-cli
render login
render deploy
```

## Troubleshooting

### Model not loading
- Check model file exists: `ls -lh model/delay_risk_model_latest.pkl`
- Check file size limits
- Check logs for loading errors

### CORS errors
- Update `api/config.py` CORS_ORIGINS with your frontend URL
- Check environment variables

### Frontend can't connect to API
- Verify `VITE_API_URL` is set correctly
- Check backend is running and accessible
- Check CORS settings

## Post-Deployment

1. Test all endpoints:
   - `/health`
   - `/predict`
   - `/data/routes`
   - `/data/locations`

2. Monitor logs for errors

3. Set up monitoring (optional):
   - Railway/Render have built-in monitoring
   - Add Sentry for error tracking
   - Add analytics to frontend

