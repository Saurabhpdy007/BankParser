#!/usr/bin/env python3
"""
PDF Password Utilities
=====================

Utility functions for handling password-protected PDFs in the CredNX system.
Provides detection, validation, and unlocking capabilities for encrypted PDFs.

Features:
- Password protection detection
- PDF unlocking with provided password
- Error handling for invalid passwords
- Support for multiple PDF libraries

Author: CredNX Team
"""

import logging
from typing import Optional, Tuple
import fitz  # PyMuPDF
import PyPDF2
from io import BytesIO

logger = logging.getLogger(__name__)


class PDFPasswordHandler:
    """
    Handles password-protected PDF operations
    """
    
    @staticmethod
    def is_password_protected(pdf_content: bytes) -> bool:
        """
        Check if a PDF is password protected
        
        Args:
            pdf_content: PDF content as bytes
            
        Returns:
            bool: True if PDF is password protected, False otherwise
        """
        try:
            # Method 1: Try PyMuPDF (fitz)
            try:
                doc = fitz.open(stream=pdf_content, filetype="pdf")
                # Check if document needs password
                needs_pass = doc.needs_pass
                doc.close()
                logger.info(f"PyMuPDF check: needs_pass = {needs_pass}")
                return needs_pass
            except Exception as e:
                error_msg = str(e).lower()
                logger.warning(f"PyMuPDF error: {str(e)}")
                # Check for password-related errors
                if any(keyword in error_msg for keyword in ["password", "encrypted", "permission", "security"]):
                    logger.info("PyMuPDF indicates password protection")
                    return True
                # Other errors might indicate corruption or other issues
                logger.warning(f"PyMuPDF error (might be password protected): {str(e)}")
            
            # Method 2: Try PyPDF2 as backup
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
                is_encrypted = pdf_reader.is_encrypted
                logger.info(f"PyPDF2 check: is_encrypted = {is_encrypted}")
                return is_encrypted
            except Exception as e:
                logger.warning(f"PyPDF2 error: {str(e)}")
                # If both methods fail, assume it's password protected
                return True
                
        except Exception as e:
            logger.error(f"Error checking password protection: {str(e)}")
            # If we can't determine, assume it's protected to be safe
            return True
    
    @staticmethod
    def unlock_pdf_with_password(pdf_content: bytes, password: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Attempt to unlock a password-protected PDF
        
        Args:
            pdf_content: PDF content as bytes
            password: Password to unlock the PDF
            
        Returns:
            Tuple of (success, unlocked_content, error_message)
        """
        logger.info(f"Attempting to unlock PDF with password (length: {len(password)})")
        
        try:
            # Method 1: Try PyMuPDF (fitz) first
            try:
                doc = fitz.open(stream=pdf_content, filetype="pdf")
                logger.info(f"PyMuPDF: Document opened, needs_pass = {doc.needs_pass}")
                
                # Check if document is encrypted
                if doc.needs_pass:
                    logger.info("PDF is encrypted, attempting authentication...")
                    # Try to authenticate with password
                    auth_result = doc.authenticate(password)
                    logger.info(f"Authentication result: {auth_result}")
                    
                    if auth_result:
                        logger.info("Successfully unlocked PDF with PyMuPDF")
                        # Get the unlocked content
                        unlocked_content = doc.write()
                        doc.close()
                        return True, unlocked_content, None
                    else:
                        doc.close()
                        logger.error("PyMuPDF authentication failed - invalid password")
                        return False, None, "Invalid password provided"
                else:
                    # Document is not encrypted
                    logger.info("PDF is not encrypted according to PyMuPDF")
                    doc.close()
                    return True, pdf_content, None
                    
            except Exception as e:
                logger.warning(f"PyMuPDF unlock failed: {str(e)}")
            
            # Method 2: Try PyPDF2 as backup
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
                logger.info(f"PyPDF2: Document opened, is_encrypted = {pdf_reader.is_encrypted}")
                
                if pdf_reader.is_encrypted:
                    logger.info("PDF is encrypted according to PyPDF2, attempting decryption...")
                    # Try to decrypt with password
                    decrypt_result = pdf_reader.decrypt(password)
                    logger.info(f"Decryption result: {decrypt_result}")
                    
                    if decrypt_result:
                        logger.info("Successfully unlocked PDF with PyPDF2")
                        # Create a new PDF with unlocked content
                        pdf_writer = PyPDF2.PdfWriter()
                        for page in pdf_reader.pages:
                            pdf_writer.add_page(page)
                        
                        # Write to bytes
                        output_buffer = BytesIO()
                        pdf_writer.write(output_buffer)
                        unlocked_content = output_buffer.getvalue()
                        output_buffer.close()
                        
                        return True, unlocked_content, None
                    else:
                        logger.error("PyPDF2 decryption failed - invalid password")
                        return False, None, "Invalid password provided"
                else:
                    # Document is not encrypted
                    logger.info("PDF is not encrypted according to PyPDF2")
                    return True, pdf_content, None
                    
            except Exception as e:
                logger.error(f"PyPDF2 unlock failed: {str(e)}")
                return False, None, f"Failed to unlock PDF: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error unlocking PDF: {str(e)}")
            return False, None, f"Unexpected error: {str(e)}"
    
    @staticmethod
    def validate_password_protection(pdf_content: bytes, password: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[bytes]]:
        """
        Validate password protection and unlock if needed
        
        Args:
            pdf_content: PDF content as bytes
            password: Optional password for protected PDFs
            
        Returns:
            Tuple of (is_valid, error_message, unlocked_content)
        """
        try:
            # Check if PDF is password protected
            is_protected = PDFPasswordHandler.is_password_protected(pdf_content)
            
            if is_protected:
                if password is None:
                    return False, "Password Protected File", None
                
                # Try to unlock with provided password
                success, unlocked_content, error_msg = PDFPasswordHandler.unlock_pdf_with_password(
                    pdf_content, password
                )
                
                if success:
                    return True, None, unlocked_content
                else:
                    return False, error_msg or "Failed to unlock PDF", None
            else:
                # PDF is not protected, return original content
                return True, None, pdf_content
                
        except Exception as e:
            logger.error(f"Error validating password protection: {str(e)}")
            return False, f"Error validating PDF: {str(e)}", None


def check_pdf_password_protection(pdf_content: bytes) -> bool:
    """
    Simple function to check if PDF is password protected
    
    Args:
        pdf_content: PDF content as bytes
        
    Returns:
        bool: True if password protected, False otherwise
    """
    return PDFPasswordHandler.is_password_protected(pdf_content)


def unlock_pdf(pdf_content: bytes, password: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
    """
    Simple function to unlock password-protected PDF
    
    Args:
        pdf_content: PDF content as bytes
        password: Password to unlock PDF
        
    Returns:
        Tuple of (success, unlocked_content, error_message)
    """
    return PDFPasswordHandler.unlock_pdf_with_password(pdf_content, password)


def validate_and_unlock_pdf(pdf_content: bytes, password: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[bytes]]:
    """
    Simple function to validate and unlock PDF if needed
    
    Args:
        pdf_content: PDF content as bytes
        password: Optional password for protected PDFs
        
    Returns:
        Tuple of (is_valid, error_message, unlocked_content)
    """
    return PDFPasswordHandler.validate_password_protection(pdf_content, password)
