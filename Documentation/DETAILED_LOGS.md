# Detailed System Log Fetching

## Overview

The script can fetch detailed system logs for each queue ID discovered in the error job history. This provides in-depth information about errors including full stack traces, error messages, and process information.

## How It Works

The script uses a two-step process:

### Step 1: Search Job History
- Calls `sbs/systemService/searchJobHistory`
- Gets list of error jobs and their queue IDs
- Counts occurrences per queue ID
- Displays summary report

### Step 2: Get System Logs (Optional)
- For each queue ID, calls `sbs/systemService/getSystemLog`
- Retrieves detailed error logs
- Displays full error information including stack traces

## Usage

### Basic Detailed Fetch

```bash
python get_error_jobs.py --fetch-details
```

This will:
1. Get all error jobs for today
2. Count unique queue IDs
3. Fetch and display detailed logs for **all** queue IDs

### Limit Number of Details

To avoid too many API calls, limit the number of queue IDs to fetch details for:

```bash
# Fetch details for top 5 queue IDs (sorted by error count)
python get_error_jobs.py --fetch-details --detail-limit 5
```

### Specific Date with Details

```bash
python get_error_jobs.py --date 2026-01-15 --fetch-details --detail-limit 3
```

### With Verbose Mode

```bash
python get_error_jobs.py --fetch-details --verbose
```

Shows progress as each queue ID is processed.

## Output Format

### Summary Report (Always Shown)

```
============================================================
SBS Error Job History Report
============================================================
Generated: 2026-01-28 14:30:45
Query Date: 2026-01-28
Queue: GENQ
Status: ERR (Error)

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

### Detailed Logs (When --fetch-details is used)

```
================================================================================
DETAILED SYSTEM LOGS
================================================================================

Fetching details for top 5 queue IDs (out of 10 total)
This may take a moment...
================================================================================

================================================================================
DETAILED ERROR LOG - Queue ID: 186000213
================================================================================

Total Log Entries: 3
Process Names: Apply Prices

--------------------------------------------------------------------------------

Log Entry #1
--------------------------------------------------------------------------------
Log ID: 157183187
Created: 2026-01-08T15:31:24.421+02:00 by engine
Process: Apply Prices
Message Code: ERR - Error

Error Message:
BRA-002 - An application error occurred. Please refer to stacktrace for further details.

Stack Trace (first 500 chars):
1. TechnicalException: BRA-001 - A technical error occurred...
2. CallException: BRA-SQLB-00316 - Could not invoke...
...

Log Entry #2
--------------------------------------------------------------------------------
...
```

## Information Displayed Per Queue ID

For each queue ID, the detailed report shows:

1. **Queue ID**: The queue identifier
2. **Total Log Entries**: Number of log records for this queue
3. **Process Names**: Unique process names associated with errors
4. **For Each Log Entry**:
   - Log ID
   - Created date and user
   - Process name
   - Message code (ERR, etc.)
   - Short error message
   - Stack trace (first 500 characters)

## Use Cases

### 1. Daily Error Monitoring with Details

```bash
# Get today's errors with details for top 10
python get_error_jobs.py --fetch-details --detail-limit 10
```

### 2. Investigating Specific Date

```bash
# Deep dive into errors from a specific date
python get_error_jobs.py --date 2026-01-15 --fetch-details
```

### 3. Quick Summary (No Details)

```bash
# Just get the counts, no detailed fetching
python get_error_jobs.py
```

### 4. Debugging Specific Queue ID

```bash
# Fetch all details with verbose output
python get_error_jobs.py --fetch-details --verbose
```

## Performance Considerations

### API Call Count

- **Without `--fetch-details`**: 1 API call total
- **With `--fetch-details`**: 1 + N API calls (where N = number of unique queue IDs)

Example:
- 10 unique queue IDs = 11 API calls (1 for job history + 10 for details)
- 100 unique queue IDs = 101 API calls

### Recommendations

1. **Use `--detail-limit` for large result sets**
   ```bash
   # If you have 100 queue IDs, only fetch top 10
   python get_error_jobs.py --fetch-details --detail-limit 10
   ```

2. **Queue IDs are sorted by error count**
   - The script fetches details for the most problematic queues first
   - Queue ID with most errors is processed first

3. **Enable verbose mode for progress tracking**
   ```bash
   python get_error_jobs.py --fetch-details --detail-limit 20 --verbose
   ```

## Error Handling

The script continues even if some queue IDs fail:

```bash
WARNING: Failed to fetch details for queue ID 12345: Connection timeout
```

- Other queue IDs will still be processed
- Failed queue IDs are skipped
- Final count shows how many were successfully processed

## Environment Variable

Add to your `.env` file:

```bash
# Always fetch details (top 5 queue IDs)
# Note: Command-line args override this
SBS_FETCH_DETAILS=true
SBS_DETAIL_LIMIT=5
```

**Note**: Currently command-line only. Environment variable support could be added if needed.

## Examples

### Example 1: Production Monitoring

```bash
#!/bin/bash
# Daily production error report with details for top 3

python get_error_jobs.py \
  --fetch-details \
  --detail-limit 3 \
  --no-verify-ssl \
  > error_report_$(date +%Y%m%d).txt 2>&1
```

### Example 2: Development Investigation

```bash
# Full details for specific date
python get_error_jobs.py \
  --date 2026-01-27 \
  --fetch-details \
  --verbose
```

### Example 3: Quick Check

```bash
# Just counts, no details
python get_error_jobs.py
```

## Testing

Test with example data files:

```bash
python test_with_details.py
```

This demonstrates:
- Summary report generation
- Detailed log fetching
- Output formatting
- No actual API calls made

## Tips

1. **Start with summary only** to see how many queue IDs you have
   ```bash
   python get_error_jobs.py
   ```

2. **Then fetch details for a few**
   ```bash
   python get_error_jobs.py --fetch-details --detail-limit 3
   ```

3. **Use grep to find specific errors**
   ```bash
   python get_error_jobs.py --fetch-details | grep "NoSuchElement"
   ```

4. **Save detailed output for analysis**
   ```bash
   python get_error_jobs.py --fetch-details > detailed_errors.log
   ```

## Troubleshooting

### "Request timeout" for details

Some queue IDs may have very large logs. The script will skip them and continue.

### Too many API calls

Use `--detail-limit` to reduce the number of queue IDs processed:

```bash
python get_error_jobs.py --fetch-details --detail-limit 5
```

### Want full stack traces

Currently limited to 500 chars. To get full traces, modify line in `get_error_jobs.py`:

```python
# Find this line and increase 500 to larger number
print(error['long_text'][:500] + "..." if len(error['long_text']) > 500 else error['long_text'])
```

Or save the full output and grep for specific queue IDs.
