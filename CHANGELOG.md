# Changelog

## [1.1.0] - 2026-01-27

### Added
- **SSL Certificate Verification Control**
  - Added `--no-verify-ssl` command-line flag
  - Added `SBS_NO_VERIFY_SSL` environment variable support
  - Automatic suppression of SSL warnings when verification is disabled
  - Warning messages when SSL verification is disabled
  - SSL verification status shown in verbose mode

### Changed
- Updated `get_error_jobs.py` to support SSL verification control
- Updated `config.env.template` with SSL verification option
- Enhanced verbose output to show SSL verification status
- Updated README.md with SSL troubleshooting section
- Updated USAGE_EXAMPLES.md with SSL examples
- Updated QUICKSTART.md with SSL error handling

### Documentation
- Added `SSL_VERIFICATION.md` - Comprehensive SSL verification guide
- Updated all documentation with SSL-related examples and warnings

### Security
- Added security warnings about SSL verification
- Clear documentation about when to disable SSL verification
- Warnings displayed to users when SSL verification is disabled

## [1.0.0] - 2026-01-27

### Added
- Initial release
- REST API client for SBS systemService/searchJobHistory
- Automatic .env file loading with python-dotenv
- Queue ID counting and analysis
- Formatted console output reports
- Command-line argument support
- Environment variable configuration
- Verbose and dry-run modes
- Error handling for network and API issues
- Test script for example data processing

### Documentation
- SPECIFICATION.md - Technical specification
- README.md - Comprehensive usage guide
- QUICKSTART.md - Quick start guide
- USAGE_EXAMPLES.md - Usage examples
- ENV_LOADING.md - .env file documentation
