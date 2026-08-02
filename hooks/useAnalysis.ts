'use client';

import { useCallback, useEffect, useState } from 'react';

import { AnalysisService } from '@/services/analysis.service';
import type { Analysis, AnalysisResult, ReadinessReport } from '@/types/analysis';

type AnalysisApiResponse = {
  success?: boolean;
  error?: string;
  detail?: string | string[];
};

function getErrorMessage(error: AnalysisApiResponse): string {
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
  return error.error || 'An unexpected error occurred';
}

export function useAnalysis(applicationId: string) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [report, setReport] = useState<ReadinessReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const applyAnalysis = useCallback((existing: Analysis | null) => {
    setAnalysis(existing);

    if (existing?.readiness_score != null) {
      const mapped = AnalysisService.analysisToResult(existing);
      setResult(mapped);
      setReport(mapped.readiness_report);
    } else {
      setResult(null);
      setReport(null);
    }
  }, []);

  const loadExisting = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const existing = await AnalysisService.getLatestForApplication(applicationId);
      applyAnalysis(existing);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load analysis';
      setError(message);
      setAnalysis(null);
      setResult(null);
      setReport(null);
    } finally {
      setIsLoading(false);
    }
  }, [applicationId, applyAnalysis]);

  useEffect(() => {
    loadExisting();
  }, [loadExisting]);

  const runAnalysis = useCallback(
    async (force = false) => {
      // Always allow running analysis for new applications or when forced
      if (!force && report && result) return result;

      setIsAnalyzing(true);
      setError(null);

      try {
        const analysisResult = await AnalysisService.runAnalysis(applicationId);
        setResult(analysisResult);
        setReport(analysisResult.readiness_report);
        await loadExisting();
        return analysisResult;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Analysis failed';
        setError(message);
        throw err;
      } finally {
        setIsAnalyzing(false);
      }
    },
    [applicationId, loadExisting, report, result],
  );

  const hasCompletedAnalysis = report !== null;

  return {
    analysis,
    result,
    report,
    isLoading,
    isAnalyzing,
    error,
    hasCompletedAnalysis,
    runAnalysis,
    refresh: loadExisting,
  };
}
