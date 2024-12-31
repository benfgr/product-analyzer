from typing import Dict, List
import pandas as pd
import numpy as np
import openai
from datetime import datetime
import os
import yaml
import json

class AnalyticsEngine:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
    def analyze_data(self, 
                    df: pd.DataFrame,
                    business_model: str,
                    value_proposition: str,
                    target_metrics: List[str],
                    revenue_drivers: List[str]) -> Dict:
        """Main analysis pipeline"""
        try:
            # 1. Prepare data summary
            data_summary = self._prepare_data_summary(df)
            
            # 2. Force reload prompts
            with open('config/prompts.yaml', 'r') as file:
                prompts = yaml.safe_load(file)
                #print("\nLoaded prompts from YAML:")
                #print(json.dumps(prompts, indent=2))
                #print("\n")
        
            # 3. Generate insights using GPT-4
            prompt = prompts['analysis']['user_template'].format(
                business_model=business_model,
                value_proposition=value_proposition,
                target_metrics=', '.join(target_metrics),
                revenue_drivers=', '.join(revenue_drivers),
                data_summary=data_summary
            )

            # Log the complete request we're sending to OpenAI
            request_payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": prompts['analysis']['system_role']},
                    {"role": "user", "content": prompt}
                ],
                "response_format": { "type": "json_object" },
                "temperature": 0.3
            }
            print("Sending prompt to OpenAI...")
            print(json.dumps(request_payload, indent=2))

            # Make the API call
            response = openai.chat.completions.create(
                **request_payload
            )
            
            # Parse the JSON response
            raw_response = response.choices[0].message.content
            print("Raw OpenAI response:", raw_response)
            
            insights = json.loads(raw_response)
            
            # Ensure we have recommendations
            if not insights.get('recommendations'):
                print("No recommendations found in response, using fallback")
                recommendations = [{
                    "recommendation": "Error: No recommendations generated. Please try again.",
                    "revenue_impact": "Unknown",
                    "confidence": 0.0
                }]
            else:
                recommendations = insights['recommendations']
            
            return {
                "success": True,
                "data": {
                    "recommendations": recommendations,
                    "metrics": data_summary["metrics"]
                }
        }
            
        except Exception as e:
            print(f"Error in analyze_data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_data_dynamic(
        self, 
        df: pd.DataFrame,
        business_model: str,
        value_proposition: str
    ) -> Dict:
        """Dynamic analysis pipeline"""
        try:
            # 1. Get data structure understanding and analysis strategy

            # Get directory of current file
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, 'config', 'prompts.yaml')
        
            print(f"Looking for config at: {config_path}")  # Debug print
        
            with open(config_path, 'r') as file:
                prompts = yaml.safe_load(file)

            # Prepare context for first GPT call
            data_context = {
                "columns": list(df.columns),
                "sample_data": df.head().to_dict(orient='records'),
                "total_rows": len(df),
                "data_types": df.dtypes.astype(str).to_dict()
            }
            
            # First GPT call - Get analysis strategy
            prompt = prompts['dynamic_analysis']['schema_understanding']['user_template'].format(
                business_model=business_model,
                value_proposition=value_proposition,
                **data_context
            )

            print("\n=== ANALYSIS STRATEGY REQUEST ===")
            analysis_request = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system", 
                        "content": prompts['dynamic_analysis']['schema_understanding']['system_role']
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.5
            }
            print(json.dumps(analysis_request, indent=2))
            print("=== END ANALYSIS STRATEGY REQUEST ===\n")

            response = openai.chat.completions.create(**analysis_request)
            analysis_plan = json.loads(response.choices[0].message.content)
            
            print("\n=== ANALYSIS PLAN ===")
            print(json.dumps(analysis_plan, indent=2))
            print("=== END ANALYSIS PLAN ===\n")
            
            # 2. Execute the analysis plan
            analysis_results = self._execute_analysis_plan(df, analysis_plan)

            # 3. Get recommendations
            
            serializable_results = {
                k: self._make_json_serializable(v) 
                for k, v in analysis_results.items()
            }
            
            recommendations_prompt = prompts['dynamic_analysis']['recommendations']['user_template'].format(
            business_model=business_model,
            value_proposition=value_proposition,
            analysis_results=json.dumps(analysis_results, indent=2)
            )

            recommendations_request = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system", 
                        "content": prompts['dynamic_analysis']['recommendations']['system_role']
                    },
                    {
                        "role": "user",
                        "content": recommendations_prompt
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }

            recommendations_response = openai.chat.completions.create(**recommendations_request)
            recommendations = json.loads(recommendations_response.choices[0].message.content)

            return {
                "success": True,
                "data": {
                    "analysis": analysis_results,
                    "recommendations": recommendations.get('recommendations', [])
                }
            }
            
        except Exception as e:
            print(f"Error in dynamic analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_analysis_plan(self, df: pd.DataFrame, analysis_plan: Dict) -> Dict:
        """Execute the analysis plan from GPT"""
        try:
            results = {}
            
            # Standardize column names to uppercase for consistency
            df.columns = df.columns.str.upper()

            print("\nAvailable columns:", df.columns.tolist())
            
            for metric in analysis_plan.get('metrics', []):
                try:
                    print(f"\nAttempting to calculate metric: {metric['name']}")
                    
                    # Clean up the code and store result explicitly
                    code = metric['code']
                    # Replace 'data' with 'df'
                    code = code.replace("data[", "df[")
                    code = code.replace("data.", "df.")
                    # Fix groupby syntax with multiple columns
                    if "'][" in code:
                        code = code.replace("']['", "', '")
                    # Remove import statements
                    code = '\n'.join(line for line in code.split('\n') 
                                if not line.strip().startswith('import'))
                    
                    # Add explicit result assignment
                    if not code.strip().startswith('result ='):
                        code = code.strip() + '\nresult = ' + code.strip().split('=')[-1].strip()
                    
                    print(f"Modified code:\n{code}")
                    
                    # Create a safe execution environment
                    local_vars = {
                        'df': df.copy(),
                        'pd': pd,
                        'np': np,
                        'result': None
                    }
                    
                    # Execute the analysis code
                    exec(code, {'__builtins__': {}}, local_vars)
                    
                    if local_vars['result'] is not None:
                        results[metric['name']] = self._make_json_serializable(local_vars['result'])
                        print(f"Successfully calculated {metric['name']}: {results[metric['name']]}")
                    else:
                        print(f"Warning: Could not find result for {metric['name']}")
                        
                except Exception as e:
                    print(f"Error calculating metric {metric['name']}: {str(e)}")
                    print(f"Code that failed: {code}")
                    results[metric['name']] = None
            
            return results
        except Exception as e:
            print(f"Error executing analysis plan: {e}")
            return {}

    def _make_json_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, pd.DataFrame):
            # If DataFrame is too large, return summary statistics
            if len(obj) > 100:  # arbitrary threshold
                return {
                    'summary': {
                        'count': len(obj),
                        'mean': obj.mean().to_dict() if obj.select_dtypes(include=['number']).columns.any() else None,
                        'sample': obj.head(5).to_dict(orient='records')  # just first 5 rows as sample
                    }
                }
            return obj.to_dict(orient='records')

        if isinstance(obj, pd.Series):
            # If Series is too large, return summary
            if len(obj) > 100:
                return {
                    'summary': {
                        'count': len(obj),
                        'mean': obj.mean() if pd.api.types.is_numeric_dtype(obj) else None,
                        'sample': dict(list(obj.items())[:5])  # first 5 items
                    }
                }
            return obj.to_dict()

        if isinstance(obj, np.integer):
            return int(obj)

        if isinstance(obj, np.floating):
            return float(obj)

        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    def _prepare_data_summary(self, df: pd.DataFrame) -> Dict:

        """Create a summary of the data for GPT-4"""
        summary = {
            "total_records": len(df),
            "metrics": {}
        }
        
        # Time range using week
        if 'week' in df.columns:
            summary["date_range"] = {
                "start": df['week'].min(),
                "end": df['week'].max()
            }
        
        # Function to safely convert string numbers with commas to float
        def safe_numeric_conversion(value):
            if isinstance(value, str):
                # Remove commas and convert to float
                return float(value.replace(',', ''))
            return float(value)
        
        # Usage metrics
        if 'views' in df.columns:
            summary["metrics"]["total_views"] = sum(safe_numeric_conversion(x) for x in df['views'])
        
        if 'clicks' in df.columns:
            summary["metrics"]["total_clicks"] = sum(safe_numeric_conversion(x) for x in df['clicks'])
        
        if 'attributed_revenue' in df.columns:
            summary["metrics"]["total_revenue"] = sum(safe_numeric_conversion(x) for x in df['attributed_revenue'])
        
        # Content metrics
        if 'widget_name' in df.columns:
            summary["metrics"]["widget_distribution"] = df['widget_name'].value_counts().to_dict()
        
        if 'layout' in df.columns:
            summary["metrics"]["layout_distribution"] = df['layout'].value_counts().to_dict()
        
        if 'customer_id' in df.columns:
            summary["metrics"]["unique_customers"] = df['customer_id'].nunique()
        
        return summary