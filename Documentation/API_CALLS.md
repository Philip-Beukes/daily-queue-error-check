# SBS API Calls Documentation

## Overview

This document describes the REST API calls made by the `get_error_jobs.py` script.

## API Call 1: Search Job History

### Endpoint
```
POST {baseUrl}/sbs/systemService/searchJobHistory
```

### Purpose
Get a list of error jobs from the queue for a specific date range.

### Request Payload
```json
{
  "callerDetails": {
    "username": "{{username}}",
    "country": "{{country}}",
    "language": "{{language}}",
    "databaseIdentifier": "{{databaseIdentifier}}"
  },
  "startDate": "2026-01-28T00:00:00.000Z",
  "endDate": "2026-01-28T23:59:59.000Z",
  "status": "ERR",
  "queue": {
    "name": "GENQ"
  }
}
```

### Response
Returns list of error jobs with queue IDs:
```json
{
  "invocationSummary": {
    "version": "12.6.204.467.6",
    "invocationId": "...",
    "executionTime": 360,
    "timestamp": "2026-01-27T08:51:04.745+02:00",
    "username": "demo"
  },
  "searchResults": [
    {
      "queueId": 185451684,
      "status": "ERR",
      "executionDate": "2026-01-07T06:00:58.604+02:00"
    },
    ...
  ]
}
```

### When Called
- Always called first
- Once per script execution
- Provides the list of queue IDs to investigate

---

## API Call 2: Get System Log

### Endpoint
```
POST {baseUrl}/sbs/systemService/getSystemLog
```

### Purpose
Get detailed error logs for a specific queue ID, including full stack traces.

### Request Payload
```json
{
  "callerDetails": {
    "username": "{{username}}",
    "country": "{{country}}",
    "language": "{{language}}",
    "databaseIdentifier": "{{databaseIdentifier}}"
  },
  "queueId": 186000213,
  "messageCode": {
    "id": 171,
    "code": "ERR",
    "codeType": "SLOG",
    "codeShortDescription": "Error",
    "codeDescription": "Error message"
  },
  "excludeLongText": false,
  "includeProcessName": true
}
```

### Request Parameters Explained

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `queueId` | Integer | The specific queue ID to get logs for |
| `messageCode.id` | 171 | Filter for error messages only |
| `messageCode.code` | "ERR" | Error message code |
| `messageCode.codeType` | "SLOG" | System log type |
| `excludeLongText` | false | **Include full stack traces** |
| `includeProcessName` | true | Include process name in results |

### Response
Returns detailed log entries:
```json
{
  "invocationSummary": {
    "version": "12.6.204.467.6",
    "invocationId": "...",
    "executionTime": 28,
    "timestamp": "2026-01-28T13:38:40.306+02:00",
    "username": "demo"
  },
  "searchResults": [
    {
      "logId": 157183187,
      "queueId": 186000213,
      "messageCode": {
        "id": 171,
        "code": "ERR",
        "codeType": "SLOG",
        "codeShortDescription": "Error",
        "codeDescription": "Error message"
      },
      "message": "BRA-002 - An application error occurred...",
      "createdDate": "2026-01-08T15:31:24.421+02:00",
      "createdBy": "engine",
      "longText": "1. TechnicalException: BRA-001...\n2. CallException...\n3. NoSuchElementException...\nFull stack trace...",
      "processName": "Apply Prices"
    },
    ...
  ]
}
```

### When Called
- Only when `--fetch-details` flag is used
- Called once per unique queue ID
- Can be limited with `--detail-limit N`

---

## API Call Flow

### Without --fetch-details (Default)
```
1. searchJobHistory → Get queue IDs and counts
2. Display summary report
3. Done (1 API call total)
```

### With --fetch-details
```
1. searchJobHistory → Get queue IDs and counts
2. Display summary report
3. For each queue ID (sorted by error count):
   a. getSystemLog → Get detailed error logs
   b. Display detailed information
4. Done (1 + N API calls, where N = number of queue IDs)
```

### With --fetch-details --detail-limit 5
```
1. searchJobHistory → Get queue IDs and counts
2. Display summary report
3. For top 5 queue IDs (by error count):
   a. getSystemLog → Get detailed error logs
   b. Display detailed information
4. Done (1 + 5 = 6 API calls)
```

---

## Authentication

Both API calls require:
- No explicit authentication headers
- Caller details in request body (username, country, language, databaseIdentifier)
- Optional SSL verification (can be disabled with `--no-verify-ssl`)

---

## Error Filtering

### searchJobHistory Filters
- **status**: "ERR" - Only error jobs
- **queue.name**: "GENQ" - Only GENQ queue
- **date range**: Today (or specified date) from 00:00:00 to 23:59:59

### getSystemLog Filters
- **queueId**: Specific queue ID
- **messageCode.code**: "ERR" - Only error messages
- **messageCode.id**: 171 - Error message type
- **excludeLongText**: false - **Include full stack traces**
- **includeProcessName**: true - Include process information

---

## Performance Considerations

### API Call Counts

| Scenario | Unique Queue IDs | API Calls | Example |
|----------|------------------|-----------|---------|
| Summary only | 100 | 1 | Default mode |
| With limit | 100 | 6 | `--detail-limit 5` |
| All details | 10 | 11 | `--fetch-details` (10 queues) |
| All details | 100 | 101 | `--fetch-details` (100 queues) |

### Timeout Settings
- Default timeout: 30 seconds per API call
- Configurable in code if needed

---

## Testing

### Test with Example Data
```bash
# Uses local JSON files, no API calls
python test_with_example.py
python test_with_details.py
```

### Test Configuration
```bash
# Validates config without making API calls
python get_error_jobs.py --dry-run
```

### Debug API Calls
```bash
# Shows full request/response details
python get_error_jobs.py --verbose --fetch-details --detail-limit 1
```

Output includes:
```
[DEBUG] Search Job History
[DEBUG] Calling API: https://server.com/sbs/systemService/searchJobHistory
[DEBUG] SSL Verification: DISABLED
[DEBUG] Request payload:
{
  "callerDetails": { ... },
  "startDate": "2026-01-28T00:00:00.000Z",
  ...
}
[DEBUG] Response status: 200
```

---

## Common Issues

### Issue 1: Empty Results
**Problem**: searchJobHistory returns no results

**Possible Causes**:
- No errors occurred on that date
- Wrong queue name (must be "GENQ")
- Date format incorrect

**Solution**:
- Check different date with `--date YYYY-MM-DD`
- Verify errors exist in the system

### Issue 2: Missing Stack Traces
**Problem**: getSystemLog returns logs without stack traces

**Possible Causes**:
- `excludeLongText` was set to true (old code)
- API version doesn't support longText

**Solution**:
- Current code has `excludeLongText: false` ✅
- Verify API response includes `longText` field

### Issue 3: Too Many API Calls
**Problem**: Script is slow or times out

**Solution**:
- Use `--detail-limit N` to reduce calls
- Start with `--detail-limit 5` for testing

---

## Configuration Variables

Set in `.env` file:

```bash
# Required for both API calls
SBS_BASE_URL=https://your-sbs-server.com/sonata/rest
SBS_USERNAME=your-username
SBS_COUNTRY=za
SBS_LANGUAGE=en
SBS_DATABASE_ID=SonataDatasource

# Optional
SBS_NO_VERIFY_SSL=true  # For self-signed certificates
```

---

## Example: Full Verbose Output

```bash
python get_error_jobs.py --verbose --fetch-details --detail-limit 1
```

Shows:
1. Configuration loaded
2. API call to searchJobHistory with full payload
3. Response status and results
4. Summary report
5. API call to getSystemLog for first queue ID
6. Detailed error log display with full stack traces

Perfect for debugging and understanding the data flow!
