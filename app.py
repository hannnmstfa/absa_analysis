from fastapi import FastAPI
from pydantic import BaseModel
from engine import run_analysis_from_csv_url

app = FastAPI(title="ABSA Analysis API")

class AnalyzeRequest(BaseModel):
    sheet_csv_url: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return run_analysis_from_csv_url(req.sheet_csv_url)
