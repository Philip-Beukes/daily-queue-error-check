#!/usr/bin/env python3
"""
SBS Error Job History Reporter
Queries SBS system for error jobs and reports counts by queue ID
"""

import argparse
import json
import sys
import os
import re
from datetime import datetime, timezone
from collections import Counter
from typing import Dict, List, Optional, Set
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
        
        return self._make_api_call(
            endpoint="/sbs/systemService/searchJobHistory",
            payload=payload,
            description="Search Job History"
        )
    
    def get_system_log(self, queue_id: int) -> Dict:
        """
        Get detailed system log for a specific queue ID
        
        Args:
            queue_id: Queue ID to fetch logs for
            
        Returns:
            API response as dictionary
        """
        # Build request payload
        payload = {
            "callerDetails": {
                "username": self.username,
                "country": self.country,
                "language": self.language,
                "databaseIdentifier": self.database_identifier
            },
            "queueId": queue_id,
            "messageCode": {
                "id": 171,
                "code": "ERR",
                "codeType": "SLOG",
                "codeShortDescription": "Error",
                "codeDescription": "Error message"
            },
            "excludeLongText": False,
            "includeProcessName": True
        }
        
        return self._make_api_call(
            endpoint="/sbs/systemService/getSystemLog",
            payload=payload,
            description=f"Get System Log for Queue ID {queue_id}"
        )
    
    def _make_api_call(self, endpoint: str, payload: Dict, description: str) -> Dict:
        """
        Make an API call to the SBS system
        
        Args:
            endpoint: API endpoint path
            payload: Request payload
            description: Human-readable description for logging
            
        Returns:
            API response as dictionary
        """
        # API endpoint
        url = f"{self.base_url}{endpoint}"
        
        if self.verbose:
            print(f"[DEBUG] {description}", file=sys.stderr)
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
            print(f"ERROR: Request timeout for {description}. The API did not respond in time.", file=sys.stderr)
            sys.exit(2)
        except requests.exceptions.ConnectionError as e:
            print(f"ERROR: Connection failed for {description}. Could not reach {url}", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
            sys.exit(2)
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: HTTP error occurred for {description}: {e}", file=sys.stderr)
            if response.text:
                print(f"Response: {response.text}", file=sys.stderr)
            sys.exit(2)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON response from API for {description}", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
            sys.exit(3)


class JobHistoryAnalyzer:
    """Analyzes job history data"""
    
    def __init__(self):
        """Initialize analyzer with storage for process analysis"""
        self.process_errors = {}  # {process_name: {queue_ids: [], error_count: N, errors: []}}
        self.process_transactions = {}  # {process_name: set(transaction_ids)}
        self.process_accounts = {}  # {process_name: set(account_ids)}
        self.process_error_causes = {}  # {process_name: Counter(error_cause)}
        self.process_transaction_errors = {}  # {process_name: {tx_id: {count: int, samples: [], causes: Counter}}}

    @staticmethod
    def _extract_apply_prices_transaction_ids(long_text: str) -> Set[str]:
        """
        Extract Apply Prices transaction IDs from stack trace text.

        Looks for applyPricesJob with arguments <transaction_id>, <queue_id>, ...
        """
        if not long_text:
            return set()

        pattern = r"applyPricesJob with arguments\s+(\d+)\s*\(java\.lang\.Long->java\.lang\.Long\)"
        return set(re.findall(pattern, long_text))

    @staticmethod
    def _extract_account_ids(message: str, long_text: str) -> Set[str]:
        """
        Extract account IDs from error message/stack trace text.

        Expected formats include:
        - "account RA104007"
        - "account TX102031"
        - "Account: TX102031"
        - "Account: IA105744"
        - "Account IA100153 :"
        - "for Account IA100153."
        """
        combined = " ".join([message or "", long_text or ""])
        patterns = [
            r"\b(?:Account:|account)\s*([A-Z]{2}\d{6,})",
            r"\bAccount\s+([A-Z]{2}\d{6,})\s*:",
            r"\bfor\s+Account\s+([A-Z]{2}\d{6,})",
        ]
        account_ids: Set[str] = set()
        for pattern in patterns:
            account_ids.update(re.findall(pattern, combined))
        return account_ids

    @staticmethod
    def _extract_disinvest_transaction_ids(long_text: str) -> Set[str]:
        """
        Extract Disinvest for Unpriced Transactions IDs from stack trace text.

        Looks for MFTransDisinvestUnpricedTransAcct.execute with arguments <transaction_id>, ...
        """
        if not long_text:
            return set()

        pattern = r"MFTransDisinvestUnpricedTransAcct\.execute with arguments\s+(\d+)\s*\(java\.lang\.Long->java\.lang\.Long\)"
        return set(re.findall(pattern, long_text))

    @staticmethod
    def _extract_regular_applications_transaction_ids(long_text: str) -> Set[str]:
        """
        Extract Regular Applications transaction IDs from stack trace text.

        Looks for MFTransRegularPayment.execute with arguments <transaction_id>, ...
        """
        if not long_text:
            return set()

        pattern = r"MFTransRegularPayment\.execute with arguments\s+(\d+)\s*\(java\.lang\.Long->java\.lang\.Long\)"
        return set(re.findall(pattern, long_text))

    @staticmethod
    def _extract_smp_rebalance_transaction_ids(long_text: str) -> Set[str]:
        """
        Extract SMP Rebalance Process transaction IDs from stack trace text.

        Looks for MFTransSMPRebalnAccount.execute with arguments <transaction_id>, ...
        """
        if not long_text:
            return set()

        pattern = r"MFTransSMPRebalnAccount\.execute with arguments\s+(\d+)\s*\(java\.lang\.Long->java\.lang\.Long\)"
        return set(re.findall(pattern, long_text))

    @staticmethod
    def _extract_cash_receipt_transaction_ids(long_text: str) -> Set[str]:
        """
        Extract Cash Receipt Creation for Expectations transaction IDs from stack trace text.

        Looks for CMUploadMatchedExpectation.processReceipt with arguments <transaction_id>, ...
        """
        if not long_text:
            return set()

        pattern = r"CMUploadMatchedExpectation\.processReceipt with arguments\s+(\d+)\s*\(java\.lang\.Long->java\.lang\.Long\)"
        return set(re.findall(pattern, long_text))

    @staticmethod
    def _extract_upload_settlement_transaction_ids(long_text: str) -> Set[str]:
        """
        Extract Upload Settlement Date transaction IDs from stack trace text.

        Looks for MFTransSettleOrderUpload.execute with arguments ... and returns the last Long->Long argument.
        """
        if not long_text:
            return set()

        pattern = r"MFTransSettleOrderUpload\.execute with arguments\s+([^\r\n]+)"
        match = re.search(pattern, long_text)
        if not match:
            return set()

        args_text = match.group(1)
        long_args = re.findall(r"(\d+)\s*\(java\.lang\.Long->java\.lang\.Long\)", args_text)
        if not long_args:
            return set()
        return {long_args[-1]}

    @staticmethod
    def _extract_finswitch_confirmation_transaction_ids(long_text: str) -> Set[str]:
        """
        Extract Upload FinSwitch Transaction Confirmation IDs from stack trace text.

        Looks for MFTransFinSwitchConfirmationUpload.execute with arguments <transaction_id>, ...
        """
        if not long_text:
            return set()

        pattern = r"MFTransFinSwitchConfirmationUpload\.execute with arguments\s+(\d+)\s*\(java\.lang\.Long->java\.lang\.Long\)"
        return set(re.findall(pattern, long_text))

    @staticmethod
    def _extract_error_causes(long_text: str) -> List[str]:
        """
        Extract root cause messages from stack trace text.

        Looks for lines starting with "ERROR:".
        """
        if not long_text:
            return []

        pattern = r"ERROR:\s*([^\r\n]+)"
        return [match.strip() for match in re.findall(pattern, long_text)]

    @staticmethod
    def _extract_regular_applications_causes(message: str, long_text: str, tx_id: Optional[str]) -> List[str]:
        """
        Extract Regular Applications causes from error message/stack trace.

        Includes:
        - BRA-49779 message line (if present)
        - BRA-115015 message line (if present)
        - NullPointerException for Transaction ID <tx_id> (if present)
        """
        causes = []
        if message and "BRA-49779" in message:
            causes.append(message.strip())
        if message and "BRA-115015" in message:
            causes.append(message.strip())
        if long_text and "NullPointerException" in long_text and tx_id:
            causes.append(f"NullPointerException for Transaction ID {tx_id}")
        return causes

    @staticmethod
    def _extract_apply_prices_causes(message: str, long_text: str, tx_id: Optional[str]) -> List[str]:
        """
        Extract Apply Prices causes from error message/stack trace.

        Includes:
        - BRA-002 message line (if present)
        - NullPointerException for Transaction ID <tx_id> (if present)
        """
        causes = []
        if message and "BRA-002" in message:
            causes.append(message.strip())
        if long_text and "NullPointerException" in long_text and tx_id:
            causes.append(f"NullPointerException for Transaction ID {tx_id}")
        return causes

    @staticmethod
    def _extract_cash_receipt_causes(message: str, long_text: str, tx_id: Optional[str]) -> List[str]:
        """
        Extract Cash Receipt Creation for Expectations causes from error message/stack trace.

        Includes:
        - BRA-200230 message line (if present)
        - NullPointerException for Transaction ID <tx_id> (if present)
        """
        causes = []
        if message and "BRA-200230" in message:
            causes.append(message.strip())
        if long_text and "NullPointerException" in long_text and tx_id:
            causes.append(f"NullPointerException for Transaction ID {tx_id}")
        return causes

    @staticmethod
    def _extract_upload_settlement_causes(message: str, long_text: str, tx_id: Optional[str]) -> List[str]:
        """
        Extract Upload Settlement Date causes from error message/stack trace.

        Includes:
        - NumberFormatException with message
        - Message line if it contains BRA-002
        """
        causes = []
        if message and "BRA-002" in message:
            causes.append(message.strip())
        if long_text:
            match = re.search(r"NumberFormatException:\s*([^\r\n]+)", long_text)
            detail_match = re.search(r"java\.lang\.NumberFormatException:\s*([^\r\n]+)", long_text)
            if match or detail_match:
                if detail_match:
                    causes.append(f"NumberFormatException - {detail_match.group(1).strip()}")
                else:
                    causes.append(f"NumberFormatException - {match.group(1).strip()}")
        if long_text and "NullPointerException" in long_text and tx_id:
            causes.append(f"NullPointerException for Transaction ID {tx_id}")
        return causes

    @staticmethod
    def _extract_finswitch_confirmation_causes(message: str, long_text: str, tx_id: Optional[str]) -> List[str]:
        """
        Extract Upload FinSwitch Transaction Confirmation causes from error message/stack trace.

        Includes:
        - BRA-002 message line (if present)
        - BRA-90117 message line (if present)
        - NumberFormatException with message
        - NullPointerException for Transaction ID <tx_id> (if present)
        """
        causes = []
        if message and "BRA-002" in message:
            causes.append(message.strip())
        if message and "BRA-90117" in message:
            causes.append(message.strip())
        if long_text:
            match = re.search(r"NumberFormatException:\s*([^\r\n]+)", long_text)
            detail_match = re.search(r"java\.lang\.NumberFormatException:\s*([^\r\n]+)", long_text)
            if match or detail_match:
                if detail_match:
                    causes.append(f"NumberFormatException - {detail_match.group(1).strip()}")
                else:
                    causes.append(f"NumberFormatException - {match.group(1).strip()}")
        if long_text and "NullPointerException" in long_text and tx_id:
            causes.append(f"NullPointerException for Transaction ID {tx_id}")
        return causes
    
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
    
    def extract_log_summary(self, log_data: Dict) -> Dict:
        """
        Extract summary information from system log response
        
        Args:
            log_data: System log API response
            
        Returns:
            Dictionary with summary information
        """
        search_results = log_data.get('searchResults', [])
        
        if not search_results:
            return {
                'queue_id': None,
                'log_count': 0,
                'errors': [],
                'process_names': set()
            }
        
        errors = []
        process_names = set()
        queue_id = None
        
        for log_entry in search_results:
            queue_id = log_entry.get('queueId', queue_id)
            
            error_info = {
                'log_id': log_entry.get('logId'),
                'message': log_entry.get('message', '').strip(),
                'created_date': log_entry.get('createdDate'),
                'created_by': log_entry.get('createdBy'),
                'long_text': log_entry.get('longText', ''),
                'process_name': log_entry.get('processName'),
                'message_code': log_entry.get('messageCode', {}),
                'queue_id': queue_id
            }
            
            errors.append(error_info)
            
            # Track errors by process name for summary
            process_name = error_info['process_name'] or 'Unknown Process'
            if process_name not in self.process_errors:
                self.process_errors[process_name] = {
                    'queue_ids': set(),
                    'error_count': 0,
                    'sample_errors': []
                }
            if process_name not in self.process_transactions:
                self.process_transactions[process_name] = set()
            if process_name not in self.process_accounts:
                self.process_accounts[process_name] = set()
            if process_name not in self.process_error_causes:
                self.process_error_causes[process_name] = Counter()
            if process_name not in self.process_transaction_errors:
                self.process_transaction_errors[process_name] = {}
            
            self.process_errors[process_name]['queue_ids'].add(queue_id)
            self.process_errors[process_name]['error_count'] += 1
            
            # Keep sample errors (first 3)
            if len(self.process_errors[process_name]['sample_errors']) < 3:
                self.process_errors[process_name]['sample_errors'].append({
                    'message': error_info['message'],
                    'queue_id': queue_id,
                    'created_date': error_info['created_date']
                })

            # Collect Apply Prices transaction IDs (if present)
            if process_name == 'Apply Prices':
                tx_ids = self._extract_apply_prices_transaction_ids(error_info['long_text'])
                self.process_transactions[process_name].update(tx_ids)
                for tx_id in tx_ids:
                    tx_entry = self.process_transaction_errors[process_name].setdefault(
                        tx_id, {'count': 0, 'samples': [], 'causes': Counter()}
                    )
                    tx_entry['count'] += 1
                    if len(tx_entry['samples']) < 3:
                        tx_entry['samples'].append({
                            'message': error_info['message'],
                            'queue_id': queue_id,
                            'created_date': error_info['created_date']
                        })
                    for cause in self._extract_apply_prices_causes(
                        error_info['message'],
                        error_info['long_text'],
                        tx_id
                    ):
                        tx_entry['causes'][cause] += 1
            if process_name in (
                'Regular Applications',
                'Regular Withdrawals',
                'Disinvest for Unpriced Transactions',
                'SMP Rebalance Process',
                'Cash Receipt Creation for Expectations',
                'Upload Settlement Date',
                'Upload FinSwitch Transaction Confirmation'
            ):
                self.process_accounts[process_name].update(
                    self._extract_account_ids(
                        error_info['message'],
                        error_info['long_text']
                    )
                )
            if process_name in ('Regular Applications', 'Regular Withdrawals'):
                tx_ids = self._extract_regular_applications_transaction_ids(error_info['long_text'])
                causes = self._extract_error_causes(error_info['long_text'])
                self.process_transactions[process_name].update(tx_ids)
                for tx_id in tx_ids:
                    tx_entry = self.process_transaction_errors[process_name].setdefault(
                        tx_id, {'count': 0, 'samples': [], 'causes': Counter()}
                    )
                    tx_entry['count'] += 1
                    if len(tx_entry['samples']) < 3:
                        tx_entry['samples'].append({
                            'message': error_info['message'],
                            'queue_id': queue_id,
                            'created_date': error_info['created_date']
                        })
                    for cause in causes:
                        tx_entry['causes'][cause] += 1
                    for cause in self._extract_regular_applications_causes(
                        error_info['message'],
                        error_info['long_text'],
                        tx_id
                    ):
                        tx_entry['causes'][cause] += 1
                for cause in causes:
                    self.process_error_causes[process_name][cause] += 1
            if process_name == 'Disinvest for Unpriced Transactions':
                tx_ids = self._extract_disinvest_transaction_ids(error_info['long_text'])
                causes = self._extract_error_causes(error_info['long_text'])
                self.process_transactions[process_name].update(tx_ids)
                for tx_id in tx_ids:
                    tx_entry = self.process_transaction_errors[process_name].setdefault(
                        tx_id, {'count': 0, 'samples': [], 'causes': Counter()}
                    )
                    tx_entry['count'] += 1
                    if len(tx_entry['samples']) < 3:
                        tx_entry['samples'].append({
                            'message': error_info['message'],
                            'queue_id': queue_id,
                            'created_date': error_info['created_date']
                        })
                    for cause in causes:
                        tx_entry['causes'][cause] += 1
                for cause in causes:
                    self.process_error_causes[process_name][cause] += 1
            if process_name == 'SMP Rebalance Process':
                tx_ids = self._extract_smp_rebalance_transaction_ids(error_info['long_text'])
                causes = self._extract_error_causes(error_info['long_text'])
                self.process_transactions[process_name].update(tx_ids)
                for tx_id in tx_ids:
                    tx_entry = self.process_transaction_errors[process_name].setdefault(
                        tx_id, {'count': 0, 'samples': [], 'causes': Counter()}
                    )
                    tx_entry['count'] += 1
                    if len(tx_entry['samples']) < 3:
                        tx_entry['samples'].append({
                            'message': error_info['message'],
                            'queue_id': queue_id,
                            'created_date': error_info['created_date']
                        })
                    for cause in causes:
                        tx_entry['causes'][cause] += 1
                for cause in causes:
                    self.process_error_causes[process_name][cause] += 1
            if process_name == 'Cash Receipt Creation for Expectations':
                tx_ids = self._extract_cash_receipt_transaction_ids(error_info['long_text'])
                causes = self._extract_error_causes(error_info['long_text'])
                self.process_transactions[process_name].update(tx_ids)
                for tx_id in tx_ids:
                    tx_entry = self.process_transaction_errors[process_name].setdefault(
                        tx_id, {'count': 0, 'samples': [], 'causes': Counter()}
                    )
                    tx_entry['count'] += 1
                    if len(tx_entry['samples']) < 3:
                        tx_entry['samples'].append({
                            'message': error_info['message'],
                            'queue_id': queue_id,
                            'created_date': error_info['created_date']
                        })
                    for cause in causes:
                        tx_entry['causes'][cause] += 1
                    for cause in self._extract_cash_receipt_causes(
                        error_info['message'],
                        error_info['long_text'],
                        tx_id
                    ):
                        tx_entry['causes'][cause] += 1
                for cause in causes:
                    self.process_error_causes[process_name][cause] += 1
            if process_name == 'Upload Settlement Date':
                tx_ids = self._extract_upload_settlement_transaction_ids(error_info['long_text'])
                causes = self._extract_error_causes(error_info['long_text'])
                self.process_transactions[process_name].update(tx_ids)
                for tx_id in tx_ids:
                    tx_entry = self.process_transaction_errors[process_name].setdefault(
                        tx_id, {'count': 0, 'samples': [], 'causes': Counter()}
                    )
                    tx_entry['count'] += 1
                    if len(tx_entry['samples']) < 3:
                        tx_entry['samples'].append({
                            'message': error_info['message'],
                            'queue_id': queue_id,
                            'created_date': error_info['created_date']
                        })
                    for cause in causes:
                        tx_entry['causes'][cause] += 1
                    for cause in self._extract_upload_settlement_causes(
                        error_info['message'],
                        error_info['long_text'],
                        tx_id
                    ):
                        tx_entry['causes'][cause] += 1
                for cause in causes:
                    self.process_error_causes[process_name][cause] += 1
            if process_name == 'Upload FinSwitch Transaction Confirmation':
                tx_ids = self._extract_finswitch_confirmation_transaction_ids(error_info['long_text'])
                causes = self._extract_error_causes(error_info['long_text'])
                fin_causes = self._extract_finswitch_confirmation_causes(
                    error_info['message'],
                    error_info['long_text'],
                    None
                )
                self.process_transactions[process_name].update(tx_ids)
                for tx_id in tx_ids:
                    tx_entry = self.process_transaction_errors[process_name].setdefault(
                        tx_id, {'count': 0, 'samples': [], 'causes': Counter()}
                    )
                    tx_entry['count'] += 1
                    if len(tx_entry['samples']) < 3:
                        tx_entry['samples'].append({
                            'message': error_info['message'],
                            'queue_id': queue_id,
                            'created_date': error_info['created_date']
                        })
                    for cause in causes:
                        tx_entry['causes'][cause] += 1
                    for cause in self._extract_finswitch_confirmation_causes(
                        error_info['message'],
                        error_info['long_text'],
                        tx_id
                    ):
                        tx_entry['causes'][cause] += 1
                for cause in causes:
                    self.process_error_causes[process_name][cause] += 1
                for cause in fin_causes:
                    self.process_error_causes[process_name][cause] += 1
            
            if error_info['process_name']:
                process_names.add(error_info['process_name'])
        
        return {
            'queue_id': queue_id,
            'log_count': len(errors),
            'errors': errors,
            'process_names': process_names
        }
    
    def get_process_summary(self) -> Dict:
        """
        Get summary of errors grouped by process name
        
        Returns:
            Dictionary with process-level error summary
        """
        # Attach transaction IDs if available
        summary = {}
        for process_name, data in self.process_errors.items():
            summary[process_name] = dict(data)
            summary[process_name]['transaction_ids'] = sorted(
                self.process_transactions.get(process_name, set()),
                key=lambda x: int(x)
            )
            summary[process_name]['account_ids'] = sorted(
                self.process_accounts.get(process_name, set())
            )
            summary[process_name]['error_causes'] = self.process_error_causes.get(process_name, Counter())
        return summary

    def get_transaction_summary(self) -> Dict:
        """
        Get transaction-level error summary grouped by process name.

        Returns:
            Dictionary with transaction-level error summary
        """
        return self.process_transaction_errors



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
    
    @staticmethod
    def print_system_log_details(queue_id: int, log_summary: Dict):
        """
        Print detailed system log information for a queue ID
        
        Args:
            queue_id: Queue ID
            log_summary: Log summary dictionary from JobHistoryAnalyzer
        """
        print("\n" + "=" * 80)
        print(f"DETAILED ERROR LOG - Queue ID: {queue_id}")
        print("=" * 80)
        
        if log_summary['log_count'] == 0:
            print("No log entries found for this queue ID.")
            return
        
        print(f"\nTotal Log Entries: {log_summary['log_count']}")
        
        if log_summary['process_names']:
            print(f"Process Names: {', '.join(sorted(log_summary['process_names']))}")
        
        print("\n" + "-" * 80)
        
        # Print each error entry
        for idx, error in enumerate(log_summary['errors'], 1):
            print(f"\nLog Entry #{idx}")
            print("-" * 80)
            print(f"Log ID: {error['log_id']}")
            print(f"Created: {error['created_date']} by {error['created_by']}")
            print(f"Process: {error['process_name']}")
            
            msg_code = error['message_code']
            if msg_code:
                print(f"Message Code: {msg_code.get('code', 'N/A')} - {msg_code.get('codeShortDescription', 'N/A')}")
            
            print(f"\nError Message:")
            print(error['message'])
            
            # Print stack trace if available
            if error['long_text']:
                print(f"\nStack Trace:")
                print(error['long_text'])
        
        print("\n" + "=" * 80)
    
    @staticmethod
    def print_detailed_report_header(total_queue_ids: int, fetch_limit: Optional[int] = None):
        """Print header for detailed report section"""
        print("\n\n" + "=" * 80)
        print("DETAILED SYSTEM LOGS")
        print("=" * 80)
        
        if fetch_limit and fetch_limit < total_queue_ids:
            print(f"\nFetching details for top {fetch_limit} queue IDs (out of {total_queue_ids} total)")
        else:
            print(f"\nFetching details for all {total_queue_ids} queue IDs")
        
        print("This may take a moment...")
        print("=" * 80)
    
    @staticmethod
    def print_process_summary(process_errors: Dict):
        """
        Print summary of errors grouped by process name
        
        Args:
            process_errors: Dictionary from JobHistoryAnalyzer.get_process_summary()
        """
        if not process_errors:
            return
        
        print("\n\n" + "=" * 80)
        print("ERROR ANALYSIS BY PROCESS")
        print("=" * 80)
        
        # Sort by error count (descending)
        sorted_processes = sorted(
            process_errors.items(),
            key=lambda x: x[1]['error_count'],
            reverse=True
        )
        
        print(f"\nTotal Processes with Errors: {len(sorted_processes)}")
        print("\n" + "-" * 80)
        
        for process_name, data in sorted_processes:
            print(f"\n{'Process:':<20} {process_name}")
            print(f"{'Error Count:':<20} {data['error_count']:,}")
            print(f"{'Affected Queue IDs:':<20} {len(data['queue_ids'])} unique queue(s)")
            print(f"{'Queue IDs:':<20} {', '.join(map(str, sorted(data['queue_ids'])))}")
            if data.get('transaction_ids'):
                print(f"{'Affected Transaction IDs:':<20} {len(data['transaction_ids'])} unique transaction(s)")
                print(f"{'Transaction IDs:':<20} {', '.join(data['transaction_ids'])}")
            if data.get('account_ids'):
                print(f"{'Affected Accounts:':<20} {len(data['account_ids'])} unique account(s)")
                print(f"{'Account IDs:':<20} {', '.join(data['account_ids'])}")
            if process_name in (
                'Disinvest for Unpriced Transactions',
                'SMP Rebalance Process',
                'Cash Receipt Creation for Expectations',
                'Upload Settlement Date',
                'Upload FinSwitch Transaction Confirmation'
            ) and data.get('error_causes'):
                print(f"{'Top Error Causes:':<20}")
                for cause, count in data['error_causes'].most_common(5):
                    print(f"  - {cause} ({count})")
            
            if data['sample_errors']:
                print(f"\n{'Sample Errors:':<20}")
                for idx, error in enumerate(data['sample_errors'], 1):
                    print(f"  {idx}. {error['message'][:100]}...")
                    print(f"     Queue ID: {error['queue_id']}, Date: {error['created_date']}")
            
            print("-" * 80)
        
        # Summary statistics
        print("\nSUMMARY STATISTICS")
        print("-" * 80)
        total_errors = sum(data['error_count'] for data in process_errors.values())
        total_queues = len(set().union(*[data['queue_ids'] for data in process_errors.values()]))
        
        print(f"{'Total Errors Analyzed:':<30} {total_errors:,}")
        print(f"{'Total Unique Queue IDs:':<30} {total_queues:,}")
        print(f"{'Total Unique Processes:':<30} {len(process_errors):,}")
        print(f"{'Average Errors per Process:':<30} {total_errors / len(process_errors):.1f}")
        
        print("=" * 80)


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
    parser.add_argument('--fetch-details',
                       action='store_true',
                       help='Fetch detailed system logs for each queue ID')
    parser.add_argument('--detail-limit',
                       type=int,
                       metavar='N',
                       help='Limit number of queue IDs to fetch details for (default: all)')
    parser.add_argument('--output-file', '-o',
                       metavar='FILE',
                       help='Write output to file instead of console')
    
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


def split_report_file(report_path: str) -> None:
    """
    Split a full report into summary, detailed logs, and process analysis files.

    Args:
        report_path: Path to the full report file
    """
    try:
        with open(report_path, 'r', encoding='utf-8') as report_file:
            lines = report_file.readlines()
    except Exception as e:
        print(f"WARNING: Could not read report for splitting: {e}", file=sys.stderr)
        return

    markers = {
        'summary': 'SBS Error Job History Report',
        'details': 'DETAILED SYSTEM LOGS',
        'process': 'ERROR ANALYSIS BY PROCESS'
    }

    def find_marker_index(marker: str) -> Optional[int]:
        for idx, line in enumerate(lines):
            if marker in line:
                return idx
        return None

    summary_idx = find_marker_index(markers['summary'])
    details_idx = find_marker_index(markers['details'])
    process_idx = find_marker_index(markers['process'])

    if summary_idx is None:
        print("WARNING: Could not find summary section in report.", file=sys.stderr)
        return

    def section_start(idx: int) -> int:
        return max(idx - 2, 0)

    summary_start = section_start(summary_idx)
    summary_end = details_idx if details_idx is not None else len(lines)

    details_start = section_start(details_idx) if details_idx is not None else None
    details_end = process_idx if process_idx is not None else len(lines)

    process_start = section_start(process_idx) if process_idx is not None else None
    process_end = len(lines)

    base_dir = os.path.dirname(report_path) or '.'
    base_name = os.path.splitext(os.path.basename(report_path))[0]

    output_files = []

    summary_path = os.path.join(base_dir, f"summary_{base_name}.txt")
    with open(summary_path, 'w', encoding='utf-8') as out:
        out.writelines(lines[summary_start:summary_end])
    output_files.append(summary_path)

    if details_start is not None:
        details_path = os.path.join(base_dir, f"detailed_{base_name}.txt")
        with open(details_path, 'w', encoding='utf-8') as out:
            out.writelines(lines[details_start:details_end])
        output_files.append(details_path)

    if process_start is not None:
        process_path = os.path.join(base_dir, f"process_{base_name}.txt")
        with open(process_path, 'w', encoding='utf-8') as out:
            out.writelines(lines[process_start:process_end])
        output_files.append(process_path)

    print("\n[SUCCESS] Split files created:", file=sys.stderr)
    for path in output_files:
        print(f"  - {path}", file=sys.stderr)


def write_transaction_report(
    report_path: str,
    transaction_summary: Dict,
    process_summary: Optional[Dict] = None,
    extra_processes: Optional[List[str]] = None,
    detail_dir: str = "detail_process"
) -> None:
    """
    Write transaction-level error summary to a separate file.

    Args:
        report_path: Path to the full report file
        transaction_summary: Dictionary from JobHistoryAnalyzer.get_transaction_summary()
        process_summary: Optional dictionary from JobHistoryAnalyzer.get_process_summary()
    """
    if not report_path:
        return

    base_dir = os.path.dirname(report_path) or '.'
    output_dir = os.path.join(base_dir, detail_dir) if not os.path.isabs(detail_dir) else detail_dir
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(report_path))[0]

    process_names = set(transaction_summary.keys())
    if process_summary:
        process_names.update(process_summary.keys())
    if extra_processes:
        process_names.update(extra_processes)

    for process_name in sorted(process_names):
        tx_map = transaction_summary.get(process_name, {})
        process_info = process_summary.get(process_name, {}) if process_summary else {}

        safe_process = re.sub(r"[^A-Za-z0-9]+", "_", process_name.strip()).strip("_").lower()
        output_path = os.path.join(output_dir, f"errors_{safe_process}_{base_name}.txt")

        with open(output_path, 'w', encoding='utf-8') as out:
            out.write("============================================================\n")
            out.write("ERRORS BY TRANSACTION ID\n")
            out.write("============================================================\n\n")
            out.write(f"Process: {process_name}\n")
            out.write("-" * 60 + "\n")
            if process_info.get('account_ids'):
                out.write(f"Affected Accounts: {len(process_info['account_ids'])} unique account(s)\n")
                out.write(f"Account IDs: {', '.join(process_info['account_ids'])}\n")
            if process_info.get('error_causes'):
                out.write("Top Error Causes:\n")
                for cause, count in process_info['error_causes'].most_common(5):
                    out.write(f"  - {cause} ({count})\n")
            out.write("\n")

            if tx_map:
                for tx_id, data in sorted(tx_map.items(), key=lambda x: int(x[0])):
                    out.write(f"Transaction ID: {tx_id}\n")
                    out.write(f"Error Count: {data['count']}\n")
                    if data.get('causes'):
                        out.write("Error Causes:\n")
                        for cause, count in data['causes'].most_common(3):
                            out.write(f"  - {cause} ({count})\n")
                    if data['samples']:
                        out.write("Sample Errors:\n")
                        for idx, sample in enumerate(data['samples'], 1):
                            out.write(
                                f"  {idx}. {sample['message']}\n"
                                f"     Queue ID: {sample['queue_id']}, Date: {sample['created_date']}\n"
                            )
                    out.write("\n")
            else:
                if not process_info:
                    out.write("No entries found for this process on this date.\n\n")
                else:
                    out.write("No transaction IDs found for this process.\n\n")

        print(f"  - {output_path}", file=sys.stderr)




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
    
    # Setup output file if specified or if fetching details
    output_file = None
    if args.output_file:
        # User specified output file
        output_path = args.output_file
    elif args.fetch_details:
        # Auto-generate filename when fetching details
        os.makedirs('results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"results/error_report_{timestamp}.txt"
    else:
        output_path = None
    
    if output_path:
        try:
            output_file = open(output_path, 'w', encoding='utf-8')
            sys.stdout = output_file
            if args.verbose:
                print(f"[DEBUG] Writing output to: {output_path}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Could not open output file {output_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
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
    
    # Fetch detailed logs if requested
    if args.fetch_details and queue_counts:
        # Get list of queue IDs sorted by count (descending)
        sorted_queue_ids = [qid for qid, count in queue_counts.most_common()]
        
        # Apply limit if specified
        detail_limit = args.detail_limit
        if detail_limit:
            sorted_queue_ids = sorted_queue_ids[:detail_limit]
        
        # Print header
        report_gen.print_detailed_report_header(
            total_queue_ids=len(queue_counts),
            fetch_limit=detail_limit
        )
        
        # Fetch and display details for each queue ID
        for idx, queue_id in enumerate(sorted_queue_ids, 1):
            try:
                if args.verbose:
                    print(f"\n[DEBUG] Fetching details for queue ID {queue_id} ({idx}/{len(sorted_queue_ids)})", 
                          file=sys.stderr)
                
                # Fetch system log
                log_response = client.get_system_log(queue_id)
                
                # Analyze log
                log_summary = analyzer.extract_log_summary(log_response)
                
                # Display details
                report_gen.print_system_log_details(queue_id, log_summary)
                
            except Exception as e:
                print(f"\nWARNING: Failed to fetch details for queue ID {queue_id}: {e}", 
                      file=sys.stderr)
                continue
        
        print("\n" + "=" * 80)
        print(f"Detailed log fetch complete. Processed {len(sorted_queue_ids)} queue IDs.")
        print("=" * 80)
        
        # Generate and display process summary
        process_summary = analyzer.get_process_summary()
        report_gen.print_process_summary(process_summary)
    
    # Close output file if used
    if output_file:
        sys.stdout = sys.__stdout__
        output_file.close()
        print(f"\n[SUCCESS] Report written to: {output_path}", file=sys.stderr)
        if args.fetch_details:
            split_report_file(output_path)
            print("[SUCCESS] Transaction summary file created:", file=sys.stderr)
            write_transaction_report(
                output_path,
                analyzer.get_transaction_summary(),
                analyzer.get_process_summary(),
                extra_processes=[
                    "Apply Prices",
                    "SMP Rebalance Process",
                    "Upload Settlement Date",
                    "Upload FinSwitch Transaction Confirmation"
                ]
            )


if __name__ == '__main__':
    main()
