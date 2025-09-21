"""
{BRAND_NAME} Bank Formatters Package
====================================

This package contains bank-specific formatters for processing bank statements.
Each formatter is designed to handle the specific format and structure of 
transactions from different banks.

Available formatters:
- HDFC Bank: hdfc_formatter.py
- ICICI Bank: icici_formatter.py
- Future banks: sbi_formatter.py, axis_formatter.py, etc.

Part of {BRAND_NAME} - {BRAND_TAGLINE}
"""

from brand_config import BRAND_NAME, BRAND_TAGLINE

# Format the docstring with brand config
__doc__ = __doc__.format(
    BRAND_NAME=BRAND_NAME,
    BRAND_TAGLINE=BRAND_TAGLINE
)

from .hdfc_formatter import TransactionFormatter as HDFCFormatter
from .icici_formatter import ICICIFormatter
from .base_formatter import BaseBankFormatter

__all__ = ['HDFCFormatter', 'ICICIFormatter', 'BaseBankFormatter']