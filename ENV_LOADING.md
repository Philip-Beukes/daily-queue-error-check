# .env File Auto-Loading

The script now automatically loads configuration from a `.env` file!

## How It Works

1. When you run `get_error_jobs.py`, it automatically looks for a `.env` file in the current directory
2. If found, all variables are loaded into the environment
3. No need to manually `source` or `export` variables!

## Setup

```bash
# 1. Copy the template
cp config.env.template .env

# 2. Edit .env with your values
nano .env

# 3. Run the script - it automatically loads .env!
python get_error_jobs.py
```

## .env File Format

**Simple key=value format** (no `export` needed):

```bash
SBS_BASE_URL=https://your-sbs-server.com
SBS_USERNAME=your-username
SBS_COUNTRY=US
SBS_LANGUAGE=en
SBS_DATABASE_ID=your-database-id
```

## Priority Order

Configuration values are loaded in this order (last one wins):

1. `.env` file (lowest priority)
2. Environment variables set in shell
3. Command-line arguments (highest priority)

## Examples

### Using just .env file

```bash
# .env is automatically loaded
python get_error_jobs.py
```

### Override .env with command-line

```bash
# Use values from .env, but override the date
python get_error_jobs.py --date 2026-01-15
```

### Check if .env was loaded

```bash
# Verbose mode shows .env file detection
python get_error_jobs.py --verbose --dry-run
```

Output:
```
[DEBUG] Loaded configuration from .env file
[DEBUG] Configuration loaded:
  Base URL: https://...
```

## Security

⚠️ **Important:** The `.env` file is already in `.gitignore` - never commit it!

## Troubleshooting

### .env not being loaded?

Make sure:
- File is named exactly `.env` (not `.env.txt`)
- File is in the same directory where you run the script
- Run with `--verbose` to confirm loading

### Want to use different .env file?

Currently not supported, but you can:
1. Copy your alternate config to `.env`
2. Or use environment variables instead
3. Or use command-line arguments
