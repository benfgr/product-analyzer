from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List
import os
from dotenv import load_dotenv, find_dotenv
from app.modules.analyzer import AnalyticsEngine

# DEBUG: Enhanced environment variable loading
print("Looking for .env file...")
env_path = find_dotenv()
print(f"Found .env at: {env_path}")

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost:5173",
    "https://product-analyzer-frontend.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    business_goal: Optional[str] = Form(None),
    questions: Optional[str] = Form(None)
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
            value_proposition=value_proposition,
            business_goal=business_goal,
            questions=questions
        )
        
        return result
    
    except Exception as e:
        print(f"Detailed error in analyze_data_dynamic: {str(e)}")
        return {
            "success": False,
            "error": f"Error processing data: {str(e)}"
        }