#!/usr/bin/env python3
"""
Model Selection and Comparison Tool
"""

import os
import time
from typing import Dict, Any, List
from setup_openrouter import setup_openrouter_env
from enhanced_rag import EnhancedRAG

class ModelSelector:
    def __init__(self):
        """Initialize the model selector"""
        setup_openrouter_env()
        
        # Available models to test (with pricing info)
        self.models = {
            "openai/gpt-4o-mini": {
                "name": "GPT-4o Mini",
                "provider": "OpenAI",
                "context": "128k tokens",
                "cost": "Very Low",
                "description": "Fast, efficient, good for most tasks"
            },
            "openai/gpt-4o": {
                "name": "GPT-4o",
                "provider": "OpenAI", 
                "context": "128k tokens",
                "cost": "High",
                "description": "Most capable, best reasoning"
            },
            "anthropic/claude-3.5-sonnet": {
                "name": "Claude 3.5 Sonnet",
                "provider": "Anthropic",
                "context": "200k tokens", 
                "cost": "Medium",
                "description": "Excellent for analysis, great reasoning"
            },
            "google/gemini-pro-1.5": {
                "name": "Gemini Pro 1.5",
                "provider": "Google",
                "context": "2M tokens",
                "cost": "Low",
                "description": "Very long context, good performance"
            },
            "meta-llama/llama-3.1-405b-instruct": {
                "name": "Llama 3.1 405B",
                "provider": "Meta",
                "context": "128k tokens",
                "cost": "Medium",
                "description": "Open source, good for complex tasks"
            }
        }
    
    def show_available_models(self):
        """Display available models with their characteristics"""
        print("🤖 Available Models on OpenRouter")
        print("="*80)
        
        for model_id, info in self.models.items():
            print(f"\n📋 {info['name']} ({model_id})")
            print(f"   Provider: {info['provider']}")
            print(f"   Context: {info['context']}")
            print(f"   Cost: {info['cost']}")
            print(f"   Description: {info['description']}")
    
    def test_model(self, model_id: str, test_query: str = "who won, blanche or elle") -> Dict[str, Any]:
        """
        Test a specific model with a query
        
        Args:
            model_id: The model to test
            test_query: The test query
            
        Returns:
            Dictionary with test results
        """
        print(f"\n🧪 Testing {self.models[model_id]['name']}...")
        print("-" * 50)
        
        # Temporarily change model
        original_model = os.getenv("OPENROUTER_MODEL")
        os.environ["OPENROUTER_MODEL"] = model_id
        
        try:
            # Initialize RAG with new model
            rag = EnhancedRAG()
            rag.initialize_book_knowledge()
            
            # Time the query
            start_time = time.time()
            result = rag.query(test_query, n_results=15, use_book_knowledge=True)
            query_time = time.time() - start_time
            
            # Analyze the response
            answer = result['answer']
            answer_length = len(answer)
            
            # Simple quality assessment
            quality_score = self.assess_response_quality(answer)
            
            return {
                'model': model_id,
                'model_name': self.models[model_id]['name'],
                'query_time': query_time,
                'answer_length': answer_length,
                'quality_score': quality_score,
                'context_used': result['context_length'],
                'book_knowledge_used': result['book_knowledge_length'],
                'answer_preview': answer[:200] + "..." if len(answer) > 200 else answer,
                'success': True
            }
            
        except Exception as e:
            return {
                'model': model_id,
                'model_name': self.models[model_id]['name'],
                'error': str(e),
                'success': False
            }
        finally:
            # Restore original model
            if original_model:
                os.environ["OPENROUTER_MODEL"] = original_model
    
    def assess_response_quality(self, answer: str) -> int:
        """
        Simple quality assessment based on answer characteristics
        
        Args:
            answer: The answer to assess
            
        Returns:
            Quality score (1-10)
        """
        score = 5  # Base score
        
        # Length bonus (longer answers often more comprehensive)
        if len(answer) > 500:
            score += 1
        if len(answer) > 1000:
            score += 1
        
        # Literary analysis indicators
        literary_terms = ['character', 'theme', 'symbolism', 'narrative', 'plot', 'development', 'conflict', 'resolution']
        literary_count = sum(1 for term in literary_terms if term.lower() in answer.lower())
        score += min(literary_count // 2, 2)  # Up to 2 points for literary analysis
        
        # Evidence indicators
        evidence_terms = ['evidence', 'example', 'specifically', 'according to', 'text shows', 'demonstrates']
        evidence_count = sum(1 for term in evidence_terms if term.lower() in answer.lower())
        score += min(evidence_count, 1)  # Up to 1 point for evidence
        
        # Analysis depth indicators
        depth_terms = ['analysis', 'interpretation', 'significance', 'meaning', 'implications', 'complexity']
        depth_count = sum(1 for term in depth_terms if term.lower() in answer.lower())
        score += min(depth_count, 1)  # Up to 1 point for depth
        
        return min(score, 10)
    
    def compare_models(self, test_query: str = "who won, blanche or elle") -> List[Dict[str, Any]]:
        """
        Compare multiple models on the same query
        
        Args:
            test_query: The test query to use
            
        Returns:
            List of comparison results
        """
        print("🔍 Comparing Models")
        print("="*60)
        print(f"Test Query: '{test_query}'")
        print()
        
        results = []
        
        for model_id in self.models.keys():
            result = self.test_model(model_id, test_query)
            results.append(result)
            
            if result['success']:
                print(f"✅ {result['model_name']}")
                print(f"   Time: {result['query_time']:.2f}s")
                print(f"   Length: {result['answer_length']} chars")
                print(f"   Quality: {result['quality_score']}/10")
                print(f"   Preview: {result['answer_preview']}")
            else:
                print(f"❌ {result['model_name']}: {result['error']}")
            
            print()
        
        return results
    
    def get_recommendations(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate recommendations based on comparison results
        
        Args:
            results: Results from model comparison
            
        Returns:
            Dictionary with recommendations
        """
        print("💡 Model Recommendations")
        print("="*60)
        
        # Filter successful results
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            return {'error': 'No successful results to compare'}
        
        # Find best performing models
        best_quality = max(successful_results, key=lambda x: x['quality_score'])
        fastest = min(successful_results, key=lambda x: x['query_time'])
        best_balance = max(successful_results, key=lambda x: x['quality_score'] / x['query_time'])
        
        print(f"🏆 Best Quality: {best_quality['model_name']}")
        print(f"   Quality: {best_quality['quality_score']}/10")
        print(f"   Time: {best_quality['query_time']:.2f}s")
        print(f"   Cost: {self.models[best_quality['model']]['cost']}")
        
        print(f"\n⚡ Fastest: {fastest['model_name']}")
        print(f"   Time: {fastest['query_time']:.2f}s")
        print(f"   Quality: {fastest['quality_score']}/10")
        print(f"   Cost: {self.models[fastest['model']]['cost']}")
        
        print(f"\n⚖️ Best Balance: {best_balance['model_name']}")
        print(f"   Quality: {best_balance['quality_score']}/10")
        print(f"   Time: {best_balance['query_time']:.2f}s")
        print(f"   Efficiency: {best_balance['quality_score'] / best_balance['query_time']:.2f}")
        print(f"   Cost: {self.models[best_balance['model']]['cost']}")
        
        # Generate recommendation
        if best_quality['quality_score'] >= 8:
            recommended = best_quality
            reason = "Excellent quality"
        elif best_balance['quality_score'] >= 7 and best_balance['query_time'] < 15:
            recommended = best_balance
            reason = "Good balance of quality and speed"
        else:
            recommended = fastest
            reason = "Fastest with acceptable quality"
        
        print(f"\n✅ RECOMMENDATION: {recommended['model_name']}")
        print(f"   Reason: {reason}")
        print(f"   Model ID: {recommended['model']}")
        
        return {
            'recommended': recommended,
            'best_quality': best_quality,
            'fastest': fastest,
            'best_balance': best_balance
        }

def main():
    """Main model selection interface"""
    print("🎯 Model Selection Tool")
    print("="*60)
    
    selector = ModelSelector()
    
    while True:
        print("\nOptions:")
        print("1. Show available models")
        print("2. Test a specific model")
        print("3. Compare all models")
        print("4. Quick recommendation")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            selector.show_available_models()
        elif choice == '2':
            selector.show_available_models()
            model_id = input("\nEnter model ID to test: ").strip()
            if model_id in selector.models:
                result = selector.test_model(model_id)
                if result['success']:
                    print(f"\n✅ Test completed successfully!")
                    print(f"Quality: {result['quality_score']}/10")
                    print(f"Time: {result['query_time']:.2f}s")
                else:
                    print(f"\n❌ Test failed: {result['error']}")
            else:
                print("❌ Invalid model ID")
        elif choice == '3':
            print("⚠️ This will test all models and may take several minutes...")
            proceed = input("Proceed? (y/n): ").strip().lower()
            if proceed == 'y':
                results = selector.compare_models()
                selector.get_recommendations(results)
        elif choice == '4':
            print("🔍 Quick recommendation based on current model...")
            current_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
            print(f"Current: {current_model}")
            
            # Test current model
            result = selector.test_model(current_model)
            if result['success']:
                print(f"Current performance: {result['quality_score']}/10 quality, {result['query_time']:.2f}s")
                
                # Suggest alternatives
                if result['quality_score'] < 7:
                    print("💡 Consider upgrading to Claude 3.5 Sonnet for better quality")
                elif result['query_time'] > 15:
                    print("💡 Consider GPT-4o Mini for faster responses")
                else:
                    print("✅ Current model is performing well!")
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
