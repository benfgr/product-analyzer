from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List
import os
from dotenv import load_dotenv
from app.modules.analyzer import AnalyticsEngine

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzer
analyzer = AnalyticsEngine()

@app.post("/analyze")
async def analyze_data(
    file: UploadFile = File(...),
    business_model: str = Form(...),
    value_proposition: str = Form(...),
    target_metrics: str = Form(...),
    revenue_drivers: str = Form(...)
):
    try:
        # Read CSV file
        df = pd.read_csv(file.file)
        
        # Clean column names by stripping whitespace
        df.columns = df.columns.str.strip()
        print("CSV columns after cleaning:", df.columns.tolist())
        
        # if 'week' not in df.columns:
        #     return {
        #         "success": False,
        #         "error": f"CSV must contain 'week' column. Found columns: {df.columns.tolist()}"
        #     }

        # Process the analysis
        result = analyzer.analyze_data(
            df=df,
            business_model=business_model,
            value_proposition=value_proposition,
            target_metrics=target_metrics.split(','),
            revenue_drivers=revenue_drivers.split(',')
        )
        
        return result
    
    except Exception as e:
        print(f"Detailed error in analyze_data: {str(e)}")
        return {
            "success": False,
            "error": f"Error processing data: {str(e)}"
        }
    

@app.post("/analyze-dynamic")
def analyze_data_dynamic(
    file: UploadFile = File(...),
    business_model: str = Form(...),
    value_proposition: str = Form(...),
):
    try:
        # Read CSV file
        df = pd.read_csv(file.file)
        
        # Clean column names by stripping whitespace
        df.columns = df.columns.str.strip()
        print("CSV columns after cleaning:", df.columns.tolist())
        
        # Process the analysis
        result = analyzer.analyze_data_dynamic(
            df=df,
            business_model=business_model,
            value_proposition=value_proposition
        )
        
        return result
    
    except Exception as e:
        print(f"Detailed error in analyze_data_dynamic: {str(e)}")
        return {
            "success": False,
            "error": f"Error processing data: {str(e)}"
        }