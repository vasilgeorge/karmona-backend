# 📊 Data Source Integration Guide

## Overview
This document outlines the 4-step process for integrating EVERY new data source into Karmona's AI context pipeline.

---

## 🔄 The 4-Step Pipeline

### Step 1: GET THE DATA
How we acquire the data (API, calculation, or scraping)

### Step 2: STORE IN S3
Where and how we store it in our S3 bucket

### Step 3: INDEX WITH EMBEDDINGS
How Bedrock Knowledge Base auto-indexes the data

### Step 4: CONSUME IN LLM CONTEXT
How we update prompts to use the data

---

## 📁 S3 Bucket Structure

```
s3://karmona-astrology-data-967392725523/
├── daily/                          # Daily data sources
│   └── YYYY-MM-DD/
│       ├── horoscopes/             # Sign-specific horoscopes
│       │   ├── astrostyle_aries.json
│       │   ├── cafeastrology_aries.json
│       │   └── ... (12 signs × sources)
│       ├── cosmic-overview/        # Daily cosmic data
│       │   ├── moon_phase.json
│       │   ├── void_of_course.json
│       │   └── retrograde_planets.json
│       ├── ephemeris/              # Planetary positions
│       │   └── planetary_positions.json
│       └── transits/               # Daily aspects
│           └── daily_aspects.json
├── weekly/                         # Weekly forecasts
│   └── YYYY-WW/
│       └── forecasts/
│           └── ... (sources)
├── monthly/                        # Monthly calendars
│   └── YYYY-MM/
│       ├── eclipse_calendar.json
│       └── moon_calendar.json
└── articles/                       # Astrological articles
    └── YYYY-MM-DD/
        └── ... (articles)
```

---

## ✅ DATA SOURCE #1: Swiss Ephemeris (Planetary Positions)

### Step 1: GET THE DATA ✅
**Method**: Calculation (no scraping)
**File**: `app/services/ephemeris_service.py`
**Function**: `run_daily_calculation()`
**Schedule**: Daily via cron job

**What it provides**:
- Positions of: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, North Node
- Zodiac signs and degrees
- Retrograde status
- Daily motion speeds

### Step 2: STORE IN S3 ✅
**Location**: `s3://karmona-astrology-data-967392725523/ephemeris/YYYY-MM-DD/planetary_positions.json`

**Format**:
```json
{
  "id": "ephemeris-2025-10-19",
  "date": "2025-10-19",
  "source": "swiss_ephemeris",
  "content": "**Planetary Positions for 2025-10-19:**\n\n**Inner & Outer Planets:**\n- Sun: 26°21' Libra\n- Moon: 4°3' Libra\n...",
  "data": {
    "positions": {
      "sun": {
        "longitude": 206.3587,
        "sign": "Libra",
        "degrees_in_sign": 26.36,
        "formatted": "26°21' Libra",
        "retrograde": false
      },
      ...
    }
  },
  "metadata": {
    "tags": ["ephemeris", "planetary-positions", "daily"],
    "calculated_at": "2025-10-19T12:00:00Z"
  }
}
```

**Upload Code**:
```python
# In ephemeris_service.py
self.s3_client.put_object(
    Bucket=settings.s3_astrology_bucket,
    Key=f"ephemeris/{target_date}/planetary_positions.json",
    Body=json.dumps(kb_document, indent=2),
    ContentType='application/json',
)
```

### Step 3: INDEX WITH EMBEDDINGS ✅
**Method**: Automatic via Bedrock Knowledge Base

**Trigger**:
```python
# In daily_scraper.py
self.bedrock_agent.start_ingestion_job(
    knowledgeBaseId=settings.bedrock_knowledge_base_id,  # ZDDIIWWBMV
    dataSourceId=settings.bedrock_data_source_id,        # GHIJ2U38LL
)
```

**What happens**:
1. Bedrock scans S3 bucket
2. Finds new/updated files
3. Extracts "content" field
4. Creates vector embeddings
5. Stores in vector database
6. Makes searchable via RAG

### Step 4: CONSUME IN LLM CONTEXT ✅
**Method**: RAG retrieval in prompt

**Example** (in reflection prompt):
```python
# Before (basic):
prompt = f"Generate a reflection for {user.sun_sign}"

# After (enhanced with ephemeris):
# RAG automatically retrieves relevant ephemeris data when we ask about:
prompt = f"""
Generate a reflection for {user.sun_sign}.

Today's date: {today}
User's sun sign: {user.sun_sign}
User's moon sign: {user.moon_sign}

Consider today's planetary positions and transits in your reflection.
"""

# Bedrock's RAG will automatically find and inject:
# - Ephemeris data for today
# - Planetary positions
# - Retrograde planets
# - Any relevant transits
```

**Status**: ✅ COMPLETE
**Integrated into**: Daily cron job (`app/jobs/daily_scrape_job.py`)
**Runs**: Daily at 3am UTC

---

## ✅ DATA SOURCE #2: Cafe Astrology Daily Horoscopes

### Step 1: GET THE DATA ✅
**Method**: Browser Agent scraping (Bedrock AgentCore + Playwright)
**File**: `app/services/daily_scraper.py`
**Function**: `scrape_source()` called from `run_daily_scrape()`
**URL Pattern**: `https://cafeastrology.com/{sign}dailyhoroscope.html`
**Schedule**: Daily via cron job

**What it provides**:
- Daily horoscope for each of 12 zodiac signs
- Planetary influences and transits
- Practical guidance and themes
- Emotional insights

**Technical Notes**:
- Uses `page.content()` + BeautifulSoup instead of `page.inner_text()` to avoid Playwright timeout issues
- Extracts text with Nova Micro LLM for cost efficiency

### Step 2: STORE IN S3 ✅
**Location**: `s3://karmona-astrology-data-967392725523/daily/YYYY-MM-DD/cafeastrology_horoscopes_{sign}.json`

**Format**:
```json
{
  "id": "cafeastrology_horoscopes-2025-10-19",
  "date": "2025-10-19",
  "source": "cafeastrology_horoscopes",
  "url": "https://cafeastrology.com/ariesdailyhoroscope.html",
  "content": "Today's main theme for Aries is...",
  "metadata": {
    "tags": ["sign-aries", "source-cafeastrology_horoscopes"],
    "scraped_at": "2025-10-19T12:00:00Z"
  }
}
```

**Upload Code**:
```python
# In daily_scraper.py _upload_to_s3()
filename = f"daily/{today.isoformat()}/{source}_{context}.json"
self.s3_client.put_object(
    Bucket=settings.s3_astrology_bucket,
    Key=filename,
    Body=json.dumps(kb_document, indent=2),
    ContentType='application/json',
)
```

### Step 3: INDEX WITH EMBEDDINGS ✅
**Method**: Automatic via Bedrock Knowledge Base

**Trigger**:
```python
# In daily_scraper.py run_daily_scrape()
if results['uploaded'] > 0:
    self.bedrock_agent.start_ingestion_job(
        knowledgeBaseId=settings.bedrock_knowledge_base_id,
        dataSourceId=settings.bedrock_data_source_id,
    )
```

### Step 4: CONSUME IN LLM CONTEXT ⏳
**Method**: RAG retrieval in prompt

**How it works**:
When generating daily reflections or counsel reports, RAG automatically retrieves horoscope data when:
- User's sun sign is mentioned
- Date is referenced
- Astrological themes are discussed

**Status**: Data is indexed and searchable, prompt optimization pending

**Overall Status**: ✅ COMPLETE (Steps 1-3), ⏳ IN PROGRESS (Step 4)

---

## 📝 Template for Future Data Sources

When adding a new data source, follow this template:

### Step 1: GET THE DATA
- [ ] Create service file or add to `scraping_sources.py`
- [ ] Implement data fetching (API/scrape/calculate)
- [ ] Test data retrieval

### Step 2: STORE IN S3
- [ ] Define S3 path structure
- [ ] Format data as JSON with:
  - `id` (unique identifier)
  - `date` (YYYY-MM-DD)
  - `source` (source name)
  - `content` (human-readable text for LLM)
  - `metadata` (tags, timestamps)
- [ ] Test S3 upload

### Step 3: INDEX WITH EMBEDDINGS
- [ ] Add to daily scraper job
- [ ] Trigger Knowledge Base sync
- [ ] Verify indexing in AWS Console

### Step 4: CONSUME IN LLM CONTEXT
- [ ] Update LLM prompts to reference data type
- [ ] Test RAG retrieval
- [ ] Validate output quality

---

## 🎯 Current Pipeline Status

| Data Source | Step 1 | Step 2 | Step 3 | Step 4 |
|-------------|--------|--------|--------|--------|
| Swiss Ephemeris | ✅ | ✅ | ✅ | ⏳ |
| Cafe Astrology Horoscopes (12 signs) | ✅ | ✅ | ✅ | ⏳ |
| Moon Phase Data | ⏳ | ⏳ | ⏳ | ⏳ |
| Void of Course Moon | ⏳ | ⏳ | ⏳ | ⏳ |
| NASA APOD | ⏳ | ⏳ | ⏳ | ⏳ |

---

## 🔧 Key Files

**Cron Job**:
- `app/jobs/daily_scrape_job.py` - Main cron entry point
- `scripts/run_daily_scrape.py` - Manual test script
- `railway.cron.toml` - Railway cron configuration

**Services**:
- `app/services/daily_scraper.py` - Main orchestrator
- `app/services/ephemeris_service.py` - Planetary calculations
- `app/services/browser_scraper.py` - Web scraping via Bedrock Agent
- `app/services/scraping_sources.py` - Source configurations

**Config**:
- `app/core/config.py` - S3 bucket, Knowledge Base IDs
- `.env` - AWS credentials

---

## ⚙️ Testing & Verification

### Test locally:
```bash
uv run python scripts/run_daily_scrape.py
```

### Check S3 bucket:
```bash
aws s3 ls s3://karmona-astrology-data-967392725523/ephemeris/2025-10-19/
```

### Verify Knowledge Base sync:
1. Go to AWS Console → Bedrock → Knowledge Bases
2. Find Knowledge Base `ZDDIIWWBMV`
3. Check "Data sources" tab
4. View last sync status and timestamp

### Test RAG retrieval:
```python
# In test file
from app.services.kb_retrieval_service import retrieve_from_kb

results = retrieve_from_kb("What are today's planetary positions?")
print(results)
```

---

## 📊 Expected Daily Data Volume

| Source Type | Files/Day | Size | Total/Month |
|-------------|-----------|------|-------------|
| Ephemeris | 1 | ~5 KB | ~150 KB |
| Horoscopes (12 signs) | 12-48 | ~2 KB each | ~3 MB |
| Moon Data | 3-5 | ~1 KB each | ~150 KB |
| Articles | 0-5 | ~10 KB each | ~1.5 MB |
| **TOTAL** | ~20-60 | - | **~5 MB/month** |

S3 cost: ~$0.02/month + negligible request costs

---

## 🚨 Important Notes

1. **All data must have**:
   - `content` field (human-readable text for LLM)
   - `date` field (for temporal relevance)
   - `source` field (for attribution)
   - `metadata.tags` (for filtering)

2. **Knowledge Base sync**:
   - Triggered once at end of daily job
   - Takes 2-5 minutes to complete
   - Don't trigger for every single file

3. **Testing**:
   - Always test locally first
   - Verify S3 upload before deploying
   - Check Knowledge Base indexing

4. **Prompt updates**:
   - Don't need to explicitly reference data
   - RAG retrieves relevant context automatically
   - Just mention relevant topics (signs, dates, planets)

---

Last updated: 2025-10-19
