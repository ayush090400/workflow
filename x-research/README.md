# X Research - Automated X Account Analysis Tool

Automate your X (Twitter) account research workflow. Replace 3-4 hours of manual research with a 15-minute routine every 3-4 days.

## What It Does

- **Stores tweet data locally** - Keep a database of tweets from accounts you're researching
- **AI-powered analysis** - Uses Claude to identify patterns, trends, and tactical insights
- **Simple commands** - Just run `analyze` to get a comprehensive research report
- **Track over time** - Build historical data to spot emerging trends

## Quick Start

### 1. Installation

```bash
cd x-research

# Install dependencies
pip install anthropic pandas
```

### 2. Configure API Key

```bash
python x-research.py config
```

You'll need an Anthropic API key. Get one at: https://console.anthropic.com/

### 3. Add Your First Data

Create a CSV file with your tweet data (see `template.csv` for format):

```csv
account_handle,tweet_url,tweet_text,likes,retweets,replies,posted_date,notes
@sama,https://x.com/sama/status/123,Great thread on AI safety,1500,230,45,2026-01-15,Good hook
@patrick,https://x.com/patrick/status/456,Building in public...,890,120,30,2026-01-14,
```

Then import it:

```bash
python x-research.py add data/my_tweets.csv
```

### 4. Run Analysis

```bash
python x-research.py analyze
```

You'll get a comprehensive report with:
- Top patterns and trends
- What's working (and what's not)
- Tactical takeaways you can implement
- New and emerging approaches

## Commands

### `add` - Import Tweet Data

```bash
# Add from CSV
python x-research.py add data/tweets.csv

# Add from JSON
python x-research.py add data/tweets.json
```

**Supported formats:**
- CSV with headers (see template.csv)
- JSON array of tweet objects

**Required fields:**
- `account_handle` - X username (with or without @)
- `tweet_text` - Full tweet content
- `posted_date` - When tweet was posted (YYYY-MM-DD or MM/DD/YYYY)

**Optional fields:**
- `tweet_url` - Link to the tweet
- `likes`, `retweets`, `replies` - Engagement metrics
- `notes` - Your observations

### `analyze` - Generate Insights

```bash
# Analyze all tweets
python x-research.py analyze

# Analyze specific accounts only
python x-research.py analyze --accounts @sama,@patrick

# Analyze tweets from last 7 days
python x-research.py analyze --days 7

# Analyze only new tweets since last analysis
python x-research.py analyze --since-last

# Output as markdown
python x-research.py analyze --format markdown

# Output as JSON
python x-research.py analyze --format json
```

Analysis reports are automatically saved to the `reports/` directory.

### `stats` - View Statistics

```bash
python x-research.py stats
```

Shows:
- Total tweets and accounts tracked
- Date range of data
- Last analysis date
- Top accounts by volume

### `accounts` - List Tracked Accounts

```bash
python x-research.py accounts
```

Shows all accounts you're tracking with tweet counts and last tweet date.

### `export` - Export Your Data

```bash
# Export as CSV
python x-research.py export --format csv

# Export as JSON
python x-research.py export --format json

# Specify output file
python x-research.py export --output my_backup.csv
```

### `config` - Setup Configuration

```bash
python x-research.py config
```

Interactive setup for:
- Anthropic API key
- Other preferences

## Workflow Example

**Initial Setup (one time):**
```bash
python x-research.py config
```

**Every 3-4 days:**
1. Export tweet data from accounts you're tracking (manually or using a tool)
2. Save as CSV file
3. Run:
```bash
python x-research.py add data/jan15.csv
python x-research.py analyze --since-last
```
4. Review the insights (5-10 minutes)
5. Implement tactical takeaways in your content

**Total time:** 15-20 minutes vs 3-4 hours of manual research

## How to Get Tweet Data

The tool doesn't scrape X directly - you provide the data. Here are ways to get it:

### Manual Method (Free)
1. Create an X List with accounts you want to track
2. Browse the list weekly
3. Copy interesting tweets into a spreadsheet
4. Export as CSV and add to the tool

### Using Third-Party Tools
- Use tools like Taplio, Tweet Hunter, or Typefully to export data
- Many have CSV export features

### Browser Extension
- Use extensions that can export tweets you're viewing
- Save to CSV format

## File Structure

```
x-research/
├── x-research.py          # Main CLI application
├── database.py            # Database operations
├── data_importer.py       # CSV/JSON import handling
├── analyzer.py            # Claude API integration
├── config.json            # Your settings (created on first run)
├── database.db            # SQLite database (created on first run)
├── data/                  # Put your import files here
│   └── template.csv       # Example CSV format
└── reports/               # Generated analysis reports
    └── analysis_2026-01-18_14-30.md
```

## API Costs

Using Claude Haiku (default):
- ~$0.02-0.05 per analysis (depending on data volume)
- Running twice a week ≈ $0.50-1.50/month

Using Claude Sonnet (higher quality):
- ~$0.08-0.15 per analysis
- Running twice a week ≈ $1.50-3.00/month

To change models, edit the `model` parameter in `analyzer.py`.

## Tips for Best Results

1. **Track 5-10 accounts consistently** - More focused is better than too broad
2. **Add engagement metrics** - Helps the AI identify what's working
3. **Use the notes field** - Add your observations for richer analysis
4. **Run regularly** - Every 3-4 days gives good trend detection
5. **Implement takeaways** - Test the tactical insights in your own content

## Troubleshooting

**"anthropic library not installed"**
```bash
pip install anthropic
```

**"API key not found"**
```bash
python x-research.py config
# Or set environment variable:
export ANTHROPIC_API_KEY='your-key-here'
```

**"No tweets found"**
- Make sure you've added data first: `python x-research.py add <file>`
- Check your filters (--accounts, --days, --since-last)

**Import errors**
- Check your CSV has the required columns: `account_handle`, `tweet_text`, `posted_date`
- Make sure dates are in a valid format (YYYY-MM-DD or MM/DD/YYYY)

## Requirements

- Python 3.8 or higher
- `anthropic` library (for Claude API)
- `pandas` library (for CSV handling)

## License

MIT License - Use freely for personal or commercial projects.

## Contributing

Found a bug or have a feature request? Open an issue or submit a PR!

---

**Questions?** Check the troubleshooting section or review the code - it's well-commented and straightforward.
