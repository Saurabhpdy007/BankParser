# Local Bank Processing Guide

## Overview

The `local_epdf_processor.py` has been updated to support multiple bank formatters (HDFC, ICICI, SBI) with both manual selection and auto-detection capabilities.

## Key Features

✅ **Multiple Bank Support**: HDFC, ICICI, SBI formatters  
✅ **Auto-Detection**: Automatically detects bank from PDF content  
✅ **Password Protection**: Handles password-protected PDFs  
✅ **Interactive Mode**: User-friendly bank selection interface  
✅ **Formatted Output**: Generates both JSON and CSV formatted results  

## Usage Methods

### 1. Interactive Mode (Recommended)

```bash
python3 local_epdf_processor.py
```

This will:
- Show available sessions
- Let you select a session
- Ask for password (if needed)
- Let you choose bank formatter or use auto-detection

### 2. Command Line with Session ID

```bash
python3 local_epdf_processor.py session_003
```

### 3. Programmatic Usage

```python
from local_epdf_processor import LocalEPdfProcessor

# Initialize processor
processor = LocalEPdfProcessor("./BSA")

# Process with specific bank formatter
result = processor.process_session("session_003", password="your_password", bank_name="ICICI")

# Process with auto-detection
result = processor.process_session("session_003", password="your_password", bank_name=None)

# Check results
if result["success"]:
    print(f"Bank detected: {result.get('bank_name')}")
    print(f"Transactions: {result.get('total_formatted_transactions', 0)}")
```

## Bank Selection Options

### Manual Selection
- **HDFC**: For HDFC Bank statements
- **ICICI**: For ICICI Bank statements  
- **SBI**: For State Bank of India statements

### Auto-Detection
- Automatically detects bank from PDF content
- Looks for bank-specific indicators in the text
- Falls back gracefully if detection fails

## Password Protection

The system handles password-protected PDFs:

```python
# Without password - will fail on protected PDFs
result = processor.process_session("session_id")

# With password - will attempt to unlock protected PDFs
result = processor.process_session("session_id", password="your_password")
```

## Output Files

For each session, the system generates:

1. **Raw Data**: `session_XXX_extracted_data.json`
2. **Formatted Data**: `session_XXX_extracted_data_formatted.json`
3. **CSV Export**: `session_XXX_extracted_data_formatted.csv`
4. **Session Results**: `session_results_session_XXX.json`

## Example Output Structure

```json
{
  "session_id": "session_003",
  "success": true,
  "bank_name": "ICICI",
  "total_formatted_transactions": 21,
  "formatted_transactions": [
    {
      "date": "17-09-2024",
      "mode": "B/F",
      "particulars": "",
      "deposits": 0.0,
      "withdrawals": 0.0,
      "balance": 93498.86,
      "amount": 93498.86,
      "type": "BALANCE",
      "bank": "ICICI",
      "narration": "B/F",
      "page": 1
    }
  ],
  "combined_data": {
    "total_pages": 40,
    "total_text_length": 125000,
    "all_text_content": "..."
  }
}
```

## Bank-Specific Features

### ICICI Formatter
- Handles multi-line headers: `DATE\nMODE**\nPARTICULARS\nDEPOSITS\nWITHDRAWALS\nBALANCE`
- Parses multi-line transactions
- Recognizes page markers: `Page x of y`
- Supports ICICI-specific transaction types

### HDFC Formatter  
- Handles HDFC statement format
- Parses transaction patterns
- Recognizes HDFC-specific indicators

### SBI Formatter
- Handles State Bank of India format
- Parses SBI-specific patterns
- Recognizes SBI indicators

## Error Handling

The system provides clear error messages for:

- **Password Protected Files**: "Password Protected File - Please provide a password"
- **Invalid Passwords**: "Invalid password provided - Please check the password"
- **Scanned PDFs**: "Please pass ePDFs for processing - File appears to be scanned/image PDF"
- **Unsupported Banks**: "Unsupported bank: XXX. Supported banks: ['HDFC', 'ICICI', 'SBI']"

## Testing

Use the example script to test different scenarios:

```bash
python3 example_local_bank_processing.py
```

This will demonstrate:
- Processing with specific bank formatters
- Auto-detection functionality
- Comparison between different formatters

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure `bank_formatters_main.py` is in the same directory
2. **Password Issues**: Use the debugging scripts to test password functionality
3. **No Transactions Found**: Check if the PDF format matches the selected bank formatter
4. **Circular Import**: Clear Python cache: `find . -name "*.pyc" -delete`

### Debugging Tools

- `debug_password_issue.py`: Test password protection functionality
- `test_password_fix.py`: Verify password handling fixes
- `test_icici_direct.py`: Test ICICI formatter directly

## Next Steps

1. **Add More Banks**: Extend `BankFormatterFactory` with new bank formatters
2. **Improve Patterns**: Enhance regex patterns for better transaction parsing
3. **Add Validation**: Implement more robust statement validation
4. **Performance**: Optimize processing for large PDF files

---

**Note**: This system is designed for local processing without S3 dependencies. For cloud processing, use `epdf_processor.py` instead.
