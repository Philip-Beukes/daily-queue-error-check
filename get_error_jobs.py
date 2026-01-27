#!/usr/bin/env python3
"""
SBS Error Job History Reporter
Queries SBS system for error jobs and reports counts by queue ID
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone
from collections import Counter
from typing import Dict, List, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Please install: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: 'python-dotenv' library not found. Please install: pip install python-dotenv")
    sys.exit(1)


class SBSJobHistoryClient:
    """Client for querying SBS job history API"""
    
    def __init__(self, base_url: str, username: str, country: str, 
                 language: str, database_identifier: str, verbose: bool = False,
                 verify_ssl: bool = True):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.country = country
        self.language = language
        self.database_identifier = database_identifier
        self.verbose = verbose
        self.verify_ssl = verify_ssl
        
        # Suppress SSL warnings if verification is disabled
        if not self.verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def search_job_history(self, date: Optional[str] = None) -> Dict:
        """
        Search for error jobs in GENQ queue for specified date
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            API response as dictionary
        """
        # Use today's date if not specified
        if date is None:
            date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        # Build request payload
        payload = {
            "callerDetails": {
                "username": self.username,
                "country": self.country,
                "language": self.language,
                "databaseIdentifier": self.database_identifier
            },
            "startDate": f"{date}T00:00:00.000Z",
            "endDate": f"{date}T23:59:59.000Z",
            "status": "ERR",
            "queue": {
                "name": "GENQ"
            }
        }
        
        # API endpoint
        url = f"{self.base_url}/sbs/systemService/searchJobHistory"
        
        if self.verbose:
            print(f"[DEBUG] Calling API: {url}", file=sys.stderr)
            print(f"[DEBUG] SSL Verification: {'Enabled' if self.verify_ssl else 'DISABLED'}", file=sys.stderr)
            print(f"[DEBUG] Request payload:", file=sys.stderr)
            print(json.dumps(payload, indent=2), file=sys.stderr)
        
        try:
            # Make API call
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
                verify=self.verify_ssl
            )
            
            if self.verbose:
                print(f"[DEBUG] Response status: {response.status_code}", file=sys.stderr)
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            return response.json()
            
        except requests.exceptions.Timeout:
            print("ERROR: Request timeout. The API did not respond in time.", file=sys.stderr)
            sys.exit(2)
        except requests.exceptions.ConnectionError as e:
            print(f"ERROR: Connection failed. Could not reach {url}", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
            sys.exit(2)
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: HTTP error occurred: {e}", file=sys.stderr)
            if response.text:
                print(f"Response: {response.text}", file=sys.stderr)
            sys.exit(2)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON response from API", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
            sys.exit(3)


class JobHistoryAnalyzer:
    """Analyzes job history data"""
    
    @staticmethod
    def count_queue_ids(response_data: Dict) -> Counter:
        """
        Count occurrences of each unique queue ID
        
        Args:
            response_data: API response dictionary
            
        Returns:
            Counter object with queue ID counts
        """
        queue_ids = []
        
        # Extract search results
        search_results = response_data.get('searchResults', [])
        
        # Collect all queue IDs
        for result in search_results:
            queue_id = result.get('queueId')
            if queue_id is not None:
                queue_ids.append(queue_id)
        
        return Counter(queue_ids)


class ReportGenerator:
    """Generates formatted reports"""
    
    @staticmethod
    def print_queue_id_report(queue_counts: Counter, date: str, 
                              invocation_summary: Optional[Dict] = None):
        """
        Print formatted report of queue ID counts
        
        Args:
            queue_counts: Counter with queue ID counts
            date: Date of the query
            invocation_summary: Optional API invocation summary
        """
        print("=" * 60)
        print("SBS Error Job History Report")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Query Date: {date}")
        print(f"Queue: GENQ")
        print(f"Status: ERR (Error)")
        
        if invocation_summary:
            print(f"\nAPI Response:")
            print(f"  Version: {invocation_summary.get('version', 'N/A')}")
            print(f"  Execution Time: {invocation_summary.get('executionTime', 'N/A')}ms")
        
        print("\n" + "=" * 60)
        print("Queue ID Statistics")
        print("=" * 60)
        
        if not queue_counts:
            print("\nNo error jobs found for the specified date.")
            return
        
        # Sort by count (descending) then by queue ID
        sorted_counts = sorted(queue_counts.items(), 
                              key=lambda x: (-x[1], x[0]))
        
        print(f"\n{'Queue ID':<20} | {'Count':>10}")
        print("-" * 60)
        
        for queue_id, count in sorted_counts:
            print(f"{queue_id:<20} | {count:>10,}")
        
        print("-" * 60)
        print(f"{'Total Unique Queue IDs:':<20} | {len(queue_counts):>10,}")
        print(f"{'Total Error Jobs:':<20} | {sum(queue_counts.values()):>10,}")
        print("=" * 60)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Query SBS for error job history and generate reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using command-line arguments
  %(prog)s --base-url https://api.example.com --username demo --country US --language en --db-id PROD01
  
  # Using environment variables
  export SBS_BASE_URL=https://api.example.com
  export SBS_USERNAME=demo
  %(prog)s
  
  # With verbose output
  %(prog)s --base-url https://api.example.com --username demo --verbose
        """
    )
    
    parser.add_argument('--base-url', 
                       help='SBS base URL (or set SBS_BASE_URL env var)')
    parser.add_argument('--username',
                       help='Username (or set SBS_USERNAME env var)')
    parser.add_argument('--country',
                       help='Country code (or set SBS_COUNTRY env var)')
    parser.add_argument('--language',
                       help='Language code (or set SBS_LANGUAGE env var)')
    parser.add_argument('--db-id',
                       help='Database identifier (or set SBS_DATABASE_ID env var)')
    parser.add_argument('--date',
                       help='Date to query (YYYY-MM-DD format, defaults to today)')
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Enable verbose output for debugging')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Test configuration without making API call')
    parser.add_argument('--no-verify-ssl',
                       action='store_true',
                       help='Disable SSL certificate verification (use for self-signed certs)')
    
    return parser.parse_args()


def get_config_value(arg_value: Optional[str], env_var: str, 
                     name: str, required: bool = True) -> Optional[str]:
    """
    Get configuration value from arguments or environment
    
    Args:
        arg_value: Value from command line argument
        env_var: Environment variable name
        name: Human-readable name for error messages
        required: Whether the value is required
        
    Returns:
        Configuration value or None
    """
    import os
    
    value = arg_value or os.environ.get(env_var)
    
    if required and not value:
        print(f"ERROR: {name} not provided.", file=sys.stderr)
        print(f"  Use --{name.lower().replace(' ', '-')} argument or set {env_var} environment variable", 
              file=sys.stderr)
        sys.exit(1)
    
    return value


def main():
    """Main entry point"""
    # Load environment variables from .env file if it exists
    env_file = Path('.env')
    env_loaded = False
    if env_file.exists():
        load_dotenv(env_file)
        env_loaded = True
    
    args = parse_arguments()
    
    # Get configuration from arguments or environment
    base_url = get_config_value(args.base_url, 'SBS_BASE_URL', 'base-url')
    username = get_config_value(args.username, 'SBS_USERNAME', 'username')
    country = get_config_value(args.country, 'SBS_COUNTRY', 'country')
    language = get_config_value(args.language, 'SBS_LANGUAGE', 'language')
    db_id = get_config_value(args.db_id, 'SBS_DATABASE_ID', 'db-id')
    
    # SSL verification - check env var or command line arg
    verify_ssl = not args.no_verify_ssl
    if not verify_ssl and not args.verbose:
        # Show warning if SSL verification is disabled (unless already in verbose mode)
        print("WARNING: SSL certificate verification is DISABLED", file=sys.stderr)
    
    # Check environment variable for SSL verification
    if os.environ.get('SBS_NO_VERIFY_SSL', '').lower() in ('true', '1', 'yes'):
        verify_ssl = False
        if not args.verbose:
            print("WARNING: SSL certificate verification is DISABLED (from env var)", file=sys.stderr)
    
    if args.verbose:
        if env_loaded:
            print(f"[DEBUG] Loaded configuration from .env file", file=sys.stderr)
        if not verify_ssl:
            print("WARNING: SSL certificate verification is DISABLED", file=sys.stderr)
        print("[DEBUG] Configuration loaded:", file=sys.stderr)
        print(f"  Base URL: {base_url}", file=sys.stderr)
        print(f"  Username: {username}", file=sys.stderr)
        print(f"  Country: {country}", file=sys.stderr)
        print(f"  Language: {language}", file=sys.stderr)
        print(f"  Database ID: {db_id}", file=sys.stderr)
        print(f"  SSL Verification: {'Enabled' if verify_ssl else 'DISABLED'}", file=sys.stderr)
    
    # Dry run mode - just validate configuration
    if args.dry_run:
        print("Configuration validated successfully!")
        print(f"  Base URL: {base_url}")
        print(f"  Username: {username}")
        print(f"  Country: {country}")
        print(f"  Language: {language}")
        print(f"  Database ID: {db_id}")
        return
    
    # Create client
    client = SBSJobHistoryClient(
        base_url=base_url,
        username=username,
        country=country,
        language=language,
        database_identifier=db_id,
        verbose=args.verbose,
        verify_ssl=verify_ssl
    )
    
    # Query date
    query_date = args.date or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    print(f"Querying SBS for error jobs on {query_date}...\n")
    
    # Make API call
    response = client.search_job_history(date=query_date)
    
    # Analyze results
    analyzer = JobHistoryAnalyzer()
    queue_counts = analyzer.count_queue_ids(response)
    
    # Generate report
    report_gen = ReportGenerator()
    report_gen.print_queue_id_report(
        queue_counts=queue_counts,
        date=query_date,
        invocation_summary=response.get('invocationSummary')
    )


if __name__ == '__main__':
    main()
