#!/usr/bin/env python3
"""
Base Bank Formatter
==================

Abstract base class for all bank statement formatters.
Defines the common interface and shared functionality.

Version: 2.0
Author: CredNX Team
"""

import re
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional

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
            
            # Create clean transactions with only the 6 required fields
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
            
            # Validate balance equation: Previous Balance + Credit - Debit = Next Balance
            # Only if the formatter has this method (optional)
            if hasattr(self, '_validate_balance_equation'):
                balance_mismatch = self._validate_balance_equation(clean_transactions)
            else:
                balance_mismatch = False  # Default to no mismatch if method not implemented
            
            return {
                "bank_name": self.bank_name,
                "success": True,
                "transactions": clean_transactions,
                "total_transactions": len(clean_transactions),
                "balance_mismatch": balance_mismatch,
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

