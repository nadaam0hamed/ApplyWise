import { NextRequest, NextResponse } from 'next/server'

type AnalyzeErrorResponse = {
  error?: string;
  detail?: string | string[];
};

function getErrorMessage(error: AnalyzeErrorResponse): string {
  if (error.detail) {
    if (Array.isArray(error.detail)) {
      return error.detail.map((d) => {
        if (typeof d === 'string') return d;
        if (typeof d === 'object' && d !== null && 'msg' in d) {
          return String((d as { msg?: string }).msg);
        }
        return 'Unknown error';
      }).join(', ');
    }
    return error.detail;
  }
  return error.error || 'Analysis request failed';
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { applicationId } = body

    if (!applicationId) {
      return NextResponse.json(
        { error: 'Application ID is required' },
        { status: 400 }
      )
    }

    // Proxy to backend
    const backendUrl = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'
    
    console.log(`Attempting to connect to backend at: ${backendUrl}/api/analyze/${applicationId}`);
    
    const backendResponse = await fetch(`${backendUrl}/api/analyze/${applicationId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(900000), // 15 minutes timeout for analysis
    })

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({})) as AnalyzeErrorResponse
      const errorMessage = getErrorMessage(errorData)
      
      console.error(`Backend error (${backendResponse.status}):`, errorMessage);
      
      switch (backendResponse.status) {
        case 400:
          return NextResponse.json(
            { error: `Invalid request: ${errorMessage}` },
            { status: 400 }
          )
        case 404:
          return NextResponse.json(
            { error: `Application not found: ${applicationId}` },
            { status: 404 }
          )
        case 422:
          return NextResponse.json(
            { error: `Validation error: ${errorMessage}` },
            { status: 422 }
          )
        case 500:
          return NextResponse.json(
            { error: `Backend analysis error: ${errorMessage}` },
            { status: 500 }
          )
        default:
          return NextResponse.json(
            { error: errorMessage || 'Backend analysis failed' },
            { status: backendResponse.status }
          )
      }
    }

    const data = await backendResponse.json()
    console.log('Backend analysis completed successfully');
    return NextResponse.json(data)
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Analysis request failed'
    console.error('Analysis request error:', errorMessage);
    
    if (error instanceof Error) {
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        return NextResponse.json(
          { error: 'Analysis request timed out. The backend is loading AI models for the first time. This can take up to 10 minutes. Please try again in a few minutes.' },
          { status: 504 }
        )
      }
      if (errorMessage.includes('fetch') || errorMessage.includes('network') || errorMessage.includes('ECONNREFUSED')) {
        const backendUrl = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';
        return NextResponse.json(
          { error: `Failed to connect to backend at ${backendUrl}. Please ensure the backend server is running on port 8000.` },
          { status: 503 }
        )
      }
    }
    
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    )
  }
}
