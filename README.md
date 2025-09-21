# BankParser - Bank Statement Processing System

A comprehensive Python-based system for extracting, parsing, and formatting bank statements from electronic PDFs (ePDFs). Supports multiple banks including HDFC, ICICI, and SBI with automatic bank detection and transaction formatting.

## 🚀 Features

- **Multi-Bank Support**: HDFC, ICICI, SBI with extensible architecture
- **Automatic Bank Detection**: Smart detection based on statement format patterns
- **Password Protection**: Handle password-protected PDFs with optional password input
- **Transaction Formatting**: Clean 6-column output (date, mode, particulars, deposits, withdrawals, balance)
- **Balance Validation**: Automatic balance equation validation with detailed reporting
- **Session Management**: Organize processing by sessions with comprehensive result tracking
- **Multiple PDF Libraries**: PyMuPDF, pdfplumber, PyPDF2 for robust text extraction
- **Local Processing**: No cloud dependencies - all processing done locally

## 📋 Prerequisites

- Python 3.7+
- Required packages (see `requirements.txt`)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd BankParser
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python3 -c "import fitz, pdfplumber, PyPDF2; print('✅ All dependencies installed successfully')"
   ```

## 📁 Project Structure

```
BankParser/
├── BSA/                          # Bank Statement Archive (input folder)
│   ├── session_001/             # Session folders
│   │   ├── *.pdf               # Bank statement PDFs
│   │   └── extractedData/       # Output folder
│   │       ├── session_001_extracted_data.json
│   │       ├── session_001_extracted_data_formatted.json
│   │       └── session_001_extracted_data_formatted.csv
│   └── session_002/
├── bank_formatters/             # Bank-specific formatters
│   ├── __init__.py
│   ├── base_formatter.py       # Abstract base class
│   ├── hdfc_formatter.py       # HDFC Bank formatter
│   └── icici_formatter.py      # ICICI Bank formatter
├── local_epdf_processor.py     # Main processing engine
├── bank_formatters_main.py     # Formatter factory and auto-detection
├── balance_validator.py        # Balance validation utilities
├── pdf_password_utils.py       # Password handling utilities
├── brand_config.py            # Brand configuration
└── requirements.txt           # Python dependencies
```

## 🎯 Quick Start

### 1. Prepare Your Bank Statements

1. Create a session folder in `BSA/`:
   ```bash
   mkdir -p BSA/session_001
   ```

2. Place your bank statement PDFs in the session folder:
   ```bash
   cp your_bank_statement.pdf BSA/session_001/
   ```

### 2. Run the Processor

```bash
python3 local_epdf_processor.py
```

Follow the interactive prompts:
- Select session ID (e.g., `session_001`)
- Enter password if PDFs are password-protected (optional)
- Choose bank or use auto-detection (recommended)

### 3. View Results

Results are saved in:
- `BSA/session_001/extractedData/session_001_extracted_data_formatted.json` - Clean transaction data
- `BSA/session_001/extractedData/session_001_extracted_data_formatted.csv` - CSV format
- `session_results_session_001.json` - Complete processing results

## 📊 Output Format

### Transaction Structure

Each transaction contains exactly 6 fields:

```json
{
  "date": "01-01-2025",
  "mode": "UPI",
  "particulars": "UPI/paytm-123456@p/Payment from Ph/YES BANK LTD/123456789012/IBL...",
  "deposits": 1000.00,
  "withdrawals": 0.00,
  "balance": 5000.00
}
```

### CSV Output

```csv
date,mode,particulars,deposits,withdrawals,balance
01-01-2025,UPI,UPI/paytm-123456@p/Payment from Ph/YES BANK LTD/123456789012/IBL...,1000.00,0.00,5000.00
```

## 🏦 Supported Banks

### HDFC Bank
- **Format**: Standard HDFC statement format
- **Features**: Multi-page support, transaction continuation handling
- **Sample**: `BSA/session_001/` (if available)

### ICICI Bank
- **Format**: ICICI-specific format with header patterns
- **Features**: Multi-line transaction parsing, keyword-based mode extraction
- **Sample**: `BSA/session_003/` (if available)

### SBI Bank
- **Status**: Framework ready, formatter can be implemented
- **Extension**: Follow `BaseBankFormatter` interface

## 🔧 Advanced Usage

### Programmatic Usage

```python
from local_epdf_processor import LocalEPdfProcessor

# Initialize processor
processor = LocalEPdfProcessor()

# Process a session
result = processor.process_session(
    session_id='session_001',
    password='your_password',  # Optional
    bank_name='HDFC'          # Optional, None for auto-detect
)

# Check results
if result['success']:
    print(f"Processed {result['pdfs_processed']} PDFs")
    print(f"Bank: {result['bank_name']}")
    print(f"Transactions: {result['total_formatted_transactions']}")
```

### Auto-Detection

The system automatically detects the bank based on:
- Statement format patterns
- Bank-specific headers
- Transaction structure
- Bank name occurrences

```python
# Auto-detect bank
result = processor.process_session('session_001', bank_name=None)
```

### Password-Protected PDFs

```python
# Process password-protected PDFs
result = processor.process_session(
    session_id='session_001',
    password='your_password'
)
```

## 🧪 Testing

### Test Individual Components

```python
# Test bank formatters
from bank_formatters_main import BankFormatterFactory

factory = BankFormatterFactory()
formatter = factory.create_formatter('HDFC')

# Test balance validation
from balance_validator import validate_balance_equation

mismatches = validate_balance_equation(transactions)
```

### Test with Sample Data

```bash
# Test with existing sessions
python3 -c "
from local_epdf_processor import LocalEPdfProcessor
processor = LocalEPdfProcessor()
result = processor.process_session('session_001', bank_name='HDFC')
print(f'Success: {result[\"success\"]}')
"
```

## 🔍 Troubleshooting

### Common Issues

1. **"Password Protected File" Error**
   - **Solution**: Provide password when prompted or set `password` parameter
   - **Note**: Only ePDFs are supported, not scanned/image PDFs

2. **"No Such Session Exists" Error**
   - **Solution**: Ensure session folder exists in `BSA/` directory
   - **Check**: `ls BSA/` to see available sessions

3. **"Please pass ePDFs for processing" Error**
   - **Solution**: Ensure PDFs are text-based (ePDFs), not scanned images
   - **Check**: Try opening PDF in text editor to verify it contains selectable text

4. **Balance Mismatch Warnings**
   - **Info**: These are validation warnings, not errors
   - **Action**: Review transactions for data quality issues

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🏗️ Extending the System

### Adding New Bank Support

1. **Create Bank Formatter:**
   ```python
   # bank_formatters/new_bank_formatter.py
   from bank_formatters.base_formatter import BaseBankFormatter
   
   class NewBankFormatter(BaseBankFormatter):
       def get_bank_name(self) -> str:
           return "NEW_BANK"
       
       def get_date_patterns(self) -> List[str]:
           return [r'\d{2}-\d{2}-\d{4}']  # Add your patterns
       
       # Implement other abstract methods...
   ```

2. **Register Formatter:**
   ```python
   # bank_formatters_main.py
   from bank_formatters.new_bank_formatter import NewBankFormatter
   
   class BankFormatterFactory:
       def __init__(self):
           self._formatters = {
               'HDFC': HDFCFormatter,
               'ICICI': ICICIFormatter,
               'NEW_BANK': NewBankFormatter,  # Add here
           }
   ```

3. **Update Auto-Detection:**
   ```python
   # bank_formatters_main.py
   def auto_detect_bank(extracted_text: str) -> Optional[str]:
       # Add detection logic for new bank
       if 'NEW_BANK_SPECIFIC_PATTERN' in extracted_text:
           return 'NEW_BANK'
   ```

### Custom Processing

```python
# Custom processing pipeline
processor = LocalEPdfProcessor()

# Extract raw data
pdf_content = processor.read_pdf_file(Path('statement.pdf'))
raw_data = processor.extract_data_from_epdf(pdf_content)

# Apply custom formatting
formatted_data = processor.format_with_bank_specific_parser(raw_data, 'HDFC')

# Save results
processor.save_formatted_results(
    Path('output/'),
    'custom_session',
    formatted_data['bank_specific_data']
)
```

## 📈 Performance

### Optimization Tips

1. **Batch Processing**: Process multiple sessions in sequence
2. **Memory Management**: Large PDFs are processed page by page
3. **Caching**: Results are cached in session folders for reuse

### Benchmarks

- **Small PDFs** (< 10 pages): ~2-5 seconds
- **Medium PDFs** (10-50 pages): ~10-30 seconds  
- **Large PDFs** (50+ pages): ~30-60 seconds

*Performance varies based on PDF complexity and system specifications.*

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-bank-support`
3. **Follow coding standards**: Use type hints, docstrings, and logging
4. **Test thoroughly**: Add tests for new functionality
5. **Submit pull request**: Include description and test results

### Code Style

- **Type Hints**: Use throughout codebase
- **Docstrings**: Follow Google style
- **Logging**: Use structured logging with appropriate levels
- **Error Handling**: Comprehensive exception handling

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

1. **Check Issues**: Search existing GitHub issues
2. **Create Issue**: Provide detailed error logs and sample data
3. **Documentation**: Review this README and inline code documentation

### Contact

- **Repository**: [GitHub Repository URL]
- **Issues**: [GitHub Issues URL]
- **Documentation**: [Documentation URL]

---

## 🎉 Quick Examples

### Example 1: Basic Processing
```bash
# 1. Place PDF in session folder
cp bank_statement.pdf BSA/session_001/

# 2. Run processor
python3 local_epdf_processor.py
# Select: session_001
# Password: (press Enter if not needed)
# Bank: 4 (auto-detect)

# 3. Check results
ls BSA/session_001/extractedData/
```

### Example 2: Programmatic Processing
```python
from local_epdf_processor import LocalEPdfProcessor

processor = LocalEPdfProcessor()
result = processor.process_session('session_001')

if result['success']:
    print(f"✅ Processed {result['total_formatted_transactions']} transactions")
    print(f"🏦 Bank: {result['bank_name']}")
else:
    print(f"❌ Error: {result['error']}")
```

### Example 3: Balance Validation
```python
from balance_validator import format_balance_validation_report

# After processing
transactions = result['bank_specific_data']['transactions']
report = format_balance_validation_report(transactions, 'HDFC')
print(report)
```

---

**Happy Processing! 🚀**