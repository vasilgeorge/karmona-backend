# Browser Agent Integration Plan

## Architecture

### 1. Browser Agent Client (`app/services/browser_agent_client.py`)
**Purpose:** Low-level browser automation using Bedrock AgentCore + Browser-Use

**Key Methods:**
- `execute_task(session, task, url)` - Run any browser task
- `fetch_from_url(url, extraction_prompt)` - High-level data extraction

**Usage:**
```python
client = BrowserAgentClient()
result = await client.fetch_from_url(
    url="https://astro.com",
    extraction_prompt="Extract today's cosmic insights"
)
```

---

### 2. Data Fetchers (`app/services/data_fetchers/`)

#### **Astrology Fetcher** (`astrology_fetcher.py`)
Scrapes real-time astrology data:
- Planetary transits for user's sign
- Daily cosmic events (moon phase, retrogrades, aspects)
- Returns enriched astrology context

**Methods:**
- `fetch_planetary_transits(sun_sign, date)`
- `fetch_daily_cosmic_events(date)`
- `fetch_enriched_astrology_context(sun_sign, moon_sign, date)` ← Main method

#### **Spiritual Fetcher** (`spiritual_fetcher.py`)
Scrapes spiritual wisdom:
- Daily spiritual teachings
- Element-specific guidance (Fire/Earth/Air/Water)
- Mindfulness practices

**Methods:**
- `fetch_daily_wisdom(theme)`
- `fetch_intention_guidance(zodiac_element)`
- `fetch_enriched_spiritual_context(zodiac_element)` ← Main method

---

### 3. Integration into Reflection Endpoint

**Current flow:**
```python
user_data → astrology_service → horoscope (Aztro API) → Claude → reflection
```

**Enhanced flow:**
```python
user_data 
  ↓
astrology_service (sun/moon signs)
  ↓
┌─────────────────────────────────┐
│ DATA ENRICHMENT (new!)          │
├─────────────────────────────────┤
│ • Astrology Fetcher:            │
│   - Planetary transits          │
│   - Cosmic events               │
│                                 │
│ • Spiritual Fetcher:            │
│   - Daily wisdom                │
│   - Element guidance            │
└─────────────────────────────────┘
  ↓
ALL enriched data → Claude → MUCH better reflection
```

---

## Implementation

### In `app/routers/reflection.py`:

```python
from app.services.data_fetchers import AstrologyDataFetcher, SpiritualDataFetcher

# ... in generate_reflection endpoint ...

# NEW: Fetch enriched data
astrology_fetcher = AstrologyDataFetcher()
spiritual_fetcher = SpiritualDataFetcher()

# Get zodiac element for spiritual guidance
zodiac_element = astrology_service.get_zodiac_element(user.sun_sign)

# Fetch enriched context in parallel
enriched_astrology = await astrology_fetcher.fetch_enriched_astrology_context(
    sun_sign=user.sun_sign,
    moon_sign=user.moon_sign,
    today=today,
)

enriched_spiritual = await spiritual_fetcher.fetch_enriched_spiritual_context(
    zodiac_element=zodiac_element,
)

# Generate reflection with ALL the enriched data
bedrock_reflection = await bedrock_service.generate_reflection(
    name=user.name,
    sun_sign=user.sun_sign,
    moon_sign=user.moon_sign,
    mood=request.mood,
    actions=request.actions,
    note=request.note,
    horoscope=horoscope,  # Keep old Aztro horoscope
    enriched_astrology=enriched_astrology,  # NEW!
    enriched_spiritual=enriched_spiritual,  # NEW!
    today=today,
)
```

---

## Data Sources You Can Add

### Astrology:
- astro.com (transits, detailed charts)
- cafeastrology.com (daily aspects)
- astrologyzone.com (Susan Miller insights)
- thepattern.com (modern astrology)

### Spiritual:
- tinybuddha.com (daily wisdom)
- mindbodygreen.com (wellness/mindfulness)
- dailyom.com (spiritual practices)
- poets.org (mystical poetry)

### Esoteric:
- biddy tarot (daily card)
- numerology.com (number of the day)
- sacred-texts.com (ancient wisdom)

---

## Configuration

Add to Railway environment variables (optional):
```
ENABLE_BROWSER_AGENT=true  # Toggle enriched data fetching
BROWSER_AGENT_TIMEOUT=30    # Max seconds per fetch
```

---

## Testing

1. Install dependencies: `uv sync`
2. Test browser client locally
3. Test individual fetchers
4. Integrate into reflection endpoint
5. Test end-to-end

---

## Benefits

### **Competitive Moat:**
- ✅ Real-time data (not static horoscopes)
- ✅ Multi-source aggregation
- ✅ Impossible to replicate with simple prompts
- ✅ Fresh insights every day
- ✅ Deep personalization

### **User Experience:**
- ✅ Reflections feel prophetic (using real cosmic data)
- ✅ Never repetitive (always fresh sources)
- ✅ More accurate to actual astrological events
- ✅ Richer, more textured responses

---

## Next Steps

1. ✅ Install dependencies (`bedrock-agentcore`, `browser-use`, `langchain-aws`)
2. ✅ Test browser client locally
3. ✅ Test data fetchers individually
4. Wire into reflection endpoint
5. Test end-to-end
6. Deploy to Railway
7. Monitor costs and performance
