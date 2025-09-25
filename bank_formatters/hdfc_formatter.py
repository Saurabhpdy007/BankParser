#!/usr/bin/env python3
"""
{BRAND_NAME} HDFC Bank Formatter
===============================

A robust text formatter specifically designed for HDFC Bank statement processing.
Extracts and structures transaction data from HDFC Bank PDF statements.

Features:
- HDFC Bank-specific transaction parsing
- Multi-page bank statements with page boundaries
- Cross-page narration merging
- Transaction parsing with proper debit/credit assignment
- Statement summary filtering
- Chronological transaction sorting

Version: {BRAND_VERSION}
Author: {BRAND_AUTHOR}
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from brand_config import BRAND_NAME, BRAND_VERSION, BRAND_AUTHOR
from .base_formatter import BaseBankFormatter

# Format the docstring with brand config
__doc__ = __doc__.format(
    BRAND_NAME=BRAND_NAME,
    BRAND_VERSION=BRAND_VERSION,
    BRAND_AUTHOR=BRAND_AUTHOR
)

logger = logging.getLogger(__name__)


class TransactionFormatter(BaseBankFormatter):
    """
    HDFC Bank statement formatter.
    
    Formats extracted text into structured transaction data
    Specifically designed for HDFC bank statement format with page headers.
    Now includes balance equation validation for data quality assurance.
    """
    
    def __init__(self):
        """Initialize the HDFC transaction formatter"""
        super().__init__()
    
    def get_bank_name(self) -> str:
        """Return the bank name this formatter handles"""
        return "HDFC"
    
    def get_date_patterns(self) -> List[str]:
        """Return list of date patterns specific to HDFC bank"""
        return [
            r'\d{2}/\d{2}/\d{2}',  # DD/MM/YY (most common in bank statements)
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{1,2}/\d{1,2}/\d{2}',  # D/M/YY or DD/MM/YY
            r'\d{1,2}/\d{1,2}/\d{4}',  # D/M/YYYY or DD/MM/YYYY
        ]
    
    def get_amount_patterns(self) -> List[str]:
        """Return list of amount patterns specific to HDFC bank"""
        return [
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)',  # 1,000.00 or 1000.00
        ]
    
    def get_transaction_patterns(self) -> Dict[str, str]:
        """Return transaction patterns specific to HDFC bank"""
        return {
            "header_pattern": r'Transaction Date.*Narration.*Reference.*Amount.*Balance',
            "transaction_line": r'(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+(\d+)\s+([+-]?\d+(?:,\d{3})*(?:\.\d{2})?)\s+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            "page_end_pattern": r'Page No \.: \d+',
            "mode_types": r'(UPI|NEFT|IMPS|ATM|POS|TRANSFER|PAYMENT|CHEQUE|ECS|DD|RTGS)',
        }
    
    def validate_statement(self, extracted_text: str) -> bool:
        """Validate HDFC statement format"""
        hdfc_indicators = [
            "HDFC BANK",
            "HDFC Bank", 
            "HDFC",
            "Account Statement",
            "Statement of Account",
            "Transaction Date",
            "Narration",
            "Reference",
            "Amount",
            "Balance"
        ]
        
        text_upper = extracted_text.upper()
        return any(indicator.upper() in text_upper for indicator in hdfc_indicators)
    
    def parse_statement_format(self, extracted_text: str) -> List[Dict[str, Any]]:
        """
        Parse HDFC bank statement format.
        This method provides the same interface as the ICICI formatter.
        
        Args:
            extracted_text: Raw extracted text from PDFs
            
        Returns:
            List of parsed transaction dictionaries
        """
        return self.parse_bank_statement_format(extracted_text)
    
    def parse_bank_statement_format(self, extracted_text: str) -> List[Dict[str, Any]]:
        """
        Parse bank statement format with proper column structure
        Only processes data between "Page x" and "Page No .: x" markers
        
        Args:
            extracted_text: Raw extracted text from PDFs
            
        Returns:
            List of formatted transaction data
        """
        logger.info("Parsing bank statement format")
        
        transactions = []
        lines = extracted_text.split('\n')
        
        # Extract only transactional data between page markers
        transactional_data = self._extract_transactional_data(lines)
        
        if not transactional_data:
            logger.warning("No transactional data found between page markers")
            return transactions
        
        logger.info(f"Extracted {len(transactional_data)} lines of transactional data")
        
        # Find page sections within transactional data
        page_sections = self._split_into_pages(transactional_data)
        
        # Process pages and merge continuation text across page boundaries
        for page_num, page_lines in page_sections.items():
            logger.info(f"Processing page {page_num} with {len(page_lines)} lines")
            
            if page_num == 1:
                # Page 1 has headers, find data start
                data_start_idx = self._find_data_start_page1(page_lines)
                if data_start_idx is not None:
                    page_transactions = self._parse_page_transactions(page_lines[data_start_idx:])
                    transactions.extend(page_transactions)
            else:
                # Page 2+ has direct data
                page_transactions = self._parse_page_transactions(page_lines)
                transactions.extend(page_transactions)
        
        # Post-process to merge continuation text across page boundaries
        transactions = self._merge_page_boundary_continuations_precise(transactions, transactional_data)
        
        # Sort transactions by date (oldest first) - BEFORE balance correction
        transactions = self._sort_transactions_by_date(transactions)
        
        # Post-process to filter out statement summary content
        transactions = self._filter_statement_summary_content(transactions)
        
        # Post-process to correct debit/credit amounts based on balance changes
        transactions = self._correct_debit_credit_amounts(transactions)
        
        logger.info(f"Parsed {len(transactions)} transactions from bank statement")
        return transactions
    
    def _extract_transactional_data(self, lines: List[str]) -> List[str]:
        """
        Extract only transactional data between "--- Page x ---" and "Page No .: x" markers
        
        Args:
            lines: All lines from extracted text
            
        Returns:
            List of lines containing only transactional data
        """
        transactional_data = []
        in_transactional_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check for start of transactional section (e.g., "--- Page 1 ---")
            if re.match(r'^--- Page \d+ ---$', line):
                in_transactional_section = True
                transactional_data.append(line)
                logger.debug(f"Found start of transactional section: {line}")
                continue
            
            # Check for end of transactional section (e.g., "Page No .: 1")
            if re.match(r'^Page No \.: \d+$', line):
                in_transactional_section = False
                transactional_data.append(line)
                logger.debug(f"Found end of transactional section: {line}")
                continue
            
            # Only include lines that are within transactional sections
            if in_transactional_section:
                transactional_data.append(line)
        
        logger.info(f"Extracted {len(transactional_data)} lines of transactional data")
        return transactional_data
    
    def _merge_page_boundary_continuations_precise(self, transactions: List[Dict[str, Any]], transactional_data: List[str]) -> List[Dict[str, Any]]:
        """
        Precise logic: Map each page boundary to the transaction that was parsed just before it
        
        Args:
            transactions: List of parsed transactions
            transactional_data: Raw transactional data lines
            
        Returns:
            Updated transactions with continuation text merged
        """
        if not transactions or not transactional_data:
            return transactions
        
        # Find all page markers and page boundaries
        page_markers = []
        page_boundaries = []
        
        for i, line in enumerate(transactional_data):
            if line.strip().startswith('--- Page'):
                page_markers.append(i)
            elif re.match(r'Page No \.: \d+', line.strip()):
                page_boundaries.append(i)
        
        logger.info(f"Found {len(page_markers)} page markers and {len(page_boundaries)} page boundaries")
        
        # Process all transactions that have "Page No .:" in their narration
        for transaction in transactions:
            narration = transaction.get('narration', '')
            if 'Page No .:' in narration:
                # Extract the page number from the narration
                page_match = re.search(r'Page No \.: (\d+)', narration)
                if page_match:
                    page_num = int(page_match.group(1))
                    
                    # Find the continuation text for this page
                    continuation_text = self._find_continuation_text_for_page(page_num, transactional_data)
                    
                    # Always remove the page number from narration
                    clean_narration = re.sub(r'Page No \.: \d+', '', narration).strip()
                    
                    if continuation_text:
                        # Merge continuation text
                        merged_narration = f"{clean_narration} {continuation_text}".strip()
                        transaction['narration'] = merged_narration
                        logger.info(f"Merged continuation text for page {page_num}: {continuation_text}")
                    else:
                        # Just remove the page number
                        transaction['narration'] = clean_narration
                        logger.info(f"Removed page number from page {page_num} (no continuation text)")
        
        return transactions
    
    def _filter_statement_summary_content(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out statement summary content from transaction narrations
        """
        logger.info("Filtering out statement summary content from transactions")
        
        for transaction in transactions:
            narration = transaction.get('narration', '')
            
            # Check if narration contains statement summary content
            if 'STATEMENT SUMMARY' in narration:
                # Extract only the transaction part (before STATEMENT SUMMARY)
                clean_narration = narration.split('STATEMENT SUMMARY')[0].strip()
                transaction['narration'] = clean_narration
                logger.info(f"Filtered statement summary from transaction: {clean_narration[:50]}...")
            
            # Also filter out other common statement footer content
            elif any(keyword in narration for keyword in ['Generated On:', 'Generated By:', 'Requesting Branch Code:', 'This is a computer generated statement']):
                # Find the last meaningful part of the narration
                lines = narration.split()
                meaningful_parts = []
                
                for part in lines:
                    if any(keyword in part for keyword in ['Generated', 'Requesting', 'This', 'computer', 'generated', 'statement', 'signature']):
                        break
                    meaningful_parts.append(part)
                
                if meaningful_parts:
                    clean_narration = ' '.join(meaningful_parts).strip()
                    transaction['narration'] = clean_narration
                    logger.info(f"Filtered statement footer from transaction: {clean_narration[:50]}...")
        
        return transactions
    
    def _find_continuation_text_for_page(self, page_num: int, transactional_data: List[str]) -> str:
        """
        Find continuation text for a specific page number
        """
        # Find the page marker for the next page
        next_page_marker = None
        for i, line in enumerate(transactional_data):
            if line.strip() == f'--- Page {page_num + 1} ---':
                next_page_marker = i
                break
        
        if next_page_marker is None:
            return ""
        
        # Find all continuation lines after the page marker
        continuation_lines = []
        next_line_idx = next_page_marker + 1
        
        while next_line_idx < len(transactional_data):
            line = transactional_data[next_line_idx].strip()
            
            # Skip empty lines
            if not line:
                next_line_idx += 1
                continue
            
            # Check if this line starts with a date (new transaction) or text (continuation)
            is_date = re.match(r'\d{2}/\d{2}/\d{2}', line)
            
            if is_date:
                # We've hit a new transaction, stop collecting continuation text
                break
            else:
                # This is continuation text
                continuation_lines.append(line)
                next_line_idx += 1
        
        return ' '.join(continuation_lines).strip()
    
    def _find_last_transaction_before_boundary(self, transactions: List[Dict[str, Any]], boundary_idx: int, transactional_data: List[str]) -> Optional[int]:
        """
        Find the index of the last transaction before a page boundary
        """
        # Look for transactions that have "Page No .: 1" in their narration
        # These are the transactions that need continuation text merged
        
        for i, transaction in enumerate(transactions):
            narration = transaction.get('narration', '')
            
            # Check if this transaction has "Page No .: 1" in its narration
            if 'Page No .: 1' in narration:
                return i
        
        return None
    
    def _extract_continuation_text_after_boundary(self, transactional_data: List[str], boundary_idx: int) -> Optional[str]:
        """
        Extract continuation text after a page boundary
        """
        # Look for the next page marker
        next_page_start = None
        for i in range(boundary_idx + 1, len(transactional_data)):
            if transactional_data[i].strip().startswith('--- Page'):
                next_page_start = i
                break
        
        if next_page_start is None:
            return None
        
        # Extract lines between page boundary and next page start
        continuation_lines = []
        for i in range(boundary_idx + 1, next_page_start):
            line = transactional_data[i].strip()
            if line and not line.startswith('--- Page'):
                continuation_lines.append(line)
        
        # Also check for continuation text right after the next page marker
        # Look for the first few lines after the page marker that might be continuation
        for i in range(next_page_start + 1, min(next_page_start + 5, len(transactional_data))):
            line = transactional_data[i].strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this looks like continuation text
            # Continuation text typically:
            # 1. Doesn't start with a date pattern
            # 2. Doesn't start with transaction keywords
            # 3. Is relatively short
            # 4. Doesn't look like a reference number
            
            is_date = re.match(r'\d{2}/\d{2}/\d{2}', line)
            is_reference = re.match(r'\d{10,}', line)
            is_transaction_keyword = line.startswith(('UPI', 'NEFT', 'IMPS', 'ATM', 'CHEQUE', 'TRANSFER'))
            is_amount = re.match(r'^\d+(?:,\d{3})*(?:\.\d{2})?$', line)
            is_header = line in ['Date', 'Narration', 'Chq./Ref.No.', 'Value Dt', 'Withdrawal Amt.', 'Deposit Amt.', 'Closing Balance']
            
            if not (is_date or is_reference or is_transaction_keyword or is_amount or is_header):
                # This might be continuation text
                continuation_lines.append(line)
            else:
                # We've hit actual transaction data, stop looking
                break
        
        if continuation_lines:
            return ' '.join(continuation_lines).strip()
        
        return None
    
    def _merge_continuation_text_from_raw(self, existing_transactions: List[Dict[str, Any]], page_lines: List[str], page_num: int) -> List[Dict[str, Any]]:
        """
        Merge continuation text from the start of a new page with the last transaction of the previous page
        Uses raw page lines to detect continuation text
        
        Args:
            existing_transactions: Transactions from previous pages
            page_lines: Raw lines from current page
            page_num: Current page number
            
        Returns:
            Updated transactions with continuation text merged
        """
        if not existing_transactions or not page_lines:
            return []
        
        # Get the last transaction from previous page
        last_transaction = existing_transactions[-1]
        
        # Look for continuation text at the start of the new page
        continuation_lines = []
        i = 0
        
        # Skip the page marker if present
        if page_lines and page_lines[0].strip().startswith('--- Page'):
            i = 1
        
        # Check the first few lines for continuation text
        # Be very conservative - only look for obvious continuation patterns
        while i < len(page_lines) and i < 2:  # Check only first 2 lines max
            line = page_lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Very strict criteria for continuation text:
            # 1. Must be short (less than 30 chars)
            # 2. Must not start with date, reference, transaction keywords
            # 3. Must not be headers
            # 4. Must not contain @ symbol (likely UPI ID)
            # 5. Must not contain numbers that look like amounts
            
            is_date = re.match(r'\d{2}/\d{2}/\d{2}', line)
            is_reference = re.match(r'\d{10,}', line)
            is_transaction_keyword = line.startswith(('UPI', 'NEFT', 'IMPS', 'ATM', 'CHEQUE', 'TRANSFER'))
            is_amount = re.match(r'^\d+(?:,\d{3})*(?:\.\d{2})?$', line)
            is_header = line in ['Date', 'Narration', 'Chq./Ref.No.', 'Value Dt', 'Withdrawal Amt.', 'Deposit Amt.', 'Closing Balance']
            is_long_text = len(line) > 30
            has_at_symbol = '@' in line
            has_upi_pattern = re.search(r'@[A-Z]+', line)
            
            if (not (is_date or is_reference or is_transaction_keyword or is_amount or is_header or is_long_text or has_at_symbol or has_upi_pattern) and
                len(line) > 0):
                # This might be continuation text
                continuation_lines.append(line)
                logger.debug(f"Found potential continuation text: {line}")
            else:
                # We've hit actual transaction data, stop looking
                break
            
            i += 1
        
        # If we found continuation text, merge it with the last transaction
        if continuation_lines:
            continuation_text = ' '.join(continuation_lines).strip()
            last_narration = last_transaction.get('narration', '')
            merged_narration = f"{last_narration} {continuation_text}".strip()
            last_transaction['narration'] = merged_narration
            
            logger.info(f"Merged continuation text from page {page_num}: {continuation_text}")
            
            # Return the page lines with continuation text removed
            return page_lines[i:]
        
        return page_lines
    
    def _split_into_pages(self, lines: List[str]) -> Dict[int, List[str]]:
        """Split text into page sections"""
        pages = {}
        current_page = 0
        current_lines = []
        
        for line in lines:
            if line.strip().startswith('--- Page'):
                # Save current page if it has content
                if current_lines:
                    pages[current_page] = current_lines
                # Start new page
                current_page += 1
                current_lines = []
                # Include the page marker in the new page
                current_lines.append(line)
            else:
                current_lines.append(line)
        
        if current_lines:
            pages[current_page] = current_lines
        
        return pages
    
    def _find_data_start_page1(self, lines: List[str]) -> Optional[int]:
        """Find where transaction data starts on page 1 (after headers)"""
        # Skip header lines and find first actual transaction date
        for i, line in enumerate(lines):
            line = line.strip()
            # Skip header lines
            if line in ["Date", "Narration", "Chq./Ref.No.", "Value Dt", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"]:
                continue
            # Look for first date pattern after headers
            if re.match(r'\d{2}/\d{2}/\d{2}', line):
                return i
        return None
    
    def _parse_page_transactions(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse transactions from a page using a precise approach"""
        transactions = []
        
        # Skip headers and get to actual data
        clean_lines = []
        skip_headers = True
        
        # Check if headers are already skipped (look for first date in first few lines)
        for line in lines[:10]:  # Check first 10 lines (increased from 5)
            if re.match(r'\d{2}/\d{2}/\d{2}', line.strip()):
                skip_headers = False
                break
        
        for line in lines:
            if line.strip() == 'Closing Balance':
                skip_headers = False
                continue
            if not skip_headers:
                clean_lines.append(line.strip())
        
        # Parse transactions using a more precise method
        i = 0
        while i < len(clean_lines):
            line = clean_lines[i]
            
            # Look for transaction start (date pattern)
            if re.match(r'\d{2}/\d{2}/\d{2}', line):
                # Check if this date is actually the start of a new transaction
                # by looking ahead to see if it's followed by narration or reference
                is_transaction_start = False
                
                # Look ahead a few lines to determine if this is a transaction start
                for j in range(i + 1, min(len(clean_lines), i + 5)):
                    if j < len(clean_lines):
                        next_line = clean_lines[j]
                        # If we see a reference number, narration, or amount, it's likely a transaction start
                        if (re.match(r'\d{10,}', next_line) or  # Pure digit reference number
                            re.match(r'^[A-Z0-9]{10,}$', next_line) or  # Alphanumeric reference number
                            len(next_line) > 10 or  # Long narration
                            re.match(r'^-?\d+(?:,\d{3})*(?:\.\d{2})?$', next_line)):  # Amount (including negative)
                            is_transaction_start = True
                            break
                
                if is_transaction_start:
                    transaction = self._parse_single_transaction_fixed(clean_lines, i)
                    if transaction:
                        transactions.append(transaction)
                        # Move to next transaction - find the next date that's not part of current transaction
                        i = self._find_next_transaction_start_fixed(clean_lines, i)
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
        
        return transactions
    
    def _parse_single_transaction_fixed(self, lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
        """Parse a single transaction with fixed additional info handling"""
        try:
            if start_idx >= len(lines):
                return None
            
            # Expected structure:
            # Date, Narration (1-2 lines), Ref.No., Value Date, Amount1, Amount2, Additional info
            
            transaction_date = lines[start_idx]
            narration_lines = []
            ref_no = ""
            value_date = ""
            amounts = []
            additional_info = []
            
            # Check if transaction date line contains narration (e.g., "01/03/25 UPI-MAHENDARBAHETIOKICIC-MAHENDAR.BAHETI")
            if re.match(r'\d{2}/\d{2}/\d{2}', transaction_date) and len(transaction_date) > 10:
                # Extract narration part after the date
                narration_part = transaction_date[8:].strip()  # Skip "01/03/25 " (8 characters)
                if narration_part:
                    narration_lines.append(narration_part)
                # Clean transaction date to just the date part
                transaction_date = transaction_date[:8].strip()
            
            i = start_idx + 1
            
            # Parse narration (until we hit a reference number)
            while i < len(lines):
                line = lines[i]
                # Check if this is a reference number (10+ digits or alphanumeric)
                if (re.match(r'\d{10,}', line) or  # Pure digits
                    re.match(r'^[A-Z0-9]{10,}$', line)):  # Alphanumeric (like ICICN22025030316)
                    ref_no = line
                    # If left 8 chars look like DD/MM/YY, strip them per rule
                    if len(ref_no) >= 8 and re.match(r'^\d{2}/\d{2}/\d{2}', ref_no[:8]):
                        ref_no = ref_no[8:].strip()
                    i += 1
                    break
                
                # Handle combined reference + value date on the same line
                combined_match = re.match(r'^([A-Z0-9]{10,})\s+(\d{2}/\d{2}/\d{2,4})$', line)
                if combined_match:
                    ref_no = combined_match.group(1)
                    value_date = combined_match.group(2)
                    i += 1
                    break
                else:
                    # Check if this line contains both date and narration (e.g., "01/03/25 UPI-...")
                    if re.match(r'\d{2}/\d{2}/\d{2}', line) and len(line) > 10:
                        # Extract narration part after the date
                        narration_part = line[8:].strip()  # Skip "01/03/25 " (8 characters)
                        if narration_part:
                            narration_lines.append(narration_part)
                    else:
                        # Add narration lines (skip lines that are just amounts or dates)
                        # Also skip lines that are just reference numbers or page markers
                        if (not re.match(r'^-?\d+(?:,\d{3})*(?:\.\d{2})?$', line) and 
                            not re.match(r'^\d{2}/\d{2}/\d{2}$', line) and
                            not re.match(r'^\d{10,}$', line) and
                            not line.strip().startswith('Page No .:') and
                            not line.strip().startswith('--- Page')):
                            narration_lines.append(line)
                    i += 1
            
            # Get value date (should be next line after reference)
            # Skip any additional reference numbers first
            while i < len(lines) and not value_date:
                line = lines[i]
                # If we hit a date, that's our value date
                if re.match(r'\d{2}/\d{2}/\d{2}', line):
                    value_date = line
                    i += 1
                    break
                # If this line has combined reference + value date, take the date and continue
                combined_match2 = re.match(r'^([A-Z0-9]{10,})\s+(\d{2}/\d{2}/\d{2,4})$', line)
                if combined_match2:
                    # Keep existing ref if present; otherwise set from this line
                    if not ref_no:
                        ref_no = combined_match2.group(1)
                    value_date = combined_match2.group(2)
                    i += 1
                    break
                # If we hit another reference number, skip it
                elif (re.match(r'\d{10,}', line) or  # Pure digits
                      re.match(r'^[A-Z0-9]{10,}$', line)):  # Alphanumeric
                    i += 1
                    continue
                else:
                    # Not a date or reference, might be value date
                    break
            
            # If we didn't find a value date, use transaction date
            if not value_date:
                value_date = transaction_date
            
            # Parse amounts (next two lines should be amounts)
            while i < len(lines):
                line = lines[i]
                # Look for amount patterns - only match pure amounts (not mixed with text)
                if re.match(r'^-?\d+(?:,\d{3})*(?:\.\d{2})?$', line):
                    amount_str = line.replace(',', '')
                    try:
                        amounts.append(float(amount_str))
                    except ValueError:
                        pass
                    i += 1
                else:
                    # If we hit a date, we've reached the next transaction
                    if re.match(r'\d{2}/\d{2}/\d{2}', line):
                        break
                    # If we hit additional info, collect it
                    if line.strip() and not re.match(r'^-?\d+(?:,\d{3})*(?:\.\d{2})?$', line):
                        additional_info.append(line.strip())
                    i += 1
            
            # Collect any remaining additional info after amounts (until next transaction)
            while i < len(lines):
                line = lines[i]
                # If we hit a date, we've reached the next transaction
                if re.match(r'\d{2}/\d{2}/\d{2}', line):
                    break
                # Collect additional info lines that don't look like amounts
                if line.strip() and not re.match(r'^-?\d+(?:,\d{3})*(?:\.\d{2})?$', line):
                    additional_info.append(line.strip())
                i += 1
            
            # Create transaction with merged narration and additional info
            narration = ' '.join(narration_lines).strip()
            if additional_info:
                additional_text = ' '.join(additional_info).strip()
                if narration:
                    narration = f"{narration} {additional_text}"
                else:
                    narration = additional_text
            
            if not narration:
                narration = "Transaction"
            
            # Determine debit/credit amounts
            debit_amount = 0
            credit_amount = 0
            closing_balance = 0
            
            if len(amounts) >= 2:
                # First amount is transaction amount, second is closing balance
                transaction_amount = amounts[0]
                closing_balance = amounts[1]
                
                # Handle negative amounts: negative amounts are debit reversals
                if transaction_amount < 0:
                    # Negative amount is a debit reversal
                    debit_amount = transaction_amount  # Keep as negative
                    credit_amount = 0
                else:
                    # Determine if debit or credit based on narration
                    narration_lower = narration.lower()
                    if any(word in narration_lower for word in ['upi', 'payment', 'withdrawal', 'debit', 'atm', 'neft', 'imps']):
                        debit_amount = transaction_amount
                    else:
                        credit_amount = transaction_amount
            
            # Normalize cheque reference by removing any embedded date tokens
            if ref_no:
                # Remove exact value_date if embedded
                if value_date and value_date in ref_no:
                    ref_no = ref_no.replace(value_date, '').strip()
                # Remove a trailing date token if present (DD/MM/YY or DD/MM/YYYY)
                ref_no = re.sub(r'\s*\d{2}/\d{2}/\d{2,4}$', '', ref_no).strip()
                # Remove a leading date token if present (DD/MM/YY)
                if len(ref_no) >= 8 and re.match(r'^\d{2}/\d{2}/\d{2}', ref_no[:8]):
                    ref_no = ref_no[8:].strip()

            transaction = {
                "transaction_date": transaction_date,
                "narration": narration,
                "cheque_reference": ref_no,
                "value_date": value_date or transaction_date,
                "debit_amount": debit_amount,
                "credit_amount": credit_amount,
                "closing_balance": closing_balance
            }
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error parsing transaction at index {start_idx}: {str(e)}")
            return None
    
    def _find_next_transaction_start(self, lines: List[str], current_idx: int) -> int:
        """Find the start of the next transaction"""
        for i in range(current_idx + 1, len(lines)):
            if re.match(r'\d{2}/\d{2}/\d{2}', lines[i]):
                return i
        return len(lines)
    
    def _find_next_transaction_start_fixed(self, lines: List[str], current_idx: int) -> int:
        """Find the start of the next transaction, accounting for additional info"""
        # Start from current transaction and find where it ends
        i = current_idx + 1
        
        # Skip narration lines until we find a reference number
        while i < len(lines):
            line = lines[i]
            # Reference numbers can be pure digits or alphanumeric (like ICICN22025030316)
            if (re.match(r'\d{10,}', line) or  # Pure digits
                re.match(r'^[A-Z0-9]{10,}$', line)):  # Alphanumeric (like ICICN22025030316)
                i += 1
                break
            i += 1
        
        # Skip value date
        if i < len(lines) and re.match(r'\d{2}/\d{2}/\d{2}', lines[i]):
            i += 1
        
        # Skip amounts (look for 2 consecutive amount patterns)
        amount_count = 0
        while i < len(lines):
            line = lines[i]
            if re.match(r'^-?\d+(?:,\d{3})*(?:\.\d{2})?$', line):
                amount_count += 1
                i += 1
                # If we've found 2 amounts, we're likely done with this transaction
                if amount_count >= 2:
                    break
            else:
                break
        
        # Skip additional info until we hit a date that looks like a new transaction
        while i < len(lines):
            line = lines[i]
            # If we hit a date, check if it looks like a new transaction
            if re.match(r'\d{2}/\d{2}/\d{2}', line):
                # Check if this date is followed by narration (not just a value date)
                # Look ahead a few lines to see if this is a new transaction
                is_new_transaction = False
                for j in range(i + 1, min(len(lines), i + 5)):
                    if j < len(lines):
                        next_line = lines[j]
                        # If we see a reference number or narration after the date, it's a new transaction
                        if (re.match(r'\d{10,}', next_line) or  # Pure digit reference number
                            re.match(r'^[A-Z0-9]{10,}$', next_line) or  # Alphanumeric reference number
                            (len(next_line) > 10 and not re.match(r'^-?\d+(?:,\d{3})*(?:\.\d{2})?$', next_line))):
                            is_new_transaction = True
                            break
                
                if is_new_transaction:
                    return i
            i += 1
        
        return len(lines)
    
    def format_transaction_data(self, extracted_text: str) -> Dict[str, Any]:
        """
        Format extracted text into transaction JSON structure
        Uses the new bank statement parser
        
        Args:
            extracted_text: Raw extracted text from PDFs
            
        Returns:
            Formatted transaction data
        """
        logger.info("Formatting extracted text into transaction structure")
        
        # Use the new bank statement parser
        transactions = self.parse_bank_statement_format(extracted_text)
        
        if not transactions:
            # Fallback to old method if no transactions found
            return self._fallback_formatting(extracted_text)
        
        # Return first transaction for single transaction format
        if len(transactions) == 1:
            return transactions[0]
        
        # For multiple transactions, return the first one as primary
        # (this maintains backward compatibility)
        return transactions[0]
    
    def format_multiple_transactions(self, extracted_text: str) -> List[Dict[str, Any]]:
        """
        Format extracted text into multiple transaction structures
        Uses the new bank statement parser
        
        Args:
            extracted_text: Raw extracted text from PDFs
            
        Returns:
            List of formatted transaction data
        """
        logger.info("Formatting extracted text into multiple transaction structures")
        
        # Use the new bank statement parser
        transactions = self.parse_bank_statement_format(extracted_text)
        
        if not transactions:
            # Fallback to old method if no transactions found
            logger.warning("No transactions found with new parser, using fallback")
            return [self._fallback_formatting(extracted_text)]
        
        logger.info(f"Formatted {len(transactions)} transactions")
        return transactions
    
    def _fallback_formatting(self, extracted_text: str) -> Dict[str, Any]:
        """
        Fallback formatting method for when bank statement parser fails
        
        Args:
            extracted_text: Raw extracted text from PDFs
            
        Returns:
            Formatted transaction data
        """
        logger.info("Using fallback formatting method")
        
        # Extract components using old method
        dates = self.extract_dates(extracted_text)
        amounts = self.extract_amounts(extracted_text)
        upi_info = self.extract_upi_info(extracted_text)
        reference = self.extract_reference(extracted_text)
        narration = self.extract_narration(extracted_text)
        
        # Use current date if no date found
        transaction_date = dates[0] if dates else datetime.now().strftime("%Y-%m-%d")
        value_date = dates[1] if len(dates) > 1 else transaction_date
        
        # Normalize cheque reference by removing a leading DD/MM/YY if present
        if reference:
            # Remove exact value_date if embedded
            if value_date and value_date in reference:
                reference = reference.replace(value_date, '').strip()
            # Remove a trailing date token (DD/MM/YY or DD/MM/YYYY)
            reference = re.sub(r'\s*\d{2}/\d{2}/\d{2,4}$', '', reference).strip()
            # Remove a leading date token (DD/MM/YY)
            if len(reference) >= 8 and re.match(r'^\d{2}/\d{2}/\d{2}', reference[:8]):
                reference = reference[8:].strip()
        
        # Determine debit/credit amounts
        debit_amount = 0
        credit_amount = 0
        closing_balance = 0
        
        if amounts:
            # Simple logic: assume largest amount is closing balance
            closing_balance = max(amounts)
            
            # Look for debit/credit indicators in text
            text_lower = extracted_text.lower()
            if any(word in text_lower for word in ['debit', 'withdrawal', 'payment', 'paid']):
                debit_amount = closing_balance
            elif any(word in text_lower for word in ['credit', 'deposit', 'received', 'income']):
                credit_amount = closing_balance
            else:
                # Default assumption
                credit_amount = closing_balance
        
        # Format UPI narration
        if upi_info:
            narration = f"UPI-{upi_info} {narration}"
        
        # Create transaction structure
        transaction_data = {
            "transaction_date": transaction_date,
            "narration": narration,
            "cheque_reference": reference or "N/A",
            "value_date": value_date,
            "debit_amount": debit_amount,
            "credit_amount": credit_amount,
            "closing_balance": closing_balance
        }
        
        logger.info(f"Fallback formatted transaction data: {transaction_data}")
        return transaction_data
    
    def extract_dates(self, text: str) -> List[str]:
        """
        Extract dates from text
        
        Args:
            text: Input text
            
        Returns:
            List of found dates
        """
        dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        # Remove duplicates and sort
        return sorted(list(set(dates)))
    
    def extract_amounts(self, text: str) -> List[float]:
        """
        Extract monetary amounts from text
        
        Args:
            text: Input text
            
        Returns:
            List of found amounts
        """
        amounts = []
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean the amount string
                    clean_amount = match.replace(',', '').replace('₹', '').replace('Rs.', '').strip()
                    amount = float(clean_amount)
                    amounts.append(amount)
                except ValueError:
                    continue
        
        # Remove duplicates and sort
        return sorted(list(set(amounts)))
    
    def extract_upi_info(self, text: str) -> Optional[str]:
        """
        Extract UPI information from text
        
        Args:
            text: Input text
            
        Returns:
            UPI ID if found, None otherwise
        """
        upi_patterns = [
            r'UPI[-\s]*([A-Za-z0-9@.-]+)',
            r'UPI\s+([A-Za-z0-9@.-]+)',
            r'([A-Za-z0-9@.-]+)@[A-Za-z]+',  # UPI ID pattern
        ]
        
        for pattern in upi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_reference(self, text: str) -> Optional[str]:
        """
        Extract reference/transaction number from text
        
        Args:
            text: Input text
            
        Returns:
            Reference number if found, None otherwise
        """
        reference_patterns = [
            r'Ref[:\s]*(\d+)',
            r'Reference[:\s]*(\d+)',
            r'Txn[:\s]*(\d+)',
            r'Transaction[:\s]*(\d+)',
            r'(\d{10,})',  # 10+ digit numbers
        ]
        
        for pattern in reference_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_narration(self, text: str) -> str:
        """
        Extract transaction narration/description
        
        Args:
            text: Input text
            
        Returns:
            Cleaned narration text
        """
        # Remove common prefixes and clean up
        narration = text.strip()
        
        # Remove date patterns
        for pattern in self.date_patterns:
            narration = re.sub(pattern, '', narration)
        
        # Remove amount patterns
        for pattern in self.amount_patterns:
            narration = re.sub(pattern, '', narration, flags=re.IGNORECASE)
        
        # Remove reference patterns
        reference_patterns = [
            r'Ref[:\s]*(\d+)',
            r'Reference[:\s]*(\d+)',
            r'Txn[:\s]*(\d+)',
            r'Transaction[:\s]*(\d+)',
            r'(\d{10,})',  # 10+ digit numbers
        ]
        for pattern in reference_patterns:
            narration = re.sub(pattern, '', narration, flags=re.IGNORECASE)
        
        # Clean up extra spaces and special characters
        narration = re.sub(r'\s+', ' ', narration)
        narration = re.sub(r'[^\w\s-]', '', narration)
        narration = narration.strip()
        
        return narration if narration else "Transaction"
    
    def process_comprehensive_file(self, comprehensive_file_path: str) -> Dict[str, Any]:
        """
        Process a comprehensive extracted data file and add formatted transactions
        
        Args:
            comprehensive_file_path: Path to the comprehensive JSON file
            
        Returns:
            Updated comprehensive data with formatted transactions
        """
        logger.info(f"Processing comprehensive file: {comprehensive_file_path}")
        
        # Load the comprehensive file
        with open(comprehensive_file_path, 'r', encoding='utf-8') as f:
            comprehensive_data = json.load(f)
        
        # Extract text content
        all_text = comprehensive_data.get('all_extracted_text', '')
        
        if not all_text:
            logger.warning("No extracted text found in comprehensive file")
            return comprehensive_data
        
        # Format transactions
        try:
            # Try to format as multiple transactions first
            formatted_transactions = self.format_multiple_transactions(all_text)
            
            # If only one transaction or multiple transactions found
            if len(formatted_transactions) == 1:
                comprehensive_data['formatted_transaction'] = formatted_transactions[0]
            else:
                comprehensive_data['formatted_transactions'] = formatted_transactions
            
            # Add formatting metadata
            comprehensive_data['formatting_info'] = {
                "formatted_at": datetime.now().isoformat(),
                "total_transactions_formatted": len(formatted_transactions),
                "text_length_processed": len(all_text),
                "formatter_version": "2.5"
            }
            
            logger.info(f"Successfully formatted {len(formatted_transactions)} transactions")
            
        except Exception as e:
            logger.error(f"Error formatting transactions: {str(e)}")
            comprehensive_data['formatting_error'] = str(e)
        
        return comprehensive_data
    
    def save_formatted_file(self, comprehensive_file_path: str, output_path: Optional[str] = None) -> str:
        """
        Process comprehensive file and save with formatted transactions
        
        Args:
            comprehensive_file_path: Path to input comprehensive file
            output_path: Optional output path (defaults to same location with _formatted suffix)
            
        Returns:
            Path to the saved formatted file
        """
        # Process the file
        formatted_data = self.process_comprehensive_file(comprehensive_file_path)
        
        # Determine output path
        if output_path is None:
            input_path = Path(comprehensive_file_path)
            output_path = str(input_path.parent / f"{input_path.stem}_formatted{input_path.suffix}")
        
        # Extract only the formatted transactions for clean output
        clean_transactions = []
        
        # Get formatted transactions
        if 'formatted_transactions' in formatted_data:
            clean_transactions = formatted_data['formatted_transactions']
        elif 'formatted_transaction' in formatted_data:
            clean_transactions = [formatted_data['formatted_transaction']]
        
        # Save clean transactions-only file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(clean_transactions, f, indent=2, ensure_ascii=False)
        
        # Also generate CSV output
        csv_path = self.save_csv_file(comprehensive_file_path, clean_transactions)
        
        logger.info(f"Saved clean formatted file: {output_path}")
        logger.info(f"Generated CSV file: {csv_path}")
        return output_path
    
    def save_csv_file(self, comprehensive_file_path: str, transactions: List[Dict[str, Any]]) -> str:
        """
        Create a CSV file from the formatted transactions
        
        Args:
            comprehensive_file_path: Path to the comprehensive JSON file (for naming)
            transactions: List of formatted transactions
            
        Returns:
            Path to the generated CSV file
        """
        import csv
        
        # Generate CSV output path
        input_path = Path(comprehensive_file_path)
        csv_path = str(input_path.parent / f"{input_path.stem}_formatted.csv")
        
        # Define CSV headers
        headers = [
            'transaction_date',
            'narration', 
            'chq./Ref.No.',
            'value_date',
            'debit_amount',
            'credit_amount',
            'closing_balance'
        ]
        
        # Write CSV file
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for transaction in transactions:
                # Clean the transaction data for CSV
                csv_row = {}
                for header in headers:
                    # Map cheque/reference special header from internal key
                    if header == 'chq./Ref.No.':
                        value = transaction.get('cheque_reference', '')
                    else:
                        value = transaction.get(header, '')
                    # Convert None to empty string and format numbers
                    if value is None:
                        csv_row[header] = ''
                    elif header in ['debit_amount', 'credit_amount', 'closing_balance']:
                        # Format numbers properly
                        csv_row[header] = value if value else 0
                    else:
                        csv_row[header] = str(value)
                
                writer.writerow(csv_row)
        
        logger.info(f"Generated CSV file with {len(transactions)} transactions: {csv_path}")
        return csv_path
    
    def _correct_debit_credit_amounts(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Correct debit/credit amounts based on balance changes
        
        Logic:
        - If balance increases → Amount should be CREDIT
        - If balance decreases → Amount should be DEBIT
        
        Args:
            transactions: List of parsed transactions
            
        Returns:
            Updated transactions with correct debit/credit amounts
        """
        if not transactions:
            return transactions
        
        logger.info("Correcting debit/credit amounts based on balance changes")
        
        for i, transaction in enumerate(transactions):
            current_balance = transaction.get('closing_balance', 0)
            previous_balance = transactions[i-1].get('closing_balance', 0) if i > 0 else 0
            
            # Calculate balance change
            balance_change = current_balance - previous_balance
            
            # Get current amounts
            current_debit = transaction.get('debit_amount', 0)
            current_credit = transaction.get('credit_amount', 0)
            
            # Determine the actual amount (either debit or credit should be non-zero)
            actual_amount = current_debit if current_debit != 0 else current_credit
            
            if actual_amount != 0:
                # Only correct if the current assignment doesn't match the balance change
                
                # Check if current assignment matches balance change
                if balance_change > 0 and current_credit > 0:
                    # Balance increased and currently credit - correct
                    logger.debug(f"Transaction {i+1}: Already correctly assigned as credit (balance increased by {balance_change})")
                elif balance_change < 0 and current_debit > 0:
                    # Balance decreased and currently debit - correct
                    logger.debug(f"Transaction {i+1}: Already correctly assigned as debit (balance decreased by {abs(balance_change)})")
                elif balance_change > 0 and current_debit > 0:
                    # Balance increased but currently debit - needs correction
                    transaction['debit_amount'] = 0
                    transaction['credit_amount'] = abs(actual_amount)
                    logger.debug(f"Transaction {i+1}: Corrected {actual_amount} from debit to credit (balance increased by {balance_change})")
                elif balance_change < 0 and current_credit > 0:
                    # Balance decreased but currently credit - needs correction
                    transaction['debit_amount'] = abs(actual_amount)
                    transaction['credit_amount'] = 0
                    logger.debug(f"Transaction {i+1}: Corrected {actual_amount} from credit to debit (balance decreased by {abs(balance_change)})")
                else:
                    # No balance change (unusual case)
                    logger.debug(f"Transaction {i+1}: No balance change detected")
        
        return transactions
    
    def _sort_transactions_by_date(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort transactions by date (oldest first)
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Sorted list of transactions by date
        """
        def parse_date(date_str: str) -> tuple:
            """
            Parse date string in DD/MM/YY format to tuple for sorting
            Returns (year, month, day) for proper chronological sorting
            """
            try:
                if not date_str or date_str.strip() == "":
                    return (9999, 12, 31)  # Put empty dates at the end
                
                parts = date_str.strip().split('/')
                if len(parts) != 3:
                    return (9999, 12, 31)  # Invalid date format
                
                day, month, year = parts
                # Convert 2-digit year to 4-digit year
                year_int = int(year)
                if year_int < 50:  # Assume years 00-49 are 2000-2049
                    year_int += 2000
                else:  # Assume years 50-99 are 1950-1999
                    year_int += 1900
                
                return (year_int, int(month), int(day))
            except (ValueError, IndexError):
                return (9999, 12, 31)  # Invalid date, put at end
        
        # Sort transactions by date
        sorted_transactions = sorted(transactions, key=lambda txn: parse_date(txn.get('transaction_date', '')))
        
        logger.info(f"Sorted {len(sorted_transactions)} transactions by date (oldest first)")
        return sorted_transactions
        
    def _validate_balance_equation(self, transactions: List[Dict[str, Any]]) -> bool:
        """
        Validate balance equation: Previous Balance + Credit - Debit = Next Balance
        Returns True if there are mismatches, False if all equations are satisfied.
        Skip the first transaction (no opening balance) and any B/F carry-forward rows.
        """
        if not transactions:
            return False
        mismatches: List[Dict[str, Any]] = []
        current_balance = 0.0
        for i, tx in enumerate(transactions):
            if i == 0:
                current_balance = float(tx.get('balance', 0.0) or 0.0)
                continue
            deposits = float(tx.get('deposits', 0.0) or 0.0)
            withdrawals = float(tx.get('withdrawals', 0.0) or 0.0)
            balance = float(tx.get('balance', 0.0) or 0.0)
            mode = (tx.get('mode') or '').upper()
            particulars = (tx.get('particulars') or '')
            if mode == 'B/F' or 'B/F' in particulars:
                current_balance = balance
                continue
            expected = current_balance + deposits - withdrawals
            diff = abs(expected - balance)
            if diff > 0.01:
                mismatches.append({'transaction_index': i, 'date': tx.get('date', ''), 'expected_balance': expected, 'actual_balance': balance, 'difference': diff})
            current_balance = balance
        return len(mismatches) > 0

    def format_transactions(self, extracted_text: str) -> Dict[str, Any]:
        """
        Map parsed HDFC transactions to the 6-field schema expected by the generic pipeline.
        Returns balance_mismatch flag using the HDFC-specific validator.
        """
        try:
            if not self.validate_statement(extracted_text):
                return {
                    "bank_name": self.get_bank_name(),
                    "success": False,
                    "error": f"Text does not match {self.get_bank_name()} statement format",
                    "transactions": []
                }

            hdfc_transactions = self.parse_bank_statement_format(extracted_text)

            clean_transactions: List[Dict[str, Any]] = []
            mode_keywords = ["UPI", "NEFT", "IMPS", "ATM", "POS", "TRANSFER", "PAYMENT", "CHEQUE", "ECS", "DD", "RTGS"]

            for tx in hdfc_transactions:
                narration = tx.get("narration", "") or ""
                upper_narr = narration.upper()
                detected_mode = ""
                for kw in mode_keywords:
                    if kw in upper_narr:
                        detected_mode = kw
                        break
                
                clean_transactions.append({
                    "date": tx.get("transaction_date", ""),
                    "mode": detected_mode,
                    "particulars": narration,
                    "deposits": tx.get("credit_amount", 0.0) or 0.0,
                    "withdrawals": tx.get("debit_amount", 0.0) or 0.0,
                    "balance": tx.get("closing_balance", 0.0) or 0.0,
                    "cheque_reference": tx.get("cheque_reference", "") or "",
                })

            balance_mismatch = self._validate_balance_equation(clean_transactions)

            return {
                "bank_name": self.get_bank_name(),
                "success": len(clean_transactions) > 0,
                "transactions": clean_transactions,
                "total_transactions": len(clean_transactions),
                "balance_mismatch": balance_mismatch,
                "formatted_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in HDFC format_transactions: {str(e)}")
            return {
                "bank_name": self.get_bank_name(),
                "success": False,
                "error": str(e),
                "transactions": []
            }


def format_session_transactions(session_id: str, bsa_folder: str = "./BSA") -> Dict[str, Any]:
    """
    Convenience function to format transactions for a specific session
    
    Args:
        session_id: Session ID to process
        bsa_folder: Path to BSA folder
        
    Returns:
        Formatted transaction data
    """
    logger.info(f"Formatting transactions for session: {session_id}")
    
    # Find the comprehensive file
    comprehensive_file = Path(bsa_folder) / session_id / "extractedData" / f"{session_id}_extracted_data.json"
    
    if not comprehensive_file.exists():
        raise FileNotFoundError(f"Comprehensive file not found: {comprehensive_file}")
    
    # Process the file
    formatter = TransactionFormatter()
    formatted_data = formatter.process_comprehensive_file(str(comprehensive_file))
    
    # Save formatted version
    formatted_file = formatter.save_formatted_file(str(comprehensive_file))
    
    return {
        "session_id": session_id,
        "formatted_file_path": formatted_file,
        "formatted_data": formatted_data,
        "success": True
    }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample text
    sample_text = """
    Transaction Date: 2025-09-21
    UPI-Naresh Payment for services rendered
    Reference: 1234567890
    Amount: ₹1,000.00
    Closing Balance: ₹1,000.00
    """
    
    formatter = TransactionFormatter()
    result = formatter.format_transaction_data(sample_text)
    
    logger.info("Sample formatting result:")
    logger.info(json.dumps(result, indent=2))