from typing import Dict, List
import pandas as pd
import numpy as np
from openai import OpenAI
from datetime import datetime
import os
import yaml
import json

class AnalyticsEngine:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
        # DEBUGGING CODE
        print(f"In AnalyticsEngine - API key present: {'Yes' if api_key else 'No'}")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        print(f"DONE DEBUGGING OPENAI API KEY IN ANALYZER")
        # END DEBUG CODE

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
            response = self.client.chat.completions.create(
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
        """Enhanced dynamic analysis pipeline"""
        try:
            # 1. First detect patterns in the data
            print("\n1. First detect patterns in the data")
            detected_patterns = self._detect_data_patterns(df)

            # 2. Load prompts
            print("\n2. Load prompts")            
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, 'config', 'prompts.yaml')
            
            with open(config_path, 'r') as file:
                prompts = yaml.safe_load(file)

            # 3. Create enhanced context for first GPT call
            print("\n3. Create enhanced context for first GPT call")            

            data_context = {
                "columns": list(df.columns),
                "sample_data": df.head().to_dict(orient='records'),
                "total_rows": len(df),
                "data_types": df.dtypes.astype(str).to_dict(),
                "data_patterns": detected_patterns
            }
            
            # 4. Get analysis strategy with enhanced context
            print("\n4. Get analysis strategy with enhanced context")            
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

            response = self.client.chat.completions.create(**analysis_request)
            analysis_plan = json.loads(response.choices[0].message.content)
            
            # 5. Execute the analysis plan
            print("\n5. Execute the analysis plan")            
            analysis_results = self._execute_analysis_plan(df, analysis_plan)
            
            # 6. Get recommendations with enhanced context
            print("\n6. Get recommendations with enhanced context")       
            print("=== RECOMMENDATION REQUEST ===\n")     
            recommendations_prompt = prompts['dynamic_analysis']['recommendations']['user_template'].format(
                business_model=business_model,
                value_proposition=value_proposition,
                analysis_results=json.dumps(analysis_results, indent=2),
                data_patterns=detected_patterns
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

            print(json.dumps(recommendations_request, indent=2))
            print("=== END RECOMMENDATION REQUEST ===\n")

            recommendations_response = self.client.chat.completions.create(**recommendations_request)
            recommendations = json.loads(recommendations_response.choices[0].message.content)
            print("=== OPENAI RECOMMENDATION RESPONSE ===\n")
            print(json.dumps(recommendations, indent=2))
            print("=== END OPENAI RECOMMENDATION RESPONSE ===\n")

            return {
                "success": True,
                "data": {
                    "analysis": analysis_results,
                    "patterns": detected_patterns,  # Include patterns in response
                    "recommendations": recommendations.get('recommendations', [])
                }
            }
                
        except Exception as e:
            print(f"Error in dynamic analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
    def _detect_data_patterns(self, df: pd.DataFrame) -> Dict:
        """Detect patterns in the data to provide better context"""
        patterns = {
            'temporal_patterns': {},
            'correlations': [],
            'categorical_patterns': {},
            'key_metrics': {},
            'relationships': {}
        }
        
        try:
            # 1. Temporal Patterns (keeping existing logic)
            date_cols = df.select_dtypes(include=['datetime64']).columns
            for col in date_cols:
                patterns['temporal_patterns'][col] = {
                    "frequency": pd.infer_freq(df[col]),
                    "range": {
                        "start": df[col].min().isoformat(),
                        "end": df[col].max().isoformat(),
                        "span_days": (df[col].max() - df[col].min()).days
                    }
                }

            # 2. Numeric Patterns and Correlations
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) >= 2:
                # Calculate correlations (keeping existing logic)
                corr_matrix = df[numeric_cols].corr()
                for i in range(len(numeric_cols)):
                    for j in range(i + 1, len(numeric_cols)):
                        corr = corr_matrix.iloc[i, j]
                        if abs(corr) > 0.7:  # Strong correlation threshold
                            patterns['correlations'].append({
                                "columns": [numeric_cols[i], numeric_cols[j]],
                                "correlation": corr
                            })
                
                # Add relationship analysis
                patterns['relationships'] = self._analyze_relationships(df)

            # 3. Categorical Patterns (enhanced from existing)
            for col in df.select_dtypes(include=['object']).columns:
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio < 0.1:  # Likely a category
                    cat_pattern = {
                        "unique_values": df[col].nunique(),
                        "distribution": df[col].value_counts(normalize=True).to_dict()
                    }
                    
                    # Add impact analysis on numeric columns
                    if len(numeric_cols) > 0:
                        cat_pattern['numeric_impacts'] = {
                            num_col: self._analyze_categorical_impact(df, col, num_col)
                            for num_col in numeric_cols
                        }
                    
                    patterns['categorical_patterns'][col] = cat_pattern

            # 4. Identify Key Metrics
            patterns['key_metrics'] = self._identify_key_metrics(df, patterns['relationships'])

            return patterns
            
        except Exception as e:
            print(f"Error in pattern detection: {e}")
            return {
                'temporal_patterns': {},
                'correlations': [],
                'categorical_patterns': {},
                'key_metrics': {},
                'relationships': {}
            }

    def _enrich_analysis_results(self, base_results: Dict, df: pd.DataFrame) -> Dict:
        """Enrich analysis results with additional context"""
        enriched = base_results.copy()
        
        # Add trend analysis for time series data
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            primary_date_col = date_cols[0]
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            
            trends = {}
            for col in numeric_cols:
                if col in base_results:  # Only analyze metrics we've calculated
                    # Calculate growth rates
                    series = df.set_index(primary_date_col)[col]
                    if len(series) > 1:
                        growth_rate = ((series.iloc[-1] / series.iloc[0]) - 1) * 100
                        trends[f"{col}_growth"] = {
                            "total_growth_percent": growth_rate,
                            "volatility": series.pct_change().std() * 100
                        }
            
            enriched["trends"] = trends
        
        # Add statistical significance
        numeric_results = {k: v for k, v in base_results.items() 
                        if isinstance(v, (int, float))}
        if numeric_results:
            enriched["statistical_significance"] = {
                metric: {
                    "zscore": abs((value - df[metric].mean()) / df[metric].std())
                    if metric in df.columns and df[metric].std() != 0 else None
                }
                for metric, value in numeric_results.items()
            }
        
        return enriched

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
                print("^^^^INPUT IS TOO LARGE, USING A SAMPLE OF 50 ROWS^^^^")
                return {
                    'summary': {
                        'count': len(obj),
                        'mean': obj.mean().to_dict() if obj.select_dtypes(include=['number']).columns.any() else None,
                        'sample': obj.head(50).to_dict(orient='records')  # just first 50 rows as sample
                    }
                }
            return obj.to_dict(orient='records')

        if isinstance(obj, pd.Series):
            # If Series is too large, return summary
            if len(obj) > 100:
                print("^^^^INPUT IS TOO LARGE, USING A SAMPLE OF 50 ROWS^^^^")
                return {
                    'summary': {
                        'count': len(obj),
                        'mean': obj.mean() if pd.api.types.is_numeric_dtype(obj) else None,
                        'sample': dict(list(obj.items())[:50])  # first 50 items
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
    
    def _analyze_data_structure(self, df: pd.DataFrame) -> Dict:
        """Analyze structure of each column"""
        structure = {}
        
        for column in df.columns:
            col_data = df[column]
            
            if pd.api.types.is_numeric_dtype(col_data):
                structure[column] = {
                    'type': 'numeric',
                    'stats': {
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'mean': float(col_data.mean()),
                        'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100
                    }
                }
            elif pd.api.types.is_datetime64_dtype(col_data):
                structure[column] = {
                    'type': 'temporal',
                    'range': {
                        'start': col_data.min().isoformat(),
                        'end': col_data.max().isoformat()
                    }
                }
            else:
                structure[column] = {
                    'type': 'categorical',
                    'unique_values': col_data.nunique(),
                    'distribution': col_data.value_counts(normalize=True).head().to_dict()
                }
        
        return structure

    def _analyze_relationships(self, df: pd.DataFrame) -> Dict:
        """Analyze relationships between columns"""
        relationships = {
            'correlations': {},
            'dependencies': {}
        }
        
        # Analyze numeric correlations
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    corr = corr_matrix.iloc[i, j]
                    if abs(corr) > 0.3:  # Only include significant correlations
                        relationships['correlations'][f"{numeric_cols[i]}_{numeric_cols[j]}"] = {
                            'strength': round(corr, 3),
                            'direction': 'positive' if corr > 0 else 'negative'
                        }
        
        # Analyze categorical dependencies
        categorical_cols = df.select_dtypes(exclude=['number', 'datetime64']).columns
        for col in categorical_cols:
            for numeric_col in numeric_cols:
                dependency = self._analyze_categorical_impact(df, col, numeric_col)
                if dependency['strength'] > 0.1:  # Only include significant dependencies
                    relationships['dependencies'][f"{col}_{numeric_col}"] = dependency
        
        return relationships

    def _analyze_categorical_impact(self, df: pd.DataFrame, cat_col: str, num_col: str) -> Dict:
        """Analyze how categorical variables impact numeric metrics"""
        try:
            # Calculate average metric value for each category
            group_means = df.groupby(cat_col)[num_col].mean()
            
            # Calculate variation between categories
            overall_mean = df[num_col].mean()
            variation = group_means.std() / overall_mean if overall_mean != 0 else 0
            
            return {
                'strength': round(variation, 3),
                'impact': 'high' if variation > 0.5 else 'medium' if variation > 0.2 else 'low'
            }
        except Exception:
            return {'strength': 0, 'impact': 'error'}

    def _identify_key_metrics(self, df: pd.DataFrame, relationships: Dict) -> Dict:
        """Identify key metrics based on their relationships and characteristics"""
        key_metrics = {}
        
        # Count relationships for each metric
        metric_influence = {}
        for metric in df.columns:
            correlation_count = sum(1 for k in relationships['correlations'].keys() if metric in k)
            dependency_count = sum(1 for k in relationships['dependencies'].keys() if metric in k)
            
            if pd.api.types.is_numeric_dtype(df[metric]):
                metric_influence[metric] = {
                    'relationship_count': correlation_count + dependency_count,
                    'type': self._determine_metric_type(df[metric]),
                    'related_metrics': [
                        k.replace(f"{metric}_", "").replace(f"_{metric}", "")
                        for k in relationships['correlations'].keys()
                        if metric in k
                    ]
                }
        
        # Select top metrics by influence
        sorted_metrics = sorted(metric_influence.items(), 
                            key=lambda x: x[1]['relationship_count'], 
                            reverse=True)
        
        for metric, info in sorted_metrics[:5]:  # Top 5 most influential metrics
            key_metrics[metric] = info
        
        return key_metrics

    def _determine_metric_type(self, series: pd.Series) -> str:
        """Determine the type and characteristics of a metric"""
        if series.min() >= 0:
            if series.dtype in ['int64', 'int32']:
                return 'count_metric'
            else:
                return 'continuous_metric'
        else:
            return 'change_metric'