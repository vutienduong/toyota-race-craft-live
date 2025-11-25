# Vercel Deployment - Quick Setup Guide

## Deploy RaceCraft Live to Vercel in 5 Minutes

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Add sample data mode for Vercel"
git push origin main
```

### Step 2: Import to Vercel

1. Go to https://vercel.com/new
2. Sign in with GitHub
3. Click "Import Git Repository"
4. Select `toyota-race-craft-live` repository
5. Configure project:
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend` ⚠️ IMPORTANT: Click "Edit" and set to `frontend`
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `.next` (default)

### Step 3: Set Environment Variables

Click "Environment Variables" section and add:

```
Name: NEXT_PUBLIC_DATA_MODE
Value: sample
```

**That's it!** No other environment variables needed for sample mode.

### Step 4: Deploy

1. Click "Deploy"
2. Wait 2-3 minutes for build
3. Your app will be live at: `https://your-project.vercel.app`

---

## Testing Your Deployment

1. Open `https://your-project.vercel.app/dashboard`
2. Open browser console (F12)
3. You should see: `[API Client] Running in SAMPLE DATA mode - no backend required`
4. The dashboard should display race data with working charts

---

## Connecting to Backend Later

When your backend is deployed, update these environment variables in Vercel:

1. Go to your Vercel project settings
2. Navigate to "Environment Variables"
3. Add/Update:

```
NEXT_PUBLIC_DATA_MODE=backend
NEXT_PUBLIC_API_URL=https://your-backend-api.com
NEXT_PUBLIC_WS_URL=wss://your-backend-api.com/ws
```

4. Click "Redeploy" to apply changes

---

## Common Issues

### ❌ "Cannot GET /" Error
**Solution:** Make sure Root Directory is set to `frontend` in project settings

### ❌ Build fails with module errors
**Solution:**
1. Check that `package-lock.json` exists in `frontend/` directory
2. Ensure all dependencies are in `frontend/package.json`

### ❌ Dashboard shows blank page
**Solution:**
1. Check browser console for errors
2. Verify `NEXT_PUBLIC_DATA_MODE=sample` is set in Vercel
3. Try redeploying

### ❌ Data not loading
**Solution:**
1. Open browser console
2. Look for `[API Client]` message to confirm mode
3. Check Network tab for any failed requests
4. In sample mode, data should load instantly without backend

---

## Environment Variables Reference

### Required for Sample Mode:
```
NEXT_PUBLIC_DATA_MODE=sample
```

### Required for Backend Mode:
```
NEXT_PUBLIC_DATA_MODE=backend
NEXT_PUBLIC_API_URL=https://your-backend-api.com
NEXT_PUBLIC_WS_URL=wss://your-backend-api.com/ws
```

### Optional:
```
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
```

---

## Custom Domain (Optional)

1. Go to Vercel project settings > Domains
2. Add your custom domain (e.g., `racecraft.your-domain.com`)
3. Follow DNS configuration instructions
4. Wait for SSL certificate (automatic, ~1 minute)

---

## Automatic Deployments

Vercel automatically redeploys when you push to GitHub:

- **Main branch** → Production deployment
- **Other branches** → Preview deployments

Each pull request gets its own preview URL!

---

## Next Steps

✅ Deploy frontend to Vercel (sample mode)
⬜ Deploy backend to Cloud Run / Railway / AWS
⬜ Update Vercel env vars to backend mode
⬜ Add custom domain
⬜ Enable analytics (Vercel Analytics)

---

## Support

- Vercel Docs: https://vercel.com/docs
- Next.js Docs: https://nextjs.org/docs
- Project README: See `DEPLOYMENT.md` for detailed mode info
