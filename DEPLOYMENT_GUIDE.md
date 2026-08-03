# 🚀 ApplyWise Deployment Guide

This guide explains how to deploy ApplyWise to production using Vercel (frontend) and Render (backend).

## 📋 Prerequisites

- GitHub account with the repository cloned
- Vercel account (free tier)
- Render account (free tier)
- Supabase project credentials
- HuggingFace API token

## 🔧 Frontend Deployment (Vercel)

### 1. Prepare for Deployment

The following files have been added to your repository:
- `vercel.json` - Vercel configuration
- `.vercelignore` - Files to exclude from deployment

### 2. Deploy to Vercel

1. **Go to [vercel.com](https://vercel.com)** and sign in with GitHub
2. **Click "Add New" → "Project"**
3. **Import your repository**: `nadaam0hamed/ApplyWise`
4. **Configure Project**:
   - Framework Preset: Next.js
   - Root Directory: `./` (leave as is)
   - Build Command: `pnpm build`
   - Output Directory: `.next`
   - Install Command: `pnpm install`

5. **Add Environment Variables**:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://nrbwgqxilnivkakmktra.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_1wGfBcZSp62s9ySD6XEoTw_721v3QT6
   HF_TOKEN=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
   NEXT_PUBLIC_FASTAPI_URL=https://applywise-backend.onrender.com
   ```

6. **Click "Deploy"**
7. **Wait for deployment to complete** (~2-3 minutes)
8. **Your frontend URL will be**: `https://applywise.vercel.app`

## 🔧 Backend Deployment (Render)

### 1. Prepare for Deployment

The following files have been added to your repository:
- `backend/render.yaml` - Render configuration
- `backend/Dockerfile` - Docker configuration for deployment

### 2. Deploy to Render

1. **Go to [render.com](https://render.com)** and sign in with GitHub
2. **Click "New" → "Web Service"**
3. **Connect your repository**: `nadaam0hamed/ApplyWise`
4. **Configure Service**:
   - Name: `applywise-backend`
   - Region: Oregon (us-west) or Frankfurt (eu-west)
   - Branch: `main`
   - Runtime: Docker
   - Docker Context: `./backend`
   - Dockerfile Path: `./backend/Dockerfile`

5. **Add Environment Variables**:
   ```
   SUPABASE_URL=https://nrbwgqxilnivkakmktra.supabase.co
   SUPABASE_ANON_KEY=sb_publishable_1wGfBcZSp62s9ySD6XEoTw_721v3QT6
   HF_TOKEN=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
   PORT=8000
   ```

6. **Click "Create Web Service"**
7. **Wait for deployment to complete** (~5-10 minutes)
8. **Your backend URL will be**: `https://applywise-backend.onrender.com`

## 🔄 Update CORS Configuration

After deployment, update the backend CORS to include your frontend URL:

1. **Go to Render Dashboard**
2. **Open your backend service**
3. **Add environment variable**:
   ```
   CORS_ORIGINS=https://applywise.vercel.app,http://localhost:3000
   ```
4. **Redeploy the service**

## ✅ Testing the Deployment

### 1. Test Backend
```bash
curl https://applywise-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ApplyWise API"
}
```

### 2. Test Frontend
1. **Visit**: `https://applywise.vercel.app`
2. **Check if the landing page loads**
3. **Try signing up/login**
4. **Test creating an application**

### 3. Test Full Analysis
1. **Create an application**
2. **Upload sample documents**
3. **Click "Generate Report"**
4. **Check if analysis completes successfully**

## 📝 Important Notes

### Free Tier Limitations
- **Vercel**: Unlimited deployments, but sleeps after inactivity
- **Render**: Free tier spins down after 15 minutes of inactivity
- **Cold starts**: First request may take 30-60 seconds to wake up

### Database Storage
- ChromaDB data is stored in `/app/data` on Render
- Data persists between deployments but may be lost if service is recreated
- For production, consider using a separate database service

### Model Download
- First deployment may take longer due to model downloads
- Subsequent deployments will be faster
- Consider using model caching for better performance

## 🛠️ Troubleshooting

### Backend Not Responding
- Check Render logs for errors
- Ensure all environment variables are set
- Verify the health endpoint is accessible

### CORS Errors
- Ensure frontend URL is in CORS_ORIGINS
- Check environment variables on both platforms
- Verify backend is running and accessible

### Analysis Timeouts
- Render free tier has timeout limits
- Consider upgrading to paid tier for longer-running tasks
- Optimize analysis pipeline for faster execution

## 🎯 Next Steps

1. **Deploy both services following the guide above**
2. **Test the full application flow**
3. **Update README.md with live demo link**
4. **Monitor performance and logs**
5. **Consider adding monitoring (Sentry, LogRocket)**

## 📞 Support

If you encounter issues:
- Check Vercel deployment logs
- Check Render service logs
- Verify environment variables
- Test endpoints locally first