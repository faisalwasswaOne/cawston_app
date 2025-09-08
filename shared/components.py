import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any


class SharedComponents:
    """Reusable UI components for both public and admin interfaces."""
    
    def __init__(self):
        self.color_scheme = {
            'income': '#2ca02c',
            'expenditure': '#d62728',
            'budget': '#1f77b4',
            'actual': '#ff7f0e',
            'positive': '#2ca02c',
            'negative': '#d62728',
            'neutral': '#7f7f7f',
            'primary': '#1f77b4',
            'secondary': '#ff7f0e'
        }
    
    def create_metric_cards(self, metrics: Dict[str, Any], columns: int = 3):
        """Create metric cards display."""
        cols = st.columns(columns)
        
        for i, (label, value) in enumerate(metrics.items()):
            with cols[i % columns]:
                if isinstance(value, dict):
                    self._create_single_metric_card(
                        label, 
                        value.get('value', 0), 
                        value.get('delta', None),
                        value.get('help', None)
                    )
                else:
                    self._create_single_metric_card(label, value)
    
    def _create_single_metric_card(self, label: str, value: float, delta: Optional[float] = None, help_text: Optional[str] = None):
        """Create a single metric card."""
        if isinstance(value, (int, float)):
            if abs(value) >= 1000:
                formatted_value = f"£{value:,.0f}"
            else:
                formatted_value = f"£{value:.2f}"
        else:
            formatted_value = str(value)
        
        if delta is not None:
            if isinstance(delta, (int, float)):
                delta_formatted = f"£{delta:,.0f}" if abs(delta) >= 1000 else f"£{delta:.2f}"
            else:
                delta_formatted = str(delta)
            st.metric(label, formatted_value, delta_formatted, help=help_text)
        else:
            st.metric(label, formatted_value, help=help_text)
    
    def create_summary_overview(self, income_summary: Dict, exp_summary: Dict, net_position: Dict):
        """Create high-level financial overview."""
        st.subheader("📊 Financial Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### 📈 Income")
            self._create_single_metric_card("Total Budget", income_summary['total_budget'])
            self._create_single_metric_card("Total Received", income_summary['total_actual'])
            self._create_single_metric_card("Outstanding", income_summary['total_balance'])
        
        with col2:
            st.markdown("##### 📉 Expenditure")
            self._create_single_metric_card("Total Budget", exp_summary['total_budget'])
            self._create_single_metric_card("Total Spent", exp_summary['total_actual'])
            self._create_single_metric_card("Remaining", exp_summary['total_balance'])
        
        with col3:
            st.markdown("##### 💰 Net Position")
            self._create_single_metric_card("Budget Net", net_position['net_budget'])
            self._create_single_metric_card("Actual Net", net_position['net_actual'])
            if net_position['net_actual'] >= 0:
                st.success(f"**Surplus:** £{net_position['net_actual']:,.0f}")
            else:
                st.error(f"**Deficit:** £{abs(net_position['net_actual']):,.0f}")
    
    def create_category_breakdown_table(self, df: pd.DataFrame, title: str, type_filter: str):
        """Create a category breakdown table with drill-down capability."""
        st.markdown(f"##### {title}")
        
        if df.empty:
            st.info(f"No {type_filter.lower()} data available.")
            return
        
        # Allow selection of category for drill-down
        categories = df['category'].unique().tolist()
        
        # Create tabs for each category
        if len(categories) > 1:
            tabs = st.tabs(categories)
            
            for i, category in enumerate(categories):
                with tabs[i]:
                    self._show_category_details(df, category)
        else:
            # Single category, show directly
            if categories:
                self._show_category_details(df, categories[0])
    
    def _show_category_details(self, df: pd.DataFrame, category: str):
        """Show detailed breakdown for a specific category."""
        category_data = df[df['category'] == category]
        
        if category_data.empty:
            st.info(f"No data available for {category}")
            return
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in category_data.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in category_data.columns else 'actual'
        
        # Summary metrics for category
        total_budget = category_data[budget_col].sum()
        total_actual = category_data[actual_col].sum()
        total_balance = total_budget - total_actual
        
        col1, col2, col3 = st.columns(3)
        with col1:
            self._create_single_metric_card("Budget", total_budget)
        with col2:
            self._create_single_metric_card("Actual", total_actual)
        with col3:
            self._create_single_metric_card("Balance", total_balance)
        
        # Detailed table
        display_df = category_data[['description', budget_col, actual_col]].copy()
        display_df['balance'] = display_df[budget_col] - display_df[actual_col]
        display_df['% utilized'] = (display_df[actual_col] / display_df[budget_col] * 100).round(1)
        
        # Format currency columns
        for col in [budget_col, actual_col, 'balance']:
            display_df[col] = display_df[col].apply(lambda x: f"£{x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    def create_financial_charts(self, df: pd.DataFrame):
        """Create standard financial visualization charts."""
        if df.empty:
            st.warning("No data available for charts")
            return
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Income vs Expenditure overview
        col1, col2 = st.columns(2)
        
        with col1:
            self._create_income_vs_expenditure_chart(df, budget_col, actual_col)
        
        with col2:
            self._create_category_pie_chart(df, budget_col)
    
    def _create_income_vs_expenditure_chart(self, df: pd.DataFrame, budget_col: str, actual_col: str):
        """Create income vs expenditure comparison chart."""
        # Group by type
        type_summary = df.groupby('type').agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        
        fig = go.Figure()
        
        # Add budget bars
        fig.add_trace(go.Bar(
            name='Budget',
            x=type_summary['type'],
            y=type_summary[budget_col],
            marker_color=self.color_scheme['budget'],
            text=type_summary[budget_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto'
        ))
        
        # Add actual bars
        fig.add_trace(go.Bar(
            name='Actual',
            x=type_summary['type'],
            y=type_summary[actual_col],
            marker_color=self.color_scheme['actual'],
            text=type_summary[actual_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto'
        ))
        
        fig.update_layout(
            title='Income vs Expenditure Overview',
            xaxis_title='Type',
            yaxis_title='Amount (£)',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_category_pie_chart(self, df: pd.DataFrame, budget_col: str):
        """Create pie chart showing budget distribution by category."""
        # Group by category for expenditure only to show where money is allocated
        exp_df = df[df['type'] == 'Expenditure']
        
        if exp_df.empty:
            st.info("No expenditure data for pie chart")
            return
        
        category_budget = exp_df.groupby('category')[budget_col].sum().reset_index()
        
        fig = px.pie(
            category_budget,
            values=budget_col,
            names='category',
            title='Budget Allocation by Category'
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_search_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create search and filter controls."""
        if df.empty:
            return df
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input(
                "🔍 Search", 
                placeholder="Search descriptions or categories...",
                key="search_filter"
            )
        
        with col2:
            categories = ["All"] + sorted(df['category'].unique().tolist())
            category_filter = st.selectbox("Category Filter", categories)
        
        with col3:
            type_filter = st.selectbox("Type Filter", ["All", "Income", "Expenditure"])
        
        # Apply filters
        filtered_df = df.copy()
        
        if search_term:
            mask = (
                filtered_df['description'].str.contains(search_term, case=False, na=False) |
                filtered_df['category'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        
        if category_filter != "All":
            filtered_df = filtered_df[filtered_df['category'] == category_filter]
        
        if type_filter != "All":
            filtered_df = filtered_df[filtered_df['type'] == type_filter]
        
        return filtered_df
    
    def show_data_info_panel(self, df: pd.DataFrame):
        """Show information panel about the current dataset."""
        if df.empty:
            return
        
        with st.expander("📋 Dataset Information"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Records", len(df))
            
            with col2:
                st.metric("Categories", df['category'].nunique())
            
            with col3:
                income_count = len(df[df['type'] == 'Income'])
                st.metric("Income Items", income_count)
            
            with col4:
                exp_count = len(df[df['type'] == 'Expenditure'])
                st.metric("Expenditure Items", exp_count)
            
            # Last updated info
            if 'data_version' in st.session_state and st.session_state.data_version > 0:
                st.success(f"Data version: {st.session_state.data_version}")
    
    def create_variance_summary_table(self, df: pd.DataFrame, title: str = "Variance Summary"):
        """Create a summary table showing variances by category."""
        if df.empty:
            return
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Group by category and type
        summary = df.groupby(['type', 'category']).agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        
        summary['variance'] = summary[budget_col] - summary[actual_col]
        summary['variance_pct'] = (summary['variance'] / summary[budget_col] * 100).round(1)
        
        # Format for display
        for col in [budget_col, actual_col, 'variance']:
            summary[f'{col}_formatted'] = summary[col].apply(lambda x: f"£{x:,.0f}")
        
        st.markdown(f"##### {title}")
        
        # Split by income/expenditure
        income_summary = summary[summary['type'] == 'Income']
        exp_summary = summary[summary['type'] == 'Expenditure']
        
        if not income_summary.empty:
            st.markdown("**Income Variance**")
            display_cols = ['category', f'{budget_col}_formatted', f'{actual_col}_formatted', 'variance_formatted', 'variance_pct']
            income_display = income_summary[display_cols].rename(columns={
                f'{budget_col}_formatted': 'Budget',
                f'{actual_col}_formatted': 'Actual',
                'variance_formatted': 'Variance',
                'variance_pct': 'Variance %'
            })
            st.dataframe(income_display, use_container_width=True, hide_index=True)
        
        if not exp_summary.empty:
            st.markdown("**Expenditure Variance**")
            display_cols = ['category', f'{budget_col}_formatted', f'{actual_col}_formatted', 'variance_formatted', 'variance_pct']
            exp_display = exp_summary[display_cols].rename(columns={
                f'{budget_col}_formatted': 'Budget',
                f'{actual_col}_formatted': 'Actual',
                'variance_formatted': 'Variance',
                'variance_pct': 'Variance %'
            })
            st.dataframe(exp_display, use_container_width=True, hide_index=True)