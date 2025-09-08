import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple
from data_processor import FinancialDataProcessor
from probability_engine import ProbabilityEngine


class FinancialDataAccess:
    """Centralized data access layer for both public and admin interfaces."""
    
    def __init__(self):
        self.processor = FinancialDataProcessor()
        self.prob_engine = ProbabilityEngine()
    
    def get_data(self) -> pd.DataFrame:
        """Get the current financial dataset."""
        if 'df' in st.session_state and not st.session_state.df.empty:
            return st.session_state.df.copy()
        return pd.DataFrame()
    
    def has_data(self) -> bool:
        """Check if financial data is available."""
        return not self.get_data().empty
    
    def get_summary_statistics(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """Get summary statistics for the financial data."""
        if df is None:
            df = self.get_data()
        
        if df.empty:
            return {}
            
        # Use cached summary stats if available and data hasn't changed
        if ('summary_stats' in st.session_state and 
            st.session_state.summary_stats and 
            st.session_state.get('data_version', 0) > 0):
            return st.session_state.summary_stats
            
        # Calculate new summary stats
        summary_stats = self.processor.get_summary_statistics(df)
        st.session_state.summary_stats = summary_stats
        return summary_stats
    
    def get_income_summary(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """Get income-specific summary statistics."""
        if df is None:
            df = self.get_data()
        
        income_df = df[df['type'] == 'Income'].copy() if not df.empty else pd.DataFrame()
        
        if income_df.empty:
            return {
                'total_budget': 0,
                'total_actual': 0,
                'total_balance': 0,
                'categories': [],
                'category_breakdown': pd.DataFrame()
            }
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in income_df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in income_df.columns else 'actual'
        
        category_breakdown = income_df.groupby('category').agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        category_breakdown['balance'] = category_breakdown[budget_col] - category_breakdown[actual_col]
        category_breakdown['percentage_received'] = (
            category_breakdown[actual_col] / category_breakdown[budget_col] * 100
        ).round(1)
        
        return {
            'total_budget': float(income_df[budget_col].sum()),
            'total_actual': float(income_df[actual_col].sum()),
            'total_balance': float(income_df[budget_col].sum() - income_df[actual_col].sum()),
            'categories': income_df['category'].unique().tolist(),
            'category_breakdown': category_breakdown
        }
    
    def get_expenditure_summary(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """Get expenditure-specific summary statistics."""
        if df is None:
            df = self.get_data()
        
        exp_df = df[df['type'] == 'Expenditure'].copy() if not df.empty else pd.DataFrame()
        
        if exp_df.empty:
            return {
                'total_budget': 0,
                'total_actual': 0,
                'total_balance': 0,
                'categories': [],
                'category_breakdown': pd.DataFrame()
            }
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in exp_df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in exp_df.columns else 'actual'
        
        category_breakdown = exp_df.groupby('category').agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        category_breakdown['balance'] = category_breakdown[budget_col] - category_breakdown[actual_col]
        category_breakdown['percentage_spent'] = (
            category_breakdown[actual_col] / category_breakdown[budget_col] * 100
        ).round(1)
        
        return {
            'total_budget': float(exp_df[budget_col].sum()),
            'total_actual': float(exp_df[actual_col].sum()),
            'total_balance': float(exp_df[budget_col].sum() - exp_df[actual_col].sum()),
            'categories': exp_df['category'].unique().tolist(),
            'category_breakdown': category_breakdown
        }
    
    def get_net_position(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """Calculate overall net financial position."""
        if df is None:
            df = self.get_data()
            
        if df.empty:
            return {'net_budget': 0, 'net_actual': 0, 'net_balance': 0}
            
        income_summary = self.get_income_summary(df)
        exp_summary = self.get_expenditure_summary(df)
        
        return {
            'net_budget': income_summary['total_budget'] - exp_summary['total_budget'],
            'net_actual': income_summary['total_actual'] - exp_summary['total_actual'],
            'net_balance': income_summary['total_balance'] - exp_summary['total_balance']
        }
    
    def get_category_details(self, category: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Get detailed breakdown for a specific category."""
        if df is None:
            df = self.get_data()
            
        if df.empty:
            return pd.DataFrame()
            
        return df[df['category'] == category].copy()
    
    def get_filtered_data(self, 
                         category_filter: Optional[str] = None,
                         type_filter: Optional[str] = None,
                         df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Get filtered financial data based on category and/or type."""
        if df is None:
            df = self.get_data()
            
        if df.empty:
            return pd.DataFrame()
            
        filtered_df = df.copy()
        
        if category_filter and category_filter != "All":
            filtered_df = filtered_df[filtered_df['category'] == category_filter]
            
        if type_filter and type_filter != "All":
            filtered_df = filtered_df[filtered_df['type'] == type_filter]
            
        return filtered_df
    
    def get_risk_analysis(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Get risk analysis for financial data."""
        if df is None:
            df = self.get_data()
            
        if df.empty:
            return pd.DataFrame()
            
        return self.prob_engine.calculate_risk_assessment(df)
    
    def get_variance_analysis(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Get variance analysis showing budget vs actual differences."""
        if df is None:
            df = self.get_data()
            
        if df.empty:
            return pd.DataFrame()
            
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        variance_df = df.copy()
        variance_df['variance'] = variance_df[budget_col] - variance_df[actual_col]
        variance_df['variance_pct'] = (
            (variance_df['variance'] / variance_df[budget_col]) * 100
        ).round(2)
        
        # Sort by absolute variance for most significant items first
        variance_df['abs_variance'] = variance_df['variance'].abs()
        variance_df = variance_df.sort_values('abs_variance', ascending=False)
        
        return variance_df.drop('abs_variance', axis=1)
    
    def search_data(self, search_term: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Search financial data for specific terms."""
        if df is None:
            df = self.get_data()
            
        if df.empty or not search_term:
            return df
            
        # Search in description and category fields
        mask = (
            df['description'].str.contains(search_term, case=False, na=False) |
            df['category'].str.contains(search_term, case=False, na=False)
        )
        
        return df[mask]


def get_data_access() -> FinancialDataAccess:
    """Get singleton instance of data access layer."""
    if 'data_access' not in st.session_state:
        st.session_state.data_access = FinancialDataAccess()
    return st.session_state.data_access