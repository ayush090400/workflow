# Quick Start Guide

Get up and running in 5 minutes.

## Step 1: Install Dependencies

```bash
cd x-research
pip install -r requirements.txt
playwright install chromium
```

## Step 2: Configure API Key

```bash
python x-research.py config
```

Enter your Anthropic API key when prompted.
Get one free at: https://console.anthropic.com/

## Step 3: Add Sample Data

Try it with the template data:

```bash
python x-research.py add data/template.csv
```

## Step 4: Run Your First Analysis

```bash
python x-research.py analyze
```

You'll get a detailed insights report!

## What's Next?

### Add Your Own Data

Create a CSV file with your tweet research:

```csv
account_handle,tweet_text,posted_date,likes,retweets,replies,notes
@username,Tweet content here,2026-01-18,100,20,5,Your notes
```

**Required columns:**
- `account_handle` (can include or omit @)
- `tweet_text`
- `posted_date` (YYYY-MM-DD or MM/DD/YYYY)

**Optional columns:**
- `likes`, `retweets`, `replies` (engagement numbers)
- `tweet_url` (link to the tweet)
- `notes` (your observations)

Then:
```bash
python x-research.py add data/your_file.csv
python x-research.py analyze
```

### Regular Workflow - Automatic (Recommended)

Every 3-4 days, just run:

```bash
python x-research.py fetch --accounts @sama,@levelsio,@patrick
python x-research.py analyze --since-last
```

Review insights (5-10 mins) and implement takeaways.

### Regular Workflow - Manual

If you prefer manual collection:

1. Collect new tweet data from accounts you're tracking
2. Save as CSV
3. Run:
   ```bash
   python x-research.py add data/latest.csv
   python x-research.py analyze --since-last
   ```
4. Review insights (5-10 mins)
5. Implement takeaways

### Other Useful Commands

```bash
# See your stats
python x-research.py stats

# List tracked accounts
python x-research.py accounts

# Export your data
python x-research.py export

# Get help
python x-research.py --help
```

## Tips

- Track 5-10 accounts consistently (quality over quantity)
- Add engagement metrics when possible - helps AI spot patterns
- Use the notes field for your observations
- Run analysis every 3-4 days for best trend detection

---

Need more details? Check the full **README.md**
