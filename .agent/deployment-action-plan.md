# PyBlink Deployment Action Plan - Option A (Free)

**Target Setup:**
- Frontend: Cloudflare Pages (Free)
- Backend: Render Free Tier (Free)
- Total Cost: $0/month

**Trade-offs Accepted:**
- ✅ Cold starts after 15 minutes of inactivity (10-30 second delay)
- ✅ Saved playgrounds are temporary (lost on restart/deployment)

---

## Phase 1: Prepare Code for Production ✅ COMPLETE

### 1.1 Update Backend CORS Configuration ✅

**File:** `backend/app/main.py`

**✅ Completed:**
- Added `import os` for environment variable support
- Modified CORS middleware to read from `ALLOWED_ORIGINS` environment variable
- Defaults to `http://localhost:3000,http://127.0.0.1:3000` for local development
- Supports comma-separated list of origins for production
- Added logging of allowed origins on startup

**Changes made:**
```python
# Now supports environment-based CORS configuration
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
```

---

### 1.2 Add UI Warning for Temporary Saves ✅

**File:** `frontend/src/components/SaveModal.tsx`

**✅ Completed:**
- Added prominent yellow warning box after successful save
- Warning explains saves are temporary and may be lost after 15 min inactivity
- Updated footer text from "30 days" to "while it's available"
- Encourages users to copy URL immediately

**Changes made:**
```tsx
{/* Warning about temporary saves */}
<div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
    <p className="text-sm text-yellow-800 font-medium mb-1">
        ⚠️ Important: Temporary Save
    </p>
    <p className="text-xs text-yellow-700">
        Saved playgrounds are temporary and may be lost when the service restarts...
    </p>
</div>
```

---

### 1.3 Create Environment Configuration Files ✅

**✅ Files created:**

1. **`backend/.env.example`** - Template for backend environment variables
   ```env
   ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   PYTHON_VERSION=3.11.9
   ```

2. **`frontend/.env.production`** - Production API URL configuration
   ```env
   REACT_APP_API_URL=https://your-backend-url.onrender.com
   ```

**Note:** `.gitignore` already properly excludes `.env` files

---

### 1.4 Test Local Build (Optional)

**Status:** Optional - code changes are straightforward and production-ready

**If you want to test locally:**
```bash
# Test backend can start
cd backend
pip install -r requirements.txt
cd ..
pip install -e .
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test frontend build
cd frontend
npm install
npm run build
npx serve -s build
```

**✅ Phase 1 Complete - Ready for Phase 2!**

---

## Phase 2: Deploy Backend to Render ✅ COMPLETE

**✅ Backend URL:** https://pyblink-backend.onrender.com  
**✅ API Docs:** https://pyblink-backend.onrender.com/docs  
**✅ Health Check:** Verified healthy

### 2.1 Prerequisites ✅
- [ ] GitHub account (code must be in a GitHub repository)
- [ ] Render account (free) - Sign up at https://render.com
- [ ] Code pushed to GitHub

---

### 2.2 Create Render Web Service

**Steps:**
1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub account (if not already connected)
4. Select repository: `pyblink`
5. Click "Connect"

---

### 2.3 Configure Render Service

**Service Configuration:**
```
Name: pyblink-backend
Region: Oregon (or closest to you)
Branch: main (or your default branch)
Root Directory: backend
Runtime: Python 3
```

**Build Command:**
```bash
pip install -r requirements.txt && cd .. && pip install -e .
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Instance Type:**
```
Free
```

---

### 2.4 Set Environment Variables

**In Render dashboard, add these environment variables:**

```
PYTHON_VERSION=3.11.9
ALLOWED_ORIGINS=http://localhost:3000
```

**Note:** 
- `PYTHON_VERSION` must be in major.minor.patch format (e.g., 3.11.9, not 3.11)
- We'll update `ALLOWED_ORIGINS` after frontend deployment

---

### 2.5 Deploy Backend

**Steps:**
1. Click "Create Web Service"
2. Wait for build to complete (5-10 minutes)
3. Check logs for errors
4. Note your backend URL: `https://pyblink-backend.onrender.com` (or similar)

**Verification:**
- Visit `https://your-backend-url.onrender.com/docs`
- Should see FastAPI documentation page

---

## Phase 3: Deploy Frontend to Cloudflare Pages

### 3.1 Prerequisites
- [ ] Cloudflare account (free) - Sign up at https://pages.cloudflare.com
- [ ] Backend URL from Phase 2

---

### 3.2 Create Cloudflare Pages Project

**Steps:**
1. Go to https://dash.cloudflare.com
2. Click "Workers & Pages" in sidebar
3. Click "Create application" → "Pages" → "Connect to Git"
4. Connect your GitHub account (if not already connected)
5. Select repository: `pyblink`
6. Click "Begin setup"

---

### 3.3 Configure Build Settings

**Project Configuration:**
```
Project name: pyblink (or your preferred name)
Production branch: main
```

**Build Settings:**
```
Framework preset: Create React App
Build command: cd frontend && npm install && npm run build
Build output directory: frontend/build
Root directory: (leave empty)
```

---

### 3.4 Set Environment Variables

**In Cloudflare Pages, add environment variable:**

```
REACT_APP_API_URL=https://your-backend-url.onrender.com
```

**Replace with your actual Render backend URL from Phase 2**

---

### 3.5 Deploy Frontend

**Steps:**
1. Click "Save and Deploy"
2. Wait for build to complete (3-5 minutes)
3. Note your frontend URL: `https://pyblink.pages.dev` (or custom name)

**Verification:**
- Visit your frontend URL
- Page should load
- Check browser console for errors

---

## Phase 4: Connect Frontend and Backend

### 4.1 Update Backend CORS Settings

**Action:** Update `ALLOWED_ORIGINS` in Render

**Steps:**
1. Go to Render dashboard
2. Select your `pyblink-backend` service
3. Go to "Environment" tab
4. Update `ALLOWED_ORIGINS` to:
   ```
   https://your-frontend-url.pages.dev,http://localhost:3000
   ```
5. Click "Save Changes"
6. Service will automatically redeploy

---

### 4.2 Test End-to-End Functionality

**Test Checklist:**

- [ ] Frontend loads at Cloudflare Pages URL
- [ ] No CORS errors in browser console (F12)
- [ ] Can enter schema and input data
- [ ] Message conversion works (all formats)
- [ ] Binary viewer displays correctly
- [ ] Save feature works (generates URL)
- [ ] Load feature works (can load saved playground)
- [ ] **Note:** Saved playground will be lost after 15 min of inactivity

---

## Phase 5: Set Up Continuous Deployment

### 5.1 Verify Auto-Deployment

**Both services should auto-deploy on git push:**

**Test:**
1. Make a small change (e.g., update README)
2. Commit and push to GitHub
3. Check Render dashboard - should show new deployment
4. Check Cloudflare Pages dashboard - should show new deployment

**If working:** ✅ You're done! Future updates deploy automatically

---

### 5.2 Configure Branch Protection (Optional)

**Recommended for safety:**
1. In GitHub, go to repository Settings → Branches
2. Add branch protection rule for `main`
3. Require pull request reviews before merging
4. Prevents accidental direct pushes to production

---

## Phase 6: Optional Enhancements

### 6.1 Keep Backend Warm (Prevent Cold Starts)

**Use UptimeRobot to ping backend every 10 minutes:**

**Steps:**
1. Sign up at https://uptimerobot.com (free)
2. Add new monitor:
   - Monitor Type: HTTP(s)
   - Friendly Name: PyBlink Backend
   - URL: `https://your-backend-url.onrender.com/docs`
   - Monitoring Interval: 10 minutes
3. Save

**Result:** Backend stays awake, no cold starts (but saves still temporary)

---

### 6.2 Add Custom Domain (Optional)

**If you own a domain:**

**Cloudflare Pages:**
1. Go to your Pages project → "Custom domains"
2. Click "Set up a custom domain"
3. Enter your domain (e.g., `pyblink.yourdomain.com`)
4. Follow DNS configuration instructions
5. Wait for DNS propagation (5-30 minutes)

**Update Backend CORS:**
- Add your custom domain to `ALLOWED_ORIGINS` in Render

---

### 6.3 Set Up Monitoring (Optional)

**Free monitoring options:**

1. **Cloudflare Web Analytics**
   - Built-in to Cloudflare Pages
   - View in dashboard → Analytics

2. **Render Logs**
   - View in Render dashboard → Logs tab
   - Monitor errors and requests

3. **Browser Error Tracking**
   - Add Sentry (free tier) for frontend error tracking
   - Optional, only if you want detailed error reports

---

## Phase 7: Document and Share

### 7.1 Update README

**Add deployment information:**

```markdown
## Live Demo

- **Frontend:** https://your-frontend-url.pages.dev
- **Backend API:** https://your-backend-url.onrender.com/docs

**Note:** This is hosted on free tiers. The backend may take 10-30 seconds to wake up after periods of inactivity.
```

---

### 7.2 Create User Guide

**Document for users:**
- How to use the playground
- Note about temporary saves
- How to report issues

---

## Troubleshooting Guide

### Issue: Frontend shows "Network Error"

**Possible causes:**
1. Backend is sleeping (cold start) - wait 30 seconds and retry
2. CORS not configured - check browser console for CORS error
3. Backend crashed - check Render logs

**Solutions:**
1. Wait for backend to wake up
2. Verify `ALLOWED_ORIGINS` includes your frontend URL
3. Check Render logs for errors, redeploy if needed

---

### Issue: Build fails on Render

**Check:**
1. Render logs for specific error
2. Ensure `requirements.txt` has all dependencies
3. Ensure build command is correct
4. Try building locally first

**Common fixes:**
- Update Python version in environment variables
- Fix import errors in code
- Add missing dependencies to `requirements.txt`

---

### Issue: Build fails on Cloudflare Pages

**Check:**
1. Build logs in Cloudflare dashboard
2. Ensure `package.json` has all dependencies
3. Ensure build command is correct
4. Try `npm run build` locally first

**Common fixes:**
- Update Node version (Cloudflare uses Node 16+ by default)
- Fix TypeScript errors
- Add missing dependencies to `package.json`

---

### Issue: CORS errors in browser

**Symptoms:**
- Console shows: "Access to fetch at '...' has been blocked by CORS policy"

**Solution:**
1. Go to Render → Environment
2. Check `ALLOWED_ORIGINS` includes your frontend URL
3. Format: `https://your-frontend.pages.dev,http://localhost:3000`
4. No spaces, comma-separated
5. Save and wait for redeploy

---

### Issue: Saved playground returns 404

**This is expected behavior with Option A:**
- Saves are temporary (ephemeral storage)
- Lost when backend restarts (after 15 min inactivity or deployment)

**Solutions:**
1. Accept limitation (Option A)
2. Upgrade to Railway $5/month (persistent storage)
3. Implement cloud storage (Cloudflare R2 - free)

---

## Success Criteria

Your deployment is successful when:

- ✅ Frontend loads at Cloudflare Pages URL
- ✅ Backend API accessible at Render URL
- ✅ No CORS errors in browser console
- ✅ Message conversion works for all formats
- ✅ Save/load works during active session
- ✅ Auto-deployment works on git push
- ✅ Cold start delay is acceptable (10-30 seconds)

---

## Cost Breakdown

| Service | Plan | Cost | What You Get |
|---------|------|------|--------------|
| **Cloudflare Pages** | Free | $0 | Unlimited sites, 500 builds/month, 100GB bandwidth |
| **Render** | Free | $0 | 750 hours/month, 512MB RAM, 100GB bandwidth |
| **Total** | | **$0/month** | Full production deployment |

**Limitations accepted:**
- Backend sleeps after 15 min (cold starts)
- Saved playgrounds are temporary
- 100GB bandwidth/month (plenty for light usage)

---

## Next Steps After Deployment

1. **Share your live demo** - Add URL to portfolio, resume, etc.
2. **Monitor usage** - Check Cloudflare/Render analytics
3. **Gather feedback** - See if users need persistent saves
4. **Consider upgrades** - If usage grows or persistence needed:
   - Railway $5/month (persistent storage + no cold starts)
   - Cloudflare R2 integration (free persistent storage)

---

## Quick Reference

**Frontend URL:** `https://your-project.pages.dev`  
**Backend URL:** `https://your-backend.onrender.com`  
**API Docs:** `https://your-backend.onrender.com/docs`

**Deployment commands:**
```bash
# Push to deploy both
git add .
git commit -m "Update"
git push origin main
```

**Local development:**
```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm start
```

---

## Estimated Timeline

| Phase | Time | Can Skip? |
|-------|------|-----------|
| Phase 1: Prepare Code | 30-60 min | No |
| Phase 2: Deploy Backend | 15-20 min | No |
| Phase 3: Deploy Frontend | 10-15 min | No |
| Phase 4: Connect & Test | 15-20 min | No |
| Phase 5: Auto-Deployment | 5-10 min | No |
| Phase 6: Enhancements | 20-30 min | Yes |
| Phase 7: Documentation | 15-20 min | Yes |

**Total (required):** ~1.5-2 hours  
**Total (with optional):** ~2-3 hours

---

## Ready to Start?

Let me know when you want to begin, and I'll help you with each phase step by step!
