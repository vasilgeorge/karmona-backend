# Daily Scraping Automation Setup

## 🎯 **Goal**

Run the astrology scraper automatically every day at 3am UTC to keep the Knowledge Base fresh.

---

## ⚙️ **Option 1: Railway Cron Service (Recommended)**

Railway doesn't support cron in `railway.toml`, but you can set it up via their dashboard:

### **Steps:**

1. **Go to Railway Dashboard** → Your project
2. **Click "+ New"** → **"Cron Job"**
3. **Configure:**
   - **Name:** `daily-astrology-scraper`
   - **Schedule:** `0 3 * * *` (3am UTC daily)
   - **Command:** `uv run python app/jobs/daily_scrape_job.py`
   - **Environment:** Same as your main service (inherit variables)

4. **Deploy**

---

## ⚙️ **Option 2: GitHub Actions (Alternative)**

If Railway doesn't support cron, use GitHub Actions:

### **Create `.github/workflows/daily-scrape.yml`:**

```yaml
name: Daily Astrology Scrape

on:
  schedule:
    - cron: '0 3 * * *'  # 3am UTC daily
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: cd karmona-backend && uv sync
      
      - name: Run scraper
        env:
          AWS_REGION: ${{ secrets.AWS_REGION }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          BEDROCK_KNOWLEDGE_BASE_ID: ${{ secrets.BEDROCK_KNOWLEDGE_BASE_ID }}
          BEDROCK_DATA_SOURCE_ID: ${{ secrets.BEDROCK_DATA_SOURCE_ID }}
          S3_ASTROLOGY_BUCKET: ${{ secrets.S3_ASTROLOGY_BUCKET }}
        run: cd karmona-backend && uv run python app/jobs/daily_scrape_job.py
```

**Then add secrets in GitHub:**
- Settings → Secrets → Add all AWS credentials

---

## ⚙️ **Option 3: AWS EventBridge + Lambda**

Most reliable but more complex:

1. **Create Lambda function** with scraping code
2. **EventBridge rule:** `cron(0 3 * * ? *)`
3. **Trigger Lambda daily**

---

## ⚙️ **Option 4: Simple Scheduler in App** (Easiest for now)

Add to your FastAPI app:

### **Install:**
```bash
uv add apscheduler
```

### **In `app/main.py`:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.daily_scraper import DailyScraper

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    def run_scraper():
        scraper = DailyScraper()
        scraper.run_daily_scrape()
    
    # Run daily at 3am UTC
    scheduler.add_job(run_scraper, 'cron', hour=3, minute=0)
    scheduler.start()
    print("✅ Daily scraper scheduled for 3am UTC")
```

**Pros:** Simple, works immediately  
**Cons:** Runs in your main app (uses resources)

---

## 🎯 **My Recommendation for Now:**

**Use Option 4 (In-App Scheduler)** because:
- ✅ Works immediately
- ✅ No external setup needed
- ✅ Easy to test
- ✅ Can migrate to Railway cron later

**Want me to implement it?** I can add it to your FastAPI app right now and it'll start running automatically! 🚀

