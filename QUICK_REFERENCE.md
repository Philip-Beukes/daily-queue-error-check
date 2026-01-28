# Quick Reference Guide

## Basic Commands

### Setup (One Time)
```bash
pip install -r requirements.txt
cp config.env.template .env
# Edit .env with your settings
```

### Simple Error Count Report
```bash
python get_error_jobs.py
```

### With Detailed Logs
```bash
python get_error_jobs.py --fetch-details
```

## Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `--date YYYY-MM-DD` | Query specific date | `--date 2026-01-15` |
| `--fetch-details` | Fetch detailed logs for each queue ID | `--fetch-details` |
| `--detail-limit N` | Limit details to top N queue IDs | `--detail-limit 5` |
| `--no-verify-ssl` | Disable SSL verification | `--no-verify-ssl` |
| `--verbose`, `-v` | Show debug information | `--verbose` |
| `--dry-run` | Test configuration only | `--dry-run` |

## Common Workflows

### 1. Daily Summary (Fast)
```bash
# Just get counts, no details (1 API call)
python get_error_jobs.py
```

**Output:**
- Queue ID counts
- Total unique queue IDs
- Total error jobs

### 2. Top Problems (Recommended)
```bash
# Get summary + details for top 5 queue IDs (6 API calls)
python get_error_jobs.py --fetch-details --detail-limit 5
```

**Output:**
- Queue ID counts
- Detailed logs for top 5 problematic queues
- Error messages and stack traces

### 3. Full Investigation
```bash
# Get everything (1 + N API calls where N = unique queue IDs)
python get_error_jobs.py --fetch-details --verbose
```

**Output:**
- Queue ID counts
- Detailed logs for ALL queue IDs
- Debug information

### 4. Specific Date Analysis
```bash
# Investigate errors from specific date
python get_error_jobs.py --date 2026-01-15 --fetch-details --detail-limit 10
```

### 5. Test Connection
```bash
# Verify configuration without querying data
python get_error_jobs.py --dry-run
```

## Environment Variables (.env file)

```bash
# Required
SBS_BASE_URL=https://your-sbs-server.com
SBS_USERNAME=your-username
SBS_COUNTRY=US
SBS_LANGUAGE=en
SBS_DATABASE_ID=your-database-id

# Optional
SBS_NO_VERIFY_SSL=true  # For self-signed certs
```

## Output Examples

### Summary Only (No --fetch-details)

```
============================================================
SBS Error Job History Report
============================================================
Queue ID Statistics
============================================================
Queue ID             |      Count
------------------------------------------------------------
185524254            |      2,203
185451684            |         40
------------------------------------------------------------
Total Unique Queue IDs: |          2
Total Error Jobs:    |      2,243
============================================================
```

### With Details (--fetch-details)

```
[Summary shown above, then:]

================================================================================
DETAILED SYSTEM LOGS
================================================================================
Fetching details for all 2 queue IDs
This may take a moment...
================================================================================

================================================================================
DETAILED ERROR LOG - Queue ID: 185524254
================================================================================
Total Log Entries: 5
Process Names: Apply Prices

Log Entry #1
--------------------------------------------------------------------------------
Log ID: 157183187
Created: 2026-01-08T15:31:24.421+02:00 by engine
Process: Apply Prices
Message Code: ERR - Error

Error Message:
BRA-002 - An application error occurred...

Stack Trace (first 500 chars):
1. TechnicalException: BRA-001...
...
```

## API Call Costs

| Command | API Calls | When to Use |
|---------|-----------|-------------|
| Basic | 1 | Daily monitoring, quick checks |
| `--detail-limit 5` | 6 | Focused investigation |
| `--detail-limit 10` | 11 | Deeper analysis |
| `--fetch-details` (all) | 1 + N | Full investigation |

*N = number of unique queue IDs*

## Tips & Tricks

### 1. Save Output to File
```bash
python get_error_jobs.py --fetch-details > report.txt 2>&1
```

### 2. Search for Specific Errors
```bash
python get_error_jobs.py --fetch-details | grep "NoSuchElement"
```

### 3. Dated Reports
```bash
python get_error_jobs.py --fetch-details > "report_$(date +%Y%m%d).txt"
```

### 4. Monitor Progress
```bash
python get_error_jobs.py --fetch-details --detail-limit 20 --verbose
```

Shows:
```
[DEBUG] Fetching details for queue ID 185524254 (1/20)
[DEBUG] Fetching details for queue ID 185451684 (2/20)
...
```

### 5. Check Configuration First
```bash
python get_error_jobs.py --dry-run --verbose
```

### 6. Override .env for Testing
```bash
python get_error_jobs.py --base-url https://test-server.com --fetch-details
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| SSL Certificate Error | Add `--no-verify-ssl` |
| Connection Timeout | Check server URL, use `--verbose` |
| Too many API calls | Use `--detail-limit N` |
| Missing configuration | Run `--dry-run` to check |
| Want full stack traces | Edit script, increase 500 char limit |

## Testing Without API

```bash
# Test with example data files
python test_with_example.py          # Basic test
python test_with_details.py          # With details test
```

## Cron Job Examples

### Daily Summary Email
```bash
0 8 * * * cd /path/to/script && python get_error_jobs.py | mail -s "Daily Error Report" admin@example.com
```

### Weekly Detailed Report
```bash
0 9 * * 1 cd /path/to/script && python get_error_jobs.py --fetch-details --detail-limit 10 > /var/log/sbs_weekly_$(date +\%Y\%m\%d).log
```

## Performance

| Queue IDs | API Calls | Approx Time* |
|-----------|-----------|--------------|
| 10 | 11 | ~11 seconds |
| 50 | 51 | ~51 seconds |
| 100 | 101 | ~100 seconds |

*Assuming 1 second per API call

**Recommendation:** Use `--detail-limit 10` for regular monitoring

## See Also

- `README.md` - Full documentation
- `DETAILED_LOGS.md` - Detailed log fetching guide
- `CHANGELOG.md` - Version history
- `--help` - Command-line help
