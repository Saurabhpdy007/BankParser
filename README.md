# BankParser - ePDF Processing Library

A comprehensive Python library for consuming ePDF files from AWS S3 buckets using session IDs and extracting structured data from them.

## 🚀 Features

- **S3 Integration**: Retrieve ePDF files from S3 using session ID as reference
- **Multiple Extraction Methods**: Uses PyMuPDF, pdfplumber, and PyPDF2 for comprehensive data extraction
- **Structured Output**: Returns extracted data as JSON with metadata, text content, tables, and image information
- **Error Handling**: Robust error handling with detailed logging
- **Configurable**: Environment-based configuration for easy deployment
- **Production Ready**: Comprehensive testing and documentation

## 📦 Installation

### From Source
```bash
git clone https://github.com/bankparser/bankparser.git
cd bankparser
pip install -r requirements.txt
pip install -e .
```

### From PyPI (when published)
```bash
pip install bankparser
```

## 🛠 Quick Start

### Basic Usage

```python
from bankparser import EPdfProcessor

# Initialize processor
processor = EPdfProcessor()

# Process ePDF
result = processor.process_epdf("your-bucket-name", "session-id-123")

# Access extracted data
print(f"Pages: {result['pages_count']}")
print(f"Text: {result['text_content']}")
print(f"Tables: {result['tables']}")
```

### Command Line Usage

```bash
# Set environment variables
export S3_BUCKET_NAME="your-bucket"
export SESSION_ID="your-session-id"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Run the processor
python example_usage.py
```

## ⚙️ Configuration

Set the following environment variables:

```bash
# Required
export S3_BUCKET_NAME="your-s3-bucket-name"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Optional
export AWS_REGION="us-east-1"
export S3_EPDF_PREFIX="epdfs/"
export OUTPUT_DIRECTORY="./output"
export LOG_LEVEL="INFO"
```

## 📊 Output Format

The processor returns a JSON object with the following structure:

```json
{
  "session_id": "session-123",
  "bucket_name": "your-bucket",
  "processing_timestamp": "2024-01-01T12:00:00",
  "pages_count": 5,
  "extraction_method": "multiple",
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "creation_date": "2024-01-01"
  },
  "text_content": "Full extracted text content...",
  "tables": [
    {
      "page": 1,
      "table_index": 0,
      "data": [["Header1", "Header2"], ["Value1", "Value2"]]
    }
  ],
  "images_info": [
    {
      "page": 1,
      "image_index": 0,
      "width": 100,
      "height": 100
    }
  ]
}
```

## 🏗 S3 File Structure

The processor expects ePDF files to be stored in S3 with the following structure:

```
your-bucket/
├── epdfs/
│   ├── session-001.pdf
│   ├── session-002.pdf
│   └── session-003.pdf
```

You can customize the prefix by setting the `S3_EPDF_PREFIX` environment variable.

## 🔧 Advanced Usage

### Custom AWS Configuration

```python
from bankparser import EPdfProcessor

# Custom AWS configuration
processor = EPdfProcessor(
    aws_access_key_id="your-key",
    aws_secret_access_key="your-secret",
    region_name="us-west-2"
)

# Process multiple sessions
session_ids = ["session_001", "session_002", "session_003"]
results = {}

for session_id in session_ids:
    try:
        result = processor.process_epdf("your-bucket", session_id)
        results[session_id] = result
    except Exception as e:
        print(f"Failed to process {session_id}: {e}")
```

### Using Configuration Class

```python
from bankparser import Config

# Validate configuration
if Config.validate():
    Config.print_config()
    
    # Use configuration
    processor = EPdfProcessor(
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        region_name=Config.AWS_REGION
    )
```

## 🧪 Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=bankparser
```

## 📚 API Reference

### EPdfProcessor Class

#### `__init__(aws_access_key_id=None, aws_secret_access_key=None, region_name='us-east-1')`
Initialize the ePDF processor with AWS credentials.

#### `get_epdf_from_s3(bucket_name, session_id)`
Retrieve ePDF from S3 bucket using session ID as reference.

#### `extract_data_from_epdf(pdf_content)`
Extract data from ePDF content and return as JSON.

#### `process_epdf(bucket_name, session_id)`
Complete workflow: retrieve ePDF from S3 and extract data.

### Config Class

Configuration management class with environment variable support.

## 🐛 Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   ```
   NoCredentialsError: Unable to locate credentials
   ```
   Solution: Set AWS credentials via environment variables or AWS CLI

2. **File Not Found**
   ```
   FileNotFoundError: ePDF not found for session_id: session-123
   ```
   Solution: Check S3 bucket name and file path structure

3. **Permission Denied**
   ```
   ClientError: An error occurred (AccessDenied)
   ```
   Solution: Ensure AWS credentials have S3 read permissions

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL="DEBUG"
python example_usage.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- 📧 Email: team@bankparser.com
- 🐛 Issues: [GitHub Issues](https://github.com/bankparser/bankparser/issues)
- 📖 Documentation: [Read the Docs](https://bankparser.readthedocs.io/)

## 🙏 Acknowledgments

- AWS SDK for Python (boto3)
- PyMuPDF for comprehensive PDF processing
- pdfplumber for table extraction
- PyPDF2 for basic PDF operations
