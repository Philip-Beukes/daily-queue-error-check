# Usage Examples

## Quick Start (3 steps!)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create and edit .env file
cp config.env.template .env
# Edit .env with your server details

# 3. Run!
python get_error_jobs.py
```

## Common Use Cases

### 1. Today's Error Report

```bash
python get_error_jobs.py
```

### 2. Specific Date

```bash
python get_error_jobs.py --date 2026-01-15
```

### 3. Debug Mode (verbose)

```bash
python get_error_jobs.py --verbose
```

Shows:
- Whether .env file was loaded
- API endpoint being called
- Request payload
- Response status

### 4. Test Configuration

```bash
python get_error_jobs.py --dry-run
```

Validates configuration without making API call.

### 5. Override Config for Testing

```bash
# Use .env for most values, but test against different server
python get_error_jobs.py --base-url https://test-server.com
```

### 6. Full Command-Line (no .env)

```bash
python get_error_jobs.py \
  --base-url https://sbs.example.com \
  --username demo \
  --country US \
  --language en \
  --db-id PROD01 \
  --date 2026-01-27 \
  --verbose
```

### 7. Test with Example Data (no API call)

```bash
# Test data processing without network call
python test_with_example.py
```

### 8. Disable SSL Verification (Self-Signed Certificates)

```bash
# Command line option
python get_error_jobs.py --no-verify-ssl

# Or add to .env file
echo "SBS_NO_VERIFY_SSL=true" >> .env
python get_error_jobs.py

# With verbose to confirm
python get_error_jobs.py --no-verify-ssl --verbose
```

⚠️ **Warning:** Only use for trusted servers with self-signed certificates!

## Expected Output

```
Querying SBS for error jobs on 2026-01-27...

============================================================
SBS Error Job History Report
============================================================
Generated: 2026-01-27 14:30:45
Query Date: 2026-01-27
Queue: GENQ
Status: ERR (Error)

API Response:
  Version: 12.6.204.467.6
  Execution Time: 360ms

============================================================
Queue ID Statistics
============================================================

Queue ID             |      Count
------------------------------------------------------------
185524254            |      2,203
185451684            |         40
185701227            |          7
------------------------------------------------------------
Total Unique Queue IDs: |          3
Total Error Jobs:    |      2,250
============================================================
```

## Automation Examples

### Daily Cron Job

```bash
# Run every day at 8 AM
0 8 * * * cd /path/to/script && python get_error_jobs.py >> /var/log/sbs_errors.log 2>&1
```

### Weekly Report

```bash
#!/bin/bash
# weekly_report.sh - Run for past 7 days

for i in {0..6}; do
  date=$(date -d "$i days ago" +%Y-%m-%d)
  echo "=== Report for $date ==="
  python get_error_jobs.py --date $date
  echo ""
done
```

### Alert on High Error Count

```bash
#!/bin/bash
# alert_if_high_errors.sh

output=$(python get_error_jobs.py)
error_count=$(echo "$output" | grep "Total Error Jobs:" | awk '{print $4}' | tr -d ',')

if [ "$error_count" -gt 1000 ]; then
  echo "HIGH ERROR COUNT: $error_count errors found!"
  # Send email or notification
fi
```

## Tips

1. **Always start with `--dry-run`** to validate configuration
2. **Use `--verbose`** when troubleshooting connection issues
3. **Test with `test_with_example.py`** before making real API calls
4. **Keep `.env` secure** - it contains credentials
5. **Check exit codes** in scripts: `0` = success, non-zero = error
