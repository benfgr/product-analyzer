from typing import Dict, List
import pandas as pd
import numpy as np
from openai import OpenAI
from datetime import datetime
import os
import yaml
import json
import ast
from typing import Tuple, Set, Any

class CodeValidator:
    """Validates and sanitizes code generated by GPT"""
    
    @classmethod
    def validate_code(cls, code: str) -> Tuple[bool, str, str]:
        """Validates and sanitizes code"""
        try:
            # Clean up the code first
            code = cls._clean_complex_expressions(code)
            
            # Parse the code into an AST to verify syntax
            tree = ast.parse(code)
            
            # Check for unsafe operations
            unsafe_ops = cls._find_unsafe_operations(tree)
            if unsafe_ops:
                return False, "", f"Unsafe operations found: {', '.join(unsafe_ops)}"
            
            # Ensure result assignment and add safety handlers
            final_code = cls._ensure_result_assignment(code)
            
            return True, final_code, ""
            
        except SyntaxError as e:
            return False, "", f"Syntax error in code: {str(e)}"
        except Exception as e:
            return False, "", f"Validation error: {str(e)}"

    @classmethod
    def _clean_complex_expressions(cls, code: str) -> str:
        """Clean up complex expressions and add safety handlers"""
        # Handle media type comparisons
        if 'str.contains' in code and 'WIDGET_MEDIA_TYPES' in code:
            code = code.replace(
                "df[df['WIDGET_MEDIA_TYPES'].str.contains",
                "df[safe_contains(df['WIDGET_MEDIA_TYPES']"
            )
            
        # Handle default values for undefined variables
        if 'conversion_rate_estimate' in code:
            code = 'conversion_rate_estimate = 0.1  # Default conversion rate\n' + code
            
        # Handle division operations
        if '/' in code:
            parts = code.split('/')
            if len(parts) == 2:
                numerator = parts[0].strip()
                denominator = parts[1].strip()
                code = f"safe_divide({numerator}, {denominator})"
        
        return code

    @classmethod
    def _ensure_result_assignment(cls, code: str) -> str:
        """Ensure the code assigns its result to the result variable"""
        lines = code.split('\n')
        
        # If the last line doesn't start with 'result ='
        if not lines[-1].strip().startswith('result ='):
            # If it contains an assignment
            if '=' in lines[-1]:
                var_name = lines[-1].split('=')[0].strip()
                lines.append(f"result = {var_name}")
            else:
                lines.append(f"result = {lines[-1]}")
        
        final_code = '\n'.join(lines)
        
        # Add NaN handling
        final_code += "\nif isinstance(result, (float, np.float64)) and (np.isnan(result) or np.isinf(result)):\n"
        final_code += "    result = 0\n"
        final_code += "elif isinstance(result, dict):\n"
        final_code += "    result = {k: 0 if isinstance(v, (float, np.float64)) and (np.isnan(v) or np.isinf(v)) else v for k, v in result.items()}\n"
        
        return final_code

    @classmethod
    def _find_unsafe_operations(cls, tree: ast.AST) -> Set[str]:
        """Find any unsafe operations in the AST"""
        unsafe_ops = set()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                unsafe_ops.add('import')
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                unsafe_ops.add('function/class definition')
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in {'eval', 'exec', 'open', 'system', 'os'}:
                        unsafe_ops.add(node.func.id)
        
        return unsafe_ops

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
        value_proposition: str,
        business_goal: str
    ) -> Dict:
        print("Starting analyze_dynamic endpoint")
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
                business_goal=business_goal,
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

            print("\n=== ANALYSIS STRATEGY RESPONSE ===")
            print(json.dumps(analysis_plan, indent=2))
            print("\n=== END ANALYSIS STRATEGY RESPONSE ===")
            
            # 5. Execute the analysis plan
            print("\n5. Execute the analysis plan")            
            analysis_results = self._execute_analysis_plan(df, analysis_plan)
            
            # 6. Get recommendations with enhanced context
            print("\n6. Get recommendations with enhanced context")       
            print("=== RECOMMENDATION REQUEST ===\n")     
            recommendations_prompt = prompts['dynamic_analysis']['recommendations']['user_template'].format(
                business_model=business_model,
                value_proposition=value_proposition,
                business_goal=business_goal,
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
        """Execute the analysis plan with improved error handling"""
        try:
            results = {}
            
            # Preprocess the dataframe
            df = df.copy()
            df.columns = df.columns.str.upper()
            
            # Remove header rows (rows where columns contain their descriptions)
            for col in df.columns:
                # Check if any values in the column match the column name description
                mask = ~df[col].astype(str).str.contains(col, case=False, na=False)
                df = df[mask]
            
            # Convert numeric columns and handle NaN values
            for col in df.columns:
                try:
                    if 'VIEWS' in col.upper() or 'CLICKS' in col.upper():
                        df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
                    elif 'NUMBER_OF' in col.upper():
                        df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
                except (ValueError, AttributeError):
                    continue
            
            # Clean string columns
            string_columns = ['WIDGET_MEDIA_TYPES', 'WIDGET_PUBLISHMETHOD', 'WIDGET_PAGE_TYPES', 'ACCOUNT_PLAN']
            for col in string_columns:
                if col in df.columns:
                    # Remove rows where the column contains its own description
                    df = df[~df[col].astype(str).str.contains('widget|account|placement', case=False, na=False)]
            
            print("\nAvailable columns:", df.columns.tolist())
            print("\nColumn dtypes after preprocessing:", df.dtypes)
            
            # Helper functions for the execution environment
            def safe_divide(a, b):
                """Safe division handling zeros and NaN"""
                try:
                    result = np.divide(a, b, out=np.zeros_like(a, dtype=float), where=b!=0)
                    if isinstance(result, np.ndarray):
                        result[np.isnan(result)] = 0
                        result[np.isinf(result)] = 0
                    elif np.isnan(result) or np.isinf(result):
                        result = 0
                    return result
                except Exception:
                    return 0

            def safe_contains(series, pattern):
                """Safe string contains operation handling NaN"""
                try:
                    return series.fillna('').astype(str).str.contains(pattern, case=False, na=False)
                except Exception:
                    return pd.Series([False] * len(series))

            def clean_result(result):
                """Clean result by replacing NaN/inf with 0"""
                if isinstance(result, (float, np.float64)):
                    return 0 if (np.isnan(result) or np.isinf(result)) else result
                elif isinstance(result, dict):
                    return {k: clean_result(v) for k, v in result.items()}
                elif isinstance(result, list):
                    return [clean_result(v) for v in result]
                elif isinstance(result, pd.Series):
                    result = result.replace([np.inf, -np.inf], np.nan).fillna(0)
                    return result.to_dict()
                elif isinstance(result, pd.DataFrame):
                    result = result.replace([np.inf, -np.inf], np.nan).fillna(0)
                    return result.to_dict('records')
                return result

            # Persistent execution environment
            execution_namespace = {
                'pd': pd,
                'np': np,
                'df': df,
                'result': None,
                'float': float,
                'int': int,
                'str': str,
                'len': len,
                'round': round,
                'safe_divide': safe_divide,
                'safe_contains': safe_contains,
                'clean_result': clean_result
            }
            
            for metric in analysis_plan.get('metrics', []):
                try:
                    print(f"\nAttempting to calculate metric: {metric['name']}")
                    
                    code = metric['code']
                    
                    # Replace unsafe operations with safe versions
                    if 'str.contains' in code:
                        code = code.replace('.str.contains', '.pipe(safe_contains')
                        code = code.replace(')', ')')
                    
                    if '/' in code and ('sum()' in code or 'mean()' in code):
                        # Replace division with safe_divide for aggregations
                        code = code.replace('x[', 'safe_divide(x[')
                        code = code.replace('] /', '].sum(), x[')
                        code = code.replace('sum()', 'sum())')
                    
                    # Add existing results to the namespace
                    for var_name, value in results.items():
                        clean_name = var_name.lower().replace(' ', '_')
                        execution_namespace[clean_name] = value
                    
                    # Validate and sanitize the code
                    is_valid, sanitized_code, error_msg = CodeValidator.validate_code(code)
                    
                    if not is_valid:
                        raise ValueError(f"Invalid code: {error_msg}")
                    
                    print(f"Sanitized code:\n{sanitized_code}")
                    
                    # Execute the validated code
                    exec(sanitized_code, execution_namespace, execution_namespace)
                    
                    result = execution_namespace.get('result')
                    if result is not None:
                        # Check if result is too large and needs percentile analysis
                        needs_percentiles, processed_result = self._check_and_convert_large_result(result, df)
                        if needs_percentiles:
                            result = processed_result
                        else:
                        # Clean the result (replace NaN/inf with 0)
                            result = clean_result(result)
                            
                        # Round floats
                        if isinstance(result, float):
                            result = round(result, 2)
                        elif isinstance(result, dict):
                            result = {k: round(v, 2) if isinstance(v, float) else v 
                                    for k, v in result.items()}
                        
                        # Store result
                        results[metric['name']] = result
                        clean_name = metric['name'].lower().replace(' ', '_')
                        execution_namespace[clean_name] = result
                        
                        print(f"Successfully calculated {metric['name']}: {result}")

                except Exception as e:
                    print(f"Error calculating metric {metric['name']}: {str(e)}")
                    results[metric['name']] = f"Error: {str(e)}"
            
            return results
            
        except Exception as e:
            print(f"Error executing analysis plan: {e}")
            return {}

    def _check_and_convert_large_result(self, result: Any, df: pd.DataFrame) -> Tuple[bool, Any]:
        """Check if result is too large and convert to percentile analysis if needed"""
        TOKEN_LIMIT = 1000  # Approximate threshold for when to switch to percentiles
        
        try:
            # Check result size
            if isinstance(result, pd.Series):
                if len(result) > TOKEN_LIMIT:
                    # Get the entity column (index name or fallback)
                    entity_col = result.index.name or 'Entity'
                    return True, self._analyze_series_by_percentiles(result, df, entity_col)
            elif isinstance(result, pd.DataFrame):
                if len(result) > TOKEN_LIMIT:
                    # Get the entity column and value column
                    entity_col = result.index.name or 'Entity'
                    value_col = result.columns[-1]
                    return True, self._analyze_series_by_percentiles(result[value_col], df, entity_col)
            
            return False, result
        except Exception as e:
            print(f"Error in size check: {e}")
            return False, result

    def _analyze_series_by_percentiles(self, series: pd.Series, df: pd.DataFrame, 
                                    entity_col: str) -> Dict:
        """Analyze a series using percentile ranges"""
        percentile_ranges = [(0,1), (1,5), (5,10), (10,25), (25,50), (50,100)]
        results = {}
        
        for start, end in percentile_ranges:
            try:
                # Get values in this percentile range
                lower = np.percentile(series, start)
                upper = np.percentile(series, end)
                mask = (series > lower) & (series <= upper)
                range_data = series[mask]
                
                if len(range_data) == 0:
                    continue
                
                # Get entities in this range
                entities = range_data.index
                if entity_col in df.columns:
                    entities_df = df[df[entity_col].isin(entities)]
                else:
                    entities_df = df.loc[df.index.isin(entities)]
                
                # Calculate range stats
                range_name = f"top_{end}%" if start == 0 else f"{start}%_to_{end}%"
                results[range_name] = {
                    "metric_stats": {
                        "min": float(range_data.min()),
                        "max": float(range_data.max()),
                        "mean": float(range_data.mean()),
                        "median": float(range_data.median())
                    },
                    "sample_size": int(len(range_data)),
                    "characteristics": self._get_range_characteristics(entities_df)
                }
            except Exception as e:
                print(f"Error analyzing range {start}-{end}: {e}")
                continue
        
        return results

    def _get_range_characteristics(self, df: pd.DataFrame) -> Dict:
        """Get key characteristics of entities in a range"""
        chars = {}
        
        # Define key columns we care about (in order of importance)
        key_categorical_cols = [
            'ACCOUNT_PLAN', 
            'WIDGET_PUBLISHMETHOD',
            'WIDGET_MEDIA_TYPES'
        ]
        
        key_numeric_cols = [
            'WIDGET_NUMBER_OF_VIDEOS',
            'WIDGET_CLICKS',
            'WIDGET_VIEWS'
        ]
        
        # Process categorical columns
        for col in key_categorical_cols:
            if col in df.columns and df[col].dtype in ['object', 'category']:
                value_counts = df[col].value_counts(normalize=True)
                if not value_counts.empty:
                    # Only take top 2 values and round frequencies
                    chars[col] = {
                        'top_values': [
                            {'value': str(k), 'freq': round(float(v), 2)}
                            for k, v in value_counts.head(2).items()
                        ]
                    }
        
        # Process numeric columns
        for col in key_numeric_cols:
            if col in df.columns and df[col].dtype in ['int64', 'float64']:
                chars[col] = {
                    'avg': round(float(df[col].mean()), 1),
                    'med': round(float(df[col].median()), 1)
                }
        
        return chars

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