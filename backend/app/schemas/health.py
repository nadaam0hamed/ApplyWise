from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    version: str = Field(..., examples=["0.1.0"])
    environment: str = Field(..., examples=["development"])


class RootResponse(BaseModel):
    message: str = Field(..., examples=["ApplyWise API"])
    docs_url: str = Field(..., examples=["/docs"])
    health_url: str = Field(..., examples=["/health"])
