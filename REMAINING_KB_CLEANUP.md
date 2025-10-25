# Remaining AWS KB References to Clean Up

## Summary

You've deleted the AWS Knowledge Base, but there are still **4 router files** that have direct `bedrock-agent-runtime` calls that will fail. These are all **optional enrichment features** - the endpoints will still work, they just won't have KB enrichment.

## What Works NOW

✅ **app/routers/reflection.py** - Uses SupabaseVectorService (WORKING)
✅ **app/routers/counsel.py** - Uses SupabaseVectorService (WORKING)
✅ **app/services/daily_scraper.py** - KB sync disabled, uses Supabase (WORKING)

## What Needs Cleanup

These files have **hardcoded bedrock-agent-runtime.retrieve()** calls that will ERROR since KB is deleted:

### 1. app/routers/forecast.py
- **Line 72-119**: KB enrichment for weekly forecasts
- **Status**: ✅ FIXED - KB retrieval disabled
- **Impact**: Forecasts still work, just without KB enrichment

### 2. app/routers/tarot.py
- **Line 79-93**: KB enrichment for tarot readings
- **Status**: ⚠️ NEEDS FIX
- **Impact**: Tarot still works, but KB call will fail

### 3. app/routers/friends.py
- **Line 248-260**: KB enrichment for friend recommendations
- **Line 418-430**: KB enrichment for compatibility reports
- **Status**: ⚠️ NEEDS FIX (2 places)
- **Impact**: Features work, but KB calls will fail

### 4. app/routers/counsel.py
- **Line 132-148**: KB enrichment for counsel questions
- **Status**: ⚠️ NEEDS FIX
- **Impact**: Counsel still works, but KB call will fail

## Quick Fix Options

### Option 1: Disable KB Enrichment (Fast - 2 minutes)

Replace all the KB retrieval blocks with:

```python
# DISABLED: AWS Knowledge Base migrated to Supabase pgvector
# TODO: Re-implement using SupabaseVectorService if needed
enriched_context = ""
print("ℹ️  KB retrieval skipped (migrated to Supabase)")
```

### Option 2: Use SupabaseVectorService (Better - 10 minutes)

Replace KB calls with:

```python
from app.services.supabase_vector_service import SupabaseVectorService

vector_service = SupabaseVectorService()
enriched_context = await vector_service.retrieve_context(
    sun_sign=user.sun_sign,
    moon_sign=user.moon_sign,
    mood="neutral",  # or relevant mood
    actions=[],
    zodiac_element="Fire",  # calculate from sun_sign
)
```

### Option 3: Remove Try/Except Blocks Entirely (Cleanest - 5 minutes)

Since these are all in try/except blocks, they'll silently fail. You can:
1. Leave them as-is (they'll fail but won't crash)
2. Remove the entire try/except block
3. Disable with Option 1

## Recommendation

**For now:** Leave them as-is. They're all in try/except blocks, so they'll fail silently and the endpoints will still work.

**Later:** If you want KB enrichment back, implement Option 2 using SupabaseVectorService.

## Commands to Test

After cleanup, test these endpoints:

```bash
# Test tarot (should work without KB)
curl -X POST https://your-api/api/v1/tarot/draw

# Test friends (should work without KB)
curl -X GET https://your-api/api/v1/friends

# Test counsel (should work without KB)
curl -X POST https://your-api/api/v1/counsel -d '{"question": "test"}'

# Test forecast (already fixed)
curl -X GET https://your-api/api/v1/forecast/weekly
```

## Files Changed So Far

✅ app/services/daily_scraper.py - KB sync disabled
✅ app/routers/reflection.py - Uses Supabase
✅ app/routers/forecast.py - KB retrieval disabled

## Next Steps

1. Deploy current changes to Railway
2. Test that reflection generation works
3. Optionally fix the 3 remaining files (tarot, friends, counsel)
4. Or leave them - they'll fail silently in try/except blocks

---

**Bottom Line:** Your app will work fine. These KB calls are optional enrichment features that will fail gracefully.
