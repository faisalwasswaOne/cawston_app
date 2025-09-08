import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Optional, Any
import numpy as np


class EnhancedVisualizations:
    """Enhanced visualizations with drill-down and interactive capabilities."""
    
    def __init__(self):
        self.color_scheme = {
            'budget': '#1f77b4',
            'actual': '#ff7f0e',
            'income': '#2ca02c',
            'expenditure': '#d62728',
            'positive': '#2ca02c',
            'negative': '#d62728',
            'neutral': '#7f7f7f',
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8'
        }
    
    def create_interactive_budget_overview(self, df: pd.DataFrame) -> go.Figure:
        """Create interactive budget overview with drill-down capability."""
        if df.empty:
            return self._create_empty_chart("No data available")
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Group by type and category for hierarchical view
        grouped = df.groupby(['type', 'category']).agg({
            budget_col: 'sum',
            actual_col: 'sum',
            'description': 'count'
        }).reset_index()
        
        grouped['variance'] = grouped[budget_col] - grouped[actual_col]
        grouped['variance_pct'] = (grouped['variance'] / grouped[budget_col] * 100).round(1)
        
        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Budget vs Actual by Type', 'Variance Analysis', 
                          'Category Breakdown - Income', 'Category Breakdown - Expenditure'),
            specs=[[{"secondary_y": False}, {"secondary_y": True}],
                   [{"type": "pie"}, {"type": "pie"}]]
        )
        
        # Top left: Budget vs Actual by Type
        type_summary = df.groupby('type').agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        
        fig.add_trace(
            go.Bar(name='Budget', x=type_summary['type'], y=type_summary[budget_col],
                  marker_color=self.color_scheme['budget'],
                  text=type_summary[budget_col].apply(lambda x: f'£{x:,.0f}'),
                  textposition='auto'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(name='Actual', x=type_summary['type'], y=type_summary[actual_col],
                  marker_color=self.color_scheme['actual'],
                  text=type_summary[actual_col].apply(lambda x: f'£{x:,.0f}'),
                  textposition='auto'),
            row=1, col=1
        )
        
        # Top right: Variance Analysis
        variance_summary = grouped.groupby('type').agg({
            'variance': 'sum'
        }).reset_index()
        
        colors = [self.color_scheme['positive'] if v >= 0 else self.color_scheme['negative'] 
                 for v in variance_summary['variance']]
        
        fig.add_trace(
            go.Bar(name='Variance', x=variance_summary['type'], y=variance_summary['variance'],
                  marker_color=colors,
                  text=variance_summary['variance'].apply(lambda x: f'£{x:,.0f}'),
                  textposition='auto'),
            row=1, col=2
        )
        
        # Bottom left: Income pie chart
        income_data = grouped[grouped['type'] == 'Income']
        if not income_data.empty:
            fig.add_trace(
                go.Pie(labels=income_data['category'], values=income_data[actual_col],
                      name="Income", title="Income by Category"),
                row=2, col=1
            )
        
        # Bottom right: Expenditure pie chart
        exp_data = grouped[grouped['type'] == 'Expenditure']
        if not exp_data.empty:
            fig.add_trace(
                go.Pie(labels=exp_data['category'], values=exp_data[actual_col],
                      name="Expenditure", title="Expenditure by Category"),
                row=2, col=2
            )
        
        fig.update_layout(
            height=800,
            title_text="Financial Overview Dashboard",
            showlegend=True
        )
        
        return fig
    
    def create_drill_down_bar_chart(self, df: pd.DataFrame, group_by: str = 'category', 
                                   title: str = None) -> go.Figure:
        """Create interactive bar chart with drill-down capability."""
        if df.empty:
            return self._create_empty_chart("No data available")
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Group by the specified column
        grouped = df.groupby(group_by).agg({
            budget_col: 'sum',
            actual_col: 'sum',
            'description': 'count'
        }).reset_index()
        
        grouped['variance'] = grouped[budget_col] - grouped[actual_col]
        
        fig = go.Figure()
        
        # Add budget bars with hover info
        fig.add_trace(go.Bar(
            name='Budget',
            x=grouped[group_by],
            y=grouped[budget_col],
            marker_color=self.color_scheme['budget'],
            text=grouped[budget_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>' +
                         'Budget: £%{y:,.0f}<br>' +
                         'Items: %{customdata}<br>' +
                         '<extra></extra>',
            customdata=grouped['description']
        ))
        
        # Add actual bars
        fig.add_trace(go.Bar(
            name='Actual',
            x=grouped[group_by],
            y=grouped[actual_col],
            marker_color=self.color_scheme['actual'],
            text=grouped[actual_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>' +
                         'Actual: £%{y:,.0f}<br>' +
                         'Variance: £%{customdata:,.0f}<br>' +
                         '<extra></extra>',
            customdata=grouped['variance']
        ))
        
        fig.update_layout(
            title=title or f'Financial Data by {group_by.title()}',
            xaxis_title=group_by.title(),
            yaxis_title='Amount (£)',
            barmode='group',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_financial_health_dashboard(self, df: pd.DataFrame) -> go.Figure:
        """Create a comprehensive financial health dashboard."""
        if df.empty:
            return self._create_empty_chart("No data available")
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Calculate key metrics
        total_budget = df[budget_col].sum()
        total_actual = df[actual_col].sum()
        total_variance = total_budget - total_actual
        
        income_budget = df[df['type'] == 'Income'][budget_col].sum()
        income_actual = df[df['type'] == 'Income'][actual_col].sum()
        exp_budget = df[df['type'] == 'Expenditure'][budget_col].sum()
        exp_actual = df[df['type'] == 'Expenditure'][actual_col].sum()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Financial Health Gauge', 'Income vs Expenditure Flow',
                          'Budget Utilization', 'Variance Trend'),
            specs=[[{"type": "indicator"}, {"type": "sankey"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # Top left: Financial Health Gauge
        health_score = self._calculate_financial_health_score(df)
        fig.add_trace(
            go.Indicator(
                mode = "gauge+number+delta",
                value = health_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Financial Health Score"},
                delta = {'reference': 80},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90}}
            ),
            row=1, col=1
        )
        
        # Top right: Sankey diagram for flow
        fig.add_trace(
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=["Income Budget", "Expenditure Budget", "Income Actual", "Expenditure Actual", "Net Position"],
                    color=["blue", "red", "green", "orange", "purple"]
                ),
                link=dict(
                    source=[0, 1, 2, 3],
                    target=[2, 3, 4, 4],
                    value=[income_budget, exp_budget, income_actual, exp_actual]
                )
            ),
            row=1, col=2
        )
        
        # Bottom left: Budget utilization
        categories = df.groupby('category').agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        
        categories['utilization'] = (categories[actual_col] / categories[budget_col] * 100).round(1)
        
        fig.add_trace(
            go.Bar(
                x=categories['category'],
                y=categories['utilization'],
                name='Utilization %',
                marker_color=[self.color_scheme['success'] if x <= 100 else self.color_scheme['danger'] 
                            for x in categories['utilization']]
            ),
            row=2, col=1
        )
        
        # Bottom right: Variance by category (scatter plot)
        categories['variance'] = categories[budget_col] - categories[actual_col]
        fig.add_trace(
            go.Scatter(
                x=categories[budget_col],
                y=categories[actual_col],
                mode='markers+text',
                text=categories['category'],
                textposition="top center",
                marker=dict(
                    size=categories['variance'].abs() / 100,
                    color=categories['variance'],
                    colorscale='RdBu',
                    colorbar=dict(title="Variance")
                ),
                name='Budget vs Actual'
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=800, title_text="Financial Health Dashboard")
        return fig
    
    def create_trend_analysis_chart(self, df: pd.DataFrame, time_column: Optional[str] = None) -> go.Figure:
        """Create trend analysis chart (placeholder for future time-series data)."""
        if df.empty:
            return self._create_empty_chart("No data available")
        
        # For now, create a category-based trend simulation
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        categories = df['category'].unique()
        
        fig = go.Figure()
        
        for category in categories:
            cat_data = df[df['category'] == category]
            budget_total = cat_data[budget_col].sum()
            actual_total = cat_data[actual_col].sum()
            
            # Simulate monthly progression (placeholder)
            months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
            
            # Simple simulation: assume linear spending pattern
            if budget_total > 0:
                monthly_budget = [budget_total / 12 * (i + 1) for i in range(12)]
                # Actual spending with some variation
                current_month = 5  # Assume we're in August (month 5)
                monthly_actual = [
                    min(actual_total * (i + 1) / current_month, budget_total) 
                    if i < current_month else budget_total 
                    for i in range(12)
                ]
                
                fig.add_trace(go.Scatter(
                    x=months,
                    y=monthly_budget,
                    mode='lines+markers',
                    name=f'{category} - Budget',
                    line=dict(dash='dash')
                ))
                
                fig.add_trace(go.Scatter(
                    x=months[:current_month + 1],
                    y=monthly_actual[:current_month + 1],
                    mode='lines+markers',
                    name=f'{category} - Actual'
                ))
        
        fig.update_layout(
            title='Financial Trend Analysis (Simulated)',
            xaxis_title='Month',
            yaxis_title='Cumulative Amount (£)',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_interactive_pie_with_drilldown(self, df: pd.DataFrame, 
                                            main_category: str = 'type',
                                            sub_category: str = 'category') -> go.Figure:
        """Create interactive pie chart with drill-down capability."""
        if df.empty:
            return self._create_empty_chart("No data available")
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        
        # Main level data
        main_data = df.groupby(main_category)[budget_col].sum().reset_index()
        
        fig = go.Figure()
        
        # Add main pie chart
        fig.add_trace(go.Pie(
            labels=main_data[main_category],
            values=main_data[budget_col],
            name="Main",
            hovertemplate='<b>%{label}</b><br>' +
                         'Amount: £%{value:,.0f}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Budget Distribution by {main_category.title()}',
            height=500
        )
        
        return fig
    
    def _calculate_financial_health_score(self, df: pd.DataFrame) -> float:
        """Calculate a financial health score (0-100)."""
        if df.empty:
            return 0
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Calculate various health metrics
        total_budget = df[budget_col].sum()
        total_actual = df[actual_col].sum()
        
        if total_budget == 0:
            return 0
        
        # Income performance (30% weight)
        income_df = df[df['type'] == 'Income']
        income_budget = income_df[budget_col].sum()
        income_actual = income_df[actual_col].sum()
        income_score = min((income_actual / income_budget * 100), 100) if income_budget > 0 else 100
        
        # Expenditure control (40% weight) - inverse relationship
        exp_df = df[df['type'] == 'Expenditure']
        exp_budget = exp_df[budget_col].sum()
        exp_actual = exp_df[actual_col].sum()
        exp_score = max(100 - (exp_actual / exp_budget * 100 - 100), 0) if exp_budget > 0 else 100
        
        # Variance management (30% weight)
        variances = df[budget_col] - df[actual_col]
        variance_score = max(100 - (variances.abs().sum() / total_budget * 100), 0)
        
        # Weighted average
        health_score = (income_score * 0.3 + exp_score * 0.4 + variance_score * 0.3)
        
        return round(health_score, 1)
    
    def _create_empty_chart(self, message: str = "No data available") -> go.Figure:
        """Create empty chart with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=400
        )
        return fig
    
    def create_budget_timeline(self, df: pd.DataFrame) -> go.Figure:
        """Create budget timeline visualization."""
        # This is a placeholder for future timeline functionality
        # For now, create a category-based progression chart
        
        if df.empty:
            return self._create_empty_chart("No data available")
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Group by category and create progression
        categories = df.groupby('category').agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        
        categories['remaining'] = categories[budget_col] - categories[actual_col]
        categories['progress'] = (categories[actual_col] / categories[budget_col] * 100).round(1)
        
        fig = go.Figure()
        
        # Create horizontal bar chart showing progress
        fig.add_trace(go.Bar(
            y=categories['category'],
            x=categories[actual_col],
            name='Spent',
            orientation='h',
            marker_color=self.color_scheme['actual']
        ))
        
        fig.add_trace(go.Bar(
            y=categories['category'],
            x=categories['remaining'],
            name='Remaining',
            orientation='h',
            marker_color=self.color_scheme['neutral']
        ))
        
        fig.update_layout(
            title='Budget Progress by Category',
            xaxis_title='Amount (£)',
            yaxis_title='Category',
            barmode='stack',
            height=max(300, len(categories) * 50)
        )
        
        return fig