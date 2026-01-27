# SBS Error Job History Reporter

Python script to query SBS system service for error jobs and generate reports grouped by queue ID.

## Prerequisites

- Python 3.6 or higher
- Linux environment (or any OS with Python installed)

## Installation

1. Install required Python packages:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests
```

## Configuration

There are three ways to provide configuration:

### Option 1: .env File (Recommended)

The script automatically loads configuration from a `.env` file in the same directory:

```bash
cp config.env.template .env
# Edit .env with your values
```

Example `.env` file:

```bash
SBS_BASE_URL=https://your-sbs-server.com
SBS_USERNAME=your-username
SBS_COUNTRY=US
SBS_LANGUAGE=en
SBS_DATABASE_ID=your-database-id
```

Then just run:

```bash
python get_error_jobs.py
```

### Option 1b: Manual Environment Variables

You can also set environment variables manually:

```bash
export SBS_BASE_URL="https://your-sbs-server.com"
export SBS_USERNAME="your-username"
export SBS_COUNTRY="US"
export SBS_LANGUAGE="en"
export SBS_DATABASE_ID="your-database-id"
```

### Option 2: Command Line Arguments

```bash
python get_error_jobs.py \
  --base-url https://your-sbs-server.com \
  --username your-username \
  --country US \
  --language en \
  --db-id your-database-id
```

### Option 3: Mix Both

Use `.env` file for defaults, command-line arguments for overrides:

```bash
# .env file will be automatically loaded
python get_error_jobs.py --date 2026-01-15
```

## Usage

### Basic Usage

Query today's error jobs:

```bash
python get_error_jobs.py
```

### Query Specific Date

```bash
python get_error_jobs.py --date 2026-01-15
```

### Enable Verbose Output (for debugging)

```bash
python get_error_jobs.py --verbose
```

### Disable SSL Verification (for self-signed certificates)

```bash
python get_error_jobs.py --no-verify-ssl
```

Or add to `.env` file:
```bash
SBS_NO_VERIFY_SSL=true
```

⚠️ **Warning:** Only use this for trusted internal servers with self-signed certificates!

### Test Configuration (Dry Run)

Test your configuration without making an API call:

```bash
python get_error_jobs.py --dry-run
```

### Complete Example

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

## Output Example

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
185451684            |      1,523
185451685            |         42
185451690            |         15
------------------------------------------------------------
Total Unique Queue IDs: |          3
Total Error Jobs:    |      1,580
============================================================
```

## Command Line Options

```
usage: get_error_jobs.py [-h] [--base-url BASE_URL] [--username USERNAME]
                        [--country COUNTRY] [--language LANGUAGE]
                        [--db-id DB_ID] [--date DATE] [--verbose] [--dry-run]

optional arguments:
  -h, --help           show this help message and exit
  --base-url           SBS base URL (or set SBS_BASE_URL env var)
  --username           Username (or set SBS_USERNAME env var)
  --country            Country code (or set SBS_COUNTRY env var)
  --language           Language code (or set SBS_LANGUAGE env var)
  --db-id              Database identifier (or set SBS_DATABASE_ID env var)
  --date               Date to query (YYYY-MM-DD format, defaults to today)
  --verbose, -v        Enable verbose output for debugging
  --dry-run            Test configuration without making API call
  --no-verify-ssl      Disable SSL certificate verification (for self-signed certs)
```

## Error Handling

The script handles the following error conditions:

- **Missing configuration**: Clear error messages indicate which parameters are missing
- **Network errors**: Connection failures and timeouts are reported
- **HTTP errors**: API errors (4xx, 5xx) are displayed with details
- **Invalid responses**: JSON parsing errors are caught and reported
- **Empty results**: Gracefully handles cases with no error jobs

## Exit Codes

- `0`: Success
- `1`: Configuration error (missing required parameters)
- `2`: Network/API error (connection failed, timeout, HTTP error)
- `3`: Data processing error (invalid JSON response)

## Troubleshooting

### Connection Test

First, verify your configuration:

```bash
python get_error_jobs.py --dry-run
```

### Enable Verbose Mode

Get detailed debug information:

```bash
python get_error_jobs.py --verbose
```

This will show:
- Configuration values
- API endpoint being called
- Request payload
- Response status code

### Common Issues

1. **"ERROR: base-url not provided"**
   - Set `SBS_BASE_URL` environment variable or use `--base-url` argument

2. **"Connection failed"**
   - Check if the SBS server URL is correct
   - Verify network connectivity to the server
   - Check firewall rules

3. **"Request timeout"**
   - Server may be slow or unreachable
   - Try again or check with system administrator

4. **"Invalid JSON response"**
   - API may have returned an error in HTML format
   - Check with `--verbose` to see the actual response

5. **"SSL: CERTIFICATE_VERIFY_FAILED"**
   - Server is using a self-signed certificate
   - Solution: Use `--no-verify-ssl` flag
   ```bash
   python get_error_jobs.py --no-verify-ssl
   ```

## Development

### Testing with Example Data

You can test the data processing without making API calls by modifying the script to load from `example-response-searchJobHistory.json`:

```python
# In main(), replace the API call with:
with open('example-response-searchJobHistory.json', 'r') as f:
    response = json.load(f)
```

## Security Notes

- Never commit `config.env` file with real credentials
- Add `config.env` to `.gitignore`
- Use environment variables in production environments
- Ensure the SBS API URL uses HTTPS

## License

Internal use only.
