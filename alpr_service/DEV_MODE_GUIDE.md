# Development vs Production Deployment Guide

## 🚀 Quick Start

### Production Mode (Current)
```bash
cd /home/pc/ALPR-V2/alpr_service
sudo docker compose up -d --build
```
- **Pros**: Optimized build, smaller image size, fast runtime
- **Cons**: Rebuild takes ~3 minutes on code changes

### Development Mode (Recommended for development)
```bash
cd /home/pc/ALPR-V2/alpr_service
sudo docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```
- **Pros**: Hot reload, instant code updates, no rebuild needed
- **Cons**: Larger image size, slightly slower runtime

---

## 📋 Comparison

| Feature | Production | Development |
|---------|-----------|-------------|
| Build time | ~3 minutes | ~1 minute (first time) |
| Code change deployment | Full rebuild required | Instant (hot reload) |
| Image size | ~500MB | ~800MB |
| Runtime performance | Optimized | Slightly slower |
| Volume mounts | No | Yes (src/, public/) |
| Node modules | Production only | All (including dev) |
| Environment | Production | Development |

---

## 🔧 Development Workflow

### Making Changes

**With Dev Mode (Fast):**
```bash
# 1. Start dev containers (only once)
sudo docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 2. Edit files in alpr_web/src/
# Changes are reflected IMMEDIATELY (hot reload)

# 3. View logs if needed
sudo docker compose logs -f nextjs-app
```

**With Production Mode (Slow):**
```bash
# 1. Edit files
# 2. Rebuild every time
sudo docker compose build nextjs-app
sudo docker compose up -d nextjs-app
# Takes ~3 minutes per change
```

### Switching Between Modes

**From Production → Development:**
```bash
sudo docker compose down
sudo docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**From Development → Production:**
```bash
sudo docker compose down
sudo docker compose up -d --build
```

---

## 🎯 When to Use Each Mode

### Use Development Mode When:
- ✅ Actively developing features
- ✅ Testing UI changes
- ✅ Debugging frontend issues
- ✅ Frequent code iterations

### Use Production Mode When:
- ✅ Deploying to production server
- ✅ Final testing before release
- ✅ Performance benchmarking
- ✅ Creating deployment images

---

## 📝 Configuration Files

### docker-compose.yml (Base)
- Core service definitions
- Used by both modes
- Contains production settings

### docker-compose.dev.yml (Dev Override)
- Overrides settings for development
- Adds volume mounts for hot reload
- Sets NODE_ENV=development

### docker-compose.gpu.yml (GPU Override)
- Adds GPU support for plate-recognizer
- Optional, only if you have NVIDIA GPU

---

## 💡 Best Practices

### Development Phase
```bash
# Start services in dev mode
sudo docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Watch logs
sudo docker compose logs -f nextjs-app video-handler

# Make changes → See results immediately
# No rebuild needed!
```

### Before Deployment
```bash
# Test in production mode
sudo docker compose down
sudo docker compose up -d --build

# Verify everything works
# Then deploy to production server
```

---

## 🐛 Troubleshooting

### Hot Reload Not Working
```bash
# Check if volume mounts are correct
sudo docker compose -f docker-compose.yml -f docker-compose.dev.yml config | grep -A 5 volumes

# Restart dev containers
sudo docker compose -f docker-compose.yml -f docker-compose.dev.yml restart nextjs-app
```

### Changes Not Reflected in Production
```bash
# Make sure you're rebuilding
sudo docker compose build nextjs-app --no-cache
sudo docker compose up -d nextjs-app
```

### Port Conflicts
```bash
# Check what's using port 80
sudo lsof -i :80

# Stop all containers
sudo docker compose down
```

---

## 🔄 Migration Guide

If you're currently using production mode and want to switch to dev mode for faster development:

1. **Stop current containers:**
   ```bash
   cd /home/pc/ALPR-V2/alpr_service
   sudo docker compose down
   ```

2. **Start in dev mode:**
   ```bash
   sudo docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

3. **Verify services:**
   ```bash
   sudo docker compose ps
   ```

4. **Edit code and see instant updates!**

---

## 📊 Performance Impact

### Video Processing (10 FPS + Duplicate Detection)

**Before:**
- Video 10s × 30 fps = 300 frames
- Same car detected ~90 times
- Processing time: ~300 seconds

**After:**
- Video 10s × 10 fps = 100 frames
- Same car detected ~2-3 times (duplicate detection)
- Processing time: ~20-30 seconds
- **10x faster!** ⚡

### Duplicate Detection Logic
```python
# Backend automatically skips duplicate plates within 3 seconds
# Example:
# Frame 10: Plate "7กก7725" detected → Saved ✅
# Frame 15: Plate "7กก7725" detected → Skipped ⏭️ (0.5s ago)
# Frame 20: Plate "7กก7725" detected → Skipped ⏭️ (1.0s ago)
# Frame 45: Plate "7กก7725" detected → Skipped ⏭️ (2.5s ago)
# Frame 70: Plate "1กข234" detected → Saved ✅ (new plate)
```

---

## 🎛️ Customization

### Adjust FPS
Edit `alpr_web/src/modules/dashboard/upload-video/_libs/videoToWebsocket.ts`:
```typescript
const fps = 10; // Change to 5, 15, 20, etc.
```

Lower = Faster + Fewer duplicates
Higher = More coverage + Better for fast cars

### Adjust Duplicate Threshold
Edit `alpr_websocket_video/src/utils/consumer.py`:
```python
DUPLICATE_THRESHOLD = 3.0  # seconds
```

Lower = More strict (less duplicates)
Higher = More lenient (more results)

---

## 📚 Additional Resources

- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Next.js Development Mode](https://nextjs.org/docs/getting-started)
- [Hot Reload in Docker](https://docs.docker.com/compose/file-watch/)
