import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_processor import FinancialDataProcessor
from probability_engine import ProbabilityEngine
from visualizations import FinancialVisualizations
from utils import export_to_excel
from auth import Authentication
from shared.data_access import get_data_access
from shared.components import SharedComponents
import io


def show_admin_dashboard():
    """Main admin dashboard with full functionality."""
    # Show admin header
    auth = Authentication()
    auth.show_admin_header()
    
    st.title("💰 Financial Budget Analysis Dashboard - Admin")
    st.markdown("Full dashboard access: Upload, manage, and analyze financial data with advanced tools.")
    
    # Initialize session state and components
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if 'processor' not in st.session_state:
        st.session_state.processor = FinancialDataProcessor()
    if 'prob_engine' not in st.session_state:
        st.session_state.prob_engine = ProbabilityEngine()
    if 'viz' not in st.session_state:
        st.session_state.viz = FinancialVisualizations()
    if 'data_version' not in st.session_state:
        st.session_state.data_version = 0
    if 'summary_stats' not in st.session_state:
        st.session_state.summary_stats = {}
    
    # Get shared components
    data_access = get_data_access()
    components = SharedComponents()
    
    # Sidebar for data input
    with st.sidebar:
        st.header("📁 Data Input")
        
        input_method = st.radio(
            "Choose input method:",
            ["Upload PDF", "Upload CSV", "Manual Entry"]
        )
        
        if input_method == "Upload PDF":
            handle_pdf_upload()
        elif input_method == "Upload CSV":
            handle_csv_upload()
        else:
            handle_manual_entry()
        
        # Display data summary if data exists
        if not st.session_state.df.empty:
            st.markdown("---")
            st.subheader("📊 Data Summary")
            st.write(f"**Total Records:** {len(st.session_state.df)}")
            st.write(f"**Categories:** {st.session_state.df['category'].nunique()}")
            
            # Show data version (indicates when charts were last updated)
            if st.session_state.data_version > 0:
                st.success(f"📈 **Charts Updated** (v{st.session_state.data_version})")
            
            # Show category breakdown
            cat_counts = st.session_state.df['category'].value_counts()
            st.write("**Records by Category:**")
            for cat, count in cat_counts.items():
                st.write(f"- {cat}: {count}")
    
    # Main content area
    if st.session_state.df.empty:
        st.info("👆 Please upload your financial data using the sidebar to get started.")
        
        # Show sample data format
        st.subheader("📋 Expected Data Format")
        sample_data = pd.DataFrame({
            'description': ['Clerk Salary', 'Hall Income', 'Insurance', 'Maintenance'],
            'category': ['Administration', 'Income', 'Administration', 'Parks & Open Spaces'],
            'budget': [42134, 40000, 900, 2000],
            'actual': [19577, 14571, 0, 484],
            'type': ['Expenditure', 'Income', 'Expenditure', 'Expenditure']
        })
        st.dataframe(sample_data, width='stretch')
        
    else:
        # Calculate or use cached summary statistics
        if not st.session_state.summary_stats or st.session_state.data_version == 0:
            st.session_state.summary_stats = st.session_state.processor.get_summary_statistics(st.session_state.df)
        
        # Display key metrics
        st.session_state.viz.create_summary_metrics_cards(st.session_state.summary_stats)
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", "🎯 Probability Scenarios", "⚠️ Risk Analysis", 
            "📈 Projections", "📋 Data Table"
        ])
        
        with tab1:
            show_overview_tab()
        
        with tab2:
            show_probability_scenarios_tab()
        
        with tab3:
            show_risk_analysis_tab()
        
        with tab4:
            show_projections_tab()
        
        with tab5:
            show_data_table_tab()


def handle_pdf_upload():
    """Handle PDF file upload and processing."""
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a financial report PDF (similar to the Cawston Parish Council format)"
    )
    
    if uploaded_file is not None:
        with st.spinner("Processing PDF..."):
            try:
                financial_data = st.session_state.processor.extract_pdf_tables(uploaded_file)
                
                if financial_data:
                    df = st.session_state.processor.create_dataframe(financial_data)
                    if not df.empty:
                        st.session_state.df = df
                        st.session_state.data_version += 1
                        st.session_state.summary_stats = st.session_state.processor.get_summary_statistics(df)
                        st.success(f"✅ Successfully processed {len(df)} financial records!")
                    else:
                        st.error("No valid financial data found in the PDF.")
                else:
                    st.error("Could not extract financial data from the PDF. Please check the format.")
                    
            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")


def handle_csv_upload():
    """Handle CSV file upload and processing."""
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="CSV should have columns: description, category, budget, actual, type"
    )
    
    if uploaded_file is not None:
        try:
            df = st.session_state.processor.process_csv(uploaded_file)
            if not df.empty:
                st.session_state.df = df
                st.session_state.data_version += 1
                st.session_state.summary_stats = st.session_state.processor.get_summary_statistics(df)
                st.success(f"✅ Successfully loaded {len(df)} records!")
            else:
                st.error("Could not process the CSV file. Please check the format.")
                
        except Exception as e:
            st.error(f"Error processing CSV: {str(e)}")


def handle_manual_entry():
    """Handle manual data entry."""
    st.write("Enter financial data manually:")
    
    with st.form("manual_entry"):
        description = st.text_input("Description")
        category = st.selectbox("Category", [
            "Administration", "Income", "Parks & Open Spaces", 
            "Cawston Community Hall", "Section 137", "Other"
        ])
        budget = st.number_input("Budget Amount", min_value=0.0, format="%.2f")
        actual = st.number_input("Actual Amount", min_value=0.0, format="%.2f")
        entry_type = st.selectbox("Type", ["Income", "Expenditure"])
        
        submitted = st.form_submit_button("Add Entry")
        
        if submitted and description:
            new_entry = pd.DataFrame({
                'description': [description],
                'category': [category],
                'budget': [budget],
                'actual': [actual],
                'balance': [budget - actual],
                'type': [entry_type]
            })
            
            if st.session_state.df.empty:
                st.session_state.df = new_entry
            else:
                st.session_state.df = pd.concat([st.session_state.df, new_entry], ignore_index=True)
            
            # Update data version and summary stats
            st.session_state.data_version += 1
            st.session_state.summary_stats = st.session_state.processor.get_summary_statistics(st.session_state.df)
            
            st.success(f"Added: {description}")
            st.rerun()


def show_overview_tab():
    """Display overview visualizations."""
    col1, col2 = st.columns(2)
    
    with col1:
        # Budget vs Actual chart
        budget_chart = st.session_state.viz.create_budget_vs_actual_chart(st.session_state.df)
        st.plotly_chart(budget_chart, width='stretch')
    
    with col2:
        # Pie chart of expenditure by category
        budget_col = 'budget_2025_26' if 'budget_2025_26' in st.session_state.df.columns else 'budget'
        expense_df = st.session_state.df[st.session_state.df['type'] == 'Expenditure']
        if not expense_df.empty:
            pie_chart = st.session_state.viz.create_pie_chart(
                expense_df, budget_col, "Budget Allocation by Category"
            )
            st.plotly_chart(pie_chart, width='stretch')
    
    # Variance waterfall chart
    st.subheader("📊 Variance Analysis")
    waterfall_chart = st.session_state.viz.create_variance_waterfall(st.session_state.df)
    st.plotly_chart(waterfall_chart, width='stretch')


def show_probability_scenarios_tab():
    """Display probability scenario analysis."""
    st.subheader("🎯 Probability Scenario Planning")
    
    # Get categories for probability adjustment
    categories = st.session_state.df['category'].unique().tolist()
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.write("**Adjust Probability by Category:**")
        st.write("*Percentage likelihood of remaining budget being spent*")
        
        probabilities = {}
        for category in categories:
            probabilities[category] = st.slider(
                f"{category}",
                min_value=0,
                max_value=100,
                value=75,
                step=5,
                key=f"prob_{category}"
            )
        
        # Preset scenarios
        st.write("**Quick Scenarios:**")
        if st.button("Conservative (60-80%)", key="conservative"):
            for i, category in enumerate(categories):
                st.session_state[f"prob_{category}"] = 70 - (i % 3) * 5
            st.rerun()
        
        if st.button("Optimistic (90-100%)", key="optimistic"):
            for category in categories:
                st.session_state[f"prob_{category}"] = 95
            st.rerun()
        
        if st.button("Pessimistic (40-60%)", key="pessimistic"):
            for i, category in enumerate(categories):
                st.session_state[f"prob_{category}"] = 50 + (i % 2) * 10
            st.rerun()
    
    with col1:
        # Apply probability scenario
        scenario_df = st.session_state.prob_engine.apply_probability_scenario(
            st.session_state.df, probabilities
        )
        
        # Show scenario results chart
        scenario_chart = st.session_state.viz.create_probability_scenario_chart(scenario_df)
        st.plotly_chart(scenario_chart, width='stretch')
        
        # Summary of scenario
        st.subheader("📋 Scenario Summary")
        budget_col = 'budget_2025_26' if 'budget_2025_26' in scenario_df.columns else 'budget'
        
        total_budget = scenario_df[budget_col].sum()
        total_projected = scenario_df['projected_total'].sum()
        total_variance = scenario_df['projected_variance'].sum()
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Budget", f"£{total_budget:,.0f}")
        with col_b:
            st.metric("Projected Total", f"£{total_projected:,.0f}")
        with col_c:
            st.metric("Projected Variance", f"£{total_variance:,.0f}")


def show_risk_analysis_tab():
    """Display risk analysis."""
    st.subheader("⚠️ Budget Risk Assessment")
    
    # Calculate risk metrics
    df_risk = st.session_state.prob_engine.calculate_risk_assessment(st.session_state.df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk assessment chart
        risk_chart = st.session_state.viz.create_risk_assessment_chart(df_risk)
        st.plotly_chart(risk_chart, width='stretch')
    
    with col2:
        # Risk category breakdown
        risk_counts = df_risk['risk_category'].value_counts()
        risk_pie = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            title="Risk Distribution",
            color_discrete_map={
                'Low Risk': '#2ca02c',
                'Medium Risk': '#ff7f0e',
                'High Risk': '#d62728',
                'Critical Risk': '#8b0000',
                'No Budget': '#7f7f7f'
            }
        )
        st.plotly_chart(risk_pie, width='stretch')
    
    # High risk items table
    st.subheader("🚨 High Risk Items")
    high_risk = df_risk[df_risk['risk_category'].isin(['High Risk', 'Critical Risk'])]
    
    if not high_risk.empty:
        display_cols = ['description', 'category', 'risk_category', 'variance_pct', 'risk_score']
        st.dataframe(
            high_risk[display_cols].sort_values('risk_score', ascending=False),
            width='stretch'
        )
    else:
        st.success("No high-risk budget items identified! 🎉")


def show_projections_tab():
    """Display future projections."""
    st.subheader("📈 Financial Projections")
    
    # Cash flow projections
    months_ahead = st.slider("Months to project ahead", 3, 24, 12)
    
    projection_df = st.session_state.prob_engine.generate_cash_flow_projection(
        st.session_state.df, months_ahead
    )
    
    if not projection_df.empty:
        cash_flow_chart = st.session_state.viz.create_cash_flow_projection(projection_df)
        st.plotly_chart(cash_flow_chart, width='stretch')
    
    # Monte Carlo simulation
    st.subheader("🎲 Monte Carlo Simulation")
    st.write("Probability distribution of potential budget outcomes")
    
    if st.button("Run Simulation", key="monte_carlo"):
        with st.spinner("Running 1000 simulations..."):
            monte_carlo_results = st.session_state.prob_engine.calculate_monte_carlo_simulation(
                st.session_state.df
            )
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Mean Variance", f"£{monte_carlo_results['mean_variance']:,.0f}")
                st.metric("Std Deviation", f"£{monte_carlo_results['std_variance']:,.0f}")
                st.metric("Probability of Surplus", f"{monte_carlo_results['probability_positive']:.1f}%")
            
            with col2:
                st.metric("5th Percentile", f"£{monte_carlo_results['percentile_5']:,.0f}")
                st.metric("95th Percentile", f"£{monte_carlo_results['percentile_95']:,.0f}")
            
            # Histogram
            histogram = st.session_state.viz.create_monte_carlo_histogram(monte_carlo_results)
            st.plotly_chart(histogram, width='stretch')


def show_data_table_tab():
    """Display and manage data table."""
    st.subheader("📋 Financial Data Table")
    
    # Data filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All"] + st.session_state.df['category'].unique().tolist()
        )
    
    with col2:
        type_filter = st.selectbox(
            "Filter by Type",
            ["All", "Income", "Expenditure"]
        )
    
    with col3:
        # Export functionality
        if st.button("📥 Export to Excel"):
            try:
                excel_buffer = export_to_excel(st.session_state.df)
                st.download_button(
                    label="Download Excel File",
                    data=excel_buffer,
                    file_name="financial_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Export error: {str(e)}")
    
    # Apply filters
    filtered_df = st.session_state.df.copy()
    
    if category_filter != "All":
        filtered_df = filtered_df[filtered_df['category'] == category_filter]
    
    if type_filter != "All":
        filtered_df = filtered_df[filtered_df['type'] == type_filter]
    
    # Display filtered data
    st.dataframe(filtered_df, width='stretch')
    
    # Data editing
    st.subheader("✏️ Edit Data")
    if st.checkbox("Enable data editing"):
        edited_df = st.data_editor(
            filtered_df,
            width='stretch',
            num_rows="dynamic"
        )
        
        if st.button("Save Changes"):
            with st.spinner("Saving changes and updating charts..."):
                # Save the edited data
                st.session_state.df = edited_df
                
                # Increment data version to trigger updates
                st.session_state.data_version += 1
                
                # Recalculate summary statistics
                st.session_state.summary_stats = st.session_state.processor.get_summary_statistics(edited_df)
                
            st.success("✅ Changes saved successfully! All charts have been updated.")
            st.info("💡 Switch between tabs to see your changes reflected in all visualizations.")
            st.rerun()


# Functions exported for main app routing