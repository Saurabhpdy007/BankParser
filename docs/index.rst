CredNX Documentation
===================

Welcome to CredNX's documentation! CredNX is a comprehensive Python library for consuming ePDF files from AWS S3 buckets using session IDs and extracting structured data from them.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api
   examples
   configuration
   troubleshooting

Features
--------

* **S3 Integration**: Retrieve ePDF files from S3 using session ID as reference
* **Multiple Extraction Methods**: Uses PyMuPDF, pdfplumber, and PyPDF2 for comprehensive data extraction
* **Structured Output**: Returns extracted data as JSON with metadata, text content, tables, and image information
* **Error Handling**: Robust error handling with detailed logging
* **Configurable**: Environment-based configuration for easy deployment
* **Production Ready**: Comprehensive testing and documentation

Quick Start
-----------

.. code-block:: python

   from crednx import EPdfProcessor

   # Initialize processor
   processor = EPdfProcessor()

   # Process ePDF
   result = processor.process_epdf("your-bucket-name", "session-id-123")

   # Access extracted data
   print(f"Pages: {result['pages_count']}")
   print(f"Text: {result['text_content']}")
   print(f"Tables: {result['tables']}")

Installation
------------

.. code-block:: bash

   pip install crednx

Or from source:

.. code-block:: bash

   git clone https://github.com/crednx/crednx.git
   cd crednx
   pip install -r requirements.txt
   pip install -e .

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
