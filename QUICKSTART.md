# Quick Start Guide

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Test with Example Data (No API Call)

```bash
python test_with_example.py
```

This will process the example JSON file and show you what the output looks like.

## 3. Configure Your Settings

```bash
cp config.env.template .env
```

Edit `.env` file and add your values:
- `SBS_BASE_URL` - Your SBS server URL (e.g., https://sbs.example.com)
- `SBS_USERNAME` - Your username
- `SBS_COUNTRY` - Country code (e.g., US)
- `SBS_LANGUAGE` - Language code (e.g., en)
- `SBS_DATABASE_ID` - Your database identifier

**Note:** The script automatically loads the `.env` file - no need to `source` it!

## 4. Test Configuration

```bash
python get_error_jobs.py --dry-run
```

If configuration is valid, you'll see:
```
Configuration validated successfully!
  Base URL: https://...
  Username: ...
```

## 5. Make Your First Real API Call

```bash
python get_error_jobs.py
```

## 6. Troubleshooting

If something goes wrong, enable verbose mode:

```bash
python get_error_jobs.py --verbose
```

### SSL Certificate Errors?

If you get SSL certificate verification errors (common with self-signed certs):

```bash
python get_error_jobs.py --no-verify-ssl
```

Or add to `.env`:
```bash
SBS_NO_VERIFY_SSL=true
```

## Command Examples

```bash
# Today's errors (using .env file - auto-loaded)
python get_error_jobs.py

# Specific date
python get_error_jobs.py --date 2026-01-15

# Override config with command line
python get_error_jobs.py --base-url https://other-server.com

# Full command line (no config file)
python get_error_jobs.py \
  --base-url https://sbs.example.com \
  --username demo \
  --country US \
  --language en \
  --db-id PROD01
```

## What You'll Get

The script will output:
- Total number of unique queue IDs
- Count of error jobs per queue ID
- Total error jobs found
- API execution time

Perfect for:
- Daily monitoring of error jobs
- Identifying which queue IDs have the most errors
- Tracking error trends over time
