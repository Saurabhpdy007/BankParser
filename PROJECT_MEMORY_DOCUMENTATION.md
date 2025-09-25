# bankParser Project Memory Documentation

## Project Overview

**bankParser** is a comprehensive ePDF (electronic PDF) processing system designed to extract, parse, and format bank statement data from various Indian banks. The system handles password-protected PDFs, supports multiple bank formats, and provides clean, structured transaction data output.

## Core Architecture

### 1. Main Components

#### **ePDF Processors**
- **`epdf_processor.py`**: AWS S3-based ePDF processor (legacy)
- **`local_epdf_processor.py`**: Local file system-based processor (current primary)
- **`pdf_password_utils.py`**: Password protection detection and unlocking utilities

#### **Bank Formatters**
- **`bank_formatters/`**: Package containing bank-specific formatters
  - **`base_formatter.py`**: Abstract base class for all bank formatters
  - **`hdfc_formatter.py`**: HDFC Bank statement formatter
  - **`icici_formatter.py`**: ICICI Bank statement formatter
  - **`__init__.py`**: Package exports and initialization
- **`bank_formatters_main.py`**: Factory and auto-detection logic

#### **Utilities**
- **`balance_validator.py`**: Balance equation validation utility
- **`brand_config.py`**: Brand configuration and metadata
- **`config.py`**: System configuration settings

### 2. Data Flow

```
PDF Files → Password Check → Text Extraction → Bank Detection → Formatting → Validation → Output
```

## Bank Statement Processing

### Supported Banks

#### **HDFC Bank**
- **Format**: Traditional bank statement with page headers
- **Date Format**: DD/MM/YYYY, DD/MM/YY
- **Structure**: Transaction Date | Narration | Reference | Amount | Balance
- **Features**: Multi-page processing, cross-page narration merging

#### **ICICI Bank**
- **Format**: Multi-line transaction format with headers on all pages
- **Date Format**: DD-MM-YYYY
- **Structure**: DATE | MODE** | PARTICULARS | DEPOSITS | WITHDRAWALS | BALANCE
- **Features**: 
  - Multi-line transaction parsing
  - Transaction ID detection and handling
  - Variable-length transaction descriptions
  - Page boundary detection with "Page x of y" markers

### Transaction Data Structure

All formatters output clean 6-column transaction data:
```json
{
  "date": "DD-MM-YYYY",
  "mode": "Transaction type (UPI, NEFT, etc.)",
  "particulars": "Full transaction description",
  "deposits": 0.0,
  "withdrawals": 0.0,
  "balance": 0.0
}
```

## Key Features

### 1. Password Protection Handling
- **Detection**: Automatically detects password-protected PDFs
- **Unlocking**: Supports password-based PDF unlocking
- **Error Handling**: Graceful handling of invalid passwords
- **Libraries**: Uses PyMuPDF (fitz) and PyPDF2 for robustness

### 2. Bank Auto-Detection
- **Smart Detection**: Scoring-based system that prioritizes format patterns over bank name occurrences
- **Pattern Matching**: Uses unique bank-specific headers and transaction patterns
- **Fallback**: Falls back to generic formatting if bank detection fails

### 3. Balance Validation
- **Equation**: Previous Balance + Credit - Debit = Next Balance
- **Validation**: Separate utility (`balance_validator.py`) for data quality assurance
- **Reporting**: Detailed console reports showing validation results
- **Mismatch Detection**: Identifies and reports specific transaction discrepancies

### 4. Multi-Page Processing
- **Page Splitting**: Automatically splits statements by page markers
- **Cross-Page Continuity**: Handles transactions that span multiple pages
- **Header Detection**: Identifies bank-specific headers on each page

## File Structure

```
bankParser/
├── bank_formatters/
│   ├── __init__.py
│   ├── base_formatter.py
│   ├── hdfc_formatter.py
│   └── icici_formatter.py
├── BSA/
│   ├── session_001/
│   ├── session_002/
│   └── session_003/
├── balance_validator.py
├── bank_formatters_main.py
├── brand_config.py
├── config.py
├── epdf_processor.py
├── local_epdf_processor.py
├── pdf_password_utils.py
└── requirements.txt
```

## Session Management

### BSA Folder Structure
```
BSA/
├── session_001/
│   ├── [PDF files]
│   └── extractedData/
│       ├── session_001_extracted_data.json
│       ├── session_001_extracted_data_formatted.json
│       └── session_001_extracted_data_formatted.csv
├── session_002/
└── session_003/
```

### Session Processing Flow
1. **PDF Detection**: Scans session folder for PDF files
2. **Password Check**: Identifies password-protected files
3. **Text Extraction**: Extracts text using PyMuPDF/pdfplumber
4. **Bank Detection**: Auto-detects or uses specified bank
5. **Formatting**: Applies bank-specific formatting
6. **Validation**: Runs balance equation validation
7. **Output**: Generates JSON and CSV files

## Technical Implementation

### 1. ICICI Formatter Specifics

#### **Transaction ID Handling**
- **Problem**: Some transactions have IDs on separate lines (e.g., `3746`, `7507574`)
- **Solution**: `_is_transaction_id()` method to identify and skip transaction IDs
- **Pattern**: Transaction IDs are 4-12 digit pure numbers without formatting

#### **Multi-line Transaction Parsing**
- **Method**: `_parse_icici_transaction_multiline()`
- **Features**: Handles variable-length descriptions, skips transaction IDs
- **Ordering**: Maintains chronological order with `_original_order` tracking

#### **Mode Extraction**
- **Keywords**: Only extracts specific modes: MOBILE BANKING, ICICI ATM, BANK CHARGES, CMS TRANSACTION, CREDIT CARD
- **Fallback**: All other transactions have blank mode field

### 2. Balance Equation Logic

#### **Implementation**
```python
def validate_balance_equation(transactions):
    current_balance = 0.0
    for tx in transactions:
        if tx['mode'] == 'B/F':  # Skip B/F transactions
            current_balance = tx['balance']
            continue
        
        expected_balance = current_balance + tx['deposits'] - tx['withdrawals']
        if abs(expected_balance - tx['balance']) > 0.01:
            # Mismatch detected
            pass
        
        current_balance = tx['balance']
```

#### **Validation Report**
- **Console Output**: Detailed report after processing
- **Mismatch Details**: Shows expected vs actual balance for each error
- **Success Rate**: Percentage of transactions with correct balance equations

### 3. Error Handling

#### **Password Protection**
- **Detection**: `PDFPasswordHandler.is_password_protected()`
- **Unlocking**: `PDFPasswordHandler.unlock_pdf()`
- **Error Messages**: Clear, specific error messages for different failure types

#### **Bank Detection**
- **Fallback**: Generic formatting if bank detection fails
- **Logging**: Detailed logging for debugging bank detection issues

## Usage Examples

### 1. Command Line Usage
```bash
# Process specific session
python local_epdf_processor.py session_003

# Interactive mode
python local_epdf_processor.py
```

### 2. Programmatic Usage
```python
from local_epdf_processor import LocalEPdfProcessor
from bank_formatters_main import BankFormatterFactory

# Initialize processor
processor = LocalEPdfProcessor("./BSA")

# Process session
result = processor.process_session("session_003", password="123456", bank_name="ICICI")

# Get formatter
formatter = BankFormatterFactory.get_formatter("ICICI")
formatted_data = formatter.format_transactions(extracted_text)
```

### 3. Balance Validation
```python
from balance_validator import validate_balance_equation, format_balance_validation_report

# Validate transactions
has_mismatches, mismatches = validate_balance_equation(transactions)

# Generate report
report = format_balance_validation_report(transactions, "ICICI")
print(report)
```

## Recent Improvements

### 1. Transaction ID Parsing Fix
- **Issue**: Transaction IDs were being misidentified as amounts
- **Solution**: Enhanced `_is_amount_line()` and added `_is_transaction_id()` methods
- **Result**: 100% success rate for amount parsing

### 2. Balance Validation Architecture
- **Previous**: Balance logic embedded in formatters
- **Current**: Separate `balance_validator.py` utility
- **Benefit**: Clean separation of concerns, reusable validation

### 3. Code Organization
- **Structure**: Clean bank_formatters package organization
- **Inheritance**: All formatters inherit from BaseBankFormatter
- **Interface**: Consistent `format_transactions()` method across all formatters

## Configuration

### Brand Configuration (`brand_config.py`)
```python
BRAND_NAME = "bankParser"
BRAND_VERSION = "2.5"
BRAND_AUTHOR = "bankParser Team"
BRAND_TAGLINE = "Intelligent Bank Statement Processing"
PACKAGE_NAME = "bankparser"
PACKAGE_DESCRIPTION = "A comprehensive bank statement processing toolkit"
CONTACT_EMAIL = "support@bankparser.com"
CONTACT_WEBSITE = "https://bankparser.com"
```

**Usage in Code:**
```python
from brand_config import BRAND_NAME, BRAND_VERSION, BRAND_AUTHOR

print(f"{BRAND_NAME} v{BRAND_VERSION} by {BRAND_AUTHOR}")
# Output: bankParser v2.5 by bankParser Team
```

**Important**: Always import brand information from `brand_config.py` instead of hardcoding values. This ensures consistency and makes it easy to update the brand name across the entire project.

### Dependencies (`requirements.txt`)
- PyMuPDF (fitz)
- pdfplumber
- PyPDF2
- pandas
- pathlib
- datetime
- logging
- typing

## Testing and Validation

### 1. Test Data
- **Session 003**: ICICI bank statement with 855 transactions
- **Validation**: All transactions pass balance equation validation
- **Success Rate**: 100% amount parsing accuracy

### 2. Test Commands
```bash
# Test formatters
python -c "from bank_formatters import ICICIFormatter; print('OK')"

# Test balance validation
python -c "from balance_validator import validate_balance_equation; print('OK')"

# Test full processing
python local_epdf_processor.py session_003
```

## Future Enhancements

### 1. Additional Banks
- **SBI**: State Bank of India formatter
- **Axis Bank**: Axis Bank formatter
- **Kotak Mahindra**: Kotak Mahindra Bank formatter

### 2. Enhanced Features
- **OCR Support**: For scanned PDF statements
- **Multi-Currency**: Support for different currencies
- **Export Formats**: Additional output formats (Excel, XML)

### 3. Performance Optimizations
- **Parallel Processing**: Multi-threaded PDF processing
- **Caching**: Transaction parsing result caching
- **Memory Optimization**: Large file handling improvements

## Troubleshooting

### Common Issues

#### 1. Password Protection
- **Error**: "Password Protected File"
- **Solution**: Provide correct password or check PDF encryption

#### 2. Bank Detection
- **Error**: "Could not auto-detect bank"
- **Solution**: Manually specify bank name or check statement format

#### 3. Transaction Parsing
- **Error**: "No transactions found"
- **Solution**: Check PDF text extraction quality, verify bank format

### Debug Commands
```bash
# Check PDF password protection
python -c "from pdf_password_utils import PDFPasswordHandler; print(PDFPasswordHandler.is_password_protected('file.pdf'))"

# Test bank detection
python -c "from bank_formatters_main import auto_detect_bank; print(auto_detect_bank(text))"

# Validate balance equations
python -c "from balance_validator import validate_balance_equation; print(validate_balance_equation(transactions))"
```

## Contact and Support

- **Project**: bankParser Bank Statement Processing System
- **Version**: 2.5
- **Team**: bankParser Development Team
- **Email**: support@bankparser.com
- **Website**: https://bankparser.com
- **Last Updated**: September 2025

---

*This document serves as a comprehensive memory reference for the bankParser project. It captures the current state, architecture, implementation details, and usage patterns for future development and maintenance.*
