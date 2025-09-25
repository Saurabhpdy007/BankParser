#!/usr/bin/env python3
"""
Bank Formatters Main
===================

Main module for bank formatter factory and auto-detection functionality.
Imports formatters from the bank_formatters package.

Author: CredNX Team
"""

import logging
from typing import Dict, List, Any, Optional
from bank_formatters import HDFCFormatter, ICICIFormatter, BaseBankFormatter

logger = logging.getLogger(__name__)

class BankFormatterFactory:
    """
    Factory class to create bank-specific formatters
    """
    
    _formatters = {
        "HDFC": HDFCFormatter,
        "ICICI": ICICIFormatter,
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
