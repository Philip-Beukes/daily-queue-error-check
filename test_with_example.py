#!/usr/bin/env python3
"""
Test script using the example JSON response file
This allows testing without making actual API calls
"""

import json
import sys
from collections import Counter
from datetime import datetime

# Import from main script
from get_error_jobs import JobHistoryAnalyzer, ReportGenerator


def main():
    """Test with example data"""
    print("Loading example response data...")
    
    try:
        with open('example-response-searchJobHistory.json', 'r') as f:
            response = json.load(f)
    except FileNotFoundError:
        print("ERROR: example-response-searchJobHistory.json not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in example file: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("Analyzing data...\n")
    
    # Analyze results
    analyzer = JobHistoryAnalyzer()
    queue_counts = analyzer.count_queue_ids(response)
    
    # Generate report
    report_gen = ReportGenerator()
    report_gen.print_queue_id_report(
        queue_counts=queue_counts,
        date="2026-01-27 (from example file)",
        invocation_summary=response.get('invocationSummary')
    )
    
    print("\n[SUCCESS] Test completed successfully!")
    print(f"\nYour script can process responses with {len(response.get('searchResults', []))} job records.")


if __name__ == '__main__':
    main()
