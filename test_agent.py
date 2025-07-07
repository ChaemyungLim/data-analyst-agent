"""
Test script for the causal analysis agent
"""

import asyncio
import pandas as pd
import numpy as np
from causal_agent import CausalAnalysisAgent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)


def create_sample_data():
    """Create sample data for testing"""
    np.random.seed(42)
    n_samples = 500
    
    # Create confounders
    age = np.random.normal(40, 10, n_samples)
    education = np.random.normal(12, 3, n_samples)
    experience = np.random.normal(10, 5, n_samples)
    
    # Create treatment (education program participation)
    # Higher education and younger age increase probability of treatment
    treatment_prob = 1 / (1 + np.exp(-(0.1 * education - 0.02 * age + np.random.normal(0, 0.5, n_samples))))
    treatment = np.random.binomial(1, treatment_prob, n_samples)
    
    # Create outcome (income)
    # Income depends on education, experience, age, and treatment
    income = (
        30000 +  # base income
        2000 * education +  # education effect
        1500 * experience +  # experience effect
        500 * age +  # age effect
        5000 * treatment +  # treatment effect (causal)
        np.random.normal(0, 3000, n_samples)  # noise
    )
    
    # Create DataFrame
    df = pd.DataFrame({
        'treatment': treatment,
        'age': age,
        'education': education,
        'experience': experience,
        'income': income
    })
    
    return df


def save_sample_data_to_csv():
    """Save sample data to CSV for testing without database"""
    df = create_sample_data()
    df.to_csv('/Users/chaemyunglim/llm_studies/sample_data.csv', index=False)
    print(f"Sample data saved to CSV: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


async def test_with_mock_db():
    """Test the agent with mock database functionality"""
    # Create sample data
    df = create_sample_data()
    
    # Mock database configuration
    db_config = {
        'host': 'localhost',
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_pass',
        'port': 5432
    }
    
    # Create agent
    agent = CausalAnalysisAgent(db_config)
    
    # Mock the database connection to return our sample data
    async def mock_get_sample_data(table_name, limit=1000):
        return df.head(limit)
    
    async def mock_connect():
        return True
    
    async def mock_disconnect():
        pass
    
    # Replace database methods with mocks
    agent.db_connection.get_sample_data = mock_get_sample_data
    agent.db_connection.connect = mock_connect
    agent.db_connection.disconnect = mock_disconnect
    
    # Test the agent
    question = "What is the causal effect of the education program (treatment) on income?"
    
    try:
        result = await agent.answer_causal_question(question)
        print("\n" + "="*50)
        print("CAUSAL ANALYSIS RESULT")
        print("="*50)
        print(result)
        print("="*50)
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def test_individual_components():
    """Test individual components separately"""
    print("Testing individual components...")
    
    # Test data preprocessing
    from preprocessing import DataPreprocessor
    df = create_sample_data()
    
    preprocessor = DataPreprocessor()
    processed_data, metadata = preprocessor.prepare_for_causal_analysis(
        df, 'treatment', 'income'
    )
    
    print(f"Preprocessing: {df.shape} -> {processed_data.shape}")
    print(f"Metadata keys: {list(metadata.keys())}")
    
    # Test causal analysis
    from causal_analysis import CausalAnalyzer
    analyzer = CausalAnalyzer()
    
    try:
        # Build causal model
        analyzer.build_causal_model(
            processed_data, 
            'treatment', 
            'income', 
            ['age', 'education', 'experience']
        )
        
        # Identify and estimate causal effect
        analyzer.identify_causal_effect()
        analyzer.estimate_causal_effect()
        
        # Get summary
        summary = analyzer.get_causal_effect_summary()
        print(f"Causal effect: {summary['causal_effect']:.4f}")
        print(f"Interpretation: {summary['interpretation']}")
        
    except Exception as e:
        print(f"Causal analysis error: {e}")
    
    # Test TabPFN (might not work without proper installation)
    try:
        from tabpfn_integration import TabPFNPredictor
        predictor = TabPFNPredictor()
        
        X = processed_data[['age', 'education', 'experience']]
        treatment = processed_data['treatment']
        outcome = processed_data['income']
        
        results = predictor.estimate_treatment_effects(X, treatment, outcome)
        print(f"TabPFN ATE: {results['ate']:.4f}")
        
    except Exception as e:
        print(f"TabPFN test skipped: {e}")


if __name__ == "__main__":
    # Save sample data
    save_sample_data_to_csv()
    
    # Test individual components
    print("Testing individual components...")
    asyncio.run(test_individual_components())
    
    # Test full agent
    print("\nTesting full agent...")
    asyncio.run(test_with_mock_db())