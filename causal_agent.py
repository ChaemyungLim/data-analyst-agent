"""
LangGraph Agent for Causal Analysis
"""

import asyncio
from typing import Dict, Any, List, Optional, TypedDict
from langgraph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import pandas as pd
import logging

from database.connection import DatabaseConnection
from preprocessing import DataPreprocessor
from causal_analysis import CausalAnalyzer
from tabpfn_integration import TabPFNPredictor


class AgentState(TypedDict):
    """State for the causal analysis agent"""
    messages: List[Dict[str, Any]]
    user_question: str
    data: Optional[pd.DataFrame]
    processed_data: Optional[pd.DataFrame]
    metadata: Optional[Dict[str, Any]]
    causal_results: Optional[Dict[str, Any]]
    tabpfn_results: Optional[Dict[str, Any]]
    final_answer: Optional[str]
    error: Optional[str]


class CausalAnalysisAgent:
    """LangGraph agent for causal analysis"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.db_connection = DatabaseConnection(db_config)
        self.preprocessor = DataPreprocessor()
        self.causal_analyzer = CausalAnalyzer()
        self.tabpfn_predictor = TabPFNPredictor()
        self.logger = logging.getLogger(__name__)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_question", self._parse_question)
        workflow.add_node("retrieve_data", self._retrieve_data)
        workflow.add_node("preprocess_data", self._preprocess_data)
        workflow.add_node("analyze_causality", self._analyze_causality)
        workflow.add_node("enhance_with_tabpfn", self._enhance_with_tabpfn)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("handle_error", self._handle_error)
        
        # Define the flow
        workflow.set_entry_point("parse_question")
        workflow.add_edge("parse_question", "retrieve_data")
        workflow.add_edge("retrieve_data", "preprocess_data")
        workflow.add_edge("preprocess_data", "analyze_causality")
        workflow.add_edge("analyze_causality", "enhance_with_tabpfn")
        workflow.add_edge("enhance_with_tabpfn", "generate_answer")
        workflow.add_edge("generate_answer", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def _parse_question(self, state: AgentState) -> AgentState:
        """Parse the user's causal question"""
        try:
            question = state["user_question"]
            self.logger.info(f"Parsing question: {question}")
            
            # Extract key components from the question
            # This is a simplified parser - in practice, you'd want more sophisticated NLP
            parsed_info = self._extract_causal_components(question)
            
            state["metadata"] = parsed_info
            state["messages"].append({
                "role": "system",
                "content": f"Parsed question components: {parsed_info}"
            })
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error parsing question: {e}")
            state["error"] = str(e)
            return state
    
    def _extract_causal_components(self, question: str) -> Dict[str, Any]:
        """Extract treatment, outcome, and other components from question"""
        # Simple keyword-based extraction
        # In practice, you'd use more sophisticated NLP
        
        components = {
            "treatment": None,
            "outcome": None,
            "confounders": [],
            "table_name": None
        }
        
        # Common causal keywords
        causal_keywords = ["effect", "impact", "influence", "cause", "treatment"]
        outcome_keywords = ["outcome", "result", "consequence", "dependent"]
        
        # Extract table name (look for SQL-like patterns)
        words = question.lower().split()
        for i, word in enumerate(words):
            if word in ["from", "table", "dataset"]:
                if i + 1 < len(words):
                    components["table_name"] = words[i + 1]
                    break
        
        # Default assumptions for demo
        if not components["table_name"]:
            components["table_name"] = "main_dataset"
        
        return components
    
    async def _retrieve_data(self, state: AgentState) -> AgentState:
        """Retrieve data from PostgreSQL database"""
        try:
            # Connect to database
            await self.db_connection.connect()
            
            # Get table name from metadata
            table_name = state["metadata"].get("table_name", "main_dataset")
            
            # Retrieve data
            data = await self.db_connection.get_sample_data(table_name, limit=1000)
            
            if data.empty:
                raise ValueError(f"No data found in table: {table_name}")
            
            state["data"] = data
            state["messages"].append({
                "role": "system",
                "content": f"Retrieved {len(data)} rows from {table_name}"
            })
            
            self.logger.info(f"Retrieved {len(data)} rows from database")
            return state
            
        except Exception as e:
            self.logger.error(f"Error retrieving data: {e}")
            state["error"] = str(e)
            return state
    
    async def _preprocess_data(self, state: AgentState) -> AgentState:
        """Preprocess the data for causal analysis"""
        try:
            data = state["data"]
            if data is None:
                raise ValueError("No data available for preprocessing")
            
            # Assume first column is treatment, last is outcome
            # In practice, you'd extract this from the question
            treatment_col = data.columns[0]
            outcome_col = data.columns[-1]
            
            # Preprocess data
            processed_data, metadata = self.preprocessor.prepare_for_causal_analysis(
                data, treatment_col, outcome_col
            )
            
            state["processed_data"] = processed_data
            state["metadata"].update(metadata)
            state["messages"].append({
                "role": "system",
                "content": f"Preprocessed data: {processed_data.shape[0]} rows, {processed_data.shape[1]} columns"
            })
            
            self.logger.info("Data preprocessing completed")
            return state
            
        except Exception as e:
            self.logger.error(f"Error preprocessing data: {e}")
            state["error"] = str(e)
            return state
    
    async def _analyze_causality(self, state: AgentState) -> AgentState:
        """Perform causal analysis using DoWhy"""
        try:
            processed_data = state["processed_data"]
            metadata = state["metadata"]
            
            if processed_data is None:
                raise ValueError("No processed data available")
            
            treatment_col = metadata["treatment_column"]
            outcome_col = metadata["outcome_column"]
            confounders = metadata["feature_columns"][:5]  # Limit confounders
            
            # Build causal model
            self.causal_analyzer.build_causal_model(
                processed_data, treatment_col, outcome_col, confounders
            )
            
            # Identify causal effect
            self.causal_analyzer.identify_causal_effect()
            
            # Estimate causal effect
            self.causal_analyzer.estimate_causal_effect()
            
            # Validate results
            validation_results = self.causal_analyzer.validate_causal_estimate()
            
            # Get summary
            causal_summary = self.causal_analyzer.get_causal_effect_summary()
            
            state["causal_results"] = {
                "summary": causal_summary,
                "validation": validation_results
            }
            
            state["messages"].append({
                "role": "system",
                "content": f"Causal analysis completed: {causal_summary['interpretation']}"
            })
            
            self.logger.info("Causal analysis completed")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in causal analysis: {e}")
            state["error"] = str(e)
            return state
    
    async def _enhance_with_tabpfn(self, state: AgentState) -> AgentState:
        """Enhance analysis with TabPFN predictions"""
        try:
            processed_data = state["processed_data"]
            metadata = state["metadata"]
            
            if processed_data is None:
                raise ValueError("No processed data available")
            
            treatment_col = metadata["treatment_column"]
            outcome_col = metadata["outcome_column"]
            feature_cols = metadata["feature_columns"]
            
            # Extract features, treatment, and outcome
            X = processed_data[feature_cols]
            treatment = processed_data[treatment_col]
            outcome = processed_data[outcome_col]
            
            # Estimate treatment effects using TabPFN
            tabpfn_results = self.tabpfn_predictor.estimate_treatment_effects(
                X, treatment, outcome
            )
            
            state["tabpfn_results"] = tabpfn_results
            state["messages"].append({
                "role": "system",
                "content": f"TabPFN analysis completed: ATE = {tabpfn_results['ate']:.4f}"
            })
            
            self.logger.info("TabPFN enhancement completed")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in TabPFN enhancement: {e}")
            # Don't fail the entire pipeline for TabPFN errors
            state["tabpfn_results"] = {"error": str(e)}
            return state
    
    async def _generate_answer(self, state: AgentState) -> AgentState:
        """Generate final answer based on analysis results"""
        try:
            causal_results = state.get("causal_results", {})
            tabpfn_results = state.get("tabpfn_results", {})
            
            # Combine results from both methods
            answer_parts = []
            
            # DoWhy results
            if "summary" in causal_results:
                summary = causal_results["summary"]
                answer_parts.append(f"Causal Analysis (DoWhy): {summary['interpretation']}")
                answer_parts.append(f"Estimated effect size: {summary['causal_effect']:.4f}")
            
            # TabPFN results
            if "ate" in tabpfn_results:
                answer_parts.append(f"Machine Learning Analysis (TabPFN): ATE = {tabpfn_results['ate']:.4f}")
                answer_parts.append(f"ATT = {tabpfn_results['att']:.4f}")
            
            # Validation information
            if "validation" in causal_results:
                answer_parts.append("Validation tests completed for robustness.")
            
            final_answer = "\n".join(answer_parts)
            
            if not final_answer:
                final_answer = "Unable to complete causal analysis due to insufficient data or errors."
            
            state["final_answer"] = final_answer
            state["messages"].append({
                "role": "assistant",
                "content": final_answer
            })
            
            self.logger.info("Final answer generated")
            return state
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            state["error"] = str(e)
            return state
    
    async def _handle_error(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow"""
        error_message = state.get("error", "Unknown error occurred")
        state["final_answer"] = f"Error: {error_message}"
        state["messages"].append({
            "role": "assistant",
            "content": f"I encountered an error: {error_message}"
        })
        
        self.logger.error(f"Workflow error: {error_message}")
        return state
    
    async def answer_causal_question(self, question: str) -> str:
        """Main method to answer causal questions"""
        initial_state = AgentState(
            messages=[],
            user_question=question,
            data=None,
            processed_data=None,
            metadata=None,
            causal_results=None,
            tabpfn_results=None,
            final_answer=None,
            error=None
        )
        
        try:
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Clean up database connection
            await self.db_connection.disconnect()
            
            return final_state.get("final_answer", "No answer generated")
            
        except Exception as e:
            self.logger.error(f"Error in workflow execution: {e}")
            await self.db_connection.disconnect()
            return f"Error: {str(e)}"