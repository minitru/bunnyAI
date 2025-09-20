#!/usr/bin/env python3
"""
Cost Calculator for Enhanced RAG System
"""

import os
from typing import Dict, Any

class CostCalculator:
    def __init__(self):
        """Initialize cost calculator with current pricing"""
        # Claude 3.5 Sonnet pricing via OpenRouter
        self.input_cost_per_1k_tokens = 0.003  # $3 per million tokens
        self.output_cost_per_1k_tokens = 0.015  # $15 per million tokens
        
        # Token estimation (1 token ≈ 4 characters for English text)
        self.chars_per_token = 4
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from character count"""
        return len(text) // self.chars_per_token
    
    def calculate_query_cost(self, context: str, book_knowledge: str, response: str, system_prompt: str = "") -> Dict[str, Any]:
        """
        Calculate the cost of a single query
        
        Args:
            context: Retrieved document context
            book_knowledge: Book analysis context
            response: Generated response
            system_prompt: System prompt (optional)
            
        Returns:
            Dictionary with cost breakdown
        """
        # Estimate tokens
        context_tokens = self.estimate_tokens(context)
        book_knowledge_tokens = self.estimate_tokens(book_knowledge)
        response_tokens = self.estimate_tokens(response)
        system_prompt_tokens = self.estimate_tokens(system_prompt) if system_prompt else 500  # Default estimate
        
        total_input_tokens = context_tokens + book_knowledge_tokens + system_prompt_tokens
        
        # Calculate costs
        input_cost = (total_input_tokens / 1000) * self.input_cost_per_1k_tokens
        output_cost = (response_tokens / 1000) * self.output_cost_per_1k_tokens
        total_cost = input_cost + output_cost
        
        return {
            'input_tokens': total_input_tokens,
            'output_tokens': response_tokens,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'breakdown': {
                'context_tokens': context_tokens,
                'book_knowledge_tokens': book_knowledge_tokens,
                'system_prompt_tokens': system_prompt_tokens,
                'response_tokens': response_tokens
            }
        }
    
    def calculate_monthly_estimate(self, queries_per_day: int = 10) -> Dict[str, Any]:
        """
        Calculate monthly cost estimate
        
        Args:
            queries_per_day: Average queries per day
            
        Returns:
            Monthly cost estimate
        """
        # Use our current system metrics
        avg_context_chars = 54314
        avg_book_knowledge_chars = 3126
        avg_response_chars = 2207
        
        # Calculate average cost per query
        avg_cost = self.calculate_query_cost(
            context="x" * avg_context_chars,
            book_knowledge="x" * avg_book_knowledge_chars,
            response="x" * avg_response_chars
        )['total_cost']
        
        queries_per_month = queries_per_day * 30
        monthly_cost = avg_cost * queries_per_month
        
        return {
            'queries_per_day': queries_per_day,
            'queries_per_month': queries_per_month,
            'avg_cost_per_query': avg_cost,
            'monthly_cost': monthly_cost,
            'yearly_cost': monthly_cost * 12
        }
    
    def compare_models(self) -> Dict[str, Any]:
        """Compare costs across different models"""
        # Our current metrics
        input_tokens = 14859
        output_tokens = 551
        
        models = {
            'Claude 3.5 Sonnet': {
                'input_cost_per_1k': 0.003,
                'output_cost_per_1k': 0.015
            },
            'GPT-4o': {
                'input_cost_per_1k': 0.005,
                'output_cost_per_1k': 0.015
            },
            'GPT-4o Mini': {
                'input_cost_per_1k': 0.00015,
                'output_cost_per_1k': 0.0006
            },
            'Gemini Pro 1.5': {
                'input_cost_per_1k': 0.0025,
                'output_cost_per_1k': 0.0075
            }
        }
        
        comparison = {}
        for model_name, pricing in models.items():
            input_cost = (input_tokens / 1000) * pricing['input_cost_per_1k']
            output_cost = (output_tokens / 1000) * pricing['output_cost_per_1k']
            total_cost = input_cost + output_cost
            
            comparison[model_name] = {
                'input_cost': input_cost,
                'output_cost': output_cost,
                'total_cost': total_cost
            }
        
        return comparison

def main():
    """Main cost analysis interface"""
    print("💰 Enhanced RAG System - Cost Analysis")
    print("="*50)
    
    calculator = CostCalculator()
    
    # Current system analysis
    print("📊 CURRENT SYSTEM ANALYSIS:")
    print("-" * 30)
    
    current_cost = calculator.calculate_query_cost(
        context="x" * 54314,  # Our current context size
        book_knowledge="x" * 3126,  # Our current book knowledge size
        response="x" * 2207  # Our current response size
    )
    
    print(f"Input tokens: {current_cost['input_tokens']:,}")
    print(f"Output tokens: {current_cost['output_tokens']:,}")
    print(f"Input cost: ${current_cost['input_cost']:.4f}")
    print(f"Output cost: ${current_cost['output_cost']:.4f}")
    print(f"Total cost per query: ${current_cost['total_cost']:.4f}")
    print()
    
    # Monthly estimates
    print("📈 MONTHLY COST ESTIMATES:")
    print("-" * 30)
    
    for queries_per_day in [5, 10, 20, 50]:
        estimate = calculator.calculate_monthly_estimate(queries_per_day)
        print(f"{queries_per_day:2d} queries/day: ${estimate['monthly_cost']:.2f}/month, ${estimate['yearly_cost']:.2f}/year")
    print()
    
    # Model comparison
    print("🔄 MODEL COST COMPARISON:")
    print("-" * 30)
    
    comparison = calculator.compare_models()
    for model_name, costs in comparison.items():
        print(f"{model_name:20s}: ${costs['total_cost']:.4f} per query")
    print()
    
    # Cost optimization tips
    print("💡 COST OPTIMIZATION TIPS:")
    print("-" * 30)
    print("• Use caching to avoid regenerating book analysis")
    print("• Consider GPT-4o Mini for simpler queries (10x cheaper)")
    print("• Reduce context size for basic questions")
    print("• Batch similar queries together")
    print("• Monitor token usage with cost calculator")
    print()
    
    print(f"✅ AVERAGE COST PER QUERY: ${current_cost['total_cost']:.4f} ({current_cost['total_cost'] * 100:.1f} cents)")

if __name__ == "__main__":
    main()
