# File Output and Process Analysis

## Overview

The script now supports:
1. **File Output** - Write reports to files instead of console
2. **Process Analysis** - Automatic error analysis grouped by process name

## File Output

### Basic Usage

Write output to a file:

```bash
python get_error_jobs.py --fetch-details -o error_report.txt
```

Or use the long form:

```bash
python get_error_jobs.py --fetch-details --output-file error_report.txt
```

### What Gets Written

Everything that would normally appear on the console:
- Summary report (queue ID counts)
- Detailed error logs (if `--fetch-details` is used)
- Process analysis summary (if `--fetch-details` is used)

### Dated Reports

Create reports with date in filename:

#### Windows (PowerShell)
```powershell
python get_error_jobs.py --fetch-details -o "report_$(Get-Date -Format 'yyyyMMdd').txt"
```

#### Linux/Mac
```bash
python get_error_jobs.py --fetch-details -o "report_$(date +%Y%m%d).txt"
```

### Verbose Mode with File Output

When using file output with verbose mode:
- Main output → File
- Debug messages → Console (stderr)

```bash
python get_error_jobs.py --fetch-details -o report.txt --verbose
```

You'll see progress on screen, but the full report goes to the file!

## Process Analysis

### Automatic Generation

When you use `--fetch-details`, the script automatically analyzes errors by process name.

### What You Get

The analysis shows:

1. **Per-Process Statistics**:
   - Process name
   - Total error count
   - Number of affected queue IDs
   - List of queue IDs
   - Sample error messages (first 3)

2. **Summary Statistics**:
   - Total errors analyzed
   - Total unique queue IDs
   - Total unique processes
   - Average errors per process

### Example Output

```
================================================================================
ERROR ANALYSIS BY PROCESS
================================================================================

Total Processes with Errors: 3

--------------------------------------------------------------------------------

Process:             Apply Prices
Error Count:         156
Affected Queue IDs:  5 unique queue(s)
Queue IDs:           186000213, 186000214, 186000215, 186000216, 186000217

Sample Errors:      
  1. BRA-002 - An application error occurred. Please refer to stacktrace...
     Queue ID: 186000213, Date: 2026-01-08T15:31:24.421+02:00
  2. BRA-002 - An application error occurred. Please refer to stacktrace...
     Queue ID: 186000214, Date: 2026-01-08T15:32:10.123+02:00
  3. BRA-SQLB-00571 - An unexpected error occurred...
     Queue ID: 186000215, Date: 2026-01-08T15:33:45.678+02:00
--------------------------------------------------------------------------------

Process:             Calculate Contributions
Error Count:         42
Affected Queue IDs:  2 unique queue(s)
Queue IDs:           186000220, 186000221

Sample Errors:      
  1. BRA-001 - A technical error occurred...
     Queue ID: 186000220, Date: 2026-01-08T16:10:15.234+02:00
  2. BRA-003 - Database connection failed...
     Queue ID: 186000221, Date: 2026-01-08T16:11:22.456+02:00
--------------------------------------------------------------------------------

SUMMARY STATISTICS
--------------------------------------------------------------------------------
Total Errors Analyzed:         198
Total Unique Queue IDs:        7
Total Unique Processes:        3
Average Errors per Process:    66.0
================================================================================
```

## Common Use Cases

### 1. Daily Error Report to File

```bash
# Generate and save today's errors with analysis
python get_error_jobs.py --fetch-details --detail-limit 10 -o daily_report.txt
```

### 2. Investigate Specific Date

```bash
# Analyze errors from a specific date
python get_error_jobs.py --date 2026-01-15 --fetch-details -o investigation_20260115.txt
```

### 3. Quick Summary Only (No File)

```bash
# Just show on screen
python get_error_jobs.py
```

### 4. Full Analysis to File

```bash
# Everything to file
python get_error_jobs.py --fetch-details -o full_analysis.txt
```

### 5. Monitor Progress While Saving

```bash
# See progress, save report
python get_error_jobs.py --fetch-details --detail-limit 20 -o report.txt --verbose
```

Console shows:
```
[DEBUG] Loaded configuration from .env file
[DEBUG] Fetching details for queue ID 185524254 (1/20)
[DEBUG] Fetching details for queue ID 185451684 (2/20)
...

Report written to: report.txt
```

## Analysis Benefits

### Identify Problem Areas

The process analysis helps you:

1. **Find the most problematic processes**
   - Sorted by error count
   - See which processes have the most failures

2. **Understand impact scope**
   - How many queue IDs are affected per process
   - Which processes impact multiple queues

3. **Get context quickly**
   - Sample errors show common failure patterns
   - Timestamps show when errors occurred

4. **Plan fixes**
   - Focus on processes with highest error counts
   - Prioritize fixes by impact (queue count)

## File Output Best Practices

### 1. Use Meaningful Filenames

```bash
# Good - descriptive and dated
python get_error_jobs.py -o "prod_errors_20260128_applyprices.txt"

# Bad - generic
python get_error_jobs.py -o "output.txt"
```

### 2. Organize by Date

```bash
# Create monthly directories
mkdir -p reports/2026-01
python get_error_jobs.py --fetch-details -o "reports/2026-01/errors_$(date +%Y%m%d).txt"
```

### 3. Save Full Details

```bash
# Always use --fetch-details when saving to file for later analysis
python get_error_jobs.py --fetch-details -o report.txt
```

### 4. Compress Old Reports

```bash
# Compress reports older than 7 days
find reports/ -name "*.txt" -mtime +7 -exec gzip {} \;
```

## Automated Reporting

### Daily Report Script (Linux/Mac)

```bash
#!/bin/bash
# daily_error_report.sh

REPORT_DIR="/var/reports/sbs"
DATE=$(date +%Y%m%d)
REPORT_FILE="$REPORT_DIR/errors_$DATE.txt"

mkdir -p "$REPORT_DIR"

cd /path/to/script
python get_error_jobs.py \
  --fetch-details \
  --detail-limit 20 \
  --output-file "$REPORT_FILE"

# Email if errors found
if [ -s "$REPORT_FILE" ]; then
    mail -s "SBS Error Report $DATE" admin@example.com < "$REPORT_FILE"
fi
```

### Daily Report Script (Windows PowerShell)

```powershell
# daily_error_report.ps1

$ReportDir = "C:\Reports\SBS"
$Date = Get-Date -Format "yyyyMMdd"
$ReportFile = "$ReportDir\errors_$Date.txt"

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

cd C:\Path\To\Script
python get_error_jobs.py `
  --fetch-details `
  --detail-limit 20 `
  --output-file $ReportFile

# Email if file has content
if ((Get-Item $ReportFile).Length -gt 0) {
    Send-MailMessage `
        -To "admin@example.com" `
        -Subject "SBS Error Report $Date" `
        -Body (Get-Content $ReportFile -Raw) `
        -SmtpServer "smtp.example.com"
}
```

### Cron Job (Linux/Mac)

```bash
# Add to crontab: crontab -e
# Run daily at 8 AM
0 8 * * * cd /path/to/script && python get_error_jobs.py --fetch-details --detail-limit 10 -o /var/reports/sbs/daily_$(date +\%Y\%m\%d).txt
```

### Scheduled Task (Windows)

```powershell
# Create scheduled task
$Action = New-ScheduledTaskAction -Execute "python.exe" `
    -Argument "C:\Path\To\get_error_jobs.py --fetch-details --detail-limit 10 -o C:\Reports\daily_report.txt" `
    -WorkingDirectory "C:\Path\To"

$Trigger = New-ScheduledTaskTrigger -Daily -At 8am

Register-ScheduledTask -TaskName "SBS Daily Error Report" `
    -Action $Action -Trigger $Trigger -Description "Generate daily SBS error report"
```

## Reading Reports

### View Report

```bash
# View entire report
cat report.txt

# View with paging
less report.txt

# Search for specific errors
grep "NoSuchElement" report.txt

# See only process summary
tail -n 50 report.txt
```

### Extract Specific Information

```bash
# Get only queue IDs
grep "Queue ID:" report.txt

# Get only process names
grep "Process:" report.txt

# Count errors per process
grep "Error Count:" report.txt
```

## Tips

1. **Always use `--fetch-details` when writing to file**
   - Files are for later analysis
   - You want complete information

2. **Use `--detail-limit` to control report size**
   - Start with 10-20 for daily monitoring
   - Use higher limits for investigations

3. **Name files descriptively**
   - Include date, environment, purpose
   - Makes finding reports easier

4. **Archive old reports**
   - Compress files older than 7-30 days
   - Keep originals for compliance if needed

5. **Use verbose mode during development**
   - See what's happening
   - Debug issues without opening files

## Troubleshooting

### File Permission Errors

```bash
# Ensure directory exists and is writable
mkdir -p reports
chmod 755 reports
python get_error_jobs.py -o reports/test.txt
```

### File Already Open

Windows may lock files. Close editors before running:

```powershell
# Check if file is open (PowerShell)
Get-Process | Where-Object {$_.MainWindowTitle -like "*report.txt*"}
```

### Large Files

For very large outputs:

```bash
# Stream to file and compress
python get_error_jobs.py --fetch-details | gzip > report.txt.gz

# Read later
zcat report.txt.gz | less
```

## Examples

### Example 1: Weekly Analysis

```bash
# Full week analysis
for day in {21..27}; do
    python get_error_jobs.py \
        --date 2026-01-$day \
        --fetch-details \
        --detail-limit 5 \
        -o "weekly_report_20260127.txt"
done
```

### Example 2: Production vs Test

```bash
# Production
python get_error_jobs.py --fetch-details -o prod_errors.txt

# Test (different server)
python get_error_jobs.py --base-url https://test-server.com --fetch-details -o test_errors.txt

# Compare
diff prod_errors.txt test_errors.txt
```

### Example 3: Email Alert on Errors

```bash
#!/bin/bash
REPORT=$(mktemp)
python get_error_jobs.py --fetch-details --detail-limit 10 -o "$REPORT"

# Check if errors found
if grep -q "Total Error Jobs:" "$REPORT"; then
    mail -s "ALERT: Errors Detected" admin@example.com < "$REPORT"
fi

rm "$REPORT"
```
