# Auto-Save to Results Folder

## Overview

When you use `--fetch-details`, the script **automatically saves** the complete report to the `results/` folder!

## How It Works

### Automatic File Saving

```bash
# Just run with --fetch-details
python get_error_jobs.py --fetch-details
```

**What happens:**
1. ✓ Creates `results/` folder if it doesn't exist
2. ✓ Generates filename with timestamp: `error_report_YYYYMMDD_HHMMSS.txt`
3. ✓ Saves complete report including process analysis
4. ✓ Shows confirmation message

**Example output:**
```
Querying SBS for error jobs on 2026-01-28...

[... report content ...]

[SUCCESS] Report written to: results/error_report_20260128_143012.txt
```

### Limit Results

```bash
# Fetch details for top 10 queue IDs and auto-save
python get_error_jobs.py --fetch-details --detail-limit 10
```

**Result:** `results/error_report_20260128_143530.txt`

### Manual Filename

If you want to specify your own filename:

```bash
# Use -o flag to override auto-save
python get_error_jobs.py --fetch-details -o my_report.txt
```

**Result:** `my_report.txt` (in current directory, not results/)

### With Verbose Mode

```bash
# See progress while saving
python get_error_jobs.py --fetch-details --verbose
```

**Console output:**
```
[DEBUG] Loaded configuration from .env file
[DEBUG] Writing output to: results/error_report_20260128_143745.txt
[DEBUG] Fetching details for queue ID 185524254 (1/10)
[DEBUG] Fetching details for queue ID 185451684 (2/10)
...

[SUCCESS] Report written to: results/error_report_20260128_143745.txt
```

## File Contents

Each auto-saved file contains:

### 1. Summary Report
```
============================================================
SBS Error Job History Report
============================================================
Generated: 2026-01-28 14:30:45
Query Date: 2026-01-28
Queue: GENQ
Status: ERR (Error)

Queue ID Statistics
============================================================
Queue ID             |      Count
------------------------------------------------------------
185524254            |      2,203
185451684            |         40
...
```

### 2. Detailed Error Logs
```
================================================================================
DETAILED ERROR LOG - Queue ID: 186000213
================================================================================

Total Log Entries: 3
Process Names: Apply Prices

Log Entry #1
--------------------------------------------------------------------------------
Log ID: 157183187
Created: 2026-01-08T15:31:24.421+02:00 by engine
Process: Apply Prices
Message Code: ERR - Error

Error Message:
BRA-002 - An application error occurred...

Stack Trace:
[Full stack trace with all details]
...
```

### 3. Process Analysis Summary
```
================================================================================
ERROR ANALYSIS BY PROCESS
================================================================================

Total Processes with Errors: 3

Process:             Apply Prices
Error Count:         156
Affected Queue IDs:  5 unique queue(s)
Queue IDs:           186000213, 186000214, 186000215

Sample Errors:      
  1. BRA-002 - An application error occurred...
  2. BRA-SQLB-00571 - An unexpected error occurred...
...

SUMMARY STATISTICS
--------------------------------------------------------------------------------
Total Errors Analyzed:         198
Total Unique Queue IDs:        7
Total Unique Processes:        3
Average Errors per Process:    66.0
```

## File Naming Convention

Auto-generated files follow this pattern:
```
error_report_YYYYMMDD_HHMMSS.txt
```

Examples:
- `error_report_20260128_143012.txt` - Jan 28, 2026 at 14:30:12
- `error_report_20260128_083045.txt` - Jan 28, 2026 at 08:30:45
- `error_report_20260201_170022.txt` - Feb 01, 2026 at 17:00:22

**Benefits:**
- ✓ Chronologically sorted
- ✓ No filename conflicts
- ✓ Easy to identify when report was generated
- ✓ Can run multiple times per day

## Folder Structure

```
getErrorSBSCalls/
├── get_error_jobs.py
├── .env
└── results/
    ├── error_report_20260128_080000.txt
    ├── error_report_20260128_140000.txt
    ├── error_report_20260128_200000.txt
    └── error_report_20260129_080000.txt
```

## Summary-Only Mode

If you **don't** use `--fetch-details`, output goes to console (no file):

```bash
# No auto-save, output to console
python get_error_jobs.py
```

**Result:** Summary displayed on screen, no file created

## Common Scenarios

### Daily Automated Report

```bash
# Add to scheduled task/cron
python get_error_jobs.py --fetch-details --detail-limit 20
```

Each run creates a new dated file in `results/` folder.

### Weekly Cleanup

```powershell
# PowerShell - Archive reports older than 7 days
Compress-Archive -Path results\*.txt -DestinationPath "archive_$(Get-Date -Format 'yyyyMMdd').zip"
Remove-Item results\*.txt -Force
```

```bash
# Linux/Mac - Archive reports older than 7 days
find results/ -name "*.txt" -mtime +7 -exec tar -czf archive_$(date +%Y%m%d).tar.gz {} \; -delete
```

### Find Latest Report

```powershell
# PowerShell - Open latest report
Get-ChildItem results\*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

```bash
# Linux/Mac - View latest report
ls -t results/*.txt | head -1 | xargs cat
```

### Search Reports

```bash
# Find all reports with specific error
grep -l "NoSuchElementException" results/*.txt

# Count errors by date
for file in results/*.txt; do
    echo "$file: $(grep -c "Error Message:" $file)"
done
```

## Tips

1. **Always use `--fetch-details` for complete reports**
   - Summary only is quick but limited
   - Detailed reports are saved automatically

2. **The `results/` folder is created automatically**
   - No need to create it manually
   - Safe to delete old files

3. **Archive old reports regularly**
   - Compress reports older than 30 days
   - Saves disk space

4. **Use meaningful limits**
   - `--detail-limit 10` for daily monitoring
   - `--detail-limit 50` for investigations
   - No limit for complete analysis

5. **Combine with other tools**
   - `grep` to search reports
   - `diff` to compare reports
   - Scripts to analyze trends

## Troubleshooting

### Permission Denied

```
ERROR: Could not open output file results/error_report_20260128_143012.txt: Permission denied
```

**Solution:**
```bash
# Check permissions
ls -la results/

# Fix permissions (Linux/Mac)
chmod 755 results/

# Windows - Run as administrator or check folder permissions
```

### Disk Space

If you run the script frequently:

```bash
# Check disk usage
du -sh results/

# Compress old reports
gzip results/*.txt
```

### Find Specific Report

```bash
# By date
ls results/error_report_20260128*.txt

# By time
ls results/*143*.txt

# Latest
ls -t results/*.txt | head -1
```

## See Also

- `FILE_OUTPUT_AND_ANALYSIS.md` - Complete file output guide
- `README.md` - General usage
- `DETAILED_LOGS.md` - Detailed log fetching guide
