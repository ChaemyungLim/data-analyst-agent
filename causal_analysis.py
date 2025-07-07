"""
Causal analysis module using DoWhy library
"""

import pandas as pd
import numpy as np
from dowhy import CausalModel
from dowhy.causal_estimators import LinearRegressionEstimator
from typing import Dict, List, Any, Optional, Tuple
import logging
import networkx as nx


class CausalAnalyzer:
    """Handles causal analysis using DoWhy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.causal_model = None
        self.identified_estimand = None
        self.causal_estimate = None
    
    def create_causal_graph(self, treatment: str, outcome: str, 
                          confounders: List[str], 
                          instruments: List[str] = None) -> str:
        """Create causal graph specification"""
        graph = f"digraph {{\n"
        
        # Treatment -> Outcome
        graph += f'    {treatment} -> {outcome};\n'
        
        # Confounders -> Treatment and Outcome
        for confounder in confounders:
            graph += f'    {confounder} -> {treatment};\n'
            graph += f'    {confounder} -> {outcome};\n'
        
        # Instruments -> Treatment (if provided)
        if instruments:
            for instrument in instruments:
                graph += f'    {instrument} -> {treatment};\n'
        
        graph += "}"
        return graph
    
    def build_causal_model(self, df: pd.DataFrame, treatment: str, 
                          outcome: str, confounders: List[str],
                          instruments: List[str] = None) -> CausalModel:
        """Build causal model using DoWhy"""
        try:
            # Create causal graph
            causal_graph = self.create_causal_graph(treatment, outcome, confounders, instruments)
            
            # Build causal model
            self.causal_model = CausalModel(
                data=df,
                treatment=treatment,
                outcome=outcome,
                graph=causal_graph,
                instruments=instruments
            )
            
            self.logger.info("Causal model created successfully")
            return self.causal_model
            
        except Exception as e:
            self.logger.error(f"Error building causal model: {e}")
            raise
    
    def identify_causal_effect(self, method: str = "backdoor") -> Any:
        """Identify causal effect using specified method"""
        if not self.causal_model:
            raise ValueError("Causal model not built yet")
        
        try:
            self.identified_estimand = self.causal_model.identify_effect(method=method)
            self.logger.info(f"Causal effect identified using {method} method")
            return self.identified_estimand
            
        except Exception as e:
            self.logger.error(f"Error identifying causal effect: {e}")
            raise
    
    def estimate_causal_effect(self, method: str = "backdoor.linear_regression") -> Any:
        """Estimate causal effect"""
        if not self.identified_estimand:
            raise ValueError("Causal effect not identified yet")
        
        try:
            self.causal_estimate = self.causal_model.estimate_effect(
                self.identified_estimand,
                method_name=method
            )
            
            self.logger.info(f"Causal effect estimated using {method}")
            return self.causal_estimate
            
        except Exception as e:
            self.logger.error(f"Error estimating causal effect: {e}")
            raise
    
    def validate_causal_estimate(self) -> Dict[str, Any]:
        """Validate causal estimate using refutation tests"""
        if not self.causal_estimate:
            raise ValueError("Causal estimate not computed yet")
        
        validation_results = {}
        
        try:
            # Placebo treatment test
            placebo_refutation = self.causal_model.refute_estimate(
                self.identified_estimand,
                self.causal_estimate,
                method_name="placebo_treatment_refuter"
            )
            validation_results['placebo_treatment'] = placebo_refutation
            
            # Random common cause test
            random_cause_refutation = self.causal_model.refute_estimate(
                self.identified_estimand,
                self.causal_estimate,
                method_name="random_common_cause"
            )
            validation_results['random_common_cause'] = random_cause_refutation
            
            # Data subset refutation
            subset_refutation = self.causal_model.refute_estimate(
                self.identified_estimand,
                self.causal_estimate,
                method_name="data_subset_refuter"
            )
            validation_results['data_subset'] = subset_refutation
            
            self.logger.info("Causal estimate validation completed")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating causal estimate: {e}")
            raise
    
    def get_causal_effect_summary(self) -> Dict[str, Any]:
        """Get summary of causal analysis results"""
        if not self.causal_estimate:
            raise ValueError("Causal estimate not computed yet")
        
        summary = {
            'causal_effect': self.causal_estimate.value,
            'confidence_interval': getattr(self.causal_estimate, 'confidence_intervals', None),
            'p_value': getattr(self.causal_estimate, 'p_value', None),
            'method': self.causal_estimate.params.get('method_name', 'Unknown'),
            'interpretation': self._interpret_causal_effect()
        }
        
        return summary
    
    def _interpret_causal_effect(self) -> str:
        """Interpret the causal effect"""
        effect_size = self.causal_estimate.value
        
        if effect_size > 0:
            return f"Positive causal effect: Treatment increases outcome by {effect_size:.4f} units"
        elif effect_size < 0:
            return f"Negative causal effect: Treatment decreases outcome by {abs(effect_size):.4f} units"
        else:
            return "No causal effect detected"
    
    def analyze_heterogeneous_effects(self, df: pd.DataFrame, 
                                    subgroup_variable: str) -> Dict[str, Any]:
        """Analyze heterogeneous treatment effects across subgroups"""
        if not self.causal_model:
            raise ValueError("Causal model not built yet")
        
        subgroup_effects = {}
        unique_values = df[subgroup_variable].unique()
        
        for value in unique_values:
            subset_df = df[df[subgroup_variable] == value]
            
            if len(subset_df) < 10:  # Skip small subgroups
                continue
            
            try:
                # Create model for subgroup
                subgroup_model = CausalModel(
                    data=subset_df,
                    treatment=self.causal_model._treatment,
                    outcome=self.causal_model._outcome,
                    graph=self.causal_model._graph
                )
                
                # Estimate effect for subgroup
                subgroup_estimand = subgroup_model.identify_effect()
                subgroup_estimate = subgroup_model.estimate_effect(
                    subgroup_estimand,
                    method_name="backdoor.linear_regression"
                )
                
                subgroup_effects[f"{subgroup_variable}_{value}"] = {
                    'effect': subgroup_estimate.value,
                    'sample_size': len(subset_df)
                }
                
            except Exception as e:
                self.logger.warning(f"Could not estimate effect for {subgroup_variable}={value}: {e}")
        
        return subgroup_effects