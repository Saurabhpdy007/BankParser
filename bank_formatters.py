#!/usr/bin/env python3
"""
BankParser Bank Formatters
==========================

A modular system for handling different bank statement formats.
Each bank has its own specific formatter that understands the unique
structure and patterns of that bank's statements.

Author: BankParser Team
"""

import re
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseBankFormatter(ABC):
    """
    Abstract base class for all bank-specific formatters.
    Each bank should implement this interface to handle their specific format.
    """
    
    def __init__(self):
        """Initialize the bank formatter"""
        self.bank_name = self.get_bank_name()
        self.date_patterns = self.get_date_patterns()
        self.amount_patterns = self.get_amount_patterns()
        self.transaction_patterns = self.get_transaction_patterns()
    
    @abstractmethod
    def get_bank_name(self) -> str:
        """Return the bank name this formatter handles"""
        pass
    
    @abstractmethod
    def get_date_patterns(self) -> List[str]:
        """Return list of date patterns specific to this bank"""
        pass
    
    @abstractmethod
    def get_amount_patterns(self) -> List[str]:
        """Return list of amount patterns specific to this bank"""
        pass
    
    @abstractmethod
    def get_transaction_patterns(self) -> Dict[str, str]:
        """Return transaction parsing patterns specific to this bank"""
        pass
    
    @abstractmethod
    def parse_statement_format(self, extracted_text: str) -> List[Dict[str, Any]]:
        """
        Parse bank statement format specific to this bank
        
        Args:
            extracted_text: Raw text extracted from PDF
            
        Returns:
            List of structured transaction dictionaries
        """
        pass
    
    @abstractmethod
    def validate_statement(self, extracted_text: str) -> bool:
        """
        Validate if the extracted text matches this bank's format
        
        Args:
            extracted_text: Raw text extracted from PDF
            
        Returns:
            True if text matches this bank's format, False otherwise
        """
        pass
    
    def format_transactions(self, extracted_text: str) -> Dict[str, Any]:
        """
        Main method to format transactions for this bank
        
        Args:
            extracted_text: Raw text extracted from PDF
            
        Returns:
            Formatted transaction data
        """
        try:
            # Validate the statement format
            if not self.validate_statement(extracted_text):
                logger.warning(f"Text does not match {self.bank_name} format")
                return {
                    "bank_name": self.bank_name,
                    "success": False,
                    "error": f"Text does not match {self.bank_name} statement format",
                    "transactions": []
                }
            
            # Parse transactions
            transactions = self.parse_statement_format(extracted_text)
            
            return {
                "bank_name": self.bank_name,
                "success": True,
                "transactions": transactions,
                "total_transactions": len(transactions),
                "formatted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error formatting {self.bank_name} transactions: {str(e)}")
            return {
                "bank_name": self.bank_name,
                "success": False,
                "error": str(e),
                "transactions": []
            }


class HDFCFormatter(BaseBankFormatter):
    """
    HDFC Bank specific formatter
    Handles HDFC bank statement format with specific patterns
    """
    
    def get_bank_name(self) -> str:
        return "HDFC"
    
    def get_date_patterns(self) -> List[str]:
        return [
            r'\d{2}/\d{2}/\d{2}',  # DD/MM/YY
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{1,2}/\d{1,2}/\d{2}',  # D/M/YY
            r'\d{1,2}/\d{1,2}/\d{4}',  # D/M/YYYY
        ]
    
    def get_amount_patterns(self) -> List[str]:
        return [
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)',  # 1,000.00 or 1000.00
        ]
    
    def get_transaction_patterns(self) -> Dict[str, str]:
        return {
            "transaction_line": r'(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            "balance_line": r'Balance\s+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            "narration_start": r'(UPI|NEFT|IMPS|RTGS|ATM|POS|TRANSFER|PAYMENT)',
        }
    
    def validate_statement(self, extracted_text: str) -> bool:
        """Validate HDFC statement format"""
        hdfc_indicators = [
            "HDFC BANK",
            "HDFC Bank",
            "HDFC",
            "Account Statement",
            "Statement of Account"
        ]
        
        text_upper = extracted_text.upper()
        return any(indicator.upper() in text_upper for indicator in hdfc_indicators)
    
    def parse_statement_format(self, extracted_text: str) -> List[Dict[str, Any]]:
        """
        Parse HDFC bank statement format
        This is a simplified version - you can enhance it based on your specific HDFC format
        """
        transactions = []
        
        # Split text into lines
        lines = extracted_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for transaction patterns
            for date_pattern in self.date_patterns:
                match = re.search(f'({date_pattern})\s+(.+?)\s+(\d+(?:,\d{3})*(?:\.\d{2})?)', line)
                if match:
                    date_str, narration, amount_str = match.groups()
                    
                    # Parse amount
                    amount = float(amount_str.replace(',', ''))
                    
                    # Determine transaction type (simplified logic)
                    transaction_type = "DEBIT" if amount < 0 else "CREDIT"
                    
                    transaction = {
                        "date": date_str,
                        "narration": narration.strip(),
                        "amount": amount,
                        "type": transaction_type,
                        "bank": "HDFC"
                    }
                    
                    transactions.append(transaction)
                    break
        
        return transactions


class ICICIFormatter(BaseBankFormatter):
    """
    ICICI Bank specific formatter
    Handles ICICI bank statement format with specific patterns
    """
    
    def get_bank_name(self) -> str:
        return "ICICI"
    
    def get_date_patterns(self) -> List[str]:
        return [
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY (ICICI format)
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{1,2}-\d{1,2}-\d{4}',  # D-M-YYYY
        ]
    
    def get_amount_patterns(self) -> List[str]:
        return [
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)',  # 1,000.00 or 1000.00
        ]
    
    def get_transaction_patterns(self) -> Dict[str, str]:
        return {
            "transaction_line": r'(\d{2}-\d{2}-\d{4})\s+(.+?)\s+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            "balance_line": r'Balance\s+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            "narration_start": r'(UPI|NEFT|IMPS|RTGS|ATM|POS|TRANSFER|PAYMENT|ICICI)',
        }
    
    def validate_statement(self, extracted_text: str) -> bool:
        """Validate ICICI statement format"""
        icici_indicators = [
            "ICICI BANK",
            "ICICI Bank",
            "ICICI",
            "Account Statement",
            "Statement of Account"
        ]
        
        text_upper = extracted_text.upper()
        return any(indicator.upper() in text_upper for indicator in icici_indicators)
    
    def parse_statement_format(self, extracted_text: str) -> List[Dict[str, Any]]:
        """
        Parse ICICI bank statement format
        This is a simplified version - you can enhance it based on your specific ICICI format
        """
        transactions = []
        
        # Split text into lines
        lines = extracted_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for transaction patterns (ICICI uses DD-MM-YYYY format)
            for date_pattern in self.date_patterns:
                match = re.search(f'({date_pattern})\s+(.+?)\s+(\d+(?:,\d{3})*(?:\.\d{2})?)', line)
                if match:
                    date_str, narration, amount_str = match.groups()
                    
                    # Parse amount
                    amount = float(amount_str.replace(',', ''))
                    
                    # Determine transaction type (simplified logic)
                    transaction_type = "DEBIT" if amount < 0 else "CREDIT"
                    
                    transaction = {
                        "date": date_str,
                        "narration": narration.strip(),
                        "amount": amount,
                        "type": transaction_type,
                        "bank": "ICICI"
                    }
                    
                    transactions.append(transaction)
                    break
        
        return transactions


class SBIFormatter(BaseBankFormatter):
    """
    State Bank of India (SBI) specific formatter
    Handles SBI bank statement format with specific patterns
    """
    
    def get_bank_name(self) -> str:
        return "SBI"
    
    def get_date_patterns(self) -> List[str]:
        return [
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{1,2}/\d{1,2}/\d{4}',  # D/M/YYYY
        ]
    
    def get_amount_patterns(self) -> List[str]:
        return [
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)',  # 1,000.00 or 1000.00
        ]
    
    def get_transaction_patterns(self) -> Dict[str, str]:
        return {
            "transaction_line": r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            "balance_line": r'Balance\s+(\d+(?:,\d{3})*(?:\.\d{2})?)',
            "narration_start": r'(UPI|NEFT|IMPS|RTGS|ATM|POS|TRANSFER|PAYMENT|SBI)',
        }
    
    def validate_statement(self, extracted_text: str) -> bool:
        """Validate SBI statement format"""
        sbi_indicators = [
            "STATE BANK OF INDIA",
            "SBI",
            "Account Statement",
            "Statement of Account"
        ]
        
        text_upper = extracted_text.upper()
        return any(indicator.upper() in text_upper for indicator in sbi_indicators)
    
    def parse_statement_format(self, extracted_text: str) -> List[Dict[str, Any]]:
        """
        Parse SBI bank statement format
        This is a simplified version - you can enhance it based on your specific SBI format
        """
        transactions = []
        
        # Split text into lines
        lines = extracted_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for transaction patterns
            for date_pattern in self.date_patterns:
                match = re.search(f'({date_pattern})\s+(.+?)\s+(\d+(?:,\d{3})*(?:\.\d{2})?)', line)
                if match:
                    date_str, narration, amount_str = match.groups()
                    
                    # Parse amount
                    amount = float(amount_str.replace(',', ''))
                    
                    # Determine transaction type (simplified logic)
                    transaction_type = "DEBIT" if amount < 0 else "CREDIT"
                    
                    transaction = {
                        "date": date_str,
                        "narration": narration.strip(),
                        "amount": amount,
                        "type": transaction_type,
                        "bank": "SBI"
                    }
                    
                    transactions.append(transaction)
                    break
        
        return transactions


class BankFormatterFactory:
    """
    Factory class to create bank-specific formatters
    """
    
    _formatters = {
        "HDFC": HDFCFormatter,
        "ICICI": ICICIFormatter,
        "SBI": SBIFormatter,
    }
    
    @classmethod
    def get_formatter(cls, bank_name: str) -> BaseBankFormatter:
        """
        Get the appropriate formatter for the specified bank
        
        Args:
            bank_name: Name of the bank (case-insensitive)
            
        Returns:
            Bank-specific formatter instance
            
        Raises:
            ValueError: If bank_name is not supported
        """
        bank_name_upper = bank_name.upper()
        
        if bank_name_upper not in cls._formatters:
            supported_banks = list(cls._formatters.keys())
            raise ValueError(f"Unsupported bank: {bank_name}. Supported banks: {supported_banks}")
        
        formatter_class = cls._formatters[bank_name_upper]
        return formatter_class()
    
    @classmethod
    def get_supported_banks(cls) -> List[str]:
        """
        Get list of supported banks
        
        Returns:
            List of supported bank names
        """
        return list(cls._formatters.keys())
    
    @classmethod
    def register_formatter(cls, bank_name: str, formatter_class: type):
        """
        Register a new bank formatter
        
        Args:
            bank_name: Name of the bank
            formatter_class: Formatter class that extends BaseBankFormatter
        """
        cls._formatters[bank_name.upper()] = formatter_class


def auto_detect_bank(extracted_text: str) -> Optional[str]:
    """
    Automatically detect the bank from extracted text
    
    Args:
        extracted_text: Raw text extracted from PDF
        
    Returns:
        Bank name if detected, None otherwise
    """
    text_upper = extracted_text.upper()
    
    bank_indicators = {
        "HDFC": ["HDFC BANK", "HDFC Bank", "HDFC"],
        "ICICI": ["ICICI BANK", "ICICI Bank", "ICICI"],
        "SBI": ["STATE BANK OF INDIA", "SBI"],
    }
    
    for bank_name, indicators in bank_indicators.items():
        if any(indicator in text_upper for indicator in indicators):
            return bank_name
    
    return None
