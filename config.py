"""
Configuration file for BankParser ePDF processing
"""

import os
from typing import Optional

class Config:
    """Configuration class for BankParser ePDF processing"""
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION: str = os.getenv('AWS_REGION', 'us-east-1')
    
    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv('S3_BUCKET_NAME', 'your-s3-bucket-name')
    S3_EPDF_PREFIX: str = os.getenv('S3_EPDF_PREFIX', 'epdfs/')  # Prefix for ePDF files in S3
    
    # Processing Configuration
    MAX_FILE_SIZE_MB: int = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    EXTRACTION_TIMEOUT_SECONDS: int = int(os.getenv('EXTRACTION_TIMEOUT_SECONDS', '300'))
    
    # Output Configuration
    OUTPUT_DIRECTORY: str = os.getenv('OUTPUT_DIRECTORY', './output')
    SAVE_INDIVIDUAL_PAGES: bool = os.getenv('SAVE_INDIVIDUAL_PAGES', 'false').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        required_fields = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'S3_BUCKET_NAME'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)"""
        print("BankParser Configuration:")
        print("-" * 30)
        print(f"AWS Region: {cls.AWS_REGION}")
        print(f"S3 Bucket: {cls.S3_BUCKET_NAME}")
        print(f"S3 ePDF Prefix: {cls.S3_EPDF_PREFIX}")
        print(f"Max File Size: {cls.MAX_FILE_SIZE_MB} MB")
        print(f"Output Directory: {cls.OUTPUT_DIRECTORY}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"AWS Credentials: {'Configured' if cls.AWS_ACCESS_KEY_ID else 'Not Configured'}")
