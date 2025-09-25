#!/usr/bin/env python3
"""
{BRAND_NAME} Deployment Script
==============================

A production-ready deployment script for the {BRAND_NAME} ePDF processing system.
Handles environment setup, validation, and initial configuration.

Usage:
    python deploy.py [--bsa-folder PATH] [--log-level LEVEL] [--create-example]

Options:
    --bsa-folder PATH    Set custom BSA folder path (default: ./BSA)
    --log-level LEVEL    Set logging level (default: INFO)
    --create-example     Create example session structure
    --validate-only      Only validate installation, don't deploy
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import json
import subprocess
from brand_config import BRAND_NAME, BRAND_VERSION, BRAND_AUTHOR

# Format the docstring with brand config
__doc__ = __doc__.format(BRAND_NAME=BRAND_NAME)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deploy.log')
    ]
)
logger = logging.getLogger(__name__)


class BSAParserDeployer:
    """Handles deployment and validation of BSAParser system"""
    
    def __init__(self, bsa_folder: str = "./BSA", log_level: str = "INFO"):
        self.bsa_folder = Path(bsa_folder)
        self.log_level = log_level
        
    def validate_environment(self) -> bool:
        """Validate Python environment and dependencies"""
        logger.info("🔍 Validating environment...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8 or higher is required")
            return False
        
        logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        
        # Check required packages
        required_packages = [
            'fitz', 'pdfplumber', 'PyPDF2', 'pandas', 'numpy'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ {package} is installed")
            except ImportError:
                missing_packages.append(package)
                logger.error(f"❌ {package} is missing")
        
        if missing_packages:
            logger.error(f"❌ Missing packages: {', '.join(missing_packages)}")
            logger.info("💡 Run: pip install -r requirements.txt")
            return False
        
        logger.info("✅ All required packages are installed")
        return True
    
    def create_directory_structure(self) -> bool:
        """Create necessary directory structure"""
        logger.info("📁 Creating directory structure...")
        
        try:
            # Create BSA folder
            self.bsa_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created BSA folder: {self.bsa_folder}")
            
            # Create example session
            example_session = self.bsa_folder / "session_001"
            example_session.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created example session: {example_session}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create directory structure: {e}")
            return False
    
    def create_config_file(self) -> bool:
        """Create configuration file"""
        logger.info("⚙️ Creating configuration file...")
        
        config_content = f'''#!/usr/bin/env python3
"""
{BRAND_NAME} Configuration
==========================

Configuration settings for the {BRAND_NAME} ePDF processing system.
"""

import os
from pathlib import Path

class Config:
    """Configuration class for {BRAND_NAME} system"""
    
    # Directory settings
    BSA_FOLDER = Path("{self.bsa_folder}")
    
    # Processing settings
    SUPPORTED_EXTENSIONS = ['.pdf', '.PDF']
    MAX_FILE_SIZE_MB = 100
    MAX_PAGES_PER_PDF = 1000
    
    # Logging settings
    LOG_LEVEL = "{self.log_level}"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Validation settings
    MIN_TEXT_LENGTH = 100
    TRANSACTION_KEYWORDS = [
        'transaction', 'date', 'amount', 'balance', 'debit', 'credit',
        'narration', 'reference', 'upi', 'neft', 'imps'
    ]
    
    # Output settings
    OUTPUT_FORMAT = 'json'
    INCLUDE_CSV = True
    INCLUDE_METADATA = True
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings"""
        if not cls.BSA_FOLDER.exists():
            cls.BSA_FOLDER.mkdir(parents=True, exist_ok=True)
        return True
'''
        
        try:
            with open('config.py', 'w') as f:
                f.write(config_content)
            logger.info("✅ Created config.py")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create config.py: {e}")
            return False
    
    def create_example_session(self) -> bool:
        """Create example session with sample data"""
        logger.info("📄 Creating example session...")
        
        try:
            example_session = self.bsa_folder / "session_001"
            
            # Create README for example session
            readme_content = f"""# Example Session

This is an example session folder for {BRAND_NAME} ePDF processing.

## How to use:

1. Add your PDF files to this folder
2. Run the processing script:
   ```python
   from local_epdf_processor import LocalEPdfProcessor
   
   processor = LocalEPdfProcessor()
   result = processor.process_session("session_001")
   ```

## Supported file types:
- PDF files (.pdf, .PDF)

## Notes:
- Only text-based PDFs (ePDFs) are supported
- Scanned/image PDFs will be rejected
- Processing results will be saved in the extractedData subfolder
"""
            
            with open(example_session / "README.md", 'w') as f:
                f.write(readme_content)
            
            logger.info("✅ Created example session README")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create example session: {e}")
            return False
    
    def run_system_test(self) -> bool:
        """Run a basic system test"""
        logger.info("🧪 Running system test...")
        
        try:
            # Import main modules
            from local_epdf_processor import LocalEPdfProcessor
            from bank_formatters.hdfc_formatter import TransactionFormatter
            
            # Test processor initialization
            processor = LocalEPdfProcessor(str(self.bsa_folder))
            logger.info("✅ LocalEPdfProcessor initialized")
            
            # Test formatter initialization
            formatter = TransactionFormatter()
            logger.info("✅ TransactionFormatter initialized")
            
            # Test session listing
            sessions = processor.list_all_sessions()
            logger.info(f"✅ Found {len(sessions)} sessions")
            
            logger.info("✅ System test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ System test failed: {e}")
            return False
    
    def deploy(self, create_example: bool = False) -> bool:
        """Deploy the BSAParser system"""
        logger.info(f"🚀 Starting {BRAND_NAME} deployment...")
        
        steps = [
            ("Environment validation", self.validate_environment),
            ("Directory structure creation", self.create_directory_structure),
            ("Configuration file creation", self.create_config_file),
            ("System test", self.run_system_test),
        ]
        
        if create_example:
            steps.append(("Example session creation", self.create_example_session))
        
        for step_name, step_func in steps:
            logger.info(f"📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ Deployment failed at: {step_name}")
                return False
            logger.info(f"✅ {step_name} completed")
        
        logger.info(f"🎉 {BRAND_NAME} deployment completed successfully!")
        logger.info(f"📁 BSA folder: {self.bsa_folder}")
        logger.info(f"📝 Log level: {self.log_level}")
        logger.info("💡 Ready to process PDF files!")
        
        return True


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(
        description=f"Deploy {BRAND_NAME} ePDF processing system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--bsa-folder',
        default='./BSA',
        help='Set custom BSA folder path (default: ./BSA)'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--create-example',
        action='store_true',
        help='Create example session structure'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate installation, don\'t deploy'
    )
    
    args = parser.parse_args()
    
    # Update logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Initialize deployer
    deployer = BSAParserDeployer(args.bsa_folder, args.log_level)
    
    if args.validate_only:
        logger.info("🔍 Running validation only...")
        success = deployer.validate_environment()
        if success:
            logger.info("✅ Validation passed")
        else:
            logger.error("❌ Validation failed")
        return success
    else:
        return deployer.deploy(args.create_example)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
