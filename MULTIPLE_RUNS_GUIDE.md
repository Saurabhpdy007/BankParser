# BankParser Multiple Runs Functionality Guide

## 🎉 **New Feature: Multiple Runs with ExtractedData Folder**

Your BankParser system now supports **multiple extraction runs** for the same session, with automatic organization and history tracking!

## 📁 **New Folder Structure**

When you process a session, the system now creates an `extractedData` folder within each session:

```
BSA/
├── session_001/
│   ├── contract_001.pdf
│   ├── invoice_001.pdf
│   └── extractedData/          ← NEW FOLDER
│       ├── session_results.json    ← Main results with run history
│       ├── run_001_20250921_002337.json  ← Individual run #1
│       ├── run_002_20250921_002337.json  ← Individual run #2
│       └── run_003_20250921_002341.json  ← Individual run #3
├── session_002/
│   ├── report_002.pdf
│   └── extractedData/
│       ├── session_results.json
│       └── run_001_20250921_002337.json
└── session_003/
    ├── agreement_003.pdf
    ├── receipt_003.pdf
    ├── statement_003.pdf
    └── extractedData/
        ├── session_results.json
        └── run_001_20250921_002337.json
```

## 🔄 **How Multiple Runs Work**

### **First Run:**
- Creates `extractedData` folder
- Saves `session_results.json` with run #1
- Saves individual run file `run_001_TIMESTAMP.json`

### **Second Run:**
- **Appends** to existing `session_results.json`
- Adds run #2 to the history
- Saves individual run file `run_002_TIMESTAMP.json`
- **Preserves** all previous run data

### **Third Run and Beyond:**
- Continues appending to history
- Each run gets a unique timestamp
- Complete history is maintained

## 📊 **Run History Structure**

The `session_results.json` file contains:

```json
{
  "session_id": "session_001",
  "total_runs": 3,
  "runs": [
    {
      "run_number": 1,
      "timestamp": "2025-09-21 00:23:37.676365",
      "datetime": "2025-09-21T00:23:37.676380",
      "success": true,
      "pdfs_processed": 2,
      "pdfs_failed": 0,
      "total_pages": 4,
      "total_text_length": 435,
      "total_tables": 0,
      "total_images": 0,
      "run_data": { /* Complete extraction data */ }
    },
    {
      "run_number": 2,
      "timestamp": "2025-09-21 00:23:37.706127",
      "datetime": "2025-09-21T00:23:37.706130",
      "success": true,
      "pdfs_processed": 2,
      "pdfs_failed": 0,
      "total_pages": 4,
      "total_text_length": 435,
      "total_tables": 0,
      "total_images": 0,
      "run_data": { /* Complete extraction data */ }
    }
  ],
  "latest_run": { /* Most recent run details */ },
  "created_at": "2025-09-21 00:23:37.676365",
  "last_updated": "2025-09-21 00:23:41.433127"
}
```

## 💻 **Usage Examples**

### **Command Line:**
```bash
# First run
python3 session_processor_example.py session_001
# Output: ✅ Successfully processed 2 PDFs, 📊 Total runs: 1

# Second run (same session)
python3 session_processor_example.py session_001  
# Output: ✅ Successfully processed 2 PDFs, 📊 Total runs: 2, 🔄 This was run #2

# Third run
python3 session_processor_example.py session_001
# Output: ✅ Successfully processed 2 PDFs, 📊 Total runs: 3, 🔄 This was run #3
```

### **Session Listing:**
```bash
python3 session_processor_example.py
# Output:
# Available sessions:
#   - session_001 (2 PDFs, 3 runs)
#   - session_002 (1 PDFs, 2 runs)  
#   - session_003 (3 PDFs, 2 runs)
```

### **Programmatic Usage:**
```python
from local_epdf_processor import LocalEPdfProcessor

processor = LocalEPdfProcessor("./BSA")

# Process session multiple times
result1 = processor.process_session("session_001")
result2 = processor.process_session("session_001") 
result3 = processor.process_session("session_001")

# Get run history
history = processor.get_run_history("session_001")
print(f"Total runs: {history['total_runs']}")
print(f"Latest run: {history['latest_run']['timestamp']}")

# List extraction files
files = processor.list_extraction_files("session_001")
print(f"Extraction files: {files}")
```

## 🎯 **Key Benefits**

1. **📈 Run Tracking**: See how many times each session has been processed
2. **📅 Timestamp History**: Know exactly when each extraction was run
3. **📊 Performance Comparison**: Compare results across multiple runs
4. **🔄 Incremental Updates**: Add new runs without losing previous data
5. **📁 Organized Storage**: All results neatly organized in `extractedData` folders
6. **🔍 Individual Run Files**: Each run saved separately for detailed analysis

## 📋 **File Types Created**

### **Main Results File:**
- `session_results.json` - Complete history with all runs
- Contains summary of each run + full data for latest run

### **Individual Run Files:**
- `run_001_TIMESTAMP.json` - Complete data for run #1
- `run_002_TIMESTAMP.json` - Complete data for run #2
- `run_003_TIMESTAMP.json` - Complete data for run #3
- Each file contains the full extraction data for that specific run

## 🚀 **Real-World Use Cases**

1. **🔄 Re-processing**: Re-run extraction after adding new PDFs to a session
2. **📊 Comparison**: Compare extraction results across different runs
3. **🐛 Debugging**: Track changes in extraction quality over time
4. **📈 Monitoring**: Monitor extraction performance and success rates
5. **🔄 Updates**: Re-process sessions when extraction algorithms improve

## ✅ **Test Results**

Successfully tested with:
- ✅ **3 sessions** processed multiple times
- ✅ **6 total PDFs** processed across all sessions
- ✅ **Multiple runs** per session (up to 3 runs)
- ✅ **Run history** properly maintained
- ✅ **Individual run files** created with timestamps
- ✅ **Session listing** shows run counts
- ✅ **Error handling** for non-existing sessions

## 🎉 **Ready to Use!**

Your BankParser system now fully supports multiple extraction runs with complete history tracking. Just run the same session multiple times and watch the magic happen! 🚀

---

**Example Output:**
```
Processing session: session_001
✅ Session 'session_001' found!
📁 PDF files found: 2
🔄 Processing PDFs...
✅ Successfully processed 2 PDFs
📄 Total pages: 4
📝 Total text length: 435 characters
💾 Results saved to: BSA/session_001/extractedData/session_results.json
📁 Extracted data folder: BSA/session_001/extractedData
📊 Total runs: 3
🔄 This was run #3
⏰ Previous run: 2025-09-21 00:23:37.706127
```
