"""
BankParser - ePDF Processing Library

A comprehensive library for consuming ePDF files from AWS S3 buckets
and extracting structured data from them.
"""

__version__ = "1.0.0"
__author__ = "BankParser Team"
__email__ = "team@bankparser.com"
__description__ = "ePDF processing library for S3 integration and data extraction"

from .epdf_processor import EPdfProcessor
from .config import Config

__all__ = ['EPdfProcessor', 'Config']
