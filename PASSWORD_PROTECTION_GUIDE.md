# Password Protection Guide

## 🔐 Overview

CredNX now supports **password-protected PDFs** with automatic detection and unlocking capabilities. The system can identify password-protected files and handle them appropriately, either by unlocking them with provided passwords or by throwing clear error messages.

## 🚀 Key Features

- **Automatic Detection**: Identifies password-protected PDFs automatically
- **Password Unlocking**: Supports unlocking with provided passwords
- **Clear Error Messages**: Throws "Password Protected File" error when no password is provided
- **Multiple Library Support**: Uses both PyMuPDF and PyPDF2 for robust handling
- **Optional Parameter**: Password is optional - only used when needed

## 📋 Usage Examples

### Basic Usage with Password

```python
from epdf_processor import EPdfProcessor

# Initialize processor
processor = EPdfProcessor()

# Process with password for protected PDFs
result = processor.process_epdf(
    bucket_name="your-bucket",
    session_id="session_001",
    bank_name="HDFC",
    password="your_password"  # Optional password
)

print(f"Success: {result.get('success', False)}")
```

### Processing Without Password (Will Fail on Protected PDFs)

```python
# This will throw "Password Protected File" error for protected PDFs
result = processor.process_epdf(
    bucket_name="your-bucket",
    session_id="session_001",
    bank_name="HDFC"
    # No password provided
)
```

### Local Processing with Password

```python
from local_epdf_processor import LocalEPdfProcessor

# Initialize processor
processor = LocalEPdfProcessor("./BSA")

# Process session with password
result = processor.process_session("session_001", password="your_password")
```

### Interactive Password Input

```python
import getpass

# Get password securely
password = getpass.getpass("Enter PDF password: ")

# Process with password
result = processor.process_session("session_001", password=password)
```

## 🛠 API Reference

### EPdfProcessor

#### `process_epdf(bucket_name, session_id, bank_name=None, password=None)`

**Parameters:**
- `bucket_name` (str): Name of the S3 bucket
- `session_id` (str): Session ID used as file reference
- `bank_name` (str, optional): Bank name for formatting
- `password` (str, optional): Password for password-protected PDFs

**Returns:**
- `Dict[str, Any]`: Extracted data with bank-specific formatting

**Example:**
```python
result = processor.process_epdf(
    bucket_name="my-bucket",
    session_id="session_001",
    bank_name="HDFC",
    password="mypassword"
)
```

### LocalEPdfProcessor

#### `process_session(session_id, password=None)`

**Parameters:**
- `session_id` (str): Session ID to process
- `password` (str, optional): Password for password-protected PDFs

**Returns:**
- `Dict[str, Any]`: Combined extracted data from all PDFs

**Example:**
```python
result = processor.process_session("session_001", password="mypassword")
```

### PDFPasswordHandler

#### `is_password_protected(pdf_content)`

**Parameters:**
- `pdf_content` (bytes): PDF content as bytes

**Returns:**
- `bool`: True if password protected, False otherwise

#### `validate_password_protection(pdf_content, password=None)`

**Parameters:**
- `pdf_content` (bytes): PDF content as bytes
- `password` (str, optional): Password for protected PDFs

**Returns:**
- `Tuple[bool, Optional[str], Optional[bytes]]`: (is_valid, error_message, unlocked_content)

## 🚨 Error Handling

### Password Protected File Error

When a password-protected PDF is encountered without a password:

```python
try:
    result = processor.process_epdf(bucket_name, session_id)
except ValueError as e:
    if "Password Protected File" in str(e):
        print("PDF is password protected. Please provide a password.")
    else:
        print(f"Other error: {e}")
```

### Invalid Password Error

When an incorrect password is provided:

```python
try:
    result = processor.process_epdf(bucket_name, session_id, password="wrong_password")
except ValueError as e:
    if "Invalid password" in str(e):
        print("Incorrect password provided.")
    else:
        print(f"Other error: {e}")
```

## 🧪 Testing Password Functionality

### Test Script Usage

```bash
# Test password detection only
python test_password_functionality.py --detect-only protected.pdf

# Test with password
python test_password_functionality.py protected.pdf mypassword

# Test without password (should fail)
python test_password_functionality.py protected.pdf
```

### Manual Testing

```python
from pdf_password_utils import check_pdf_password_protection

# Read PDF file
with open("test.pdf", "rb") as f:
    pdf_content = f.read()

# Check if password protected
is_protected = check_pdf_password_protection(pdf_content)
print(f"Password protected: {is_protected}")
```

## 🔒 Security Considerations

### Password Handling

- **No Storage**: Passwords are not stored or logged
- **Memory Cleanup**: Password variables are cleared after use
- **Secure Input**: Use `getpass` for interactive password input
- **Error Messages**: No sensitive information in error messages

### Best Practices

1. **Use Environment Variables**: Store passwords in environment variables when possible
2. **Secure Input**: Use `getpass.getpass()` for interactive password input
3. **Error Handling**: Always handle password-related errors gracefully
4. **Logging**: Avoid logging passwords in any form

## 📊 Performance Impact

### Detection Overhead
- **Password Detection**: ~10-50ms per PDF
- **Unlocking**: ~100-500ms per PDF (depending on size)
- **Memory Usage**: Minimal additional memory usage

### Optimization Tips
1. **Batch Processing**: Process multiple PDFs with same password together
2. **Caching**: Cache unlocked content for repeated processing
3. **Early Detection**: Check password protection before full processing

## 🔧 Troubleshooting

### Common Issues

1. **"Password Protected File" Error**
   - **Cause**: PDF is password protected but no password provided
   - **Solution**: Provide correct password parameter

2. **"Invalid password provided" Error**
   - **Cause**: Incorrect password for protected PDF
   - **Solution**: Verify password is correct

3. **"Failed to unlock PDF" Error**
   - **Cause**: PDF corruption or unsupported encryption
   - **Solution**: Verify PDF file integrity

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed logs about password handling
```

## 🎯 Integration Examples

### Command Line Tool

```python
#!/usr/bin/env python3
import argparse
import getpass
from epdf_processor import EPdfProcessor

def main():
    parser = argparse.ArgumentParser(description='Process PDF with optional password')
    parser.add_argument('bucket', help='S3 bucket name')
    parser.add_argument('session', help='Session ID')
    parser.add_argument('--password', help='PDF password')
    parser.add_argument('--bank', help='Bank name')
    
    args = parser.parse_args()
    
    # Get password if not provided
    password = args.password
    if not password:
        password = getpass.getpass("Enter PDF password (press Enter to skip): ")
        if not password.strip():
            password = None
    
    # Process PDF
    processor = EPdfProcessor()
    result = processor.process_epdf(
        bucket_name=args.bucket,
        session_id=args.session,
        bank_name=args.bank,
        password=password
    )
    
    print(f"Success: {result.get('success', False)}")

if __name__ == "__main__":
    main()
```

### Web API Integration

```python
from flask import Flask, request, jsonify
from epdf_processor import EPdfProcessor

app = Flask(__name__)

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    data = request.json
    bucket_name = data.get('bucket_name')
    session_id = data.get('session_id')
    password = data.get('password')  # Optional
    bank_name = data.get('bank_name')
    
    try:
        processor = EPdfProcessor()
        result = processor.process_epdf(
            bucket_name=bucket_name,
            session_id=session_id,
            bank_name=bank_name,
            password=password
        )
        return jsonify({"success": True, "data": result})
    except ValueError as e:
        if "Password Protected File" in str(e):
            return jsonify({"success": False, "error": "Password required"}), 400
        else:
            return jsonify({"success": False, "error": str(e)}), 500
```

## 📈 Future Enhancements

- **Password Caching**: Cache passwords for batch processing
- **Multiple Password Support**: Support multiple passwords per PDF
- **Password Recovery**: Attempt common passwords automatically
- **Encryption Detection**: Detect encryption type and strength
- **Performance Metrics**: Track password handling performance

---

**CredNX Team** - Secure PDF processing made simple! 🔐
