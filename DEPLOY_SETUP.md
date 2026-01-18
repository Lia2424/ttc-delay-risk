# Deployment Setup Guide

## Step 1: Initialize Git Repository

```bash
# Initialize git repo
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: TTC Delay Risk Predictor"
```

## Step 2: Handle Large Model File (265MB)

GitHub has a 100MB file limit. Your model file is 265MB, so you need Git LFS:

### Option A: Use Git LFS (Recommended)

```bash
# Install Git LFS (if not installed)
brew install git-lfs  # macOS
# OR download from: https://git-lfs.github.com

# Initialize Git LFS
git lfs install

# Track .pkl files
git lfs track "*.pkl"
git add .gitattributes

# Add model file
git add model/delay_risk_model_latest.pkl
```

### Option B: Exclude Model File (Upload Separately)

If Git LFS doesn't work, exclude the model and upload it separately:

```bash
# Add to .gitignore
echo "model/delay_risk_model_latest.pkl" >> .gitignore

# Then upload model file separately to your deployment platform
```

## Step 3: Create GitHub Repository

1. Go to [github.com](https://github.com) and sign in
2. Click **"New repository"**
3. Name it: `ttc-delay-risk` (or your preferred name)
4. **Don't** initialize with README (you already have files)
5. Click **"Create repository"**

## Step 4: Push to GitHub

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/ttc-delay-risk.git

# Push to GitHub
git branch -M main
git push -u origin main
```

If using Git LFS, make sure it's installed on your system first!

## Step 5: Deploy

After pushing to GitHub, follow the deployment guide in `DEPLOYMENT.md`:

### Quick Deploy Options:

**Railway (Easiest):**
1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select your repo
4. Railway auto-detects and deploys!

**Render:**
1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect GitHub repo
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

## Troubleshooting

### Git LFS Issues
- Make sure Git LFS is installed: `git lfs version`
- If files are already committed, migrate: `git lfs migrate import --include="*.pkl"`

### Model File Too Large
- Use Git LFS (Option A above)
- OR exclude from git and upload separately to deployment platform
- OR compress the model (may reduce accuracy)

### Deployment Issues
- Check `DEPLOYMENT.md` for platform-specific guides
- Make sure all required files are committed
- Verify environment variables are set

