# 🚀 Deploy to Render - Complete Guide

## 📋 Prerequisites

✅ Render account (free): https://render.com/
✅ GitHub account (to push your code)
✅ Bot token from @BotFather

---

## 🎯 Deployment Steps

### Step 1: Prepare Your Code

Your bot is already configured for Render! Files created:
- ✅ `render.yaml` - Render configuration
- ✅ `Aptfile` - Installs FFmpeg on Render
- ✅ `Procfile` - Tells Render how to run the bot
- ✅ `runtime.txt` - Python version specification
- ✅ `.renderignore` - Files to exclude from deployment

### Step 2: Push to GitHub

```bash
# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Telegram audio bot"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Render

1. **Go to Render Dashboard**: https://dashboard.render.com/

2. **Click "New +" → "Web Service"**

3. **Connect Your GitHub Repo**:
   - Click "Connect GitHub"
   - Select your repository
   - Click "Connect"

4. **Configure the Service**:
   
   | Setting | Value |
   |---------|-------|
   | Name | `muffled-music-bot` (or any name) |
   | Region | `Oregon (US West)` (closest free region) |
   | Branch | `main` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements_production.txt` |
   | Start Command | `python bot.py` |
   | Plan | **Free** |

5. **Add Environment Variables**:
   - Click "Advanced"
   - Click "Add Environment Variable"
   - Key: `BOT_TOKEN`
   - Value: `your_bot_token_from_botfather`

6. **Add FFmpeg Buildpack** (IMPORTANT):
   - Scroll to "Build Command"
   - Replace with:
     ```bash
     apt-get update && apt-get install -y ffmpeg && pip install -r requirements_production.txt
     ```

7. **Click "Create Web Service"**

### Step 4: Wait for Deployment

- Render will build your app (~3-5 minutes)
- You'll see build logs in real-time
- Look for: "Build successful" and "Your service is live"

### Step 5: Check if Bot is Running

1. Open Telegram
2. Find your bot
3. Send `/start`
4. Upload an audio file
5. Choose an effect
6. Get processed audio!

---

## ⚠️ Important Notes

### Free Tier Limitations:
- ✅ **100% Free Forever**
- ⚠️ **Spins down after 15 minutes of inactivity**
- ⚠️ **Takes ~30 seconds to wake up** (first message after sleep)
- ✅ **750 hours/month free** (enough for one bot)
- ✅ **Automatic deploys** on git push

### Bot Behavior:
- First message after sleep: 30-60 seconds delay
- Subsequent messages: Instant response
- Bot stays awake while processing files
- Automatically sleeps when idle

---

## 🔧 Alternative: Using render.yaml (Auto-Deploy)

Instead of manual setup, you can use Infrastructure as Code:

1. **Push your code to GitHub** (with render.yaml included)

2. **Go to Render Dashboard** → "New +" → "Blueprint"

3. **Connect your repo**

4. **Render reads render.yaml automatically**

5. **Set environment variables** when prompted:
   - `BOT_TOKEN`: Your bot token

6. **Click "Apply"**

Done! Render deploys everything automatically.

---

## 🐛 Troubleshooting

### Bot doesn't respond:
- Check Render logs: Dashboard → Your Service → Logs
- Verify `BOT_TOKEN` is set correctly
- Make sure service is "Live" (not "Build failed")

### "Couldn't find ffmpeg" error:
- Make sure build command includes: `apt-get install -y ffmpeg`
- Check build logs to verify FFmpeg installation

### Build fails:
- Check if `requirements_production.txt` exists
- Verify Python version in `runtime.txt` is supported
- Check build logs for specific error

### Bot sleeps too often:
- Free tier limitation - can't be avoided
- Consider upgrading to paid tier ($7/month for always-on)
- Or use a ping service (not recommended for bots)

---

## 💰 Cost Comparison

| Service | Free Tier | Always-On | FFmpeg Support |
|---------|-----------|-----------|----------------|
| Render | ✅ Yes (sleeps) | $7/month | ✅ Yes |
| Heroku | ❌ No longer free | $7/month | ✅ Yes |
| Railway | ⚠️ $5 credit | $5/month | ✅ Yes |
| Fly.io | ✅ Yes (limited) | $3/month | ✅ Yes |

**Recommendation**: Start with Render free tier. If you need always-on, upgrade to Render's $7/month plan.

---

## 🔄 Update Your Bot

After pushing changes to GitHub:

**Automatic (if using Blueprint/render.yaml):**
- Just push to GitHub
- Render auto-deploys

**Manual:**
1. Go to Render Dashboard
2. Click your service
3. Click "Manual Deploy" → "Deploy latest commit"

---

## 📊 Monitor Your Bot

**View Logs:**
- Dashboard → Your Service → Logs
- See real-time bot activity
- Debug errors

**Check Status:**
- Dashboard → Your Service
- See "Live" or "Sleeping"
- View CPU/Memory usage

---

## 🎉 Success Checklist

- ✅ Code pushed to GitHub
- ✅ Render service created
- ✅ `BOT_TOKEN` environment variable set
- ✅ FFmpeg installed in build command
- ✅ Build successful
- ✅ Service shows "Live"
- ✅ Bot responds to /start on Telegram
- ✅ Audio processing works

---

## 🆘 Need Help?

Common issues and solutions:

**Q: Bot is slow to respond first time**
A: Normal - free tier spins down. First message wakes it up (30s delay)

**Q: Can I keep it always awake?**
A: Upgrade to paid tier ($7/month) or use a different service

**Q: How do I see errors?**
A: Dashboard → Your Service → Logs (real-time)

**Q: Can I use a custom domain?**
A: Not needed for Telegram bots (but yes, Render supports it)

---

**Ready to deploy!** 🚀

Follow the steps above and your bot will be live in ~5 minutes!
