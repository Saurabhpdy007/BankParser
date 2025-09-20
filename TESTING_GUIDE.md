# BankParser Data Extraction Testing Guide

This guide provides comprehensive instructions on how to test and verify the data extraction functionality in your BankParser project.

## 🚀 Quick Start

### 1. Run the Comprehensive Test (Recommended)
```bash
python3 test_data_extraction.py
```
This will:
- Create a sample PDF automatically
- Test all extraction methods
- Compare different PDF libraries
- Validate extraction quality
- Generate a detailed report

### 2. Run Unit Tests
```bash
python3 -m pytest tests/test_epdf_processor.py -v
```

### 3. Test with Your Own PDF
```bash
python3 -c "
from epdf_processor import EPdfProcessor
import json

# Initialize processor
processor = EPdfProcessor()

# Read your PDF file
with open('your_file.pdf', 'rb') as f:
    pdf_content = f.read()

# Extract data
result = processor.extract_data_from_epdf(pdf_content)

# Print results
print(json.dumps(result, indent=2))
"
```

## 📋 Available Testing Methods

### 1. **Local PDF Testing** (No AWS Required)
- **Best for**: Development, debugging, quick verification
- **Requirements**: None (uses sample PDF)
- **Command**: `python3 test_data_extraction.py`

**What it tests:**
- ✅ Text extraction from all 3 PDF libraries (PyMuPDF, pdfplumber, PyPDF2)
- ✅ Metadata extraction
- ✅ Page count accuracy
- ✅ Extraction method comparison
- ✅ Quality validation scoring

**Sample Output:**
```
Main Extraction Results:
  Pages: 3
  Text Length: 710 characters
  Tables: 0
  Images: 0
  Method: multiple

Quality Validation:
  Overall Score: 60/100
  required_fields: ✓ (Score: 20)
  text_quality: ✓ (Score: 30)
  metadata: ✓ (Score: 10)
```

### 2. **S3 Integration Testing** (AWS Required)
- **Best for**: End-to-end testing, production validation
- **Requirements**: AWS credentials, S3 bucket access
- **Command**: `python3 test_data_extraction.py --s3 --bucket YOUR_BUCKET --session YOUR_SESSION_ID`

**What it tests:**
- ✅ S3 file retrieval
- ✅ Complete workflow from S3 to extraction
- ✅ Error handling for missing files/buckets
- ✅ Session ID processing

### 3. **Unit Testing**
- **Best for**: Code quality, regression testing
- **Requirements**: pytest
- **Command**: `python3 -m pytest tests/test_epdf_processor.py -v`

**What it tests:**
- ✅ Class initialization
- ✅ Error handling
- ✅ Mocked S3 operations
- ✅ Configuration validation

### 4. **Example Usage Testing**
- **Best for**: Learning the API, integration examples
- **Requirements**: Environment variables
- **Command**: `python3 example_usage.py`

## 🔧 Environment Setup

### Option 1: Automated Setup
```bash
./setup_test_environment.sh
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip3 install -r requirements.txt
pip3 install pytest reportlab

# Set environment variables (for S3 testing)
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export S3_BUCKET_NAME="your_bucket"
```

## 📊 Understanding Test Results

### Quality Validation Scores
- **Overall Score**: 0-100 (higher is better)
- **Required Fields**: 20 points (all extraction fields present)
- **Text Quality**: 30 points (text length, numbers, emails/URLs)
- **Metadata**: 10 points (title, author, dates)
- **Tables**: 10 points (table extraction)
- **Images**: 10 points (image detection)

### Method Comparison
The test compares three PDF extraction libraries:
- **PyMuPDF (fitz)**: Best for comprehensive extraction
- **pdfplumber**: Best for table extraction
- **PyPDF2**: Fallback method

### Extraction Methods
- **multiple**: Uses PyMuPDF + pdfplumber (recommended)
- **fallback_pypdf2**: Uses PyPDF2 only (when others fail)

## 🐛 Troubleshooting

### Common Issues

1. **"AWS credentials not found"**
   - **Solution**: Set environment variables or use local testing only
   - **Command**: `python3 test_data_extraction.py` (no AWS needed)

2. **"No such key" error**
   - **Solution**: Check S3 bucket name and session ID
   - **Verify**: File exists at `epdfs/{session_id}.pdf` in your bucket

3. **Low quality scores**
   - **Cause**: PDF might be image-based or corrupted
   - **Solution**: Try with a text-based PDF

4. **Import errors**
   - **Solution**: Install missing packages
   - **Command**: `pip3 install -r requirements.txt`

### Debug Mode
Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python3 test_data_extraction.py
```

## 📁 Output Files

### test_results.json
Detailed test results including:
- Extraction data
- Method comparisons
- Quality validation
- Recommendations

### extracted_data_{session_id}.json
Actual extracted data from your PDFs (when using S3)

## 🔍 What Gets Extracted

### Text Content
- All readable text from PDF pages
- Page-by-page organization
- Special characters and formatting

### Metadata
- Document title, author, subject
- Creation and modification dates
- Creator and producer information

### Tables
- Structured data extraction
- Table boundaries and cell content
- Page location information

### Images
- Image detection and metadata
- Dimensions and properties
- Page location information

## 🎯 Best Practices

1. **Start with Local Testing**: Always test locally first
2. **Check Quality Scores**: Aim for scores above 70/100
3. **Compare Methods**: Use method comparison to choose best approach
4. **Validate Results**: Check extracted text manually for accuracy
5. **Handle Errors**: Always implement proper error handling

## 📞 Support

If you encounter issues:
1. Check the test results in `test_results.json`
2. Review the quality validation recommendations
3. Try different PDF files
4. Check AWS credentials and S3 permissions

---

**Happy Testing! 🎉**

Your BankParser data extraction system is now ready for comprehensive testing and validation.
