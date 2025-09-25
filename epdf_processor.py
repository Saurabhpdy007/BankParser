import boto3
import json
import logging
import tempfile
import os
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from io import BytesIO
import pandas as pd
from bank_formatters import BankFormatterFactory, auto_detect_bank
from pdf_password_utils import PDFPasswordHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EPdfProcessor:
    """
    A class to handle ePDF consumption from S3 and data extraction
    """
    
    def __init__(self, aws_access_key_id: str = None, aws_secret_access_key: str = None, 
                 region_name: str = 'us-east-1'):
        """
        Initialize the ePDF processor with AWS credentials
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region name
        """
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )
            logger.info("S3 client initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise
    
    def get_epdf_from_s3(self, bucket_name: str, session_id: str) -> bytes:
        """
        Retrieve ePDF from S3 bucket using session ID as reference
        
        Args:
            bucket_name: Name of the S3 bucket
            session_id: Session ID used as file reference/key
            
        Returns:
            bytes: PDF content as bytes
        """
        try:
            # Construct the object key using session_id
            # You may need to adjust this based on your S3 structure
            object_key = f"epdfs/{session_id}.pdf"  # Adjust path as needed
            
            logger.info(f"Attempting to retrieve ePDF for session_id: {session_id}")
            
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            pdf_content = response['Body'].read()
            
            logger.info(f"Successfully retrieved ePDF for session_id: {session_id}")
            return pdf_content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"ePDF not found for session_id: {session_id}")
                raise FileNotFoundError(f"ePDF not found for session_id: {session_id}")
            elif error_code == 'NoSuchBucket':
                logger.error(f"S3 bucket not found: {bucket_name}")
                raise FileNotFoundError(f"S3 bucket not found: {bucket_name}")
            else:
                logger.error(f"AWS S3 error: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving ePDF: {str(e)}")
            raise
    
    def extract_data_from_epdf(self, pdf_content: bytes, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract data from ePDF content and return as JSON
        
        Args:
            pdf_content: PDF content as bytes
            password: Optional password for password-protected PDFs
            
        Returns:
            Dict[str, Any]: Extracted data as dictionary
        """
        extracted_data = {
            "metadata": {},
            "text_content": "",
            "tables": [],
            "images_info": [],
            "pages_count": 0,
            "extraction_method": "multiple"
        }
        
        try:
            # Check if PDF is password protected and unlock if needed
            logger.info(f"Validating password protection (password provided: {password is not None})")
            is_valid, error_msg, unlocked_content = PDFPasswordHandler.validate_password_protection(
                pdf_content, password
            )
            
            if not is_valid:
                logger.error(f"Password protection error: {error_msg}")
                # Provide more specific error messages
                if "Password Protected File" in error_msg:
                    raise ValueError("Password Protected File - Please provide a password to unlock this PDF")
                elif "Invalid password" in error_msg:
                    raise ValueError("Invalid password provided - Please check the password and try again")
                else:
                    raise ValueError(f"PDF processing error: {error_msg}")
            
            # Use unlocked content for processing
            pdf_content = unlocked_content
            logger.info(f"PDF successfully validated/unlocked, proceeding with extraction")
            # Method 1: Using PyMuPDF (fitz) for comprehensive extraction
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            extracted_data["pages_count"] = len(pdf_document)
            
            # Extract metadata
            metadata = pdf_document.metadata
            extracted_data["metadata"] = {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", "")
            }
            
            # Extract text content
            full_text = ""
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text()
                full_text += f"\n--- Page {page_num + 1} ---\n{text}"
                
                # Extract images info
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    extracted_data["images_info"].append({
                        "page": page_num + 1,
                        "image_index": img_index,
                        "xref": img[0],
                        "smask": img[1],
                        "width": img[2],
                        "height": img[3],
                        "bpc": img[4],
                        "colorspace": img[5],
                        "alt": img[6],
                        "name": img[7],
                        "filter": img[8]
                    })
            
            extracted_data["text_content"] = full_text.strip()
            pdf_document.close()
            
            # Method 2: Using pdfplumber for table extraction
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                tables = []
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table_index, table in enumerate(page_tables):
                        tables.append({
                            "page": page_num + 1,
                            "table_index": table_index,
                            "data": table
                        })
                extracted_data["tables"] = tables
            
            logger.info(f"Successfully extracted data from ePDF with {extracted_data['pages_count']} pages")
            
        except Exception as e:
            logger.error(f"Error extracting data from ePDF: {str(e)}")
            # Fallback to basic PyPDF2 extraction
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
                extracted_data["pages_count"] = len(pdf_reader.pages)
                extracted_data["extraction_method"] = "fallback_pypdf2"
                
                text_content = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    text_content += f"\n--- Page {page_num + 1} ---\n{page.extract_text()}"
                
                extracted_data["text_content"] = text_content.strip()
                logger.info("Used fallback PyPDF2 extraction method")
                
            except Exception as fallback_error:
                logger.error(f"Fallback extraction also failed: {str(fallback_error)}")
                raise
        
        return extracted_data
    
    def format_with_bank_specific_parser(self, extracted_data: Dict[str, Any], bank_name: str = None) -> Dict[str, Any]:
        """
        Apply bank-specific formatting to extracted data
        
        Args:
            extracted_data: Raw extracted data from PDF
            bank_name: Name of the bank (optional, will auto-detect if not provided)
            
        Returns:
            Dict[str, Any]: Data with bank-specific formatting applied
        """
        try:
            text_content = extracted_data.get("text_content", "")
            
            # Auto-detect bank if not provided
            if not bank_name:
                detected_bank = auto_detect_bank(text_content)
                if detected_bank:
                    bank_name = detected_bank
                    logger.info(f"Auto-detected bank: {bank_name}")
                else:
                    logger.warning("Could not auto-detect bank, using generic formatting")
                    return extracted_data
            
            # Get bank-specific formatter
            try:
                formatter = BankFormatterFactory.get_formatter(bank_name)
                logger.info(f"Using {bank_name} formatter")
            except ValueError as e:
                logger.error(f"Bank formatter error: {str(e)}")
                logger.info("Falling back to generic formatting")
                return extracted_data
            
            # Apply bank-specific formatting
            formatted_result = formatter.format_transactions(text_content)
            
            # Merge formatted data with original extracted data
            result = extracted_data.copy()
            result["bank_specific_data"] = formatted_result
            result["bank_name"] = bank_name
            
            # Add formatted transactions to main result if successful
            if formatted_result.get("success", False):
                result["formatted_transactions"] = formatted_result.get("transactions", [])
                result["total_formatted_transactions"] = formatted_result.get("total_transactions", 0)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in bank-specific formatting: {str(e)}")
            # Return original data if formatting fails
            return extracted_data
    
    def process_epdf(self, bucket_name: str, session_id: str, bank_name: str = None, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete workflow: retrieve ePDF from S3 and extract data with bank-specific formatting
        
        Args:
            bucket_name: Name of the S3 bucket
            session_id: Session ID used as file reference
            bank_name: Name of the bank (optional, will auto-detect if not provided)
            password: Optional password for password-protected PDFs
            
        Returns:
            Dict[str, Any]: Extracted data as JSON-serializable dictionary with bank-specific formatting
        """
        try:
            logger.info(f"Starting ePDF processing for session_id: {session_id}, bank: {bank_name or 'auto-detect'}")
            
            # Step 1: Retrieve ePDF from S3
            pdf_content = self.get_epdf_from_s3(bucket_name, session_id)
            
            # Step 2: Extract data from ePDF
            extracted_data = self.extract_data_from_epdf(pdf_content, password)
            
            # Step 3: Apply bank-specific formatting
            formatted_data = self.format_with_bank_specific_parser(extracted_data, bank_name)
            
            # Add session information
            formatted_data["session_id"] = session_id
            formatted_data["bucket_name"] = bucket_name
            formatted_data["processing_timestamp"] = str(pd.Timestamp.now())
            
            logger.info(f"Successfully processed ePDF for session_id: {session_id}")
            return formatted_data
            
        except Exception as e:
            logger.error(f"Failed to process ePDF for session_id {session_id}: {str(e)}")
            raise


def main():
    """
    Example usage of the EPdfProcessor with bank-specific formatting
    """
    # Configuration - replace with your actual values
    BUCKET_NAME = "your-s3-bucket-name"
    SESSION_ID = "your-session-id"
    BANK_NAME = "HDFC"  # Specify bank name: HDFC, ICICI, SBI, or None for auto-detect
    PASSWORD = None  # Optional password for password-protected PDFs
    AWS_ACCESS_KEY_ID = "your-access-key"  # or use environment variables
    AWS_SECRET_ACCESS_KEY = "your-secret-key"  # or use environment variables
    AWS_REGION = "us-east-1"
    
    try:
        # Initialize processor
        processor = EPdfProcessor(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        # Process ePDF with bank-specific formatting
        result = processor.process_epdf(BUCKET_NAME, SESSION_ID, BANK_NAME, PASSWORD)
        
        # Print results summary
        print("=" * 60)
        print("BankParser ePDF Processing Results")
        print("=" * 60)
        print(f"Session ID: {result.get('session_id', 'N/A')}")
        print(f"Bank Name: {result.get('bank_name', 'N/A')}")
        print(f"Pages Count: {result.get('pages_count', 'N/A')}")
        print(f"Total Formatted Transactions: {result.get('total_formatted_transactions', 0)}")
        print(f"Processing Timestamp: {result.get('processing_timestamp', 'N/A')}")
        
        # Print bank-specific data if available
        if 'bank_specific_data' in result:
            bank_data = result['bank_specific_data']
            print(f"\nBank-Specific Formatting:")
            print(f"  Success: {bank_data.get('success', False)}")
            if bank_data.get('success'):
                print(f"  Total Transactions: {bank_data.get('total_transactions', 0)}")
            else:
                print(f"  Error: {bank_data.get('error', 'Unknown error')}")
        
        # Print sample transactions
        if 'formatted_transactions' in result and result['formatted_transactions']:
            print(f"\nSample Transactions (first 3):")
            for i, transaction in enumerate(result['formatted_transactions'][:3]):
                print(f"  {i+1}. {transaction.get('date', 'N/A')} - {transaction.get('narration', 'N/A')} - {transaction.get('amount', 'N/A')} ({transaction.get('type', 'N/A')})")
        
        # Save to file if needed
        output_filename = f"extracted_data_{SESSION_ID}_{BANK_NAME or 'auto'}.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nData saved to: {output_filename}")
        
        # Show supported banks
        print(f"\nSupported Banks: {BankFormatterFactory.get_supported_banks()}")
        
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
