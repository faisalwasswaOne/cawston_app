import pandas as pd
import io
from typing import Dict, List, Optional, Union
import streamlit as st


def format_currency(amount: float, currency_symbol: str = "£") -> str:
    """Format a number as currency with proper formatting."""
    if pd.isna(amount):
        return f"{currency_symbol}0.00"
    
    # Handle negative values
    if amount < 0:
        return f"-{currency_symbol}{abs(amount):,.2f}"
    else:
        return f"{currency_symbol}{amount:,.2f}"


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format a number as a percentage."""
    if pd.isna(value):
        return "0.0%"
    return f"{value:.{decimal_places}f}%"


def export_to_excel(df: pd.DataFrame, sheet_name: str = "Financial Data") -> io.BytesIO:
    """Export DataFrame to Excel format in memory."""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Main data sheet
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Summary sheet
        if not df.empty:
            summary_data = create_summary_sheet(df)
            summary_data.to_excel(writer, sheet_name="Summary", index=False)
        
        # Format the worksheets
        workbook = writer.book
        
        # Format main data sheet
        if sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    buffer.seek(0)
    return buffer


def create_summary_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Create a summary sheet for Excel export."""
    budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
    actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
    
    # Overall summary
    total_budget = df[budget_col].sum()
    total_actual = df[actual_col].sum()
    total_variance = total_budget - total_actual
    
    # Category summary
    category_summary = df.groupby('category').agg({
        budget_col: 'sum',
        actual_col: 'sum'
    }).reset_index()
    
    category_summary['variance'] = category_summary[budget_col] - category_summary[actual_col]
    category_summary['variance_pct'] = (
        category_summary['variance'] / category_summary[budget_col] * 100
    ).fillna(0)
    
    # Type summary
    type_summary = df.groupby('type').agg({
        budget_col: 'sum',
        actual_col: 'sum'
    }).reset_index()
    
    type_summary['variance'] = type_summary[budget_col] - type_summary[actual_col]
    
    # Combine all summaries
    summary_rows = []
    
    # Add overall totals
    summary_rows.append({
        'Category': 'TOTAL',
        'Type': 'All',
        'Budget': total_budget,
        'Actual': total_actual,
        'Variance': total_variance,
        'Variance_%': (total_variance / total_budget * 100) if total_budget != 0 else 0
    })
    
    # Add category breakdowns
    for _, row in category_summary.iterrows():
        summary_rows.append({
            'Category': row['category'],
            'Type': 'Category Total',
            'Budget': row[budget_col],
            'Actual': row[actual_col],
            'Variance': row['variance'],
            'Variance_%': row['variance_pct']
        })
    
    # Add type breakdowns
    for _, row in type_summary.iterrows():
        summary_rows.append({
            'Category': row['type'],
            'Type': 'Type Total',
            'Budget': row[budget_col],
            'Actual': row[actual_col],
            'Variance': row['variance'],
            'Variance_%': (row['variance'] / row[budget_col] * 100) if row[budget_col] != 0 else 0
        })
    
    return pd.DataFrame(summary_rows)


def validate_financial_data(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Validate financial data and return issues found."""
    issues = {
        'errors': [],
        'warnings': [],
        'info': []
    }
    
    if df.empty:
        issues['errors'].append("Dataset is empty")
        return issues
    
    # Check required columns
    required_columns = ['description', 'budget', 'actual']
    budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
    actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
    
    if 'description' not in df.columns:
        issues['errors'].append("Missing 'description' column")
    
    if budget_col not in df.columns:
        issues['errors'].append(f"Missing budget column (expected '{budget_col}' or 'budget')")
    
    if actual_col not in df.columns:
        issues['errors'].append(f"Missing actual column (expected '{actual_col}' or 'actual')")
    
    # Check for missing values
    if 'description' in df.columns:
        missing_desc = df['description'].isna().sum()
        if missing_desc > 0:
            issues['warnings'].append(f"{missing_desc} rows have missing descriptions")
    
    if budget_col in df.columns:
        missing_budget = df[budget_col].isna().sum()
        if missing_budget > 0:
            issues['warnings'].append(f"{missing_budget} rows have missing budget values")
    
    if actual_col in df.columns:
        missing_actual = df[actual_col].isna().sum()
        if missing_actual > 0:
            issues['warnings'].append(f"{missing_actual} rows have missing actual values")
    
    # Check for negative budgets (might be intentional for income)
    if budget_col in df.columns:
        negative_budgets = (df[budget_col] < 0).sum()
        if negative_budgets > 0:
            issues['info'].append(f"{negative_budgets} items have negative budget values")
    
    # Check for zero budgets with actual spending
    if budget_col in df.columns and actual_col in df.columns:
        zero_budget_with_actual = ((df[budget_col] == 0) & (df[actual_col] != 0)).sum()
        if zero_budget_with_actual > 0:
            issues['warnings'].append(
                f"{zero_budget_with_actual} items have zero budget but actual spending"
            )
    
    # Check for large variances
    if budget_col in df.columns and actual_col in df.columns:
        df_temp = df.copy()
        df_temp['variance_pct'] = (
            (df_temp[budget_col] - df_temp[actual_col]) / df_temp[budget_col] * 100
        ).fillna(0)
        
        large_variances = (abs(df_temp['variance_pct']) > 50).sum()
        if large_variances > 0:
            issues['warnings'].append(f"{large_variances} items have >50% variance")
    
    # Data quality info
    issues['info'].append(f"Total records: {len(df)}")
    
    if 'category' in df.columns:
        unique_categories = df['category'].nunique()
        issues['info'].append(f"Unique categories: {unique_categories}")
    
    if 'type' in df.columns:
        type_distribution = df['type'].value_counts().to_dict()
        issues['info'].append(f"Type distribution: {type_distribution}")
    
    return issues


def clean_financial_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize financial data."""
    df_clean = df.copy()
    
    # Standardize column names
    df_clean.columns = df_clean.columns.str.strip().str.lower()
    
    # Handle common column name variations
    column_mapping = {
        'budget_2025_26': 'budget',
        'actual_net': 'actual',
        'desc': 'description',
        'cat': 'category'
    }
    
    df_clean = df_clean.rename(columns=column_mapping)
    
    # Clean text columns
    text_columns = ['description', 'category', 'type']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
            df_clean[col] = df_clean[col].replace('nan', '')
    
    # Clean numeric columns
    numeric_columns = ['budget', 'actual', 'balance']
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
    
    # Calculate balance if missing
    if 'balance' not in df_clean.columns and 'budget' in df_clean.columns and 'actual' in df_clean.columns:
        df_clean['balance'] = df_clean['budget'] - df_clean['actual']
    
    # Set default category if missing
    if 'category' not in df_clean.columns:
        df_clean['category'] = 'Uncategorized'
    
    # Set default type if missing
    if 'type' not in df_clean.columns:
        df_clean['type'] = df_clean['budget'].apply(
            lambda x: 'Income' if x < 0 else 'Expenditure'
        )
    
    # Remove empty rows
    df_clean = df_clean[df_clean['description'] != ''].reset_index(drop=True)
    
    return df_clean


def generate_sample_data() -> pd.DataFrame:
    """Generate sample financial data for testing."""
    sample_data = pd.DataFrame({
        'description': [
            'Clerk Salary', 'Employer Pension', 'Training', 'Phone Rental',
            'Insurance', 'IT Software', 'Website Hosting', 'Bank Charges',
            'Precept Income', 'Hall Income', 'VAT Reclaim', 'Bank Interest',
            'Parks Maintenance', 'Street Lighting', 'Christmas Tree',
            'Hall Utilities', 'Hall Cleaning', 'Caretaker Salary'
        ],
        'category': [
            'Administration', 'Administration', 'Administration', 'Administration',
            'Administration', 'Administration', 'Administration', 'Administration',
            'Income', 'Income', 'Income', 'Income',
            'Parks & Open Spaces', 'Parks & Open Spaces', 'Parks & Open Spaces',
            'Community Hall', 'Community Hall', 'Community Hall'
        ],
        'budget': [
            42134, 5099, 500, 800, 900, 1000, 300, 54,
            -94160, -40000, -1000, -1500,
            2000, 1500, 1500,
            32000, 1800, 13828
        ],
        'actual': [
            19577, 2617, 35, 316, 0, 0, 228, 17,
            -48351, -14571, -1012, -1076,
            484, 0, 0,
            2598, 534, 5419
        ],
        'type': [
            'Expenditure', 'Expenditure', 'Expenditure', 'Expenditure',
            'Expenditure', 'Expenditure', 'Expenditure', 'Expenditure',
            'Income', 'Income', 'Income', 'Income',
            'Expenditure', 'Expenditure', 'Expenditure',
            'Expenditure', 'Expenditure', 'Expenditure'
        ]
    })
    
    # Calculate balance
    sample_data['balance'] = sample_data['budget'] - sample_data['actual']
    
    return sample_data


def display_validation_results(validation_results: Dict[str, List[str]]):
    """Display data validation results in Streamlit."""
    if validation_results['errors']:
        st.error("❌ **Data Errors Found:**")
        for error in validation_results['errors']:
            st.error(f"• {error}")
    
    if validation_results['warnings']:
        st.warning("⚠️ **Data Warnings:**")
        for warning in validation_results['warnings']:
            st.warning(f"• {warning}")
    
    if validation_results['info']:
        with st.expander("ℹ️ Data Information"):
            for info in validation_results['info']:
                st.info(f"• {info}")


@st.cache_data
def load_sample_pdf_data() -> pd.DataFrame:
    """Load sample data that mimics the Cawston Parish Council PDF structure."""
    return generate_sample_data()