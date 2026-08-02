from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AnalyzeResponse
from app.services.analysis_service import AnalysisService
from app.services.exceptions import AnalysisServiceError, ApplicationNotFoundError

router = APIRouter()


@router.post("/analyze/{application_id}", response_model=AnalyzeResponse)
def analyze_application(application_id: str) -> AnalyzeResponse:
    try:
        return AnalysisService.run_analysis(application_id)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AnalysisServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
