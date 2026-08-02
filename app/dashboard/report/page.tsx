'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Download, Printer, Share2, Loader2, AlertCircle } from 'lucide-react'
import { useAnalysis } from '@/hooks/useAnalysis'
import type { ReadinessReport } from '@/types/analysis'

export default function ReportPage() {
  const params = useParams()
  const applicationId = params.applicationId as string
  const reportRef = useRef<HTMLDivElement>(null)
  const [isPrinting, setIsPrinting] = useState(false)

  const { report, isLoading, error, refresh } = useAnalysis(applicationId)

  const handlePrint = () => {
    setIsPrinting(true)
    window.print()
    setIsPrinting(false)
  }

  const handleDownloadPDF = () => {
    // Mock PDF download - in real app, would use a library like jsPDF
    alert('PDF download initiated. In a real app, this would generate and download a PDF file.')
  }

  const reportDate = new Date().toLocaleDateString()
  const readinessScore = report?.overall_readiness.readiness_score ?? 0

  if (isLoading) {
    return (
      <>
        <Navigation />
        <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-8 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto flex items-center justify-center">
            <div className="text-center space-y-4">
              <Loader2 size={48} className="animate-spin text-secondary mx-auto" />
              <p className="text-muted-foreground">Loading report...</p>
            </div>
          </div>
        </div>
      </>
    )
  }

  if (error || !report) {
    return (
      <>
        <Navigation />
        <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-8 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto">
            <div className="premium-card p-8 text-center space-y-4">
              <AlertCircle size={48} className="text-red-400 mx-auto" />
              <h2 className="text-2xl font-bold text-foreground">Report Not Available</h2>
              <p className="text-muted-foreground">{error || 'No analysis report found for this application.'}</p>
              {error && (
                <button
                  onClick={refresh}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-secondary/40 text-foreground hover:bg-secondary/10 transition"
                >
                  <Loader2 size={18} className="animate-spin" />
                  Retry
                </button>
              )}
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-secondary/40 text-foreground hover:bg-secondary/10 transition"
              >
                ← Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Header with Actions */}
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-foreground">Application Report</h1>
            <div className="flex gap-3">
              <button
                onClick={handleDownloadPDF}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-secondary/40 text-foreground hover:bg-secondary/10 transition"
              >
                <Download size={18} />
                <span className="hidden sm:inline">PDF</span>
              </button>
              <button
                onClick={handlePrint}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-secondary/40 text-foreground hover:bg-secondary/10 transition"
              >
                <Printer size={18} />
                <span className="hidden sm:inline">Print</span>
              </button>
              <Link
                href="/dashboard"
                className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition"
              >
                ← Back
              </Link>
            </div>
          </div>

          {/* Report Content */}
          <div ref={reportRef} className="glassmorphism rounded-xl border border-secondary/20 print:border-0 print:rounded-0 print:bg-white print:text-black p-8 sm:p-12 space-y-8">
            {/* Title Page */}
            <div className="text-center border-b border-secondary/20 pb-8">
              <h1 className="text-4xl font-bold mb-2">ApplyWise</h1>
              <p className="text-xl text-muted-foreground">Application Analysis Report</p>
              <p className="text-sm text-muted-foreground mt-4">Report Generated: {reportDate}</p>
            </div>

            {/* Executive Summary - Display at top of report */}
            <section className="space-y-4 p-6 rounded-lg bg-secondary/5 border border-secondary/20">
              <h2 className="text-2xl font-bold text-foreground">Executive Summary</h2>
              <div className="space-y-3">
                <p className="text-foreground leading-relaxed">
                  {report.executive_summary || 'This comprehensive report analyzes your application readiness and provides detailed insights into your submission status.'}
                </p>
                <p className="text-foreground leading-relaxed">
                  Based on our analysis, your application is {readinessScore}% complete.
                </p>
              </div>
            </section>

            {/* Applicant Information */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold text-foreground">Applicant Information</h2>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Full Name</p>
                  <p className="font-semibold text-foreground">{report.applicant_profile_summary.personal_information.full_name || '—'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Nationality</p>
                  <p className="font-semibold text-foreground">{report.applicant_profile_summary.personal_information.nationality || '—'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">University</p>
                  <p className="font-semibold text-foreground">{report.applicant_profile_summary.academic_information.university || '—'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Degree</p>
                  <p className="font-semibold text-foreground">{report.applicant_profile_summary.academic_information.degree || '—'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Major</p>
                  <p className="font-semibold text-foreground">{report.applicant_profile_summary.academic_information.major || '—'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">GPA</p>
                  <p className="font-semibold text-foreground">{report.applicant_profile_summary.academic_information.gpa || '—'}</p>
                </div>
              </div>
            </section>

            {/* Readiness Score */}
            <section className="space-y-4 p-6 rounded-lg bg-secondary/5 border border-secondary/20">
              <h2 className="text-xl font-bold text-foreground">Readiness Assessment</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-foreground">Overall Readiness Score</span>
                    <span className="text-3xl font-bold text-secondary">{readinessScore}%</span>
                  </div>
                  <div className="w-full h-3 bg-secondary/20 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary to-secondary transition-all"
                      style={{ width: `${readinessScore}%` }}
                    ></div>
                  </div>
                </div>
                <p className="text-sm text-foreground">
                  Your application is nearly complete. Focus on submitting the remaining documents to achieve a higher readiness score.
                </p>
              </div>
            </section>

            {/* Document Status */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold text-foreground">Document Status</h2>

              <div>
                <h3 className="text-lg font-semibold text-foreground mb-3">Uploaded Documents</h3>
                <ul className="space-y-2">
                  {report.document_assessment.filter(doc => doc.uploaded).map((doc, idx) => (
                    <li key={idx} className="flex items-center gap-3">
                      <span className="w-2 h-2 rounded-full bg-secondary"></span>
                      <span className="text-foreground">{doc.document_name || doc.name}</span>
                      <span className="ml-auto text-sm text-muted-foreground">✓ Submitted</span>
                    </li>
                  ))}
                  {report.document_assessment.filter(doc => doc.uploaded).length === 0 && (
                    <li className="text-sm text-muted-foreground">No documents uploaded</li>
                  )}
                </ul>
              </div>

              {report.missing_documents.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-3">Missing Documents (Priority Order)</h3>
                  <ul className="space-y-2">
                    {report.missing_documents.map((doc, idx) => (
                      <li key={idx} className="flex items-center gap-3">
                        <span className={`w-2 h-2 rounded-full ${doc.priority === 'high' ? 'bg-red-500' : doc.priority === 'medium' ? 'bg-yellow-500' : 'bg-gray-500'}`}></span>
                        <span className="text-foreground">{doc.name}</span>
                        <span className={`ml-auto text-sm font-semibold ${doc.priority === 'high' ? 'text-red-500' : doc.priority === 'medium' ? 'text-yellow-500' : 'text-gray-500'}`}>
                          {doc.priority.toUpperCase()}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>

            {/* Missing Requirements - Separate section */}
            {report.missing_requirements.length > 0 && (
              <section className="space-y-4">
                <h2 className="text-2xl font-bold text-foreground">Missing Requirements</h2>
                <ul className="space-y-2">
                  {report.missing_requirements.map((req, idx) => (
                    <li key={idx} className="flex items-center justify-between gap-3 p-3 rounded-lg bg-accent/5 border border-accent/20">
                      <div className="flex-1">
                        <span className="text-foreground">{String(req.name || 'Unknown requirement')}</span>
                        {req.category && (
                          <span className="text-xs text-muted-foreground ml-2">({String(req.category)})</span>
                        )}
                      </div>
                      <span className={`text-xs font-semibold px-3 py-1 rounded-full ${
                        req.priority === 'high' ? 'bg-red-500/20 text-red-400' : req.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-gray-500/20 text-gray-400'
                      }`}>
                        {String(req.priority || 'medium').toUpperCase()}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Timeline */}
            {report.timeline.length > 0 && (
              <section className="space-y-4">
                <h2 className="text-2xl font-bold text-foreground">Important Dates</h2>
                <ul className="space-y-4">
                  {report.timeline.map((entry, idx) => (
                    <li key={idx} className="flex gap-4">
                      <div className="w-24 text-sm font-semibold text-secondary">{entry.date}</div>
                      <div className="flex-1">
                        <p className="font-semibold text-foreground">{entry.event}</p>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          entry.priority === 'high' ? 'bg-red-500/20 text-red-400' : entry.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-gray-500/20 text-gray-400'
                        }`}>
                          {entry.priority}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Recommendations */}
            {report.recommendations.length > 0 && (
              <section className="space-y-4 p-6 rounded-lg bg-accent/5 border border-accent/20">
                <h2 className="text-2xl font-bold text-foreground">Recommendations</h2>
                <ol className="space-y-3 list-decimal list-inside">
                  {report.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-foreground">
                      {rec}
                    </li>
                  ))}
                </ol>
              </section>
            )}

            {/* Final Verdict */}
            <section className="space-y-4 p-6 rounded-lg bg-secondary/5 border border-secondary/20">
              <h2 className="text-2xl font-bold text-foreground">Final Verdict</h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Summary</p>
                  <p className="text-foreground leading-relaxed">{report.final_verdict.summary}</p>
                </div>
                <div className="flex flex-wrap items-center gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Recommendation</p>
                    <span className="px-3 py-1.5 rounded-lg text-sm font-semibold bg-secondary/20 text-secondary">
                      {report.final_verdict.recommendation}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Confidence</p>
                    <span className="text-xs text-muted-foreground">{report.final_verdict.confidence}</span>
                  </div>
                </div>
              </div>
            </section>

            {/* Footer */}
            <div className="border-t border-secondary/20 pt-8 text-center text-sm text-muted-foreground">
              <p>This report was generated by ApplyWise AI Analysis System</p>
              <p className="mt-2">For questions or additional support, visit our AI Chat Assistant</p>
            </div>
          </div>

          {/* Print-specific styles */}
          <style>{`
            @media print {
              body {
                background: white;
              }
              .print\\:border-0 {
                border: none !important;
              }
              .print\\:rounded-0 {
                border-radius: 0 !important;
              }
              .print\\:bg-white {
                background-color: white !important;
              }
              .print\\:text-black {
                color: black !important;
              }
            }
          `}</style>
        </div>
      </div>
    </>
  )
}
