"""
Unit tests for EPdfProcessor class
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
import boto3
from botocore.exceptions import ClientError

from epdf_processor import EPdfProcessor


class TestEPdfProcessor:
    """Test cases for EPdfProcessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = EPdfProcessor(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-east-1"
        )
    
    @patch('boto3.client')
    def test_init_success(self, mock_boto_client):
        """Test successful initialization"""
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        processor = EPdfProcessor()
        
        mock_boto_client.assert_called_once_with(
            's3',
            aws_access_key_id=None,
            aws_secret_access_key=None,
            region_name='us-east-1'
        )
        assert processor.s3_client == mock_s3_client
    
    @patch('boto3.client')
    def test_init_with_credentials(self, mock_boto_client):
        """Test initialization with custom credentials"""
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client
        
        processor = EPdfProcessor(
            aws_access_key_id="custom_key",
            aws_secret_access_key="custom_secret",
            region_name="us-west-2"
        )
        
        mock_boto_client.assert_called_once_with(
            's3',
            aws_access_key_id="custom_key",
            aws_secret_access_key="custom_secret",
            region_name="us-west-2"
        )
    
    @patch('boto3.client')
    def test_init_no_credentials(self, mock_boto_client):
        """Test initialization failure with no credentials"""
        from botocore.exceptions import NoCredentialsError
        
        mock_boto_client.side_effect = NoCredentialsError()
        
        with pytest.raises(NoCredentialsError):
            EPdfProcessor()
    
    def test_get_epdf_from_s3_success(self):
        """Test successful ePDF retrieval from S3"""
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = b"fake pdf content"
        
        self.processor.s3_client.get_object.return_value = mock_response
        
        result = self.processor.get_epdf_from_s3("test-bucket", "test-session")
        
        assert result == b"fake pdf content"
        self.processor.s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="epdfs/test-session.pdf"
        )
    
    def test_get_epdf_from_s3_no_such_key(self):
        """Test ePDF retrieval when file doesn't exist"""
        error_response = {
            'Error': {
                'Code': 'NoSuchKey',
                'Message': 'The specified key does not exist.'
            }
        }
        
        self.processor.s3_client.get_object.side_effect = ClientError(
            error_response, 'GetObject'
        )
        
        with pytest.raises(FileNotFoundError, match="ePDF not found for session_id: test-session"):
            self.processor.get_epdf_from_s3("test-bucket", "test-session")
    
    def test_get_epdf_from_s3_no_such_bucket(self):
        """Test ePDF retrieval when bucket doesn't exist"""
        error_response = {
            'Error': {
                'Code': 'NoSuchBucket',
                'Message': 'The specified bucket does not exist.'
            }
        }
        
        self.processor.s3_client.get_object.side_effect = ClientError(
            error_response, 'GetObject'
        )
        
        with pytest.raises(FileNotFoundError, match="S3 bucket not found: test-bucket"):
            self.processor.get_epdf_from_s3("test-bucket", "test-session")
    
    @patch('fitz.open')
    @patch('pdfplumber.open')
    def test_extract_data_from_epdf_success(self, mock_pdfplumber, mock_fitz):
        """Test successful data extraction from ePDF"""
        # Mock PyMuPDF
        mock_doc = Mock()
        mock_doc.metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "creationDate": "2024-01-01"
        }
        mock_doc.__len__ = Mock(return_value=2)
        
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page1.get_images.return_value = []
        
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 content"
        mock_page2.get_images.return_value = []
        
        mock_doc.__getitem__ = Mock(side_effect=[mock_page1, mock_page2])
        mock_fitz.return_value = mock_doc
        
        # Mock pdfplumber
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_tables.return_value = [
            [["Header1", "Header2"], ["Value1", "Value2"]]
        ]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        result = self.processor.extract_data_from_epdf(b"fake pdf content")
        
        assert result["pages_count"] == 2
        assert result["extraction_method"] == "multiple"
        assert "Test Document" in result["metadata"]["title"]
        assert "Page 1 content" in result["text_content"]
        assert "Page 2 content" in result["text_content"]
        assert len(result["tables"]) == 1
        assert result["tables"][0]["data"] == [["Header1", "Header2"], ["Value1", "Value2"]]
    
    @patch('fitz.open')
    @patch('PyPDF2.PdfReader')
    def test_extract_data_from_epdf_fallback(self, mock_pypdf2, mock_fitz):
        """Test fallback extraction when PyMuPDF fails"""
        # Mock PyMuPDF failure
        mock_fitz.side_effect = Exception("PyMuPDF failed")
        
        # Mock PyPDF2 fallback
        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock()]
        mock_page = Mock()
        mock_page.extract_text.return_value = "Fallback text content"
        mock_reader.pages.__getitem__ = Mock(return_value=mock_page)
        mock_pypdf2.return_value = mock_reader
        
        result = self.processor.extract_data_from_epdf(b"fake pdf content")
        
        assert result["pages_count"] == 2
        assert result["extraction_method"] == "fallback_pypdf2"
        assert "Fallback text content" in result["text_content"]
    
    @patch('epdf_processor.EPdfProcessor.extract_data_from_epdf')
    @patch('epdf_processor.EPdfProcessor.get_epdf_from_s3')
    def test_process_epdf_success(self, mock_get_epdf, mock_extract_data):
        """Test successful complete ePDF processing"""
        mock_get_epdf.return_value = b"fake pdf content"
        mock_extract_data.return_value = {
            "pages_count": 2,
            "text_content": "Test content",
            "metadata": {},
            "tables": [],
            "images_info": []
        }
        
        with patch('pandas.Timestamp') as mock_timestamp:
            mock_timestamp.now.return_value = "2024-01-01T12:00:00"
            
            result = self.processor.process_epdf("test-bucket", "test-session")
        
        assert result["session_id"] == "test-session"
        assert result["bucket_name"] == "test-bucket"
        assert result["pages_count"] == 2
        assert result["processing_timestamp"] == "2024-01-01T12:00:00"
        
        mock_get_epdf.assert_called_once_with("test-bucket", "test-session")
        mock_extract_data.assert_called_once_with(b"fake pdf content")
    
    @patch('epdf_processor.EPdfProcessor.get_epdf_from_s3')
    def test_process_epdf_failure(self, mock_get_epdf):
        """Test ePDF processing failure"""
        mock_get_epdf.side_effect = FileNotFoundError("ePDF not found")
        
        with pytest.raises(FileNotFoundError):
            self.processor.process_epdf("test-bucket", "test-session")


class TestConfig:
    """Test cases for Config class"""
    
    def test_config_validation_success(self):
        """Test successful configuration validation"""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret',
            'S3_BUCKET_NAME': 'test-bucket'
        }):
            from config import Config
            assert Config.validate() is True
    
    def test_config_validation_failure(self):
        """Test configuration validation failure"""
        with patch.dict('os.environ', {}, clear=True):
            from config import Config
            assert Config.validate() is False
    
    def test_config_print(self):
        """Test configuration printing"""
        with patch.dict('os.environ', {
            'AWS_REGION': 'us-west-2',
            'S3_BUCKET_NAME': 'test-bucket',
            'S3_EPDF_PREFIX': 'custom/',
            'MAX_FILE_SIZE_MB': '200',
            'OUTPUT_DIRECTORY': './custom-output',
            'LOG_LEVEL': 'DEBUG',
            'AWS_ACCESS_KEY_ID': 'test_key'
        }):
            from config import Config
            # This test just ensures the method doesn't raise an exception
            Config.print_config()


if __name__ == "__main__":
    pytest.main([__file__])
