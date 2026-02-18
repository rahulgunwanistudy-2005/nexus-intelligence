# Deploying Nexus Intelligence to Streamlit Cloud

## Important: Architecture for Cloud Deployment

**Streamlit Cloud cannot run Playwright** (browser automation is blocked). You need to deploy the API separately and connect the dashboard to it.

### Recommended Architecture

```
┌─────────────────────┐
│  Streamlit Cloud    │
│    (Dashboard)      │  ──HTTP──>  ┌─────────────────┐
│  streamlit.app      │             │   Render/Railway│
└─────────────────────┘             │   (API + Scraper)│
                                    │   your-api.onrender.com
                                    └─────────────────┘
```

---

## Option 1: Dashboard on Streamlit + API on Render (Recommended)

### Step 1: Deploy API to Render

1. Go to https://render.com and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Configure:
   ```
   Name: nexus-api
   Environment: Docker
   Dockerfile Path: Dockerfile.api
   Instance Type: Free (or Starter for better performance)
   ```
5. Add Environment Variables:
   ```
   MAX_PAGES=3
   CACHE_TTL_HOURS=24
   ```
6. Click "Create Web Service"
7. Wait for deployment (~5 minutes)
8. Copy your API URL: `https://nexus-api-xxxx.onrender.com`

### Step 2: Deploy Dashboard to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select your repo: `nexus-intelligence`
5. Main file path: `src/dashboard/app.py`
6. Advanced settings:
   - Python version: `3.10`
   - Secrets:
     ```toml
     API_URL = "https://nexus-api-xxxx.onrender.com"
     ```
7. Click "Deploy"

### Step 3: Test

Visit your Streamlit app URL and search for a product. First search will take 60s (API is scraping), then subsequent searches are instant.

---

## Option 2: Dashboard on Streamlit + API on Railway

Railway has better performance than Render's free tier.

### Step 1: Deploy API to Railway

1. Go to https://railway.app and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repo
4. Railway will auto-detect the Dockerfile
5. Add variables:
   ```
   DOCKERFILE_PATH=Dockerfile.api
   MAX_PAGES=3
   CACHE_TTL_HOURS=24
   ```
6. Click "Deploy"
7. Under "Settings" → "Networking" → "Generate Domain"
8. Copy your URL: `https://nexus-api.up.railway.app`

### Step 2: Deploy Dashboard (same as Option 1, Step 2)

Use Railway API URL in the secrets.

---

## Option 3: Full Stack on Render (Docker Compose)

If you upgrade to a paid plan, Render supports docker-compose.

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: nexus-api
    env: docker
    dockerfilePath: ./Dockerfile.api
    envVars:
      - key: MAX_PAGES
        value: 3
      - key: CACHE_TTL_HOURS
        value: 24

  - type: web
    name: nexus-dashboard
    env: docker
    dockerfilePath: ./Dockerfile.dashboard
    envVars:
      - key: API_URL
        value: https://nexus-api.onrender.com
```

2. Push to GitHub
3. Render will auto-deploy both services

---

## Option 4: Everything on AWS/GCP (Full Control)

### AWS EC2

```bash
# 1. Launch Ubuntu 22.04 instance (t2.medium or larger)
# 2. SSH in and install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu

# 3. Clone and deploy
git clone https://github.com/yourusername/nexus-intelligence
cd nexus-intelligence
docker-compose up -d

# 4. Configure security group to allow ports 8000, 8501
```

Your dashboard: `http://<instance-ip>:8501`

### Google Cloud Run

```bash
# Deploy API
gcloud run deploy nexus-api \
  --source . \
  --dockerfile Dockerfile.api \
  --set-env-vars MAX_PAGES=3,CACHE_TTL_HOURS=24 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi

# Get API URL
API_URL=$(gcloud run services describe nexus-api --region us-central1 --format 'value(status.url)')

# Deploy Dashboard
gcloud run deploy nexus-dashboard \
  --source . \
  --dockerfile Dockerfile.dashboard \
  --set-env-vars API_URL=$API_URL \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Files to Commit for Streamlit Cloud

```bash
# Add these files to your repo:
git add .streamlit/config.toml
git add packages.txt
git add requirements-streamlit.txt
git commit -m "Add Streamlit Cloud config"
git push
```

---

## Cost Comparison

| Platform | API | Dashboard | Total/month |
|----------|-----|-----------|-------------|
| **Render Free + Streamlit** | $0 (sleeps after 15min) | $0 | $0 |
| **Railway Hobby + Streamlit** | $5 | $0 | $5 |
| **Render Standard + Streamlit** | $7 | $0 | $7 |
| **AWS EC2 t2.medium** | $30 | - | $30 |
| **GCP Cloud Run (pay-per-use)** | ~$2-10 | ~$1-5 | $3-15 |

---

## Troubleshooting

### "Playwright not found" on Render/Railway

Make sure your `Dockerfile.api` has:
```dockerfile
RUN playwright install chromium --with-deps
```

### Dashboard shows "API Offline"

1. Check API logs on Render/Railway
2. Verify API_URL in Streamlit secrets matches your deployed API
3. Test API directly: `curl https://your-api-url/health`

### API times out on first request

Free tiers of Render/Railway "sleep" after inactivity. First request wakes the service (takes 30-60s), then it's fast.

Upgrade to paid tier for always-on service.

---

## Recommended Setup for Production

**Best value:** Railway API ($5/mo) + Streamlit Cloud (free)
- Always-on API (no cold starts)
- Unlimited dashboard usage
- Total: $5/month

**Enterprise:** AWS/GCP
- Full control
- Custom domain
- Scalable
- Total: $30-50/month