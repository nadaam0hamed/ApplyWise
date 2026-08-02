/** FastAPI backend client for AI analysis. */

export interface BackendAnalyzeResponse {
  application_id: string;
  analysis_id: string;
  created_at: string;
  readiness_score: number;
  strengths: string[];
  weaknesses: string[];
  missing_documents: string[];
  recommendations: string[];
  next_steps: string[];
  report?: import('@/types/analysis').ReadinessReport | null;
}

export interface BackendError {
  detail?: string | Array<{ msg?: string; loc?: Array<string | number>; type?: string }>;
}

function getBackendUrl(): string {
  return process.env.NEXT_PUBLIC_FASTAPI_URL ?? 'http://localhost:8000';
}

function getBackendErrorMessage(error: BackendError): string {
  if (error.detail) {
    if (Array.isArray(error.detail)) {
      return error.detail.map((item) => {
        if (typeof item === 'string') return item;
        if (typeof item === 'object' && item !== null && 'msg' in item) {
          return String((item as { msg?: string }).msg);
        }
        return 'Unknown error';
      }).join(', ');
    }
    return error.detail;
  }
  return 'Analysis request failed';
}

export async function runBackendAnalysis(
  applicationId: string,
): Promise<BackendAnalyzeResponse> {
  const backendUrl = getBackendUrl();
  
  try {
    const response = await fetch(`${backendUrl}/api/analyze/${applicationId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(900000), // 15 minutes timeout for analysis
    });

    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as BackendError;
      const detail = getBackendErrorMessage(body);
      
      switch (response.status) {
        case 400:
          throw new Error(`Invalid request: ${detail}`);
        case 404:
          throw new Error(`Application not found: ${applicationId}`);
        case 422:
          throw new Error(`Validation error: ${detail}`);
        case 500:
          throw new Error(`Backend analysis error: ${detail}`);
        default:
          throw new Error(detail || `Analysis failed (${response.status})`);
      }
    }

    return response.json() as Promise<BackendAnalyzeResponse>;
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        throw new Error('Analysis request timed out. The backend is processing your documents with the new extraction system. This can take up to 15 minutes. Please try again in a few minutes.');
      }
      if (error.message.includes('fetch') || error.message.includes('network')) {
        throw new Error(`Failed to connect to backend at ${backendUrl}. Please ensure the backend server is running.`);
      }
      throw error;
    }
    throw new Error('Failed to connect to backend. Please ensure the backend server is running.');
  }
}
