#!/usr/bin/env python3
"""
Test script using example JSON files to demonstrate detailed log fetching
This allows testing without making actual API calls
"""

import json
import sys
from collections import Counter
from datetime import datetime

# Import from main script
from get_error_jobs import JobHistoryAnalyzer, ReportGenerator


def main():
    """Test with example data including detailed logs"""
    print("Loading example job history data...")
    
    try:
        with open('example-response-searchJobHistory.json', 'r') as f:
            job_history = json.load(f)
    except FileNotFoundError:
        print("ERROR: example-response-searchJobHistory.json not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open('example-response-getSystemLog.json', 'r') as f:
            system_log = json.load(f)
    except FileNotFoundError:
        print("ERROR: example-response-getSystemLog.json not found", file=sys.stderr)
        sys.exit(1)
    
    print("Analyzing job history data...\n")
    
    # Analyze job history
    analyzer = JobHistoryAnalyzer()
    queue_counts = JobHistoryAnalyzer.count_queue_ids(job_history)
    
    # Generate main report
    report_gen = ReportGenerator()
    report_gen.print_queue_id_report(
        queue_counts=queue_counts,
        date="2026-01-27 (from example file)",
        invocation_summary=job_history.get('invocationSummary')
    )
    
    # Show detailed logs example
    print("\n\nDemonstrating detailed log fetching...")
    
    # Get a queue ID from the example system log
    log_summary = analyzer.extract_log_summary(system_log)
    
    if log_summary['queue_id']:
        report_gen.print_detailed_report_header(
            total_queue_ids=len(queue_counts),
            fetch_limit=1
        )
        
        report_gen.print_system_log_details(
            queue_id=log_summary['queue_id'],
            log_summary=log_summary
        )
        
        # Show process summary
        process_summary = analyzer.get_process_summary()
        report_gen.print_process_summary(process_summary)
    
    print("\n[SUCCESS] Test completed successfully!")
    print(f"\nYour script can process:")
    print(f"  - {len(job_history.get('searchResults', []))} job history records")
    print(f"  - {log_summary['log_count']} detailed log entries")
    print(f"  - Queue ID {log_summary['queue_id']} details shown above")
    print(f"  - Process summary generated")


if __name__ == '__main__':
    main()
