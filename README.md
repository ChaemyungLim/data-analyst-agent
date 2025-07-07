# Causal Analysis Agent

A LangGraph-based agent that uses DoWhy and TabPFN to answer causal questions from data stored in PostgreSQL.

## Features

- **Database Integration**: Connect to PostgreSQL and retrieve data
- **Data Preprocessing**: Clean and prepare data for causal analysis
- **Causal Analysis**: Use DoWhy library for robust causal inference
- **Machine Learning Enhancement**: Leverage TabPFN for treatment effect estimation
- **LangGraph Workflow**: Structured agent workflow for complex causal questions

## Architecture

The agent follows a multi-step workflow:

1. **Parse Question**: Extract causal components from user question
2. **Retrieve Data**: Connect to PostgreSQL and fetch relevant data
3. **Preprocess Data**: Clean and prepare data for analysis
4. **Analyze Causality**: Use DoWhy for causal inference
5. **Enhance with TabPFN**: Add ML-based treatment effect estimation
6. **Generate Answer**: Combine results into a comprehensive answer

## Components

### Core Modules

- `causal_agent.py`: Main LangGraph agent implementation
- `database/connection.py`: PostgreSQL database connection and queries
- `preprocessing.py`: Data cleaning and preprocessing
- `causal_analysis.py`: DoWhy-based causal inference
- `tabpfn_integration.py`: TabPFN integration for ML predictions

### Testing

- `test_agent.py`: Test script with sample data generation
- `sample_data.csv`: Generated sample dataset for testing

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database (optional for testing):
```bash
# Configure your database credentials in main.py
```

## Usage

### Basic Usage

```python
from causal_agent import CausalAnalysisAgent

# Configure database
db_config = {
    'host': 'localhost',
    'database': 'your_db',
    'user': 'your_user',
    'password': 'your_password',
    'port': 5432
}

# Create agent
agent = CausalAnalysisAgent(db_config)

# Ask causal question
question = "What is the causal effect of education on income?"
result = await agent.answer_causal_question(question)
print(result)
```

### Testing

Run the test script to try the agent with sample data:

```bash
python test_agent.py
```

## Example Questions

The agent can answer questions like:
- "What is the causal effect of education on income?"
- "How does treatment X impact outcome Y?"
- "What is the average treatment effect of intervention A?"

## Dependencies

- `langgraph`: Workflow orchestration
- `dowhy`: Causal inference
- `tabpfn`: Machine learning predictions
- `psycopg2-binary`: PostgreSQL connection
- `pandas`, `numpy`, `scikit-learn`: Data manipulation and ML
- `matplotlib`, `seaborn`: Visualization

## Notes

- TabPFN works best with datasets < 1000 samples
- DoWhy requires proper specification of causal assumptions
- The agent includes validation tests for robustness
- Database connection is optional for testing (uses mock data)