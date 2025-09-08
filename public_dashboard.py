import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shared.data_access import get_data_access
from shared.components import SharedComponents
from typing import Dict, Optional


def show_public_dashboard():
    """Public-facing financial dashboard with read-only access."""
    st.title("💰 Cawston Parish Council Financial Dashboard")
    st.markdown("Public financial overview showing income, expenditure, and key budget information.")
    
    # Get data access and components
    data_access = get_data_access()
    components = SharedComponents()
    
    # Check if data is available
    if not data_access.has_data():
        st.info("📊 Financial data is being prepared. Please check back later.")
        _show_placeholder_content()
        return
    
    # Get financial summaries
    df = data_access.get_data()
    income_summary = data_access.get_income_summary(df)
    exp_summary = data_access.get_expenditure_summary(df)
    net_position = data_access.get_net_position(df)
    
    # Show main overview
    components.create_summary_overview(income_summary, exp_summary, net_position)
    
    st.markdown("---")
    
    # Create main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview", 
        "📈 Income Details", 
        "📉 Expenditure Details", 
        "📋 Summary Reports"
    ])
    
    with tab1:
        _show_overview_tab(df, components)
    
    with tab2:
        _show_income_tab(df, data_access, components)
    
    with tab3:
        _show_expenditure_tab(df, data_access, components)
    
    with tab4:
        _show_summary_reports_tab(df, data_access, components)


def _show_placeholder_content():
    """Show placeholder content when no data is available."""
    st.markdown("## 📋 About This Dashboard")
    st.markdown(
        """
        This financial dashboard provides transparency into Cawston Parish Council's 
        financial position, including:
        
        - **Income tracking**: Precept, grants, and other revenue sources
        - **Expenditure monitoring**: Spending across all council activities
        - **Budget analysis**: Comparison of planned vs actual amounts
        - **Category breakdowns**: Detailed view of spending by area
        
        Data is updated regularly by council administrators.
        """
    )
    
    # Show sample/expected data structure
    st.markdown("### 📊 Financial Categories")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Income Categories:**")
        st.markdown(
            """
            - Precept
            - Grants & Donations
            - Hall Rental Income
            - Investment Interest
            - Other Income
            """
        )
    
    with col2:
        st.markdown("**Expenditure Categories:**")
        st.markdown(
            """
            - Administration
            - Parks & Open Spaces
            - Community Hall
            - Section 137 Payments
            - Professional Services
            """
        )


def _show_overview_tab(df: pd.DataFrame, components: SharedComponents):
    """Show financial overview with charts and key metrics."""
    st.subheader("📊 Financial Overview")
    
    # Create main financial charts
    components.create_financial_charts(df)
    
    st.markdown("---")
    
    # Variance analysis
    st.subheader("📈 Budget Performance")
    
    # Get variance analysis
    data_access = get_data_access()
    variance_df = data_access.get_variance_analysis(df)
    
    if not variance_df.empty:
        # Show top variances (both positive and negative)
        st.markdown("##### Significant Budget Variances")
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in variance_df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in variance_df.columns else 'actual'
        
        # Filter for significant variances (>5% or >£1000)
        significant_variances = variance_df[
            (variance_df['variance'].abs() >= 1000) | 
            (variance_df['variance_pct'].abs() >= 5)
        ].head(10)
        
        if not significant_variances.empty:
            display_df = significant_variances[['description', 'category', budget_col, actual_col, 'variance', 'variance_pct']].copy()
            
            # Format currency columns
            for col in [budget_col, actual_col, 'variance']:
                display_df[col] = display_df[col].apply(lambda x: f"£{x:,.0f}")
            
            # Format percentage
            display_df['variance_pct'] = display_df['variance_pct'].apply(lambda x: f"{x:.1f}%")
            
            # Rename columns for display
            display_df = display_df.rename(columns={
                budget_col: 'Budget',
                actual_col: 'Actual',
                'variance': 'Variance',
                'variance_pct': 'Variance %',
                'description': 'Description',
                'category': 'Category'
            })
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No significant budget variances identified")


def _show_income_tab(df: pd.DataFrame, data_access, components: SharedComponents):
    """Show detailed income information with drill-down capability."""
    st.subheader("📈 Income Details")
    
    income_summary = data_access.get_income_summary(df)
    
    if not income_summary['category_breakdown'].empty:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            components._create_single_metric_card("Total Budget", income_summary['total_budget'])
        with col2:
            components._create_single_metric_card("Total Received", income_summary['total_actual'])
        with col3:
            components._create_single_metric_card("Outstanding", income_summary['total_balance'])
        
        st.markdown("---")
        
        # Category breakdown
        st.markdown("##### Income by Category")
        
        category_df = income_summary['category_breakdown']
        budget_col = 'budget_2025_26' if 'budget_2025_26' in category_df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in category_df.columns else 'actual'
        
        # Create bar chart for income categories
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Budget',
            x=category_df['category'],
            y=category_df[budget_col],
            marker_color=components.color_scheme['budget'],
            text=category_df[budget_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name='Received',
            x=category_df['category'],
            y=category_df[actual_col],
            marker_color=components.color_scheme['income'],
            text=category_df[actual_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto'
        ))
        
        fig.update_layout(
            title='Income by Category',
            xaxis_title='Category',
            yaxis_title='Amount (£)',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed breakdown by category
        income_df = df[df['type'] == 'Income'].copy()
        components.create_category_breakdown_table(income_df, "Income Breakdown", "Income")
        
    else:
        st.info("No income data available")


def _show_expenditure_tab(df: pd.DataFrame, data_access, components: SharedComponents):
    """Show detailed expenditure information with drill-down capability."""
    st.subheader("📉 Expenditure Details")
    
    exp_summary = data_access.get_expenditure_summary(df)
    
    if not exp_summary['category_breakdown'].empty:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            components._create_single_metric_card("Total Budget", exp_summary['total_budget'])
        with col2:
            components._create_single_metric_card("Total Spent", exp_summary['total_actual'])
        with col3:
            components._create_single_metric_card("Remaining", exp_summary['total_balance'])
        
        st.markdown("---")
        
        # Category breakdown
        st.markdown("##### Expenditure by Category")
        
        category_df = exp_summary['category_breakdown']
        budget_col = 'budget_2025_26' if 'budget_2025_26' in category_df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in category_df.columns else 'actual'
        
        # Create bar chart for expenditure categories
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Budget',
            x=category_df['category'],
            y=category_df[budget_col],
            marker_color=components.color_scheme['budget'],
            text=category_df[budget_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name='Spent',
            x=category_df['category'],
            y=category_df[actual_col],
            marker_color=components.color_scheme['expenditure'],
            text=category_df[actual_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto'
        ))
        
        fig.update_layout(
            title='Expenditure by Category',
            xaxis_title='Category',
            yaxis_title='Amount (£)',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show spending progress
        st.markdown("##### Spending Progress by Category")
        
        progress_df = category_df.copy()
        progress_df['spending_progress'] = (progress_df[actual_col] / progress_df[budget_col] * 100).round(1)
        
        for _, row in progress_df.iterrows():
            progress_value = min(row['spending_progress'], 100) / 100
            st.progress(
                progress_value, 
                text=f"**{row['category']}**: {row['spending_progress']:.1f}% spent (£{row[actual_col]:,.0f} of £{row[budget_col]:,.0f})"
            )
        
        st.markdown("---")
        
        # Detailed breakdown by category
        exp_df = df[df['type'] == 'Expenditure'].copy()
        components.create_category_breakdown_table(exp_df, "Expenditure Breakdown", "Expenditure")
        
    else:
        st.info("No expenditure data available")


def _show_summary_reports_tab(df: pd.DataFrame, data_access, components: SharedComponents):
    """Show summary reports and variance analysis."""
    st.subheader("📋 Financial Summary Reports")
    
    # Dataset information
    components.show_data_info_panel(df)
    
    # Variance summary table
    components.create_variance_summary_table(df, "Budget vs Actual Summary")
    
    st.markdown("---")
    
    # Search and filter functionality
    st.markdown("##### 🔍 Search Financial Records")
    filtered_df = components.create_search_filter(df)
    
    if not filtered_df.empty:
        st.markdown(f"**Showing {len(filtered_df)} records**")
        
        # Display columns for public view (hide sensitive details)
        budget_col = 'budget_2025_26' if 'budget_2025_26' in filtered_df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in filtered_df.columns else 'actual'
        
        display_df = filtered_df[['description', 'category', 'type', budget_col, actual_col]].copy()
        display_df['balance'] = display_df[budget_col] - display_df[actual_col]
        
        # Format currency columns
        for col in [budget_col, actual_col, 'balance']:
            display_df[col] = display_df[col].apply(lambda x: f"£{x:,.0f}")
        
        # Rename for public display
        display_df = display_df.rename(columns={
            'description': 'Description',
            'category': 'Category',
            'type': 'Type',
            budget_col: 'Budget',
            actual_col: 'Actual',
            'balance': 'Balance'
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No records match your search criteria")
    
    # Footer information
    st.markdown("---")
    st.markdown(
        """
        ### 📞 Contact Information
        
        For questions about this financial information, please contact:
        
        **Cawston Parish Council**  
        Email: clerk@cawston-pc.org.uk  
        Phone: [Contact Number]
        
        *This dashboard provides public transparency into council finances. 
        For detailed financial reports, please see the full council meeting minutes.*
        """
    )