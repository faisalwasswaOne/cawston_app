import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import streamlit as st


class ProbabilityEngine:
    """Handles probability scenarios and budget projections."""
    
    def __init__(self):
        self.scenarios = {}
        
    def apply_probability_scenario(self, df: pd.DataFrame, probabilities: Dict[str, float]) -> pd.DataFrame:
        """Apply probability adjustments to budget data."""
        df_scenario = df.copy()
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Apply probabilities to remaining budget
        df_scenario['probability_factor'] = df_scenario.apply(
            lambda row: probabilities.get(row['category'], 100) / 100, axis=1
        )
        
        # Calculate adjusted projections
        df_scenario['remaining_budget'] = df_scenario[budget_col] - df_scenario[actual_col]
        df_scenario['projected_remaining'] = df_scenario['remaining_budget'] * df_scenario['probability_factor']
        df_scenario['projected_total'] = df_scenario[actual_col] + df_scenario['projected_remaining']
        df_scenario['projected_variance'] = df_scenario[budget_col] - df_scenario['projected_total']
        
        return df_scenario
    
    def calculate_risk_assessment(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate risk metrics for budget items."""
        df_risk = df.copy()
        
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Calculate variance percentage
        df_risk['variance_pct'] = ((df_risk[budget_col] - df_risk[actual_col]) / 
                                   df_risk[budget_col] * 100).fillna(0)
        
        # Risk categories
        def categorize_risk(variance_pct, budget_amount):
            abs_variance = abs(variance_pct)
            if budget_amount == 0:
                return 'No Budget'
            elif abs_variance <= 5:
                return 'Low Risk'
            elif abs_variance <= 15:
                return 'Medium Risk'
            elif abs_variance <= 30:
                return 'High Risk'
            else:
                return 'Critical Risk'
        
        df_risk['risk_category'] = df_risk.apply(
            lambda row: categorize_risk(row['variance_pct'], row[budget_col]), axis=1
        )
        
        # Risk score (0-100, higher = more risky)
        df_risk['risk_score'] = np.clip(abs(df_risk['variance_pct']) * 2, 0, 100)
        
        return df_risk
    
    def generate_cash_flow_projection(self, df: pd.DataFrame, months_ahead: int = 12) -> pd.DataFrame:
        """Generate monthly cash flow projections."""
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        # Calculate monthly burn rate based on current actual spending
        months_elapsed = 5  # Assuming April to August (5 months)
        
        projections = []
        
        for index, row in df.iterrows():
            monthly_actual = row[actual_col] / months_elapsed if months_elapsed > 0 else 0
            remaining_budget = row[budget_col] - row[actual_col]
            
            # Project future months
            cumulative_projected = row[actual_col]
            
            for month in range(1, months_ahead + 1):
                cumulative_projected += monthly_actual
                
                projections.append({
                    'description': row['description'],
                    'category': row['category'],
                    'month': month,
                    'monthly_projected': monthly_actual,
                    'cumulative_projected': cumulative_projected,
                    'budget': row[budget_col],
                    'remaining_budget': row[budget_col] - cumulative_projected
                })
        
        return pd.DataFrame(projections)
    
    def calculate_scenario_comparison(self, df: pd.DataFrame, scenarios: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """Compare multiple probability scenarios."""
        comparison_data = []
        
        for scenario_name, probabilities in scenarios.items():
            scenario_df = self.apply_probability_scenario(df, probabilities)
            
            total_budget = scenario_df['budget_2025_26' if 'budget_2025_26' in scenario_df.columns else 'budget'].sum()
            total_projected = scenario_df['projected_total'].sum()
            total_variance = scenario_df['projected_variance'].sum()
            
            comparison_data.append({
                'scenario': scenario_name,
                'total_budget': total_budget,
                'total_projected': total_projected,
                'total_variance': total_variance,
                'variance_percentage': (total_variance / total_budget * 100) if total_budget != 0 else 0
            })
        
        return pd.DataFrame(comparison_data)
    
    def save_scenario(self, name: str, probabilities: Dict[str, float]):
        """Save a probability scenario for later use."""
        self.scenarios[name] = probabilities.copy()
    
    def load_scenario(self, name: str) -> Optional[Dict[str, float]]:
        """Load a saved probability scenario."""
        return self.scenarios.get(name)
    
    def get_default_scenarios(self, categories: List[str]) -> Dict[str, Dict[str, float]]:
        """Generate default probability scenarios."""
        scenarios = {}
        
        # Conservative scenario (60-80% realization)
        conservative = {cat: np.random.uniform(60, 80) for cat in categories}
        scenarios['Conservative'] = conservative
        
        # Optimistic scenario (90-100% realization)
        optimistic = {cat: np.random.uniform(90, 100) for cat in categories}
        scenarios['Optimistic'] = optimistic
        
        # Pessimistic scenario (40-60% realization)
        pessimistic = {cat: np.random.uniform(40, 60) for cat in categories}
        scenarios['Pessimistic'] = pessimistic
        
        # Realistic scenario (70-90% realization)
        realistic = {cat: np.random.uniform(70, 90) for cat in categories}
        scenarios['Realistic'] = realistic
        
        return scenarios
    
    def calculate_monte_carlo_simulation(self, df: pd.DataFrame, simulations: int = 1000) -> Dict:
        """Run Monte Carlo simulation for budget outcomes."""
        budget_col = 'budget_2025_26' if 'budget_2025_26' in df.columns else 'budget'
        actual_col = 'actual_net' if 'actual_net' in df.columns else 'actual'
        
        results = []
        
        for _ in range(simulations):
            # Generate random probabilities for each category
            scenario_df = df.copy()
            random_probs = {}
            
            for category in df['category'].unique():
                # Assume normal distribution around 75% with std dev of 20%
                prob = np.random.normal(75, 20)
                prob = np.clip(prob, 10, 100)  # Keep between 10% and 100%
                random_probs[category] = prob
            
            scenario_df = self.apply_probability_scenario(scenario_df, random_probs)
            total_variance = scenario_df['projected_variance'].sum()
            results.append(total_variance)
        
        results = np.array(results)
        
        return {
            'mean_variance': np.mean(results),
            'std_variance': np.std(results),
            'percentile_5': np.percentile(results, 5),
            'percentile_25': np.percentile(results, 25),
            'percentile_75': np.percentile(results, 75),
            'percentile_95': np.percentile(results, 95),
            'probability_positive': np.sum(results > 0) / len(results) * 100,
            'all_results': results
        }