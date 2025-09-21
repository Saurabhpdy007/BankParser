#!/usr/bin/env python3
"""
ICICI Bank Statement Formatter
============================

A robust formatter specifically designed for ICICI Bank statement processing.
Extracts and structures transaction data from ICICI Bank PDF statements.

Features:
- Multi-line transaction parsing
- Transaction ID detection and handling
- Balance equation validation
- Clean 6-column output (date, mode, particulars, deposits, withdrawals, balance)

Version: 2.0
Author: CredNX Team
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from .base_formatter import BaseBankFormatter

logger = logging.getLogger(__name__)

class ICICIFormatter(BaseBankFormatter):
    """
    ICICI Bank statement formatter.
    
    Handles ICICI bank statements with multi-line transaction format where:
    - Headers appear on all pages with pattern: DATE\\nMODE**\\nPARTICULARS\\nDEPOSITS\\nWITHDRAWALS\\nBALANCE
    - Transactions can span multiple lines with variable-length descriptions
    - Some transactions have transaction IDs on separate lines between description and amounts
    - Uses balance equation logic to determine credit/debit: Previous Balance + Credit - Debit = Next Balance
    
    Key features:
    - Multi-line transaction parsing
    - Transaction ID detection and handling
    - Balance equation validation
    - Clean 6-column output (date, mode, particulars, deposits, withdrawals, balance)
    """
    
    def get_bank_name(self) -> str:
        return "ICICI"
    
    def get_date_patterns(self) -> List[str]:
        return [
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY (ICICI format)
            r'\d{1,2}-\d{1,2}-\d{4}',  # D-M-YYYY
        ]
    
    def get_amount_patterns(self) -> List[str]:
        return [
            r'(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)',  # 1,000.00 or 1000.00
        ]
    
    def get_transaction_patterns(self) -> Dict[str, str]:
        return {
            "header_pattern": r'DATE\\s+MODE\\*\\*\\s+PARTICULARS\\s+DEPOSITS\\s+WITHDRAWALS\\s+BALANCE',
            "transaction_line": r'(\\d{2}-\\d{2}-\\d{4})\\s+([^\\s]+)\\s+(.+?)\\s+(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)\\s+(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)\\s+(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)',
            "page_end_pattern": r'Page \d+ of \d+',
            "mode_types": r'(B/F|NEFT|IMPS|UPI|ATM|POS|TRANSFER|PAYMENT|CHEQUE|ECS|DD|RTGS)',
        }
    
    def validate_statement(self, extracted_text: str) -> bool:
        """Validate ICICI statement format"""
        icici_indicators = [
            "ICICI BANK",
            "ICICI Bank", 
            "ICICI",
            "Account Statement",
            "Statement of Account",
            "DATE\nMODE**\nPARTICULARS\nDEPOSITS\nWITHDRAWALS\nBALANCE"
        ]
        
        text_upper = extracted_text.upper()
        return any(indicator.upper() in text_upper for indicator in icici_indicators)
    
    def parse_statement_format(self, extracted_text: str) -> List[Dict[str, Any]]:
        """
        Parse ICICI bank statement format with proper column structure
        Handles multi-page statements with headers on each page
        """
        logger.info("Parsing ICICI bank statement format")
        
        transactions = []
        lines = extracted_text.split('\n')
        
        # Find all page sections
        page_sections = self._split_into_pages(lines)
        
        # Track global transaction order across all pages
        global_transaction_order = 0
        
        for page_num, page_lines in page_sections.items():
            logger.info(f"Processing ICICI page {page_num} with {len(page_lines)} lines")
            
            # Find header and transaction data for this page
            page_transactions = self._parse_icici_page(page_lines, page_num, global_transaction_order)
            
            # Update global transaction order for next page
            global_transaction_order += len(page_transactions)
            
            transactions.extend(page_transactions)
        
        # Sort transactions by date, but maintain original order within same date
        # This ensures transactions on the same date appear in the correct chronological order
        transactions.sort(key=lambda x: (self._parse_date(x['date']), x.get('_original_order', 0)))
        
        # Apply balance equation logic to determine credit/debit
        transactions = self._apply_balance_equation_logic(transactions)
        
        logger.info(f"Successfully parsed {len(transactions)} ICICI transactions")
        return transactions
    
    def _find_first_page_marker_line(self, lines: List[str]) -> int:
        """Find the line number of the first page marker"""
        for i, line in enumerate(lines):
            if re.search(r'Page \d+ of \d+', line):
                return i
        return -1
    
    def _split_into_pages(self, lines: List[str]) -> Dict[int, List[str]]:
        """Split text into page sections based on 'Page x of y' markers"""
        page_sections = {}
        current_page = 1
        current_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Check for page marker
            page_match = re.search(r'Page (\d+) of (\d+)', line)
            if page_match:
                # Save current page
                if current_lines:
                    page_sections[current_page] = current_lines
                
                # Start new page
                current_page = int(page_match.group(1))
                current_lines = []
            else:
                current_lines.append(line)
        
        # Add the last page
        if current_lines:
            page_sections[current_page] = current_lines
        
        # Special handling: If page 1 exists, merge pre-page content into it
        # This ensures transactions before the first "Page 1 of X" marker are included in page 1
        if 1 in page_sections:
            first_page_marker_line = self._find_first_page_marker_line(lines)
            if first_page_marker_line > 0:
                # Merge pre-page content into page 1
                pre_page_content = lines[:first_page_marker_line]
                page_1_content = page_sections[1]
                page_sections[1] = pre_page_content + page_1_content
                logger.info(f"Merged pre-page content ({len(pre_page_content)} lines) into page 1")
        
        return page_sections
    
    def _parse_icici_page(self, page_lines: List[str], page_num: int, global_transaction_order: int = 0) -> List[Dict[str, Any]]:
        """Parse a single ICICI page for transactions"""
        transactions = []
        
        # Find the header (ICICI uses multi-line headers)
        header_found = False
        data_start_idx = -1
        
        for i, line in enumerate(page_lines):
            line = line.strip()
            if line == 'DATE':
                # Check if next lines contain the header
                if (i + 5 < len(page_lines) and 
                    page_lines[i + 1].strip() == 'MODE**' and
                    page_lines[i + 2].strip() == 'PARTICULARS' and
                    page_lines[i + 3].strip() == 'DEPOSITS' and
                    page_lines[i + 4].strip() == 'WITHDRAWALS' and
                    page_lines[i + 5].strip() == 'BALANCE'):
                    header_found = True
                    data_start_idx = i + 6  # Start after the header
                    break
        
        if not header_found:
            logger.warning(f"No ICICI header found on page {page_num}")
            return transactions
        
        # Parse transaction lines (ICICI format: each transaction spans multiple lines)
        i = data_start_idx
        page_transaction_order = 0  # Order within this page
        while i < len(page_lines):
            line = page_lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Skip if this is a page end marker
            if re.search(r'Page \d+ of \d+', line):
                break
            
            # Check if this looks like a transaction start (date pattern)
            if re.match(r'\d{2}-\d{2}-\d{4}', line):
                # This is the start of a transaction
                transaction = self._parse_icici_transaction_multiline(page_lines, i)
                if transaction:
                    transaction['page'] = page_num
                    transaction['_original_order'] = global_transaction_order + page_transaction_order
                    transactions.append(transaction)
                    page_transaction_order += 1
                    # Move to next transaction
                    i = transaction.get('_next_line', i + 1)
                else:
                    i += 1
            else:
                i += 1
        
        logger.info(f"Found {len(transactions)} transactions on ICICI page {page_num}")
        return transactions
    
    def _parse_icici_transaction_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single ICICI transaction line"""
        # ICICI format: DATE MODE PARTICULARS DEPOSITS WITHDRAWALS BALANCE
        # Example: 17-09-2024 B/F 93,498.86
        
        # Try to match the full 6-column format
        full_match = re.search(
            r'(\\d{2}-\\d{2}-\\d{4})\\s+([^\\s]+)\\s+(.+?)\\s+(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)\\s+(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)\\s+(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)',
            line
        )
        
        if full_match:
            date_str, mode, particulars, deposits_str, withdrawals_str, balance_str = full_match.groups()
            
            # Parse amounts
            deposits = float(deposits_str.replace(',', '')) if deposits_str != '0.00' else 0.0
            withdrawals = float(withdrawals_str.replace(',', '')) if withdrawals_str != '0.00' else 0.0
            balance = float(balance_str.replace(',', ''))
            
            # Determine transaction type and amount
            if deposits > 0:
                transaction_type = "CREDIT"
                amount = deposits
            elif withdrawals > 0:
                transaction_type = "DEBIT"
                amount = withdrawals
            else:
                # For B/F (brought forward) or other cases
                transaction_type = "BALANCE"
                amount = balance
            
            return {
                "date": date_str,
                "mode": mode.strip(),
                "particulars": particulars.strip(),
                "deposits": deposits,
                "withdrawals": withdrawals,
                "balance": balance,
                "amount": amount,
                "type": transaction_type,
                "bank": "ICICI",
                "narration": f"{mode} - {particulars}".strip()
            }
        
        # Try simpler format for cases where columns might be merged
        simple_match = re.search(
            r'(\\d{2}-\\d{2}-\\d{4})\\s+([^\\s]+)\\s+(.+?)\\s+(\\d+(?:,\\d{3})*(?:\\.\\d{2})?)',
            line
        )
        
        if simple_match:
            date_str, mode, particulars, amount_str = simple_match.groups()
            amount = float(amount_str.replace(',', ''))
            
            # Determine transaction type based on mode
            if mode in ['B/F', 'BALANCE']:
                transaction_type = "BALANCE"
            elif mode in ['NEFT', 'IMPS', 'UPI', 'TRANSFER', 'PAYMENT']:
                # Need to determine if it's credit or debit based on context
                transaction_type = "UNKNOWN"
            else:
                transaction_type = "UNKNOWN"
            
            return {
                "date": date_str,
                "mode": mode.strip(),
                "particulars": particulars.strip(),
                "deposits": 0.0,
                "withdrawals": 0.0,
                "balance": amount,
                "amount": amount,
                "type": transaction_type,
                "bank": "ICICI",
                "narration": f"{mode} - {particulars}".strip()
            }
        
        return None
    
    def _parse_icici_transaction_multiline(self, page_lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
        """Parse ICICI transaction with smart variable-length handling"""
        try:
            if start_idx >= len(page_lines):
                return None
            
            date_str = page_lines[start_idx].strip()
            
            # Collect mode lines (until we hit an amount)
            mode_lines = []
            i = start_idx + 1
            
            # Look for mode lines (non-amount lines after date)
            while i < len(page_lines):
                line = page_lines[i].strip()
                if not line:
                    i += 1
                    continue
                
                # Skip if this is a page end marker
                if re.search(r'Page \d+ of \d+', line):
                    break
                
                # Skip if this is a new date (start of next transaction)
                if re.match(r'\d{2}-\d{2}-\d{4}', line):
                    break
                
                # Check if this line contains an amount (deposits/withdrawals/balance)
                if self._is_amount_line(line):
                    break
                
                # This is part of the mode
                mode_lines.append(line)
                i += 1
            
            mode = ' '.join(mode_lines).strip()
            
            # Now look for amounts (deposits, withdrawals, balance)
            amounts = []
            while i < len(page_lines):
                line = page_lines[i].strip()
                if not line:
                    i += 1
                    continue
                
                # Skip if this is a page end marker
                if re.search(r'Page \d+ of \d+', line):
                    break
                
                # Skip if this is a new date (start of next transaction)
                if re.match(r'\d{2}-\d{2}-\d{4}', line):
                    break
                
                # Check if this line contains an amount
                if self._is_amount_line(line):
                    amounts.append(line)
                    i += 1
                elif self._is_transaction_id(line):
                    # Skip transaction ID lines (like 3746, 8552, 7507574)
                    i += 1
                    continue
                else:
                    # Non-amount line, might be part of mode continuation
                    break
            
            # Parse amounts based on ICICI format using balance equation logic
            deposits = 0.0
            withdrawals = 0.0
            balance = 0.0
            
            if len(amounts) == 1:
                # Single amount - could be B/F (balance) or deposits/withdrawals
                amount = self._parse_amount(amounts[0])
                if amount is not None:
                    if mode == 'B/F':
                        # B/F is a balance carryover
                        balance = amount
                    else:
                        # For single amount transactions, we need to determine credit/debit
                        # This will be handled by balance equation logic later
                        deposits = amount  # Temporary assignment
            elif len(amounts) == 2:
                # Two amounts - first is deposits/withdrawals, second is balance
                first_amount = self._parse_amount(amounts[0])
                second_amount = self._parse_amount(amounts[1])
                
                if first_amount is not None and second_amount is not None:
                    # Use balance equation logic: Previous Balance + Credit - Debit = Next Balance
                    # We'll determine credit/debit based on balance progression
                    deposits = first_amount  # Temporary assignment
                    balance = second_amount
            
            # Determine transaction type and amount
            if deposits > 0:
                transaction_type = "CREDIT"
                amount = deposits
            elif withdrawals > 0:
                transaction_type = "DEBIT"
                amount = withdrawals
            elif mode == 'B/F':
                # Brought forward - this is a balance carryover
                transaction_type = "BALANCE"
                amount = balance
            else:
                # For other cases, use balance as amount
                transaction_type = "UNKNOWN"
                amount = balance
            
            # Extract clean mode from the full mode string
            clean_mode = self._extract_icici_mode(mode)
            
            transaction = {
                "date": date_str,
                "mode": clean_mode,
                "particulars": mode,  # Full mode string becomes particulars
                "deposits": deposits,
                "withdrawals": withdrawals,
                "balance": balance,
                "amount": amount,
                "type": transaction_type,
                "bank": "ICICI",
                "narration": mode,
                "_next_line": i
            }
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error parsing ICICI transaction at line {start_idx}: {str(e)}")
            return None
    
    def _is_transaction_id(self, line: str) -> bool:
        """
        Check if a line contains a transaction ID (not an amount).
        
        Transaction IDs are pure numbers without commas or decimals,
        typically 4-12 digits long, that appear on separate lines
        between transaction descriptions and amounts.
        
        Args:
            line: The line to check
            
        Returns:
            True if the line contains a transaction ID, False otherwise
        """
        line = line.strip()
        
        # Transaction IDs are pure numbers without commas or decimals
        # They can be various lengths but are typically 4-12 digits
        if re.match(r'^\d+$', line):
            # Must not contain letters or special characters
            if re.search(r'[a-zA-Z]', line):
                return False
            if re.search(r'[/\\\\@#]', line):
                return False
            
            # Transaction IDs are typically 4-12 digits without formatting
            if 4 <= len(line) <= 12 and ',' not in line and '.' not in line:
                return True
        
        return False
    
    def _is_amount_line(self, line: str) -> bool:
        """
        Check if a line contains a financial amount.
        
        Identifies lines containing monetary values in various formats:
        - Western format: 78,410.00
        - Indian format: 1,71,908.86
        - Simple format: 5000.0
        
        Args:
            line: The line to check
            
        Returns:
            True if the line contains an amount, False otherwise
        """
        line = line.strip()
        
        # First check if this is a transaction ID - if so, it's not an amount
        if self._is_transaction_id(line):
            return False
        
        # Look for patterns like: 78,410.00, 1,71,908.86, 5000.0, etc.
        # Must start with digits and contain only digits, commas, and decimal point
        # Support both Western (78,410.00) and Indian (1,71,908.86) formats
        # Allow 1 or 2 decimal places
        amount_pattern = r'^\d+(?:,\d{2,3})*(?:\.\d{1,2})?$'
        
        # Additional checks to avoid false positives
        if re.match(amount_pattern, line):
            # Must not contain letters or special characters (except commas and decimal)
            if re.search(r'[a-zA-Z]', line):
                return False
            # Must not contain slashes or other special characters
            if re.search(r'[/\\@#]', line):
                return False
            
            # Specific check for transaction IDs: reject pure numbers that are likely transaction IDs
            # Reject 5-digit numbers without formatting (like 57065)
            # Reject 9-digit numbers without formatting (like 770593868)
            # Reject very long numbers (10+ digits) that are clearly transaction IDs (like 202412220504)
            if ',' not in line and '.' not in line:
                if len(line) == 5 or len(line) == 9 or len(line) >= 10:  # 5-digit, 9-digit, or 10+ digit pure numbers are likely transaction IDs
                    return False
                
            return True
        
        return False
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        try:
            return float(amount_str.replace(',', ''))
        except ValueError:
            return None
    
    def _apply_balance_equation_logic(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply balance equation logic: Previous Balance + Credit - Debit = Next Balance
        to determine whether amounts are credits or debits
        """
        if not transactions:
            return transactions
        
        # Start with the first transaction (usually B/F with balance)
        current_balance = 0.0
        
        for i, tx in enumerate(transactions):
            # Skip B/F transactions as they set the initial balance
            if tx['mode'] == 'B/F' or tx['mode'] == '' and 'B/F' in tx['particulars']:
                current_balance = tx['balance']
                tx['deposits'] = 0.0
                tx['withdrawals'] = 0.0
                continue
            
            # For transactions with amounts, determine credit/debit using balance equation
            if tx['deposits'] > 0:  # Temporary assignment from parsing
                amount = tx['deposits']
                next_balance = tx['balance']
                
                # Calculate what the balance should be if this is a credit
                expected_balance_if_credit = current_balance + amount
                
                # Calculate what the balance should be if this is a debit
                expected_balance_if_debit = current_balance - amount
                
                # Check which calculation matches the actual next balance
                if abs(expected_balance_if_credit - next_balance) < 0.01:  # Credit
                    tx['deposits'] = amount
                    tx['withdrawals'] = 0.0
                elif abs(expected_balance_if_debit - next_balance) < 0.01:  # Debit
                    tx['deposits'] = 0.0
                    tx['withdrawals'] = amount
                else:
                    # If neither matches exactly, use the closer one
                    credit_diff = abs(expected_balance_if_credit - next_balance)
                    debit_diff = abs(expected_balance_if_debit - next_balance)
                    
                    if credit_diff < debit_diff:
                        tx['deposits'] = amount
                        tx['withdrawals'] = 0.0
                    else:
                        tx['deposits'] = 0.0
                        tx['withdrawals'] = amount
                
                # Update current balance for next transaction
                current_balance = next_balance
        
        return transactions
    
    def _validate_balance_equation(self, transactions: List[Dict[str, Any]]) -> bool:
        """
        Validate balance equation: Previous Balance + Credit - Debit = Next Balance
        Returns True if there are mismatches, False if all equations are satisfied
        """
        if not transactions:
            return False
        
        current_balance = 0.0
        mismatches = []
        
        for i, tx in enumerate(transactions):
            deposits = tx.get('deposits', 0.0)
            withdrawals = tx.get('withdrawals', 0.0)
            balance = tx.get('balance', 0.0)
            
            # Skip B/F transactions as they set the initial balance
            if tx.get('mode') == 'B/F' or (tx.get('mode') == '' and 'B/F' in tx.get('particulars', '')):
                current_balance = balance
                continue
            
            # Calculate expected balance using the equation
            expected_balance = current_balance + deposits - withdrawals
            difference = abs(expected_balance - balance)
            
            # Check if there's a mismatch (allow small floating point differences)
            if difference > 0.01:
                mismatches.append({
                    'transaction_index': i,
                    'date': tx.get('date', ''),
                    'expected_balance': expected_balance,
                    'actual_balance': balance,
                    'difference': difference,
                    'deposits': deposits,
                    'withdrawals': withdrawals,
                    'previous_balance': current_balance
                })
            
            # Update current balance for next transaction
            current_balance = balance
        
        # Log mismatches if any
        if mismatches:
            logger.warning(f"Found {len(mismatches)} balance mismatches in ICICI statement")
            for mismatch in mismatches[:5]:  # Log first 5 mismatches
                logger.warning(f"  Transaction {mismatch['transaction_index']+1} ({mismatch['date']}): "
                             f"Expected {mismatch['expected_balance']:.2f}, "
                             f"Actual {mismatch['actual_balance']:.2f}, "
                             f"Difference {mismatch['difference']:.2f}")
        else:
            logger.info("All balance equations satisfied - no mismatches found")
        
        return len(mismatches) > 0
    
    def format_transactions(self, extracted_text: str) -> Dict[str, Any]:
        """
        Format extracted text into clean transaction structure.
        
        Args:
            extracted_text: Raw extracted text from PDFs
            
        Returns:
            Dictionary containing formatted transactions and metadata
        """
        logger.info("Formatting ICICI transactions")
        
        # Parse transactions using existing logic
        transactions = self.parse_statement_format(extracted_text)
        
        if not transactions:
            logger.warning("No transactions found in ICICI statement")
            return {
                "bank_name": self.get_bank_name(),
                "success": False,
                "transactions": [],
                "total_transactions": 0,
                "formatted_at": datetime.now().isoformat(),
                "error": "No transactions found"
            }
        
        # Convert to clean format
        clean_transactions = []
        for tx in transactions:
            clean_tx = {
                'date': tx.get('date', ''),
                'mode': tx.get('mode', ''),
                'particulars': tx.get('particulars', ''),
                'deposits': tx.get('deposits', 0.0),
                'withdrawals': tx.get('withdrawals', 0.0),
                'balance': tx.get('balance', 0.0)
            }
            clean_transactions.append(clean_tx)
        
        logger.info(f"Formatted {len(clean_transactions)} ICICI transactions")
        
        return {
            "bank_name": self.get_bank_name(),
            "success": True,
            "transactions": clean_transactions,
            "total_transactions": len(clean_transactions),
            "formatted_at": datetime.now().isoformat()
        }
    
    def _extract_icici_mode(self, full_mode: str) -> str:
        """Extract clean mode from full ICICI mode string - only use specified keywords"""
        full_mode_upper = full_mode.upper()
        
        # Check for ONLY the specific ICICI mode keywords provided by user
        if 'MOBILE BANKING' in full_mode_upper:
            return 'MOBILE BANKING'
        elif 'ICICI ATM' in full_mode_upper:
            return 'ICICI ATM'
        elif 'BANK CHARGES' in full_mode_upper:
            return 'BANK CHARGES'
        elif 'CMS TRANSACTION' in full_mode_upper:
            return 'CMS TRANSACTION'
        elif 'CREDIT CARD' in full_mode_upper:
            return 'CREDIT CARD'
        else:
            # For all other cases, keep mode column blank
            return ''
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse ICICI date format (DD-MM-YYYY) to datetime object"""
        try:
            return datetime.strptime(date_str, '%d-%m-%Y')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%d-%m-%y')
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return datetime.min

