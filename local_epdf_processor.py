#!/usr/bin/env python3
"""
CredNX Local ePDF Processor
===========================

A comprehensive ePDF processing system for bank statement extraction and analysis.
Handles local file-based processing with advanced features:

- ePDF validation (text-based vs scanned PDFs)
- Multi-library text extraction (PyMuPDF, pdfplumber, PyPDF2)
- Comprehensive data extraction (text, tables, images, metadata)
- Transaction formatting and structuring
- Session-based organization
- Error handling and validation

Version: 2.0
Author: CredNX Team
"""

import os
import json
import logging
import glob
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import fitz  # PyMuPDF
import pdfplumber
import PyPDF2
from io import BytesIO
import pandas as pd
from datetime import datetime
from text_formatter import TransactionFormatter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LocalEPdfProcessor:
    """
    A class to handle local ePDF processing from BSA folder structure
    """
    
    def __init__(self, bsa_folder_path: str = "./BSA"):
        """
        Initialize the local ePDF processor
        
        Args:
            bsa_folder_path: Path to the BSA folder containing session IDs
        """
        self.bsa_folder_path = Path(bsa_folder_path)
        self.supported_extensions = ['.pdf', '.PDF']
        
        # Validate BSA folder exists
        if not self.bsa_folder_path.exists():
            logger.warning(f"BSA folder does not exist: {self.bsa_folder_path}")
            logger.info("Creating BSA folder structure...")
            self.bsa_folder_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Local ePDF processor initialized with BSA folder: {self.bsa_folder_path}")
    
    def is_epdf(self, pdf_path: Path) -> bool:
        """
        Check if a PDF is a true ePDF (text-based) and not a scanned/image PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            bool: True if it's an ePDF, False if it's scanned/image
        """
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            
            # Check first few pages for text content
            text_content = ""
            pages_to_check = min(3, len(doc))  # Check first 3 pages or all pages if less than 3
            
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text()
                text_content += text
            
            doc.close()
            
            # Check if we have substantial text content
            # Scanned PDFs typically have very little or no text
            text_length = len(text_content.strip())
            
            # Also check for common scanned PDF characteristics
            has_substantial_text = text_length > 100  # At least 100 characters of text
            
            # Additional check: look for common text patterns that indicate ePDF
            has_text_patterns = any(pattern in text_content.lower() for pattern in [
                'transaction', 'date', 'amount', 'balance', 'debit', 'credit', 
                'narration', 'reference', 'upi', 'neft', 'imps'
            ])
            
            is_valid_epdf = has_substantial_text and has_text_patterns
            
            if not is_valid_epdf:
                logger.warning(f"PDF appears to be scanned/image-based: {pdf_path.name} (text length: {text_length})")
            
            return is_valid_epdf
            
        except Exception as e:
            logger.error(f"Error checking PDF type for {pdf_path.name}: {str(e)}")
            return False
    
    def get_session_folder(self, session_id: str) -> Path:
        """
        Get the session folder path for a given session ID
        
        Args:
            session_id: Session ID to look for
            
        Returns:
            Path: Path to the session folder
        """
        return self.bsa_folder_path / session_id
    
    def get_extracted_data_folder(self, session_id: str) -> Path:
        """
        Get the extractedData folder path for a given session ID
        
        Args:
            session_id: Session ID to look for
            
        Returns:
            Path: Path to the extractedData folder within the session
        """
        session_folder = self.get_session_folder(session_id)
        extracted_data_folder = session_folder / "extractedData"
        return extracted_data_folder
    
    def create_extracted_data_folder(self, session_id: str) -> Path:
        """
        Create the extractedData folder for a session if it doesn't exist
        
        Args:
            session_id: Session ID to create folder for
            
        Returns:
            Path: Path to the created extractedData folder
        """
        extracted_data_folder = self.get_extracted_data_folder(session_id)
        extracted_data_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created/verified extractedData folder: {extracted_data_folder}")
        return extracted_data_folder
    
    def get_existing_results(self, session_id: str) -> Dict[str, Any]:
        """
        Get existing results from previous runs for a session
        
        Args:
            session_id: Session ID to get results for
            
        Returns:
            Dict[str, Any]: Existing results or empty structure
        """
        extracted_data_folder = self.get_extracted_data_folder(session_id)
        results_file = extracted_data_folder / "session_results.json"
        
        if results_file.exists():
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                logger.info(f"Found existing results for session {session_id}")
                return existing_results
            except Exception as e:
                logger.warning(f"Failed to read existing results for {session_id}: {str(e)}")
        
        # Return empty structure for new sessions
        return {
            "session_id": session_id,
            "total_runs": 0,
            "runs": [],
            "latest_run": None,
            "created_at": None,
            "last_updated": None
        }
    
    def save_comprehensive_results(self, session_id: str, current_run_data: Dict[str, Any], start_time: float = None) -> str:
        """
        Save comprehensive results in a single file with all metadata and extracted text
        
        Args:
            session_id: Session ID
            current_run_data: Current run data to save
            
        Returns:
            str: Path to the saved comprehensive results file
        """
        # Create comprehensive output structure
        comprehensive_data = {
            "session_info": {
                "session_id": session_id,
                "processing_timestamp": str(pd.Timestamp.now()),
                "processing_datetime": datetime.now().isoformat(),
                "bsa_folder": str(self.bsa_folder_path),
                "session_folder": str(self.get_session_folder(session_id))
            },
            "extraction_summary": {
                "success": current_run_data.get("success", False),
                "pdfs_found": current_run_data.get("pdfs_found", 0),
                "pdfs_processed": current_run_data.get("pdfs_processed", 0),
                "pdfs_failed": current_run_data.get("pdfs_failed", 0),
                "total_pages": current_run_data.get("combined_data", {}).get("total_pages", 0),
                "total_text_length": current_run_data.get("combined_data", {}).get("total_text_length", 0),
                "total_tables": current_run_data.get("combined_data", {}).get("total_tables", 0),
                "total_images": current_run_data.get("combined_data", {}).get("total_images", 0),
                "extraction_method": current_run_data.get("pdfs", [{}])[0].get("extraction_method", "unknown") if current_run_data.get("pdfs") else "unknown"
            },
            "all_extracted_text": current_run_data.get("combined_data", {}).get("all_text_content", ""),
            "all_metadata": current_run_data.get("combined_data", {}).get("all_metadata", []),
            "all_tables": current_run_data.get("combined_data", {}).get("all_tables", []),
            "all_images": current_run_data.get("combined_data", {}).get("all_images", []),
            "individual_pdfs": current_run_data.get("pdfs", []),
            "processing_details": {
                "files_processed": [
                    {
                        "file_name": pdf.get("pdf_name", "unknown"),
                        "file_path": pdf.get("file_path", "unknown"),
                        "file_size": pdf.get("file_size", 0),
                        "pages": pdf.get("pages_count", 0),
                        "text_length": len(pdf.get("text_content", "")),
                        "tables_count": len(pdf.get("tables", [])),
                        "images_count": len(pdf.get("images_info", [])),
                        "metadata": pdf.get("metadata", {}),
                        "extraction_method": pdf.get("extraction_method", "unknown")
                    }
                    for pdf in current_run_data.get("pdfs", [])
                ]
            }
        }
        
        # Create extractedData folder
        extracted_data_folder = self.create_extracted_data_folder(session_id)
        
        # Save comprehensive results in a single file
        comprehensive_file = extracted_data_folder / f"{session_id}_extracted_data.json"
        with open(comprehensive_file, "w", encoding="utf-8") as f:
            json.dump(comprehensive_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved comprehensive results for session {session_id}: {comprehensive_file}")
        
        # Run formatting function to add transaction structure
        try:
            formatter = TransactionFormatter()
            
            # Generate clean formatted file and CSV
            formatted_file = formatter.save_formatted_file(str(comprehensive_file))
            logger.info(f"Saved clean formatted transaction data: {formatted_file}")
            
        except Exception as e:
            logger.error(f"Error formatting transactions: {str(e)}")
        
        # Calculate and display total processing time
        if start_time is not None:
            end_time = time.time()
            total_time = end_time - start_time
            minutes = int(total_time // 60)
            seconds = int(total_time % 60)
            logger.info(f"⏱️  Total processing time: {minutes:02d}:{seconds:02d}")
        
        return str(comprehensive_file)
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session ID exists in the BSA folder
        
        Args:
            session_id: Session ID to check
            
        Returns:
            bool: True if session exists, False otherwise
        """
        session_folder = self.get_session_folder(session_id)
        return session_folder.exists() and session_folder.is_dir()
    
    def get_session_pdfs(self, session_id: str) -> List[Path]:
        """
        Get all PDF files for a given session ID
        
        Args:
            session_id: Session ID to get PDFs for
            
        Returns:
            List[Path]: List of PDF file paths
        """
        if not self.session_exists(session_id):
            return []
        
        session_folder = self.get_session_folder(session_id)
        pdf_files = []
        
        # Find all PDF files in the session folder
        for extension in self.supported_extensions:
            pattern = f"*{extension}"
            pdf_files.extend(session_folder.glob(pattern))
        
        # Also check subdirectories if any
        for extension in self.supported_extensions:
            pattern = f"**/*{extension}"
            pdf_files.extend(session_folder.glob(pattern))
        
        # Remove duplicates and sort
        pdf_files = sorted(list(set(pdf_files)))
        
        logger.info(f"Found {len(pdf_files)} PDF files for session: {session_id}")
        return pdf_files
    
    def read_pdf_file(self, pdf_path: Path) -> bytes:
        """
        Read PDF file and return its content as bytes
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            bytes: PDF content as bytes
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            logger.info(f"Successfully read PDF: {pdf_path.name}")
            return pdf_content
        except Exception as e:
            logger.error(f"Failed to read PDF {pdf_path}: {str(e)}")
            raise
    
    def extract_data_from_epdf(self, pdf_content: bytes, pdf_name: str = "unknown") -> Dict[str, Any]:
        """
        Extract data from ePDF content and return as JSON
        (Same as original EPdfProcessor but with additional file info)
        
        Args:
            pdf_content: PDF content as bytes
            pdf_name: Name of the PDF file for logging
            
        Returns:
            Dict[str, Any]: Extracted data as dictionary
        """
        extracted_data = {
            "metadata": {},
            "text_content": "",
            "tables": [],
            "images_info": [],
            "pages_count": 0,
            "extraction_method": "multiple",
            "pdf_name": pdf_name
        }
        
        try:
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
            
            logger.info(f"Successfully extracted data from {pdf_name} with {extracted_data['pages_count']} pages")
            
        except Exception as e:
            logger.error(f"Error extracting data from {pdf_name}: {str(e)}")
            # Fallback to basic PyPDF2 extraction
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
                extracted_data["pages_count"] = len(pdf_reader.pages)
                extracted_data["extraction_method"] = "fallback_pypdf2"
                
                text_content = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    text_content += f"\n--- Page {page_num + 1} ---\n{page.extract_text()}"
                
                extracted_data["text_content"] = text_content.strip()
                logger.info(f"Used fallback PyPDF2 extraction method for {pdf_name}")
                
            except Exception as fallback_error:
                logger.error(f"Fallback extraction also failed for {pdf_name}: {str(fallback_error)}")
                raise
        
        return extracted_data
    
    def process_session(self, session_id: str) -> Dict[str, Any]:
        """
        Process all ePDFs for a given session ID
        
        Args:
            session_id: Session ID to process
            
        Returns:
            Dict[str, Any]: Combined extracted data from all PDFs in the session
        """
        start_time = time.time()
        logger.info(f"Starting session processing for: {session_id}")
        
        # Check if session exists
        if not self.session_exists(session_id):
            error_msg = f"No Such Session Exists: {session_id}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "session_id": session_id,
                "success": False
            }
        
        # Get all PDFs for the session
        pdf_files = self.get_session_pdfs(session_id)
        
        if not pdf_files:
            error_msg = f"No PDF files found for session: {session_id}"
            logger.warning(error_msg)
            return {
                "error": error_msg,
                "session_id": session_id,
                "success": False,
                "pdfs_found": 0
            }
        
        # Validate all PDFs are ePDFs before processing
        scanned_pdfs = []
        for pdf_path in pdf_files:
            if not self.is_epdf(pdf_path):
                scanned_pdfs.append(pdf_path.name)
        
        if scanned_pdfs:
            error_msg = f"Please pass ePDFs for processing. The following files appear to be scanned/image PDFs: {', '.join(scanned_pdfs)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "session_id": session_id,
                "success": False,
                "pdfs_found": len(pdf_files),
                "scanned_pdfs": scanned_pdfs
            }
        
        # Process each PDF
        session_results = {
            "session_id": session_id,
            "success": True,
            "pdfs_found": len(pdf_files),
            "pdfs_processed": 0,
            "pdfs_failed": 0,
            "processing_timestamp": str(pd.Timestamp.now()),
            "pdfs": [],
            "combined_data": {
                "total_pages": 0,
                "total_text_length": 0,
                "total_tables": 0,
                "total_images": 0,
                "all_text_content": "",
                "all_metadata": [],
                "all_tables": [],
                "all_images": []
            }
        }
        
        for pdf_path in pdf_files:
            try:
                logger.info(f"Processing PDF: {pdf_path.name}")
                
                # Check if PDF is a true ePDF (text-based) and not scanned/image
                if not self.is_epdf(pdf_path):
                    error_msg = f"Please pass ePDFs for processing. File '{pdf_path.name}' appears to be a scanned/image PDF."
                    logger.error(error_msg)
                    session_results["pdfs_failed"] += 1
                    session_results["pdfs"].append({
                        "file_name": pdf_path.name,
                        "file_path": str(pdf_path),
                        "error": error_msg,
                        "success": False
                    })
                    continue
                
                # Read PDF content
                pdf_content = self.read_pdf_file(pdf_path)
                
                # Extract data
                extracted_data = self.extract_data_from_epdf(pdf_content, pdf_path.name)
                
                # Add file path info
                extracted_data["file_path"] = str(pdf_path)
                extracted_data["file_size"] = len(pdf_content)
                
                # Add to session results
                session_results["pdfs"].append(extracted_data)
                session_results["pdfs_processed"] += 1
                
                # Update combined data
                session_results["combined_data"]["total_pages"] += extracted_data["pages_count"]
                session_results["combined_data"]["total_text_length"] += len(extracted_data["text_content"])
                session_results["combined_data"]["total_tables"] += len(extracted_data["tables"])
                session_results["combined_data"]["total_images"] += len(extracted_data["images_info"])
                
                # Combine text content
                session_results["combined_data"]["all_text_content"] += f"\n\n=== {pdf_path.name} ===\n"
                session_results["combined_data"]["all_text_content"] += extracted_data["text_content"]
                
                # Combine metadata
                session_results["combined_data"]["all_metadata"].append({
                    "file_name": pdf_path.name,
                    "metadata": extracted_data["metadata"]
                })
                
                # Combine tables
                for table in extracted_data["tables"]:
                    table["source_file"] = pdf_path.name
                    session_results["combined_data"]["all_tables"].append(table)
                
                # Combine images
                for image in extracted_data["images_info"]:
                    image["source_file"] = pdf_path.name
                    session_results["combined_data"]["all_images"].append(image)
                
                logger.info(f"Successfully processed: {pdf_path.name}")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_path.name}: {str(e)}")
                session_results["pdfs_failed"] += 1
                session_results["pdfs"].append({
                    "file_name": pdf_path.name,
                    "file_path": str(pdf_path),
                    "error": str(e),
                    "success": False
                })
        
        # Determine overall success
        if session_results["pdfs_failed"] == len(pdf_files):
            session_results["success"] = False
            session_results["error"] = "All PDFs failed to process"
        elif session_results["pdfs_failed"] > 0:
            session_results["warning"] = f"{session_results['pdfs_failed']} out of {len(pdf_files)} PDFs failed to process"
        
        logger.info(f"Session processing completed for {session_id}: {session_results['pdfs_processed']}/{len(pdf_files)} PDFs processed successfully")
        
        # Save comprehensive results in single file
        if session_results["success"] or session_results["pdfs_processed"] > 0:
            results_file_path = self.save_comprehensive_results(session_id, session_results, start_time)
            session_results["results_file_path"] = results_file_path
            session_results["extracted_data_folder"] = str(self.get_extracted_data_folder(session_id))
        
        return session_results
    
    def list_all_sessions(self) -> List[str]:
        """
        List all available session IDs in the BSA folder
        
        Returns:
            List[str]: List of session IDs
        """
        sessions = []
        
        if self.bsa_folder_path.exists():
            for item in self.bsa_folder_path.iterdir():
                if item.is_dir():
                    sessions.append(item.name)
        
        sessions.sort()
        logger.info(f"Found {len(sessions)} sessions: {sessions}")
        return sessions
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of a session without processing PDFs
        
        Args:
            session_id: Session ID to summarize
            
        Returns:
            Dict[str, Any]: Session summary
        """
        if not self.session_exists(session_id):
            return {
                "session_id": session_id,
                "exists": False,
                "error": f"No Such Session Exists: {session_id}"
            }
        
        pdf_files = self.get_session_pdfs(session_id)
        extracted_data_folder = self.get_extracted_data_folder(session_id)
        
        # Check if comprehensive results file exists
        comprehensive_file = extracted_data_folder / f"{session_id}_extracted_data.json"
        has_extracted_data = comprehensive_file.exists()
        
        summary = {
            "session_id": session_id,
            "exists": True,
            "pdf_count": len(pdf_files),
            "pdf_files": [str(pdf) for pdf in pdf_files],
            "session_folder": str(self.get_session_folder(session_id)),
            "extracted_data_folder": str(extracted_data_folder),
            "has_extracted_data": has_extracted_data,
            "extracted_data_file": str(comprehensive_file) if has_extracted_data else None
        }
        
        return summary
    
    def get_run_history(self, session_id: str) -> Dict[str, Any]:
        """
        Get the complete run history for a session
        
        Args:
            session_id: Session ID to get history for
            
        Returns:
            Dict[str, Any]: Complete run history
        """
        if not self.session_exists(session_id):
            return {
                "session_id": session_id,
                "exists": False,
                "error": f"No Such Session Exists: {session_id}"
            }
        
        return self.get_existing_results(session_id)
    
    def list_extraction_files(self, session_id: str) -> List[str]:
        """
        List all extraction result files for a session
        
        Args:
            session_id: Session ID to list files for
            
        Returns:
            List[str]: List of extraction file paths
        """
        if not self.session_exists(session_id):
            return []
        
        extracted_data_folder = self.get_extracted_data_folder(session_id)
        
        if not extracted_data_folder.exists():
            return []
        
        # Get all JSON files in the extractedData folder
        json_files = list(extracted_data_folder.glob("*.json"))
        return [str(f) for f in sorted(json_files)]


def main():
    """
    Main function to run the local ePDF processor with session selection
    """
    import sys
    
    # Initialize processor
    processor = LocalEPdfProcessor("./BSA")
    
    # List all available sessions
    logger.info("Available Sessions:")
    sessions = processor.list_all_sessions()
    logger.info(f"Found {len(sessions)} sessions: {sessions}")
    for session in sessions:
        logger.info(f"  - {session}")
    
    if not sessions:
        logger.info("No sessions found. Creating example structure...")
        
        # Create example session structure
        example_session = "session_001"
        session_folder = processor.get_session_folder(example_session)
        session_folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created example session folder: {session_folder}")
        logger.info("Please add PDF files to this folder and run the script again.")
        return
    
    # Check if session ID is provided as command line argument
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        logger.info(f"Processing specified session: {session_id}")
    else:
        # Interactive mode - ask user to choose
        print("\n" + "="*50)
        print("🎯 CredNX Session Selector")
        print("="*50)
        print("Available sessions:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session}")
        
        while True:
            try:
                choice = input(f"\nEnter session number (1-{len(sessions)}) or session name: ").strip()
                
                # Check if it's a number
                if choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(sessions):
                        session_id = sessions[choice_num - 1]
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(sessions)}")
                else:
                    # Check if it's a valid session name
                    if choice in sessions:
                        session_id = choice
                        break
                    else:
                        print(f"Session '{choice}' not found. Available sessions: {', '.join(sessions)}")
                        
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return
            except Exception as e:
                print(f"Invalid input: {e}")
        
        logger.info(f"Processing selected session: {session_id}")
    
    # Validate session exists
    if not processor.session_exists(session_id):
        logger.error(f"Session '{session_id}' does not exist!")
        logger.info(f"Available sessions: {', '.join(sessions)}")
        return
    
    try:
        result = processor.process_session(session_id)
        
        if result["success"]:
            logger.info(f"✓ Successfully processed {result['pdfs_processed']} PDFs")
            logger.info(f"  Total pages: {result['combined_data']['total_pages']}")
            logger.info(f"  Total text length: {result['combined_data']['total_text_length']} characters")
            logger.info(f"  Total tables: {result['combined_data']['total_tables']}")
            logger.info(f"  Total images: {result['combined_data']['total_images']}")
            
            # Save results
            output_file = f"session_results_{session_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to: {output_file}")
            
        else:
            logger.error(f"✗ Processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
