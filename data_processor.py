import pandas as pd
import pdfplumber
import re
from io import StringIO
from typing import Dict, List, Optional, Tuple
import streamlit as st


class FinancialDataProcessor:
    """Handles processing of financial data from PDFs and CSVs."""
    
    def __init__(self):
        self.processed_data = None
        
    def extract_pdf_tables(self, pdf_file) -> List[Dict]:
        """Extract financial tables from PDF file."""
        tables_data = []
        
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text and look for financial data patterns
                    text = page.extract_text()
                    
                    if text:
                        # Look for budget comparison patterns
                        financial_lines = self._parse_financial_text(text)
                        if financial_lines:
                            tables_data.extend(financial_lines)
                            
        except Exception as e:
            st.error(f"Error extracting PDF: {str(e)}")
            
        return tables_data
    
    def _parse_financial_text(self, text: str) -> List[Dict]:
        """Parse financial text and extract budget/actual data."""
        financial_data = []
        lines = text.split('\n')
        
        current_category = ""
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or 'Balance' in line or 'Actual Net' in line:
                continue
                
            # Identify category headers
            if self._is_category_header(line):
                current_category = line
                continue
                
            # Parse financial line items
            financial_item = self._parse_financial_line(line, current_category)
            if financial_item:
                financial_data.append(financial_item)
                
        return financial_data
    
    def _is_category_header(self, line: str) -> bool:
        """Check if line is a category header."""
        category_indicators = [
            'INCOME', 'EXPENDITURE', 'Administration', 
            'Cawston Community Hall', 'Parks & Open Spaces', 
            'Section 137', 'Total'
        ]
        return any(indicator in line for indicator in category_indicators) and not any(c.isdigit() for c in line)
    
    def _parse_financial_line(self, line: str, category: str) -> Optional[Dict]:
        """Parse a single financial line to extract budget/actual data."""
        # Look for patterns like: "4000 Clerks Salary £42,134.00 £19,577.64 £22,556.36"
        # or "1076 Precept £94,160.00 £48,351.00 -£45,809.00"
        
        # Pattern to match financial lines with amounts
        pattern = r'(\d{3,4})\s+([^£]+?)\s+(£[\d,.-]+)\s+(£[\d,.-]+)\s+(£?-?[\d,.-]+)'
        match = re.search(pattern, line)
        
        if match:
            code = match.group(1).strip()
            description = match.group(2).strip()
            budget = self._clean_currency(match.group(3))
            actual = self._clean_currency(match.group(4))
            balance = self._clean_currency(match.group(5))
            
            return {
                'code': code,
                'description': description,
                'category': category,
                'budget_2025_26': budget,
                'actual_net': actual,
                'balance': balance,
                'type': 'Income' if 'INCOME' in category else 'Expenditure'
            }
        
        # Try simpler pattern for lines without codes
        simple_pattern = r'([^£]+?)\s+(£[\d,.-]+)\s+(£[\d,.-]+)\s+(£?-?[\d,.-]+)'
        simple_match = re.search(simple_pattern, line)
        
        if simple_match and len(simple_match.group(1).split()) <= 5:
            description = simple_match.group(1).strip()
            budget = self._clean_currency(simple_match.group(2))
            actual = self._clean_currency(simple_match.group(3))
            balance = self._clean_currency(simple_match.group(4))
            
            return {
                'code': '',
                'description': description,
                'category': category,
                'budget_2025_26': budget,
                'actual_net': actual,
                'balance': balance,
                'type': 'Income' if 'INCOME' in category else 'Expenditure'
            }
            
        return None
    
    def _clean_currency(self, amount_str: str) -> float:
        """Clean and convert currency string to float."""
        try:
            # Remove £, commas, and handle negative values
            cleaned = amount_str.replace('£', '').replace(',', '').strip()
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def process_csv(self, csv_file) -> pd.DataFrame:
        """Process uploaded CSV file with intelligent column mapping."""
        try:
            df = pd.read_csv(csv_file)
            
            # Store original column names for user feedback
            original_columns = list(df.columns)
            
            # Standardize column names
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # Try intelligent column mapping
            df = self._map_csv_columns(df, original_columns)
            
            if df.empty:
                return df  # Error already shown in mapping function
            
            # Add derived columns
            if 'balance' not in df.columns and 'budget' in df.columns and 'actual' in df.columns:
                df['balance'] = df['budget'] - df['actual']
            
            if 'category' not in df.columns:
                df['category'] = 'General'
                
            if 'type' not in df.columns and 'budget' in df.columns:
                df['type'] = df['budget'].apply(lambda x: 'Income' if x < 0 else 'Expenditure')
            
            return df
            
        except Exception as e:
            st.error(f"Error processing CSV: {str(e)}")
            return pd.DataFrame()
    
    def _map_csv_columns(self, df: pd.DataFrame, original_columns: List[str]) -> pd.DataFrame:
        """Intelligently map CSV columns to expected format."""
        
        # Define column mapping patterns
        column_mappings = {
            'description': ['description', 'desc', 'item', 'name', 'details'],
            'budget': ['budget', 'budget_2025_26', 'budgeted', 'planned', 'allocation'],
            'actual': ['actual', 'actual_net', 'spent', 'used', 'expenditure'],
            'category': ['category', 'cat', 'type', 'group', 'section'],
            'balance': ['balance', 'remaining', 'variance', 'difference'],
            'code': ['code', 'account_code', 'ref', 'reference', 'id']
        }
        
        # Create mapping dictionary
        column_map = {}
        mapped_columns = []
        
        for target_col, possible_names in column_mappings.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    column_map[possible_name] = target_col
                    mapped_columns.append(f"{possible_name} → {target_col}")
                    break
        
        # Apply the mapping
        df = df.rename(columns=column_map)
        
        # Show user what mappings were applied
        if mapped_columns:
            st.success("✅ **Column Mapping Applied:**")
            for mapping in mapped_columns:
                st.write(f"  • {mapping}")
        
        # Check if we have the essential columns after mapping
        essential_cols = ['description', 'budget', 'actual']
        missing_essential = [col for col in essential_cols if col not in df.columns]
        
        if missing_essential:
            st.error("❌ **Could not find required columns after intelligent mapping.**")
            st.write("**Original columns found:**", ", ".join(original_columns))
            st.write("**Missing required columns:**", ", ".join(missing_essential))
            st.write("**Expected column names:**")
            st.write("- `description` (or `desc`, `item`, `name`)")
            st.write("- `budget` (or `budget_2025_26`, `budgeted`, `planned`)")
            st.write("- `actual` (or `actual_net`, `spent`, `used`)")
            return pd.DataFrame()
        
        # Show successful column detection
        found_cols = [col for col in ['description', 'budget', 'actual', 'category', 'balance'] if col in df.columns]
        st.info(f"✅ **Successfully mapped columns:** {', '.join(found_cols)}")
        
        return df
    
    def create_dataframe(self, financial_data: List[Dict]) -> pd.DataFrame:
        """Convert financial data to pandas DataFrame."""
        if not financial_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(financial_data)
        
        # Clean up the data
        df = df[df['description'] != '']  # Remove empty descriptions
        df = df[~df['description'].str.contains('Total|Page', case=False, na=False)]  # Remove total lines
        
        # Ensure numeric columns are float
        numeric_cols = ['budget_2025_26', 'actual_net', 'balance']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    def get_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate summary statistics for the financial data."""
        if df.empty:
            return {}
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        total_budget = df[budget_col].sum()
        total_actual = df[actual_col].sum()
        total_variance = total_budget - total_actual
        variance_percentage = (total_variance / total_budget * 100) if total_budget != 0 else 0
        
        # Category breakdowns
        income_budget = df[df['type'] == 'Income'][budget_col].sum()
        income_actual = df[df['type'] == 'Income'][actual_col].sum()
        
        expense_budget = df[df['type'] == 'Expenditure'][budget_col].sum()
        expense_actual = df[df['type'] == 'Expenditure'][actual_col].sum()
        
        return {
            'total_budget': total_budget,
            'total_actual': total_actual,
            'total_variance': total_variance,
            'variance_percentage': variance_percentage,
            'income_budget': income_budget,
            'income_actual': income_actual,
            'expense_budget': expense_budget,
            'expense_actual': expense_actual,
            'completion_rate': (total_actual / total_budget * 100) if total_budget != 0 else 0
        }