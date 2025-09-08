import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Optional


class FinancialVisualizations:
    """Create interactive visualizations for financial data."""
    
    def __init__(self):
        self.color_scheme = {
            'budget': '#1f77b4',
            'actual': '#ff7f0e',
            'positive': '#2ca02c',
            'negative': '#d62728',
            'neutral': '#7f7f7f'
        }
    
    def create_budget_vs_actual_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create budget vs actual comparison chart."""
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Group by category for cleaner visualization
        grouped = df.groupby('category').agg({
            budget_col: 'sum',
            actual_col: 'sum',
            'description': 'count'
        }).reset_index()
        
        fig = go.Figure()
        
        # Add budget bars
        fig.add_trace(go.Bar(
            name='Budget',
            x=grouped['category'],
            y=grouped[budget_col],
            marker_color=self.color_scheme['budget'],
            text=grouped[budget_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto'
        ))
        
        # Add actual bars
        fig.add_trace(go.Bar(
            name='Actual',
            x=grouped['category'],
            y=grouped[actual_col],
            marker_color=self.color_scheme['actual'],
            text=grouped[actual_col].apply(lambda x: f'£{x:,.0f}'),
            textposition='auto'
        ))
        
        fig.update_layout(
            title='Budget vs Actual by Category',
            xaxis_title='Category',
            yaxis_title='Amount (£)',
            barmode='group',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_variance_waterfall(self, df: pd.DataFrame) -> go.Figure:
        """Create waterfall chart showing variances."""
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Calculate variance by category
        grouped = df.groupby('category').agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        
        grouped['variance'] = grouped[budget_col] - grouped[actual_col]
        
        # Prepare waterfall data
        categories = grouped['category'].tolist()
        variances = grouped['variance'].tolist()
        
        fig = go.Figure(go.Waterfall(
            name="Variance Analysis",
            orientation="v",
            measure=["relative"] * len(categories) + ["total"],
            x=categories + ["Total Variance"],
            y=variances + [sum(variances)],
            text=[f'£{v:,.0f}' for v in variances] + [f'£{sum(variances):,.0f}'],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": self.color_scheme['positive']}},
            decreasing={"marker": {"color": self.color_scheme['negative']}},
            totals={"marker": {"color": self.color_scheme['neutral']}}
        ))
        
        fig.update_layout(
            title="Budget Variance Waterfall",
            xaxis_title="Category",
            yaxis_title="Variance (£)",
            height=500
        )
        
        return fig
    
    def create_risk_assessment_chart(self, df_risk: pd.DataFrame) -> go.Figure:
        """Create risk assessment bubble chart."""
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df_risk.columns else 'budget'
        
        # Color mapping for risk categories
        risk_colors = {
            'Low Risk': '#2ca02c',
            'Medium Risk': '#ff7f0e',
            'High Risk': '#d62728',
            'Critical Risk': '#8b0000',
            'No Budget': '#7f7f7f'
        }
        
        fig = go.Figure()
        
        for risk_cat in df_risk['risk_category'].unique():
            risk_data = df_risk[df_risk['risk_category'] == risk_cat]
            
            fig.add_trace(go.Scatter(
                x=risk_data[budget_col],
                y=risk_data['variance_pct'],
                mode='markers',
                marker=dict(
                    size=risk_data['risk_score'] / 5 + 10,  # Size based on risk score
                    color=risk_colors.get(risk_cat, '#7f7f7f'),
                    opacity=0.7,
                    line=dict(width=2, color='DarkSlateGrey')
                ),
                name=risk_cat,
                text=risk_data['description'],
                hovertemplate='<b>%{text}</b><br>' +
                            'Budget: £%{x:,.0f}<br>' +
                            'Variance: %{y:.1f}%<br>' +
                            'Risk: %{marker.size}<extra></extra>'
            ))
        
        fig.update_layout(
            title='Risk Assessment: Budget vs Variance',
            xaxis_title='Budget Amount (£)',
            yaxis_title='Variance Percentage (%)',
            height=500,
            showlegend=True
        )
        
        return fig
    
    def create_probability_scenario_chart(self, scenario_df: pd.DataFrame) -> go.Figure:
        """Create chart showing probability scenario results."""
        budget_col = 'budget_2025_26' if 'budget_2025_26' in scenario_df.columns else 'budget'
        
        # Group by category
        grouped = scenario_df.groupby('category').agg({
            budget_col: 'sum',
            'projected_total': 'sum',
            'projected_variance': 'sum',
            'probability_factor': 'mean'
        }).reset_index()
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Projected vs Budget', 'Probability Factors'),
            vertical_spacing=0.12
        )
        
        # Budget vs Projected
        fig.add_trace(
            go.Bar(name='Budget', x=grouped['category'], y=grouped[budget_col],
                  marker_color=self.color_scheme['budget']),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(name='Projected', x=grouped['category'], y=grouped['projected_total'],
                  marker_color=self.color_scheme['actual']),
            row=1, col=1
        )
        
        # Probability factors
        fig.add_trace(
            go.Bar(name='Probability Factor', x=grouped['category'], 
                  y=grouped['probability_factor'],
                  marker_color='purple', showlegend=False),
            row=2, col=1
        )
        
        fig.update_layout(
            height=600,
            title_text="Probability Scenario Analysis"
        )
        
        fig.update_yaxes(title_text="Amount (£)", row=1, col=1)
        fig.update_yaxes(title_text="Probability Factor", row=2, col=1)
        
        return fig
    
    def create_cash_flow_projection(self, projection_df: pd.DataFrame) -> go.Figure:
        """Create cash flow projection chart."""
        # Group by month and category
        monthly_data = projection_df.groupby(['month', 'category']).agg({
            'monthly_projected': 'sum',
            'cumulative_projected': 'sum'
        }).reset_index()
        
        fig = go.Figure()
        
        # Create line for each category
        for category in monthly_data['category'].unique():
            cat_data = monthly_data[monthly_data['category'] == category]
            
            fig.add_trace(go.Scatter(
                x=cat_data['month'],
                y=cat_data['cumulative_projected'],
                mode='lines+markers',
                name=category,
                line=dict(width=3),
                hovertemplate=f'<b>{category}</b><br>' +
                            'Month: %{x}<br>' +
                            'Cumulative: £%{y:,.0f}<extra></extra>'
            ))
        
        fig.update_layout(
            title='Projected Cash Flow by Category',
            xaxis_title='Month',
            yaxis_title='Cumulative Amount (£)',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_pie_chart(self, df: pd.DataFrame, value_col: str, title: str) -> go.Figure:
        """Create pie chart for category breakdown."""
        grouped = df.groupby('category')[value_col].sum().reset_index()
        
        fig = px.pie(
            grouped, 
            values=value_col, 
            names='category',
            title=title,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        return fig
    
    def create_summary_metrics_cards(self, summary_stats: Dict) -> None:
        """Create metric cards for key statistics."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Budget",
                f"£{summary_stats.get('total_budget', 0):,.0f}",
                f"{summary_stats.get('completion_rate', 0):.1f}% Complete"
            )
        
        with col2:
            st.metric(
                "Total Actual",
                f"£{summary_stats.get('total_actual', 0):,.0f}",
                f"£{summary_stats.get('total_variance', 0):,.0f} Variance"
            )
        
        with col3:
            variance_pct = summary_stats.get('variance_percentage', 0)
            st.metric(
                "Variance %",
                f"{variance_pct:.1f}%",
                f"{'Over' if variance_pct < 0 else 'Under'} Budget"
            )
        
        with col4:
            net_position = summary_stats.get('income_actual', 0) - summary_stats.get('expense_actual', 0)
            st.metric(
                "Net Position",
                f"£{net_position:,.0f}",
                f"{'Surplus' if net_position > 0 else 'Deficit'}"
            )
    
    def create_monte_carlo_histogram(self, monte_carlo_results: Dict) -> go.Figure:
        """Create histogram of Monte Carlo simulation results."""
        results = monte_carlo_results['all_results']
        
        fig = go.Figure(data=[go.Histogram(
            x=results,
            nbinsx=50,
            marker_color='skyblue',
            opacity=0.7
        )])
        
        # Add vertical lines for percentiles
        percentiles = [5, 25, 75, 95]
        percentile_values = [monte_carlo_results[f'percentile_{p}'] for p in percentiles]
        colors = ['red', 'orange', 'orange', 'red']
        
        for p, val, color in zip(percentiles, percentile_values, colors):
            fig.add_vline(x=val, line_dash="dash", line_color=color,
                         annotation_text=f"{p}th percentile")
        
        fig.update_layout(
            title='Monte Carlo Simulation - Budget Variance Distribution',
            xaxis_title='Variance (£)',
            yaxis_title='Frequency',
            height=400
        )
        
        return fig