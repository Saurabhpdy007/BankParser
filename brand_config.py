"""
Brand Configuration
==================

Centralized configuration for brand name and related information.
This ensures consistency across all files and makes it easy to update
the brand name in one place.

Usage:
    from brand_config import BRAND_NAME, BRAND_TAGLINE
    
    print(f"{BRAND_NAME} - {BRAND_TAGLINE}")
"""

# Brand Information
BRAND_NAME = "bankParser"
BRAND_TAGLINE = "Intelligent Bank Statement Processing"
BRAND_VERSION = "2.5"
BRAND_AUTHOR = "bankParser Team"

# Package Information
PACKAGE_NAME = "bankparser"
PACKAGE_DESCRIPTION = "A comprehensive bank statement processing toolkit"

# Contact Information
CONTACT_EMAIL = "support@bankparser.com"
CONTACT_WEBSITE = "https://bankparser.com"

# Export all brand constants
__all__ = [
    'BRAND_NAME',
    'BRAND_TAGLINE', 
    'BRAND_VERSION',
    'BRAND_AUTHOR',
    'PACKAGE_NAME',
    'PACKAGE_DESCRIPTION',
    'CONTACT_EMAIL',
    'CONTACT_WEBSITE'
]