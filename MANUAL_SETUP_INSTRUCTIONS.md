# Manual Setup Instructions

## Part 1: Supabase Setup (5 minutes)

### Step 1: Run SQL Migration

1. Go to https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new
2. Copy and paste the ENTIRE contents of `migrations/create_astrology_documents_table.sql`
3. Click **RUN** button
4. You should see: **"Success. No rows returned"**

### Step 2: Verify Table Created

Run this query to verify:

```sql
SELECT COUNT(*) FROM astrology_documents;
```

Expected result: `0` (empty table, which is correct)

### Step 3: Verify Function Created

Run this query to verify:

```sql
SELECT proname FROM pg_proc WHERE proname = 'match_astrology_documents';
```

Expected result: `match_astrology_documents` (function exists)

## Part 2: Deploy Updated Backend (2 minutes)

### Push Code to Railway

```bash
cd /Users/georgiosvasilakis/src/karmona-backend

# Commit changes
git add .
git commit -m "Migrate from AWS OpenSearch to Supabase pgvector - saves $175/month"
git push origin main
```

Railway will automatically redeploy.

### Verify Deployment

1. Go to Railway dashboard
2. Check deployment logs for "Deployment successful"
3. Wait ~2 minutes for build to complete

## Part 3: Test the Migration (5 minutes)

### Test 1: Run Scraping Job

This will populate Supabase with astrology data:

```bash
cd /Users/georgiosvasilakis/src/karmona-backend
uv run python scripts/run_daily_scrape.py
```

**Watch for these lines:**
```
✅ Uploaded daily/2025-10-25/ephemeris_planetary_positions.json to S3
✅ Stored ephemeris-planetary_positions-2025-10-25 in Supabase pgvector
```

If you see errors, check:
- Supabase credentials in .env
- Table was created correctly
- pgvector extension is enabled

### Test 2: Verify Data in Supabase

Go to Supabase → SQL Editor and run:

```sql
SELECT
    id,
    LEFT(content, 100) as content_preview,
    metadata->>'source' as source,
    metadata->>'date' as date
FROM astrology_documents
ORDER BY created_at DESC
LIMIT 10;
```

You should see documents with ephemeris data, cafe astrology, etc.

### Test 3: Test Reflection Generation

Use your mobile app or make a curl request:

```bash
curl -X POST https://karmona-backend-production.up.railway.app/api/v1/reflection/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mood": "good",
    "actions": ["meditated", "helped"],
    "note": "Testing Supabase vector retrieval"
  }'
```

**Check Railway logs for:**
```
🔍 Searching Supabase with query: Capricorn zodiac sign ...
✅ Retrieved 5 chunks from Supabase
   Chunk 1 similarity: 0.845
   Chunk 2 similarity: 0.782
   ...
```

If you see this, **IT'S WORKING!** 🎉

## Part 4: Delete AWS OpenSearch (SAVES $175/MONTH) ⚠️

### IMPORTANT: Wait 24-48 hours before deleting!

Test the new system for 1-2 days first. Once you're confident:

### Step 1: Delete Knowledge Base

1. Go to https://console.aws.amazon.com/bedrock/
2. Click **Knowledge bases** in left sidebar
3. Find **ZDDIIWWBMV** (your knowledge base)
4. Click **Delete**
5. Type the confirmation text
6. Click **Delete knowledge base**

### Step 2: Delete Data Source

1. In Bedrock console, go to **Data sources**
2. Find data source **GHIJ2U38LL**
3. Click **Delete**
4. Confirm deletion

### Step 3: Delete OpenSearch Collection

1. Go to https://console.aws.amazon.com/aos/ (OpenSearch Service)
2. Click **Collections** in left sidebar
3. Find your OpenSearch Serverless collection (likely named `bedrock-knowledge-base-*`)
4. Click **Delete**
5. Type DELETE to confirm
6. Click **Delete collection**

**This step saves you ~$175/month!**

### Step 4: Keep S3 Bucket (Optional)

The S3 bucket (`karmona-astrology-data-967392725523`) costs ~$0.10/month.

**Recommendation:** Keep it for backups and compliance.

If you want to delete it:
1. Go to https://s3.console.aws.amazon.com/s3/
2. Find bucket `karmona-astrology-data-967392725523`
3. **Empty bucket first** (delete all objects)
4. Then **Delete bucket**

## Part 5: Verify Cost Savings (1 week later)

### Check AWS Billing

1. Go to https://console.aws.amazon.com/billing/
2. Click **Bills** → Current month
3. Look for **OpenSearch** line item
4. It should show $0 or significantly reduced costs

### Expected Savings Timeline

- **Week 1:** Still billed for partial month (~$43)
- **Week 2-4:** Prorated refund or credits
- **Next month:** $0 OpenSearch charges ✅

## 🎉 You're Done!

### Summary

✅ Migrated vector storage from AWS OpenSearch → Supabase pgvector
✅ Backend updated and deployed
✅ Scraping job now stores in Supabase
✅ Reflections use Supabase for retrieval
✅ AWS OpenSearch deleted
✅ **Saving $175/month!**

### Cost Breakdown

| Service | Before | After | Savings |
|---------|--------|-------|---------|
| OpenSearch | $175/mo | $0/mo | $175 ✅ |
| S3 Storage | $0.10/mo | $0.10/mo | $0 |
| Titan Embeddings | $3/mo | $3/mo | $0 |
| Supabase | $0/mo | $0-25/mo | -$25 |
| **Total** | **$178/mo** | **$3-28/mo** | **$150-175/mo** |

## 🆘 Troubleshooting

### Issue: "extension vector does not exist"

**Fix:** Run in Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue: "relation astrology_documents does not exist"

**Fix:** You forgot to run the migration. Go back to Part 1, Step 1.

### Issue: Scraping fails with "Error storing document"

**Check:**
1. Supabase credentials in Railway env vars
2. Table exists: `SELECT * FROM astrology_documents LIMIT 1;`
3. Check Supabase logs for errors

### Issue: No results from Supabase search

**Fix:**
```sql
-- Check if data exists
SELECT COUNT(*) FROM astrology_documents;

-- If 0, run scraping job again
uv run python scripts/run_daily_scrape.py
```

### Issue: Reflections are worse quality

**Possible causes:**
1. Supabase doesn't have enough data yet (run scraping job)
2. Similarity threshold too high (edit `match_threshold` in code)
3. Need to wait for more daily scrapes to accumulate data

---

## 📞 Need Help?

If you run into issues:
1. Check Railway logs (Backend → Deployments → View Logs)
2. Check Supabase logs (Dashboard → Logs)
3. Verify migration SQL ran successfully
4. Make sure AWS credentials still work (for Titan embeddings)

**Remember:** You can always rollback by reverting the git commit!
