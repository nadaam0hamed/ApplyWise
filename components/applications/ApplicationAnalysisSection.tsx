'use client';

import {
  AlertCircle,
  ArrowRight,
  Award,
  Calendar,
  FileText,
  GraduationCap,
  Lightbulb,
  Loader2,
  RefreshCw,
  Sparkles,
  User,
  XCircle,
} from 'lucide-react';

import { useAnalysis } from '@/hooks/useAnalysis';
import type {
  ApplicantProfileSummary,
  DocumentAssessmentEntry,
  EligibilityComparisonRow,
  FinalVerdict,
  ReadinessReport,
  ReadinessStatus,
  ReportTimelineEntry,
} from '@/types/analysis';

type ApplicationAnalysisSectionProps = {
  applicationId: string;
  onAnalysisComplete?: () => void;
};

const READINESS_STATUS_STYLES: Record<ReadinessStatus, string> = {
  Ready: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  'Moderate Readiness': 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  'Needs Improvement': 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  'Not Ready': 'bg-red-500/20 text-red-300 border-red-500/30',
};

const PRIORITY_STYLES = {
  high: 'bg-red-500/20 text-red-300',
  medium: 'bg-amber-500/20 text-amber-300',
  low: 'bg-muted/50 text-muted-foreground',
};

const MATCH_STATUS_STYLES: Record<string, string> = {
  PASS: 'bg-emerald-500/20 text-emerald-300',
  FAIL: 'bg-red-500/20 text-red-300',
  PARTIAL: 'bg-amber-500/20 text-amber-300',
  UNKNOWN: 'bg-muted/50 text-muted-foreground',
  'NOT VERIFIED': 'bg-muted/50 text-muted-foreground',
};

function ScoreRing({ score }: { score: number }) {
  const circumference = 188.4;
  const offset = circumference * (1 - score / 100);

  return (
    <div className="relative w-24 h-24">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="5" className="text-muted/30" />
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="url(#analysisScoreGradient)"
          strokeWidth="5"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
        <defs>
          <linearGradient id="analysisScoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0F766E" />
            <stop offset="100%" stopColor="#14B8A6" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold text-foreground">{score}%</span>
      </div>
    </div>
  );
}

function SectionHeading({ icon: Icon, title }: { icon: typeof Sparkles; title: string }) {
  return (
    <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
      <Icon size={20} className="text-secondary" />
      {title}
    </h3>
  );
}

function ProfileField({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm text-foreground">{value || '—'}</p>
    </div>
  );
}

function ApplicantProfileSummarySection({ profile }: { profile: ApplicantProfileSummary }) {
  const { personal_information, academic_information, language_scores } = profile;

  return (
    <div className="premium-card p-6 space-y-6">
      <SectionHeading icon={User} title="Applicant Profile" />

      <div>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Personal Information
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <ProfileField label="Full Name" value={personal_information.full_name} />
          <ProfileField label="Nationality" value={personal_information.nationality} />
          <ProfileField label="Passport No." value={personal_information.passport_number} />
          <ProfileField label="Passport Expiry" value={personal_information.passport_expiry} />
        </div>
      </div>

      <div>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Academic Information
        </p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <ProfileField label="University" value={academic_information.university} />
          <ProfileField label="Degree" value={academic_information.degree} />
          <ProfileField label="Major" value={academic_information.major} />
          <ProfileField label="GPA" value={academic_information.gpa} />
          <ProfileField label="Graduation Year" value={academic_information.graduation_year} />
        </div>
      </div>

      <div>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Language Scores
        </p>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <ProfileField label="Test" value={language_scores.test_type} />
          <ProfileField label="Overall" value={language_scores.overall_score} />
          <ProfileField label="Reading" value={language_scores.reading} />
          <ProfileField label="Listening" value={language_scores.listening} />
          <ProfileField label="Writing" value={language_scores.writing} />
          <ProfileField label="Speaking" value={language_scores.speaking} />
        </div>
      </div>

      {profile.skills.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Skills</p>
          <div className="flex flex-wrap gap-2">
            {profile.skills.map((skill, idx) => (
              <span key={idx} className="px-2 py-1 rounded-full text-xs bg-secondary/20 text-secondary">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {profile.experience.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Experience</p>
          <ul className="space-y-1">
            {profile.experience.map((item, idx) => (
              <li key={idx} className="text-sm text-foreground flex items-start gap-2">
                <ArrowRight size={14} className="text-secondary mt-0.5 flex-shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {profile.leadership.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Leadership</p>
          <ul className="space-y-1">
            {profile.leadership.map((item, idx) => (
              <li key={idx} className="text-sm text-foreground flex items-start gap-2">
                <Award size={14} className="text-amber-400 mt-0.5 flex-shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function EligibilityComparisonTable({ rows }: { rows: EligibilityComparisonRow[] }) {
  if (rows.length === 0) return null;

  return (
    <div className="premium-card p-6 space-y-4">
      <SectionHeading icon={GraduationCap} title="Eligibility Comparison" />
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border/50">
              <th className="text-left py-2 pr-4 text-xs text-muted-foreground font-semibold">Requirement</th>
              <th className="text-left py-2 pr-4 text-xs text-muted-foreground font-semibold">Required</th>
              <th className="text-left py-2 pr-4 text-xs text-muted-foreground font-semibold">Applicant</th>
              <th className="text-left py-2 pr-4 text-xs text-muted-foreground font-semibold">Status</th>
              <th className="text-left py-2 pr-4 text-xs text-muted-foreground font-semibold">Confidence</th>
              <th className="text-left py-2 text-xs text-muted-foreground font-semibold">Explanation</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx} className="border-b border-border/30">
                <td className="py-3 pr-4 font-medium text-foreground">{row.requirement_name}</td>
                <td className="py-3 pr-4 text-muted-foreground">{row.required_value ?? '—'}</td>
                <td className="py-3 pr-4 text-muted-foreground">{row.applicant_value ?? '—'}</td>
                <td className="py-3 pr-4">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      MATCH_STATUS_STYLES[row.status] ?? 'bg-muted/50 text-muted-foreground'
                    }`}
                  >
                    {row.status}
                  </span>
                </td>
                <td className="py-3 pr-4 text-muted-foreground">{Math.round(row.confidence * 100)}%</td>
                <td className="py-3 text-muted-foreground">{row.explanation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Suggested Actions */}
      {rows.some((row) => row.suggested_action) && (
        <div className="mt-4 space-y-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Suggested Actions</p>
          {rows
            .filter((row) => row.suggested_action)
            .map((row, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm text-foreground">
                <ArrowRight size={14} className="text-secondary mt-0.5 flex-shrink-0" />
                <span>
                  <span className="font-medium">{row.requirement_name}:</span> {row.suggested_action}
                </span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

function DocumentAssessmentSection({ assessments }: { assessments: DocumentAssessmentEntry[] }) {
  const items = assessments.length > 0 ? assessments : [];

  if (items.length === 0) return null;

  return (
    <div className="premium-card p-6 space-y-4">
      <SectionHeading icon={FileText} title="Document Assessment" />
      <div className="space-y-4">
        {items.map((doc, idx) => (
          <div key={idx} className="p-4 rounded-lg bg-muted/20 border border-border/50 space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <p className="font-medium text-foreground">{doc.document_name || doc.name}</p>
                {doc.document_type && (
                  <p className="text-xs text-muted-foreground mt-1">{doc.document_type}</p>
                )}
                <div className="flex flex-wrap gap-2 mt-2">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      doc.uploaded ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
                    }`}
                  >
                    {doc.uploaded ? 'Uploaded' : 'Missing'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-muted/50 text-muted-foreground">
                    {doc.completeness}
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-muted/50 text-muted-foreground">
                    Quality: {doc.quality}
                  </span>
                  {doc.quality_score !== undefined && doc.quality_score !== null && (
                    <span className="px-2 py-0.5 rounded text-xs bg-secondary/20 text-secondary">
                      Score: {doc.quality_score}%
                    </span>
                  )}
                  {doc.completeness_level && (
                    <span className="px-2 py-0.5 rounded text-xs bg-muted/50 text-muted-foreground">
                      Level: {doc.completeness_level}
                    </span>
                  )}
                  {doc.confidence !== undefined && doc.confidence !== null && (
                    <span className="px-2 py-0.5 rounded text-xs bg-muted/50 text-muted-foreground">
                      Confidence: {Math.round(doc.confidence * 100)}%
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Professional Evaluation Fields */}
            {doc.strengths.length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Strengths</p>
                <ul className="text-sm text-foreground space-y-1">
                  {doc.strengths.map((strength, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <Award size={12} className="text-emerald-400 mt-1 flex-shrink-0" />
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {doc.weaknesses.length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Weaknesses</p>
                <ul className="text-sm text-foreground space-y-1">
                  {doc.weaknesses.map((weakness, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <XCircle size={12} className="text-red-400 mt-1 flex-shrink-0" />
                      {weakness}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {doc.missing_information.length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Missing Information</p>
                <ul className="text-sm text-foreground space-y-1">
                  {doc.missing_information.map((info, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <XCircle size={12} className="text-red-400 mt-1 flex-shrink-0" />
                      {info}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {doc.suggestions.length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Suggestions</p>
                <ul className="text-sm text-foreground space-y-1">
                  {doc.suggestions.map((suggestion, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <Lightbulb size={12} className="text-amber-400 mt-1 flex-shrink-0" />
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {doc.extracted_information && Object.keys(doc.extracted_information).length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Extracted Information</p>
                <div className="text-sm text-foreground space-y-1">
                  {Object.entries(doc.extracted_information).map(([key, value]) => (
                    <div key={String(key)} className="flex items-start gap-2">
                      <span className="font-medium text-muted-foreground">{String(key)}:</span>
                      <span>{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function TimelineSection({ timeline }: { timeline: ReportTimelineEntry[] }) {
  if (timeline.length === 0) return null;

  const PRIORITY_COLORS: Record<string, string> = {
    high: 'bg-red-500/20 text-red-300',
    medium: 'bg-amber-500/20 text-amber-300',
    low: 'bg-muted/50 text-muted-foreground',
  };

  return (
    <div className="premium-card p-6 space-y-4">
      <SectionHeading icon={Calendar} title="Timeline" />
      <div className="space-y-3">
        {timeline.map((entry, idx) => (
          <div key={idx} className="flex items-start gap-4">
            <span className="text-xs text-muted-foreground font-mono w-24 flex-shrink-0 pt-0.5">
              {entry.date}
            </span>
            <div className="flex-1 pb-3 border-l-2 border-secondary/30 pl-4">
              <div className="flex items-center gap-2">
                <p className="text-sm text-foreground">{entry.event}</p>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-semibold ${
                    PRIORITY_COLORS[entry.priority] ?? PRIORITY_COLORS.medium
                  }`}
                >
                  {entry.priority}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FinalVerdictSection({ verdict }: { verdict: FinalVerdict }) {
  return (
    <div className="premium-card p-6 space-y-4 border border-secondary/30">
      <SectionHeading icon={Award} title="Final Verdict" />
      <div className="space-y-3">
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Summary</p>
          <p className="text-sm text-foreground leading-relaxed">{verdict.summary}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Recommendation</p>
            <span className="px-3 py-1.5 rounded-lg text-sm font-semibold bg-secondary/20 text-secondary">
              {verdict.recommendation}
            </span>
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Confidence</p>
            <span className="text-xs text-muted-foreground">{verdict.confidence}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AnalysisResults({ report }: { report: ReadinessReport }) {
  const { overall_readiness } = report;
  const readinessStatus = overall_readiness.status as ReadinessStatus;

  return (
    <div className="space-y-6">
      {/* Overall Readiness */}
      <div className="premium-card p-6 space-y-4">
        <SectionHeading icon={Sparkles} title="Overall Readiness" />
        <div className="flex flex-col items-center text-center gap-3">
          <ScoreRing score={overall_readiness.readiness_score} />
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold border ${
              READINESS_STATUS_STYLES[readinessStatus] ?? 'bg-muted/50 text-muted-foreground border-border/50'
            }`}
          >
            {overall_readiness.status}
          </span>
        </div>
      </div>

      {/* Executive Summary - Display at top of report */}
      {report.executive_summary && (
        <div className="premium-card p-6 space-y-4 border border-secondary/30">
          <SectionHeading icon={Sparkles} title="Executive Summary" />
          <p className="text-sm text-foreground leading-relaxed">{report.executive_summary}</p>
        </div>
      )}

      {/* Applicant Profile */}
      <ApplicantProfileSummarySection profile={report.applicant_profile_summary} />

      {/* Eligibility Comparison */}
      <EligibilityComparisonTable rows={report.eligibility_comparison} />

      {/* Document Assessment */}
      <DocumentAssessmentSection assessments={report.document_assessment} />

      {/* Missing Documents */}
      {report.missing_documents.length > 0 && (
        <div className="premium-card p-6 space-y-4">
          <SectionHeading icon={AlertCircle} title="Missing Documents" />
          <div className="space-y-2">
            {report.missing_documents.map((doc, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between gap-3 p-3 rounded-lg bg-muted/20"
              >
                <span className="text-sm text-foreground">{doc.name}</span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-semibold ${
                    PRIORITY_STYLES[doc.priority] ?? PRIORITY_STYLES.medium
                  }`}
                >
                  {doc.priority}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing Requirements */}
      {report.missing_requirements && report.missing_requirements.length > 0 && (
        <div className="premium-card p-6 space-y-4">
          <SectionHeading icon={AlertCircle} title="Missing Requirements" />
          <div className="space-y-2">
            {report.missing_requirements.map((req, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between gap-3 p-3 rounded-lg bg-muted/20"
              >
                <div className="flex-1">
                  <span className="text-sm text-foreground">{String(req.name || 'Unknown requirement')}</span>
                  {req.category && (
                    <span className="text-xs text-muted-foreground ml-2">({String(req.category)})</span>
                  )}
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-semibold ${
                    PRIORITY_STYLES[String(req.priority) as keyof typeof PRIORITY_STYLES] ?? PRIORITY_STYLES.medium
                  }`}
                >
                  {String(req.priority || 'medium')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {report.recommendations.length > 0 && (
        <div className="premium-card p-6 space-y-4">
          <SectionHeading icon={Lightbulb} title="Recommendations" />
          <ul className="space-y-2">
            {report.recommendations.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-foreground">
                <ArrowRight size={14} className="text-secondary mt-1 flex-shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Timeline */}
      <TimelineSection timeline={report.timeline} />

      {/* Final Verdict */}
      <FinalVerdictSection verdict={report.final_verdict} />
    </div>
  );
}

export function ApplicationAnalysisSection({
  applicationId,
  onAnalysisComplete,
}: ApplicationAnalysisSectionProps) {
  const {
    report,
    isLoading,
    isAnalyzing,
    error,
    hasCompletedAnalysis,
    runAnalysis,
    refresh,
  } = useAnalysis(applicationId);

  const handleAnalyze = async (force = false) => {
    try {
      await runAnalysis(force);
      onAnalysisComplete?.();
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Sparkles size={24} className="text-secondary" />
            AI Readiness Report
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Professional assessment of your application readiness
          </p>
        </div>

        <button
          type="button"
          onClick={() => handleAnalyze(true)}
          disabled={isAnalyzing || isLoading}
          className="inline-flex items-center gap-2 px-5 py-2.5 btn-gradient-primary text-background rounded-lg font-semibold text-sm disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isAnalyzing ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Analyzing…
            </>
          ) : hasCompletedAnalysis ? (
            <>
              <RefreshCw size={16} />
              Re-run Analysis
            </>
          ) : (
            <>
              <Sparkles size={16} />
              Generate Report
            </>
          )}
        </button>
      </div>

      {isLoading && (
        <div className="premium-card p-8 flex items-center justify-center gap-3">
          <Loader2 size={24} className="animate-spin text-secondary" />
          <span className="text-muted-foreground">Loading analysis…</span>
        </div>
      )}

      {!isLoading && error && (
        <div className="premium-card p-4 border border-red-500/30 bg-red-500/10 flex items-start gap-3">
          <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium text-foreground">Analysis failed</p>
            <p className="text-sm text-muted-foreground mt-1">{error}</p>
            <button
              onClick={refresh}
              className="mt-2 text-sm text-secondary hover:underline flex items-center gap-1"
            >
              <RefreshCw size={14} />
              Retry
            </button>
          </div>
        </div>
      )}

      {!isLoading && isAnalyzing && (
        <div className="premium-card p-8 flex flex-col items-center justify-center gap-4 text-center">
          <Loader2 size={40} className="animate-spin text-secondary" />
          <div>
            <p className="font-semibold text-foreground">Generating AI Readiness Report…</p>
            <p className="text-sm text-muted-foreground mt-1">
              Reviewing documents, eligibility criteria, and scholarship requirements
            </p>
          </div>
        </div>
      )}

      {!isLoading && !isAnalyzing && hasCompletedAnalysis && report && (
        <AnalysisResults report={report} />
      )}

      {!isLoading && !isAnalyzing && !hasCompletedAnalysis && !error && (
        <div className="premium-card p-8 text-center space-y-3">
          <Sparkles size={32} className="mx-auto text-secondary" />
          <p className="font-semibold text-foreground">No report yet</p>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            Click &ldquo;Generate Report&rdquo; to receive a professional AI Readiness Report with
            eligibility comparison, document assessment, and personalized recommendations.
          </p>
          <button
            onClick={() => handleAnalyze(true)}
            disabled={isAnalyzing || isLoading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-primary to-secondary text-background hover:shadow-lg hover:shadow-primary/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Generating Report…
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Generate Report
              </>
            )}
          </button>
        </div>
      )}
    </section>
  );
}
