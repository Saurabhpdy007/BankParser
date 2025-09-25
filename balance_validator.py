#!/usr/bin/env python3
"""
Balance Validator
================

Utility for validating balance equations in bank statements.
Checks if the balance equation holds: Previous Balance + Credit - Debit = Next Balance

Author: CredNX Team
"""

import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


def validate_balance_equation(transactions: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate balance equation: Previous Balance + Credit - Debit = Next Balance
    
    Args:
        transactions: List of transaction dictionaries with 'deposits', 'withdrawals', 'balance' fields
        
    Returns:
        Tuple of (has_mismatches, list_of_mismatches)
    """
    if not transactions:
        return False, []
    
    current_balance = 0.0
    mismatches = []
    
    for i, tx in enumerate(transactions):
        deposits = tx.get('deposits', 0.0)
        withdrawals = tx.get('withdrawals', 0.0)
        balance = tx.get('balance', 0.0)
        
        # Skip first transaction due to unknown opening balance
        if i == 0:
            current_balance = balance
            continue
        
        # Skip B/F transactions as they set the initial balance
        if tx.get('mode') == 'B/F' or (tx.get('mode') == '' and 'B/F' in tx.get('particulars', '')):
            current_balance = balance
            continue
        
        # Calculate expected balance using the equation
        expected_balance = current_balance + deposits - withdrawals
        difference = abs(expected_balance - balance)
        
        # Check if there's a mismatch (allow small floating point differences)
        if difference > 0.01:
            mismatches.append({
                'transaction_index': i,
                'date': tx.get('date', ''),
                'expected_balance': expected_balance,
                'actual_balance': balance,
                'difference': difference,
                'deposits': deposits,
                'withdrawals': withdrawals,
                'previous_balance': current_balance
            })
        
        # Update current balance for next transaction
        current_balance = balance
    
    return len(mismatches) > 0, mismatches


def format_balance_validation_report(transactions: List[Dict[str, Any]], bank_name: str) -> str:
    """
    Generate a formatted balance validation report for console display
    
    Args:
        transactions: List of transaction dictionaries
        bank_name: Name of the bank (HDFC, ICICI, etc.)
        
    Returns:
        Formatted report string
    """
    has_mismatches, mismatches = validate_balance_equation(transactions)
    
    report_lines = []
    report_lines.append(f"\n{'='*60}")
    report_lines.append(f"BALANCE VALIDATION REPORT - {bank_name}")
    report_lines.append(f"{'='*60}")
    
    if not has_mismatches:
        report_lines.append("✅ BALANCE EQUATION VALIDATION: PASSED")
        report_lines.append("   All transactions satisfy the balance equation:")
        report_lines.append("   Previous Balance + Credit - Debit = Next Balance")
        report_lines.append(f"   Total transactions validated: {len(transactions)}")
    else:
        report_lines.append("❌ BALANCE EQUATION VALIDATION: FAILED")
        report_lines.append(f"   Found {len(mismatches)} balance mismatches out of {len(transactions)} transactions")
        report_lines.append("   Balance equation: Previous Balance + Credit - Debit = Next Balance")
        report_lines.append("")
        report_lines.append("   MISMATCH DETAILS:")
        
        # Show first 10 mismatches
        for i, mismatch in enumerate(mismatches[:10]):
            report_lines.append(f"   {i+1}. Transaction #{mismatch['transaction_index']+1} ({mismatch['date']})")
            report_lines.append(f"      Expected Balance: ₹{mismatch['expected_balance']:,.2f}")
            report_lines.append(f"      Actual Balance:   ₹{mismatch['actual_balance']:,.2f}")
            report_lines.append(f"      Difference:       ₹{mismatch['difference']:,.2f}")
            report_lines.append(f"      Deposits:         ₹{mismatch['deposits']:,.2f}")
            report_lines.append(f"      Withdrawals:      ₹{mismatch['withdrawals']:,.2f}")
            report_lines.append(f"      Previous Balance: ₹{mismatch['previous_balance']:,.2f}")
            report_lines.append("")
        
        if len(mismatches) > 10:
            report_lines.append(f"   ... and {len(mismatches) - 10} more mismatches")
    
    report_lines.append(f"{'='*60}")
    
    return "\n".join(report_lines)


def get_balance_summary(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get a summary of balance validation results
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Dictionary with validation summary
    """
    has_mismatches, mismatches = validate_balance_equation(transactions)
    
    return {
        "total_transactions": len(transactions),
        "balance_mismatch": has_mismatches,
        "mismatch_count": len(mismatches),
        "success_rate": ((len(transactions) - len(mismatches)) / len(transactions) * 100) if transactions else 100.0,
        "mismatches": mismatches[:5] if mismatches else []  # Return first 5 for summary
    }
