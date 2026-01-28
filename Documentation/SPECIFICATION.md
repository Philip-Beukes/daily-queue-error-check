# SBS Error Job History Reporter - Technical Specification

## Overview
Python script to query SBS system service for error jobs in a specified queue and generate a report of job counts grouped by unique queue IDs.

## System Requirements
- **Platform**: Linux
- **Python Version**: 3.6+ (assumed pre-installed)
- **Dependencies**: 
  - `requests` library (for HTTP REST API calls)
  - Standard library modules: `datetime`, `json`, `collections`

## Functional Requirements

### 1. API Call Configuration

**Endpoint**: `{{baseUrl}}/sbs/systemService/searchJobHistory`

**HTTP Method**: POST

**Authentication**: None required

**Request Headers**:
```
Content-Type: application/json
```

**Request Body Structure**:
```json
{
  "callerDetails": {
    "username": "{{username}}",
    "country": "{{country}}",
    "language": "{{language}}",
    "databaseIdentifier": "{{databaseIdentifier}}"
  },
  "startDate": "{YYYY-MM-DD}T00:00:00.000Z",
  "endDate": "{YYYY-MM-DD}T23:59:59.000Z",
  "status": "ERR",
  "queue": {
    "name": "GENQ"
  }
}
```

**Dynamic Parameters**:
- `{{baseUrl}}`: Base URL of the SBS system
- `{{username}}`: Caller username
- `{{country}}`: Country code
- `{{language}}`: Language code
- `{{databaseIdentifier}}`: Database identifier
- `startDate` / `endDate`: Automatically set to current date (today's date in UTC)

### 2. Response Structure

**Expected Response Format**:
```json
{
  "invocationSummary": {
    "version": "string",
    "invocationId": "string",
    "executionTime": number,
    "timestamp": "string",
    "username": "string"
  },
  "searchResults": [
    {
      "queueId": number,
      "status": "string",
      "executionDate": "string"
    }
  ]
}
```

### 3. Data Processing

**Objective**: Extract and analyze queue IDs from the response

**Processing Steps**:
1. Parse JSON response
2. Extract `searchResults` array
3. Iterate through all results and collect `queueId` values
4. Count occurrences of each unique `queueId`
5. Generate summary report

### 4. Output Requirements

**Phase 1 Output** (Current Requirement):
- Display count of entries per unique `queueId`
- Format: Console/stdout output
- Example output format:
```
SBS Error Job History Report
Generated: 2026-01-27 12:00:00
Query Date Range: 2026-01-27

Queue ID Statistics:
==================
Queue ID: 185451684 | Count: 1523
Queue ID: 185451685 | Count: 42
Queue ID: 185451690 | Count: 15

Total Unique Queue IDs: 3
Total Error Jobs: 1580
```

## Configuration Management

### Configuration Method Options:

**Option A: Environment Variables**
```bash
export SBS_BASE_URL="https://example.com"
export SBS_USERNAME="demo"
export SBS_COUNTRY="US"
export SBS_LANGUAGE="en"
export SBS_DATABASE_ID="PROD01"
```

**Option B: Configuration File** (config.ini)
```ini
[sbs]
base_url = https://example.com
username = demo
country = US
language = en
database_identifier = PROD01
```

**Option C: Command Line Arguments**
```bash
python get_error_jobs.py --base-url https://example.com --username demo --country US --language en --db-id PROD01
```

**Recommended**: Combination of configuration file (for defaults) and command-line arguments (for overrides)

## Error Handling

### Required Error Handling:
1. **Network Errors**: Handle connection failures, timeouts
2. **HTTP Errors**: Handle 4xx and 5xx status codes
3. **JSON Parsing Errors**: Handle malformed responses
4. **Missing Configuration**: Validate all required parameters are provided
5. **Empty Results**: Handle case where no error jobs are found

### Exit Codes:
- `0`: Success
- `1`: Configuration error
- `2`: Network/API error
- `3`: Data processing error

## Script Structure

### Recommended Module Organization:

```
get_error_jobs.py
├── Configuration Management
│   └── Load config from file/env/args
├── API Client
│   └── Make REST API call
├── Data Processor
│   └── Parse response and count queue IDs
├── Report Generator
│   └── Format and output results
└── Main Entry Point
    └── Orchestrate the workflow
```

## Non-Functional Requirements

### Performance:
- Handle response files up to 100MB
- Process up to 10,000+ job records efficiently

### Logging:
- Optional verbose mode for debugging
- Log API request/response details when verbose flag is enabled
- Log errors to stderr

### Usability:
- Clear error messages
- Help text for command-line usage
- Dry-run mode option (for testing configuration without API call)

## Future Enhancements (Not in Phase 1)

1. Export results to CSV/JSON file
2. Email notification support
3. Filter by date range (custom dates)
4. Query multiple queues simultaneously
5. Detailed job information retrieval
6. Historical trend analysis

## Testing Considerations

### Test Cases:
1. Successful API call with results
2. API call with no results (empty searchResults array)
3. Network timeout
4. Invalid configuration
5. Malformed JSON response
6. Large result set (10,000+ records)

### Test Data:
- Use provided `example-response-searchJobHistory.json` for unit testing data processing logic

## Deliverables

1. Python script: `get_error_jobs.py`
2. Configuration file template: `config.ini.template`
3. Requirements file: `requirements.txt`
4. README with usage instructions: `README.md`

## Usage Example

```bash
# Install dependencies
pip install -r requirements.txt

# Run with configuration file
python get_error_jobs.py --config config.ini

# Run with environment variables
export SBS_BASE_URL="https://api.example.com"
export SBS_USERNAME="demo"
python get_error_jobs.py

# Run with command-line arguments
python get_error_jobs.py \
  --base-url https://api.example.com \
  --username demo \
  --country US \
  --language en \
  --db-id PROD01
```

## Security Considerations

1. Do not hard-code credentials in the script
2. Configuration files should be added to `.gitignore`
3. Use environment variables for sensitive information in production
4. Consider using HTTPS for API calls (if not enforced at baseUrl)

## Maintenance

- Script should be version controlled
- Configuration should be documented for each environment (dev, test, prod)
- Regular testing recommended to ensure API compatibility
