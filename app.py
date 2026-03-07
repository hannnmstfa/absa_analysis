from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from engine import run_analysis_from_csv_url

app = FastAPI(title="ABSA Analysis API")

class AnalyzeRequest(BaseModel):
    sheet_csv_url: str = Field(..., min_length=20, max_length=500)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    sheet_csv_url = req.sheet_csv_url.strip()
    if not sheet_csv_url:
        raise HTTPException(status_code=422, detail="sheet_csv_url tidak boleh kosong")
    if "docs.google.com/spreadsheets" not in sheet_csv_url:
        raise HTTPException(
            status_code=422,
            detail="URL harus berasal dari Google Sheets (docs.google.com/spreadsheets)",
        )

    try:
        return run_analysis_from_csv_url(sheet_csv_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan internal saat memproses analisis",
        ) from exc
