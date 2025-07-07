"""
Data preprocessing module for causal analysis
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from typing import Dict, List, Tuple, Any
import logging


class DataPreprocessor:
    """Handles data preprocessing for causal analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean raw data"""
        df_clean = df.copy()
        
        # Remove duplicate rows
        df_clean = df_clean.drop_duplicates()
        
        # Remove columns with too many missing values (>50%)
        missing_threshold = 0.5
        missing_ratio = df_clean.isnull().sum() / len(df_clean)
        cols_to_drop = missing_ratio[missing_ratio > missing_threshold].index
        df_clean = df_clean.drop(columns=cols_to_drop)
        
        self.logger.info(f"Removed {len(cols_to_drop)} columns with >50% missing values")
        return df_clean
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset"""
        df_imputed = df.copy()
        
        # Separate numeric and categorical columns
        numeric_cols = df_imputed.select_dtypes(include=[np.number]).columns
        categorical_cols = df_imputed.select_dtypes(include=['object']).columns
        
        # Impute numeric columns with median
        if len(numeric_cols) > 0:
            numeric_imputer = SimpleImputer(strategy='median')
            df_imputed[numeric_cols] = numeric_imputer.fit_transform(df_imputed[numeric_cols])
            self.imputers['numeric'] = numeric_imputer
        
        # Impute categorical columns with mode
        if len(categorical_cols) > 0:
            categorical_imputer = SimpleImputer(strategy='most_frequent')
            df_imputed[categorical_cols] = categorical_imputer.fit_transform(df_imputed[categorical_cols])
            self.imputers['categorical'] = categorical_imputer
        
        return df_imputed
    
    def encode_categorical_variables(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical variables"""
        df_encoded = df.copy()
        categorical_cols = df_encoded.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
            self.encoders[col] = le
        
        return df_encoded
    
    def scale_features(self, df: pd.DataFrame, exclude_cols: List[str] = None) -> pd.DataFrame:
        """Scale numerical features"""
        df_scaled = df.copy()
        exclude_cols = exclude_cols or []
        
        numeric_cols = df_scaled.select_dtypes(include=[np.number]).columns
        cols_to_scale = [col for col in numeric_cols if col not in exclude_cols]
        
        if len(cols_to_scale) > 0:
            scaler = StandardScaler()
            df_scaled[cols_to_scale] = scaler.fit_transform(df_scaled[cols_to_scale])
            self.scalers['features'] = scaler
        
        return df_scaled
    
    def detect_outliers(self, df: pd.DataFrame, method: str = 'iqr') -> pd.DataFrame:
        """Detect and handle outliers"""
        df_clean = df.copy()
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        
        if method == 'iqr':
            for col in numeric_cols:
                Q1 = df_clean[col].quantile(0.25)
                Q3 = df_clean[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Cap outliers instead of removing them
                df_clean[col] = np.clip(df_clean[col], lower_bound, upper_bound)
        
        return df_clean
    
    def prepare_for_causal_analysis(self, df: pd.DataFrame, treatment_col: str, 
                                   outcome_col: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Prepare data specifically for causal analysis"""
        # Full preprocessing pipeline
        df_processed = self.clean_data(df)
        df_processed = self.handle_missing_values(df_processed)
        df_processed = self.encode_categorical_variables(df_processed)
        df_processed = self.detect_outliers(df_processed)
        
        # Don't scale treatment and outcome columns
        exclude_cols = [treatment_col, outcome_col]
        df_processed = self.scale_features(df_processed, exclude_cols)
        
        # Prepare metadata
        metadata = {
            'treatment_column': treatment_col,
            'outcome_column': outcome_col,
            'feature_columns': [col for col in df_processed.columns 
                              if col not in [treatment_col, outcome_col]],
            'original_shape': df.shape,
            'processed_shape': df_processed.shape,
            'encoders': self.encoders,
            'scalers': self.scalers,
            'imputers': self.imputers
        }
        
        return df_processed, metadata