# SSL Certificate Verification

## Overview

The script supports disabling SSL/TLS certificate verification for servers with self-signed certificates or when connecting to internal development/test environments.

## ⚠️ Security Warning

**Disabling SSL verification reduces security!** Only use this option when:
- Connecting to trusted internal servers
- Server uses self-signed certificates
- You're in a development/test environment
- You understand the security implications

**Never disable SSL verification in production with untrusted servers!**

## How to Disable SSL Verification

### Method 1: Command Line Argument (Recommended)

```bash
python get_error_jobs.py --no-verify-ssl
```

### Method 2: Environment Variable

Add to your `.env` file:

```bash
SBS_NO_VERIFY_SSL=true
```

Or set as environment variable:

```bash
export SBS_NO_VERIFY_SSL=true
python get_error_jobs.py
```

### Method 3: Temporary Override

```bash
# Use .env settings but force no SSL verification
python get_error_jobs.py --no-verify-ssl
```

## What Happens When Disabled

1. **SSL Certificate Validation is Skipped**
   - Self-signed certificates are accepted
   - Expired certificates are ignored
   - Hostname mismatches are ignored

2. **Warning Messages Displayed**
   ```
   WARNING: SSL certificate verification is DISABLED
   ```

3. **SSL Warnings Suppressed**
   - Python's urllib3 InsecureRequestWarning is silenced
   - Prevents console spam from warning messages

## Testing SSL Settings

### Check Current SSL Setting

```bash
python get_error_jobs.py --dry-run --verbose
```

Output shows:
```
[DEBUG] Configuration loaded:
  ...
  SSL Verification: DISABLED  # or Enabled
```

### During API Call

```bash
python get_error_jobs.py --verbose --no-verify-ssl
```

Output shows:
```
[DEBUG] Calling API: https://...
[DEBUG] SSL Verification: DISABLED
[DEBUG] Request payload:
...
```

## Common Use Cases

### Self-Signed Certificate Error

**Error:**
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Solution:**
```bash
python get_error_jobs.py --no-verify-ssl
```

### Development/Test Environment

Add to `.env`:
```bash
# Development environment - self-signed cert
SBS_BASE_URL=https://sbs-dev.internal
SBS_NO_VERIFY_SSL=true
```

### Production with Valid Certificate

Don't set `SBS_NO_VERIFY_SSL` - verification is enabled by default.

## Examples

### Basic Usage with SSL Disabled

```bash
# Command line
python get_error_jobs.py --no-verify-ssl

# Or in .env
echo "SBS_NO_VERIFY_SSL=true" >> .env
python get_error_jobs.py
```

### Verbose Mode to Confirm Setting

```bash
python get_error_jobs.py --no-verify-ssl --verbose --dry-run
```

Output:
```
WARNING: SSL certificate verification is DISABLED
[DEBUG] Configuration loaded:
  Base URL: https://sbs-server.com
  SSL Verification: DISABLED
```

### Override .env Setting

If `.env` has `SBS_NO_VERIFY_SSL=true` but you want to enable SSL:

**Note:** Currently, command-line always disables when `--no-verify-ssl` is used. To enable SSL when env var is set, simply don't use the flag and remove/comment the env var.

## Troubleshooting

### Still Getting SSL Errors?

1. **Check Python Version**
   ```bash
   python --version  # Should be 3.6+
   ```

2. **Update requests library**
   ```bash
   pip install --upgrade requests urllib3
   ```

3. **Verify flag is set**
   ```bash
   python get_error_jobs.py --no-verify-ssl --verbose --dry-run
   ```

### Warning Not Appearing?

The warning is shown to stderr:
```bash
python get_error_jobs.py --no-verify-ssl 2>&1 | grep WARNING
```

## Best Practices

1. **Use Environment-Specific Config**
   - Dev: `.env.dev` with `SBS_NO_VERIFY_SSL=true`
   - Prod: `.env.prod` without SSL disabled

2. **Document Why It's Disabled**
   ```bash
   # .env
   # SSL disabled because dev server uses self-signed cert
   SBS_NO_VERIFY_SSL=true
   ```

3. **Enable for Production**
   - Never commit `.env` with `SBS_NO_VERIFY_SSL=true` for production
   - Use proper SSL certificates in production

4. **Test Both Modes**
   ```bash
   # Test without SSL verification
   python get_error_jobs.py --no-verify-ssl --dry-run
   
   # Test with SSL verification (production-like)
   python get_error_jobs.py --dry-run
   ```

## Technical Details

- Uses `requests` library's `verify=False` parameter
- Suppresses `urllib3.exceptions.InsecureRequestWarning`
- Setting is passed to all HTTP requests made by the client
- No certificate validation or hostname checking performed

## See Also

- [Python requests SSL Verification](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)
- [urllib3 SSL Documentation](https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings)
