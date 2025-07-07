"""
TabPFN integration for machine learning predictions in causal analysis
"""

import pandas as pd
import numpy as np
from tabpfn import TabPFNClassifier, TabPFNRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from typing import Dict, Any, List, Tuple, Optional
import logging


class TabPFNPredictor:
    """Handles TabPFN-based predictions for causal analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.classifier = None
        self.regressor = None
        self.is_classification = None
    
    def _determine_task_type(self, y: pd.Series) -> str:
        """Determine if task is classification or regression"""
        if y.dtype == 'object' or len(y.unique()) <= 10:
            return 'classification'
        else:
            return 'regression'
    
    def train_propensity_model(self, X: pd.DataFrame, treatment: pd.Series) -> Dict[str, Any]:
        """Train propensity score model using TabPFN"""
        try:
            # TabPFN works best with smaller datasets
            if len(X) > 1000:
                self.logger.warning("TabPFN works best with <1000 samples. Consider sampling.")
            
            # Initialize classifier
            self.classifier = TabPFNClassifier(device='cpu', N_ensemble_configurations=4)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, treatment, test_size=0.2, random_state=42, stratify=treatment
            )
            
            # Train model
            self.classifier.fit(X_train.values, y_train.values)
            
            # Predict propensity scores
            propensity_scores = self.classifier.predict_proba(X.values)[:, 1]
            
            # Evaluate on test set
            y_pred = self.classifier.predict(X_test.values)
            accuracy = accuracy_score(y_test, y_pred)
            
            results = {
                'model': self.classifier,
                'propensity_scores': propensity_scores,
                'accuracy': accuracy,
                'task_type': 'classification'
            }
            
            self.logger.info(f"Propensity model trained with accuracy: {accuracy:.4f}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error training propensity model: {e}")
            raise
    
    def train_outcome_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train outcome model using TabPFN"""
        try:
            # Determine task type
            task_type = self._determine_task_type(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            if task_type == 'classification':
                # Classification task
                self.classifier = TabPFNClassifier(device='cpu', N_ensemble_configurations=4)
                self.classifier.fit(X_train.values, y_train.values)
                
                # Predictions
                y_pred = self.classifier.predict(X_test.values)
                predictions = self.classifier.predict(X.values)
                
                # Metrics
                accuracy = accuracy_score(y_test, y_pred)
                metrics = {'accuracy': accuracy}
                
            else:
                # Regression task
                self.regressor = TabPFNRegressor(device='cpu', N_ensemble_configurations=4)
                self.regressor.fit(X_train.values, y_train.values)
                
                # Predictions
                y_pred = self.regressor.predict(X_test.values)
                predictions = self.regressor.predict(X.values)
                
                # Metrics
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                metrics = {'mse': mse, 'r2': r2}
            
            results = {
                'model': self.classifier if task_type == 'classification' else self.regressor,
                'predictions': predictions,
                'metrics': metrics,
                'task_type': task_type
            }
            
            self.logger.info(f"Outcome model trained for {task_type} task")
            return results
            
        except Exception as e:
            self.logger.error(f"Error training outcome model: {e}")
            raise
    
    def estimate_treatment_effects(self, X: pd.DataFrame, treatment: pd.Series, 
                                 outcome: pd.Series) -> Dict[str, Any]:
        """Estimate treatment effects using TabPFN models"""
        try:
            # Train propensity model
            propensity_results = self.train_propensity_model(X, treatment)
            propensity_scores = propensity_results['propensity_scores']
            
            # Create datasets for treated and control groups
            treated_data = X[treatment == 1].copy()
            control_data = X[treatment == 0].copy()
            
            # Train outcome models for each group
            if len(treated_data) > 0:
                treated_outcomes = outcome[treatment == 1]
                treated_model_results = self.train_outcome_model(treated_data, treated_outcomes)
            
            if len(control_data) > 0:
                control_outcomes = outcome[treatment == 0]
                control_model_results = self.train_outcome_model(control_data, control_outcomes)
            
            # Estimate individual treatment effects
            individual_effects = []
            
            for i in range(len(X)):
                # Predict outcome under treatment
                if hasattr(self, 'regressor') and self.regressor is not None:
                    y1_pred = self.regressor.predict(X.iloc[i:i+1].values)[0]
                else:
                    y1_pred = np.mean(outcome[treatment == 1]) if len(outcome[treatment == 1]) > 0 else 0
                
                # Predict outcome under control
                y0_pred = np.mean(outcome[treatment == 0]) if len(outcome[treatment == 0]) > 0 else 0
                
                # Individual treatment effect
                ite = y1_pred - y0_pred
                individual_effects.append(ite)
            
            # Average treatment effect
            ate = np.mean(individual_effects)
            
            # Treatment effect on treated
            treated_indices = treatment == 1
            att = np.mean(np.array(individual_effects)[treated_indices]) if np.any(treated_indices) else 0
            
            results = {
                'ate': ate,
                'att': att,
                'individual_effects': individual_effects,
                'propensity_scores': propensity_scores,
                'propensity_model_accuracy': propensity_results['accuracy']
            }
            
            self.logger.info(f"Treatment effects estimated - ATE: {ate:.4f}, ATT: {att:.4f}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error estimating treatment effects: {e}")
            raise
    
    def predict_counterfactuals(self, X: pd.DataFrame, treatment: pd.Series) -> Dict[str, Any]:
        """Predict counterfactual outcomes"""
        try:
            # Create counterfactual treatment assignments
            counterfactual_treatment = 1 - treatment
            
            # Combine original and counterfactual data
            X_combined = pd.concat([X, X], ignore_index=True)
            treatment_combined = pd.concat([treatment, counterfactual_treatment], ignore_index=True)
            
            # Add treatment as feature
            X_with_treatment = X_combined.copy()
            X_with_treatment['treatment'] = treatment_combined
            
            if self.regressor is not None:
                # Use trained regressor for predictions
                counterfactual_outcomes = self.regressor.predict(X_with_treatment.values)
                
                # Split back to original and counterfactual
                original_outcomes = counterfactual_outcomes[:len(X)]
                counterfactual_outcomes = counterfactual_outcomes[len(X):]
                
                results = {
                    'original_outcomes': original_outcomes,
                    'counterfactual_outcomes': counterfactual_outcomes,
                    'treatment_effects': original_outcomes - counterfactual_outcomes
                }
                
                return results
            else:
                self.logger.warning("No trained regressor available for counterfactual prediction")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error predicting counterfactuals: {e}")
            raise
    
    def validate_model_performance(self, X: pd.DataFrame, y: pd.Series, 
                                 cv_folds: int = 5) -> Dict[str, Any]:
        """Validate model performance using cross-validation"""
        try:
            from sklearn.model_selection import cross_val_score
            
            task_type = self._determine_task_type(y)
            
            if task_type == 'classification':
                model = TabPFNClassifier(device='cpu', N_ensemble_configurations=4)
                scoring = 'accuracy'
            else:
                model = TabPFNRegressor(device='cpu', N_ensemble_configurations=4)
                scoring = 'r2'
            
            # Perform cross-validation
            cv_scores = cross_val_score(model, X.values, y.values, 
                                      cv=cv_folds, scoring=scoring)
            
            validation_results = {
                'cv_scores': cv_scores,
                'mean_score': np.mean(cv_scores),
                'std_score': np.std(cv_scores),
                'scoring_metric': scoring,
                'task_type': task_type
            }
            
            self.logger.info(f"Model validation completed - Mean {scoring}: {np.mean(cv_scores):.4f}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating model performance: {e}")
            raise