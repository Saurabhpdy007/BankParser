#!/usr/bin/env python3
"""
Example usage script for ePDF processing from S3
"""

import os
import json
from epdf_processor import EPdfProcessor

def example_usage():
    """
    Example of how to use the EPdfProcessor class
    """
    
    # Configuration - Set these as environment variables or replace with actual values
    BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'your-s3-bucket-name')
    SESSION_ID = os.getenv('SESSION_ID', 'your-session-id')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    print("CredNX ePDF Processor Example")
    print("=" * 50)
    
    try:
        # Initialize processor
        print("Initializing ePDF processor...")
        processor = EPdfProcessor(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        # Process ePDF
        print(f"Processing ePDF for session_id: {SESSION_ID}")
        result = processor.process_epdf(BUCKET_NAME, SESSION_ID)
        
        # Display results summary
        print("\nExtraction Results Summary:")
        print("-" * 30)
        print(f"Session ID: {result['session_id']}")
        print(f"Pages Count: {result['pages_count']}")
        print(f"Extraction Method: {result['extraction_method']}")
        print(f"Tables Found: {len(result['tables'])}")
        print(f"Images Found: {len(result['images_info'])}")
        print(f"Text Length: {len(result['text_content'])} characters")
        
        # Save detailed results to file
        output_filename = f"extracted_data_{SESSION_ID}.json"
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
    Example of processing multiple ePDFs
    """
    session_ids = ["session_001", "session_002", "session_003"]
    bucket_name = os.getenv('S3_BUCKET_NAME', 'your-s3-bucket-name')
    
    processor = EPdfProcessor()
    
    results = {}
    for session_id in session_ids:
        try:
            print(f"Processing session: {session_id}")
            result = processor.process_epdf(bucket_name, session_id)
            results[session_id] = {
                "success": True,
                "pages_count": result['pages_count'],
                "tables_count": len(result['tables']),
                "text_length": len(result['text_content'])
            }
        except Exception as e:
            print(f"Failed to process {session_id}: {str(e)}")
            results[session_id] = {
                "success": False,
                "error": str(e)
            }
    
    return results

if __name__ == "__main__":
    # Run single session example
    example_usage()
    
    # Uncomment to run multiple sessions example
    # print("\n" + "="*50)
    # print("Multiple Sessions Processing")
    # print("="*50)
    # multiple_results = process_multiple_sessions()
    # print(json.dumps(multiple_results, indent=2))
