# Changelog

## [1.3.0] - 2026-01-28

### Added
- **File Output Support**
  - Added `--output-file FILE` / `-o FILE` option
  - Write complete reports to files for later analysis
  - Support for dated filenames for automated reporting
  - Console output for progress when using file output with verbose mode

- **Process-Level Error Analysis**
  - Automatic analysis of errors grouped by process name
  - Shows error count per process
  - Lists affected queue IDs per process
  - Sample error messages for each process
  - Summary statistics (total errors, unique processes, averages)
  - Sorted by error count to identify most problematic processes

- **Enhanced Stack Traces**
  - Removed 500 character limit on stack traces
  - Now displays complete stack traces with all details
  - Better debugging with full error context

### Changed
- `JobHistoryAnalyzer` now maintains state for process analysis
- Changed from static methods to instance methods for analyzer
- Enhanced `getSystemLog` API call with proper filtering:
  - Added `messageCode` filter for errors only
  - Added `excludeLongText: false` to ensure full stack traces
  - Added `includeProcessName: true` for process information
- Updated test scripts to show process analysis

### Documentation
- Added `FILE_OUTPUT_AND_ANALYSIS.md` - Complete guide to file output and process analysis
- Added `API_CALLS.md` - Detailed API documentation
- Updated README.md with file output and process analysis examples
- Updated CHANGELOG.md with version history

## [1.2.0] - 2026-01-28

### Added
- **Detailed System Log Fetching**
  - Added `--fetch-details` flag to fetch detailed logs for each queue ID
  - Added `--detail-limit N` to limit number of queue IDs to fetch details for
  - New API method `get_system_log()` to fetch detailed error logs
  - Detailed report showing log entries, stack traces, and process names
  - Automatic sorting by error count (most problematic queues first)
  - Progress tracking in verbose mode
  - Error handling for failed detail fetches

### Changed
- Refactored API calling logic into `_make_api_call()` method
- Enhanced `JobHistoryAnalyzer` with `extract_log_summary()` method
- Enhanced `ReportGenerator` with detailed log formatting methods
- Updated README.md with detailed fetching examples
- Updated help text with new options

### Documentation
- Added `DETAILED_LOGS.md` - Comprehensive detailed log fetching guide
- Added `test_with_details.py` - Test script demonstrating detailed fetching
- Updated CHANGELOG.md with version history

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
