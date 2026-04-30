# Generation System Setup & Fixes

## ✅ What Has Been Fixed

### Backend Fixes (Already Applied)

1. **SQLAlchemy Connection Timeouts** (`app/db/session.py`)
   - Added `pool_timeout=10` - prevents infinite pool waits
   - Added PostgreSQL `connect_timeout=5` 
   - Added `pool_size=5` and `max_overflow=5` for better resource management

2. **Celery Broker Timeouts** (`app/tasks/celery_app.py`)
   - Added `broker_transport_options` with socket timeouts
   - `socket_timeout=10` - Redis connection timeout
   - `socket_connect_timeout=5` - Initial connection timeout
   - `broker_connection_retry_on_startup=True` - Resilient startup

3. **Website Discovery Timeout** (`app/api/v1/routes/generate.py`)
   - Wrapped `_discover_website_like()` in ThreadPoolExecutor with 5-second hard timeout
   - Prevents slow network calls from blocking the web request thread

---

## ⚠️ Critical: Missing Celery Worker

**Your jobs are stuck because the Celery worker is not running!**

### How to Start the Celery Worker

Open a **new PowerShell terminal** and run:

```powershell
cd "d:\paxarisglobal product\python_foundry_code\python_foundry"
.venv\Scripts\activate
celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO --pool=solo
```

You should see:
```
 -------------- celery v5.4.0 (opal)
 --- ***** -----
 -- ******* ----
 - *** --- * ---
 - ** ---------- [config]
 - ** ---------- .broker: redis://localhost:6379/0
 ...
 celery ready.
```

**Keep this terminal open while running generation jobs.**

---

## 🎯 Frontend Fix: Replace Polling Code

Your Angular app is polling too aggressively (every ~100ms instead of every 2-3 seconds).

### Step 1: Copy the Polling Service

Copy [job-polling.service.ts](./job-polling.service.ts) to your Angular project:
```
src/app/services/job-polling.service.ts
```

### Step 2: Update Your Generation Component

Replace your current polling code with the pattern from [generation.component.example.ts](./generation.component.example.ts):

**OLD (❌ Don't Use):**
```ts
setInterval(() => {
  this.http.get(`/api/v1/jobs/${jobId}`).subscribe(job => {
    this.job = job;
  });
}, 100);  // TOO FAST - Causes zone.js violations
```

**NEW (✅ Use This):**
```ts
constructor(private jobPolling: JobPollingService) {}

ngOnInit(): void {
  this.jobPolling.startPolling(jobId);
  
  // Subscribe to updates
  this.jobPolling.jobStatus$.subscribe(job => {
    if (job) {
      this.progress = job.progress;
      this.currentStage = job.current_stage;
    }
  });
}

ngOnDestroy(): void {
  this.jobPolling.stopPolling();
}
```

### Key Improvements:
- ✅ Polls every 2.5 seconds (not 100ms)
- ✅ `switchMap` prevents overlapping requests
- ✅ Stops polling when job completes
- ✅ Proper cleanup on component destroy
- ✅ No more `zone.js` violations

---

## 🧪 Testing Your Setup

### 1. Verify Backend is Running
```bash
curl http://localhost:8000/api/v1/health
```
Should return: `{"status":"ok","dependencies":{"database":"up",...}}`

### 2. Verify Celery Worker is Running
Check the terminal where you started the worker - you should see `celery ready.`

### 3. Test Generation Request
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "test-app",
    "backend": "springboot",
    "frontend": "angular",
    "features": ["auth", "crud"]
  }'
```

Expected response:
```json
{
  "job_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "pending",
  "cache_hit": false
}
```

### 4. Poll Job Status
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}
```

The status should change from `pending` → `running` → `completed` **if the Celery worker is active**.

---

## 📋 Checklist

- [ ] Celery worker is running in a separate terminal
- [ ] Backend API responds to `/api/v1/health` ✅ (200 OK)
- [ ] Can POST to `/api/v1/generate` ✅ (202 Accepted)
- [ ] Job status changes from `pending` to `running` after 30 seconds
- [ ] Angular component uses `JobPollingService` (not `setInterval`)
- [ ] No `zone.js` violations in browser console
- [ ] Generation completes and downloads ZIP to `\Downloads`

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Job stuck in "pending" | Start Celery worker (see above) |
| `zone.js` violations | Update Angular component to use the new polling service |
| "too many files open" | Increase file descriptor limit (Windows: usually not needed) |
| Redis connection error | Verify Redis is running: `redis-cli ping` |
| Generation fails after 30min | Check logs in Celery worker terminal |

---

## 📂 Files Modified

- ✅ `app/db/session.py` - Added connection timeouts
- ✅ `app/tasks/celery_app.py` - Added broker timeouts
- ✅ `app/api/v1/routes/generate.py` - Added website discovery timeout
- ✨ `job-polling.service.ts` - NEW: Safe Angular polling service
- ✨ `generation.component.example.ts` - NEW: Example component usage
