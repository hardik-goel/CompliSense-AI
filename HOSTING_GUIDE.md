# Hosting Guide - Cheapest Options for CompliSense-AI

## 🏆 Recommended: Railway.app (Easiest & Cheapest)

### Why Railway?
- **Free tier**: $5/month credit (enough for small apps)
- **Easy deployment**: Connect GitHub, auto-deploy
- **Built-in MongoDB**: Free tier available
- **No credit card required** for free tier
- **Automatic HTTPS**: SSL certificates included

### Setup Steps:

1. **Sign up**: https://railway.app
2. **Create new project**: Click "New Project"
3. **Deploy from GitHub**:
   - Connect your GitHub repo
   - Select `CompliSense-AI` repository
   - Railway auto-detects Python

4. **Configure environment variables**:
   ```
   SECRET_KEY=your-secret-key-here
   MONGO_URI=mongodb://localhost:27017  # Or use Railway's MongoDB
   ```

5. **Set start command**:
   ```
   cd saas/app && python3 main.py
   ```

6. **Deploy**: Railway automatically builds and deploys

**Cost**: $0/month (free tier) or $5/month for more resources

---

## 🥈 Alternative: Render.com (Free Tier)

### Why Render?
- **Free tier**: 750 hours/month (enough for always-on)
- **Free PostgreSQL**: Can use instead of MongoDB
- **Easy setup**: Similar to Railway

### Setup Steps:

1. **Sign up**: https://render.com
2. **Create Web Service**:
   - Connect GitHub repo
   - Select Python environment
   - Build command: `pip install -r requirements.txt`
   - Start command: `cd saas/app && python3 main.py`

3. **Add MongoDB** (or use PostgreSQL):
   - Create MongoDB database
   - Update `MONGO_URI` in environment variables

**Cost**: $0/month (free tier) - spins down after 15min inactivity

---

## 🥉 Alternative: Fly.io (Good for Python)

### Why Fly.io?
- **Free tier**: 3 shared VMs
- **Global edge network**: Fast worldwide
- **Good Python support**

### Setup Steps:

1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`
2. **Login**: `fly auth login`
3. **Create app**: `fly launch`
4. **Deploy**: `fly deploy`

**Cost**: $0/month (free tier) - limited resources

---

## 💰 Budget Option: DigitalOcean App Platform

### Why DigitalOcean?
- **$5/month**: Basic droplet
- **Reliable**: Good uptime
- **Simple**: One-click Python apps

### Setup Steps:

1. **Sign up**: https://digitalocean.com
2. **Create App**:
   - Choose Python
   - Connect GitHub
   - Set build/run commands

**Cost**: $5/month minimum

---

## 🚀 Production Option: AWS/GCP

### AWS (More Complex)
- **EC2**: $5-10/month for t2.micro
- **Elastic Beanstalk**: Easier deployment
- **RDS**: Managed database ($15+/month)

### GCP (Similar)
- **App Engine**: Free tier available
- **Cloud Run**: Pay per use
- **Firestore**: Database option

**Cost**: $10-50/month depending on usage

---

## 📊 Comparison Table

| Provider | Free Tier | Paid Tier | Ease | MongoDB | Best For |
|----------|-----------|-----------|------|---------|----------|
| **Railway** | ✅ $5 credit | $5+/mo | ⭐⭐⭐⭐⭐ | ✅ | **MVP/Demo** |
| **Render** | ✅ 750hrs | $7+/mo | ⭐⭐⭐⭐ | ✅ | MVP/Demo |
| **Fly.io** | ✅ 3 VMs | $5+/mo | ⭐⭐⭐ | ❌ | Dev/Testing |
| **DigitalOcean** | ❌ | $5/mo | ⭐⭐⭐⭐ | ❌ | Production |
| **AWS** | ❌ | $10+/mo | ⭐⭐ | ✅ | Enterprise |

---

## 🎯 Recommendation for Your MVP

### For Demo/Showcase: **Railway.app**

**Why:**
1. Easiest setup (5 minutes)
2. Free tier covers MVP needs
3. Auto-deploy from GitHub
4. Built-in MongoDB option
5. Professional URLs (your-app.railway.app)

### Setup Script:

```bash
# 1. Install Railway CLI (optional)
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add environment variables
railway variables set SECRET_KEY=your-secret-key
railway variables set MONGO_URI=mongodb://localhost:27017

# 5. Deploy
railway up
```

### Or use GitHub integration:
1. Push code to GitHub
2. Connect Railway to GitHub
3. Select repo
4. Railway auto-detects and deploys

---

## 🔧 Required Changes for Hosting

### 1. Update `saas/app/main.py`:

```python
# Add host/port configuration
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
```

### 2. Create `Procfile` (for Railway/Render):

```
web: cd saas/app && python3 main.py
```

### 3. Create `requirements.txt` at root:

```txt
fastapi
uvicorn[standard]
pymongo
pyyaml
jinja2
weasyprint
...
```

### 4. Update CORS settings:

```python
# In saas/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 Environment Variables Needed

```bash
# Required
SECRET_KEY=your-secret-key-here-change-this
MONGO_URI=mongodb://localhost:27017  # Or Railway MongoDB URI

# Optional
PORT=8000
HOST=0.0.0.0
DEBUG=False
```

---

## 🚀 Quick Deploy Checklist

- [ ] Code pushed to GitHub
- [ ] `requirements.txt` created
- [ ] `Procfile` created (if needed)
- [ ] Environment variables set
- [ ] MongoDB configured
- [ ] Domain/URL configured
- [ ] SSL certificate (auto on Railway/Render)

---

## 💡 Pro Tips

1. **Use Railway MongoDB**: Free tier includes MongoDB
2. **Enable auto-deploy**: Deploy on every push
3. **Set up monitoring**: Use Railway's built-in logs
4. **Backup database**: Regular backups for production
5. **Use environment variables**: Never commit secrets

---

## 🆘 Troubleshooting

### Issue: App won't start
- Check logs: `railway logs` or Render dashboard
- Verify `requirements.txt` includes all dependencies
- Check PORT environment variable

### Issue: Database connection fails
- Verify MONGO_URI is correct
- Check MongoDB is running/accessible
- Test connection locally first

### Issue: 502 Bad Gateway
- Check app is listening on correct port
- Verify HOST is set to `0.0.0.0`
- Check app logs for errors

---

## 📞 Next Steps

1. **Choose Railway** (recommended for MVP)
2. **Set up account** and connect GitHub
3. **Deploy** and get your URL
4. **Test** the deployed app
5. **Share** with potential customers!

**Your app will be live at**: `https://your-app-name.railway.app`
