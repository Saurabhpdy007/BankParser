#!/usr/bin/env python3
"""
Example usage script for ePDF processing from S3
"""

import os
import json
from epdf_processor import EPdfProcessor

def example_usage():
    """
    Example of how to use the EPdfProcessor class with bank-specific formatting
    """
    
    # Configuration - Set these as environment variables or replace with actual values
    BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'your-s3-bucket-name')
    SESSION_ID = os.getenv('SESSION_ID', 'your-session-id')
    BANK_NAME = os.getenv('BANK_NAME', 'HDFC')  # HDFC, ICICI, SBI, or None for auto-detect
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    print("BankParser ePDF Processor Example")
    print("=" * 50)
    
    try:
        # Initialize processor
        print("Initializing ePDF processor...")
        processor = EPdfProcessor(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        # Process ePDF with bank-specific formatting
        print(f"Processing ePDF for session_id: {SESSION_ID}, bank: {BANK_NAME or 'auto-detect'}")
        result = processor.process_epdf(BUCKET_NAME, SESSION_ID, BANK_NAME)
        
        # Display results summary
        print("\nExtraction Results Summary:")
        print("-" * 30)
        print(f"Session ID: {result['session_id']}")
        print(f"Bank Name: {result.get('bank_name', 'N/A')}")
        print(f"Pages Count: {result['pages_count']}")
        print(f"Extraction Method: {result['extraction_method']}")
        print(f"Tables Found: {len(result['tables'])}")
        print(f"Images Found: {len(result['images_info'])}")
        print(f"Text Length: {len(result['text_content'])} characters")
        print(f"Formatted Transactions: {result.get('total_formatted_transactions', 0)}")
        
        # Display bank-specific formatting results
        if 'bank_specific_data' in result:
            bank_data = result['bank_specific_data']
            print(f"\nBank-Specific Formatting:")
            print(f"  Success: {bank_data.get('success', False)}")
            if bank_data.get('success'):
                print(f"  Total Transactions: {bank_data.get('total_transactions', 0)}")
            else:
                print(f"  Error: {bank_data.get('error', 'Unknown error')}")
        
        # Display sample transactions
        if 'formatted_transactions' in result and result['formatted_transactions']:
            print(f"\nSample Transactions (first 5):")
            print("-" * 50)
            for i, transaction in enumerate(result['formatted_transactions'][:5]):
                print(f"  {i+1}. {transaction.get('date', 'N/A')} - {transaction.get('narration', 'N/A')} - {transaction.get('amount', 'N/A')} ({transaction.get('type', 'N/A')})")
        
        # Save detailed results to file
        output_filename = f"extracted_data_{SESSION_ID}_{BANK_NAME or 'auto'}.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nDetailed results saved to: {output_filename}")
        
        # Display first 500 characters of text content
        print("\nFirst 500 characters of extracted text:")
        print("-" * 50)
        print(result['text_content'][:500] + "..." if len(result['text_content']) > 500 else result['text_content'])
        
        return result
        
    except FileNotFoundError as e:
        print(f"File not found error: {str(e)}")
        print("Please check:")
        print("1. S3 bucket name is correct")
        print("2. Session ID exists in the bucket")
        print("3. AWS credentials are properly configured")
        
    except Exception as e:
        print(f"Error processing ePDF: {str(e)}")
        return None

def process_multiple_sessions():
    """
    Example of processing multiple ePDFs with different banks
    """
    # Example configuration for multiple sessions with different banks
    sessions_config = [
        {"session_id": "session_001", "bank": "HDFC"},
        {"session_id": "session_002", "bank": "ICICI"},
        {"session_id": "session_003", "bank": "SBI"},
        {"session_id": "session_004", "bank": None},  # Auto-detect
    ]
    
    bucket_name = os.getenv('S3_BUCKET_NAME', 'your-s3-bucket-name')
    
    processor = EPdfProcessor()
    
    results = {}
    for config in sessions_config:
        session_id = config["session_id"]
        bank_name = config["bank"]
        
        try:
            print(f"Processing session: {session_id}, bank: {bank_name or 'auto-detect'}")
            result = processor.process_epdf(bucket_name, session_id, bank_name)
            results[session_id] = {
                "success": True,
                "bank_name": result.get('bank_name', 'N/A'),
                "pages_count": result['pages_count'],
                "tables_count": len(result['tables']),
                "text_length": len(result['text_content']),
                "formatted_transactions": result.get('total_formatted_transactions', 0)
            }
        except Exception as e:
            print(f"Failed to process {session_id}: {str(e)}")
            results[session_id] = {
                "success": False,
                "error": str(e)
            }
    
    return results


def demonstrate_bank_formatters():
    """
    Demonstrate different bank formatters with sample text
    """
    from bank_formatters import BankFormatterFactory
    
    print("BankParser Bank Formatters Demonstration")
    print("=" * 50)
    
    # Sample text for different banks
    sample_texts = {
        "HDFC": """
        HDFC BANK
        Account Statement
        01/01/2024 UPI Payment to Merchant 1000.00
        02/01/2024 Salary Credit 50000.00
        03/01/2024 ATM Withdrawal 2000.00
        """,
        "ICICI": """
        ICICI BANK
        Account Statement
        01-01-2024 UPI Payment to Merchant 1000.00
        02-01-2024 Salary Credit 50000.00
        03-01-2024 ATM Withdrawal 2000.00
        """,
        "SBI": """
        STATE BANK OF INDIA
        Account Statement
        01/01/2024 UPI Payment to Merchant 1000.00
        02/01/2024 Salary Credit 50000.00
        03/01/2024 ATM Withdrawal 2000.00
        """
    }
    
    for bank_name, sample_text in sample_texts.items():
        print(f"\nTesting {bank_name} Formatter:")
        print("-" * 30)
        
        try:
            formatter = BankFormatterFactory.get_formatter(bank_name)
            result = formatter.format_transactions(sample_text)
            
            print(f"Success: {result.get('success', False)}")
            print(f"Bank: {result.get('bank_name', 'N/A')}")
            print(f"Total Transactions: {result.get('total_transactions', 0)}")
            
            if result.get('transactions'):
                print("Sample Transactions:")
                for i, transaction in enumerate(result['transactions'][:3]):
                    print(f"  {i+1}. {transaction.get('date', 'N/A')} - {transaction.get('narration', 'N/A')} - {transaction.get('amount', 'N/A')}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print(f"\nSupported Banks: {BankFormatterFactory.get_supported_banks()}")

if __name__ == "__main__":
    # Run bank formatters demonstration
    demonstrate_bank_formatters()
    
    print("\n" + "="*50)
    print("Single Session Processing Example")
    print("="*50)
    
    # Run single session example
    example_usage()
    
    # Uncomment to run multiple sessions example
    # print("\n" + "="*50)
    # print("Multiple Sessions Processing")
    # print("="*50)
    # multiple_results = process_multiple_sessions()
    # print(json.dumps(multiple_results, indent=2))
