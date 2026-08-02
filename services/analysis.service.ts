import { requireUserId } from '@/lib/auth-helpers';
import {
  AI_ANALYSIS_COLUMNS,
  APPLICATION_COLUMNS,
  TIMELINE_TASK_COLUMNS,
} from '@/lib/supabase-live-schema';
import { supabase } from '@/lib/supabase';
import {
  APPLICATION_DOCUMENT_SLOTS,
  DOCUMENT_TYPE_LABELS,
  DocumentType,
} from '@/constants/documentTypes';
import { RequirementCategory } from '@/constants/requirementCategories';
import { DocumentService } from '@/services/document.service';
import { RequirementService } from '@/services/requirement.service';
import { runBackendAnalysis } from '@/lib/backend-api';
import { clampScore } from '@/utils/scoreCalculator';
import type {
  Analysis,
  AnalysisDocumentEntry,
  AnalysisResult,
  ApplicantInfo,
  ApplicantProfileSummary,
  ChecklistEntry,
  DocumentAssessmentEntry,
  DocumentEvaluation,
  EligibilityComparisonRow,
  FinalVerdict,
  MissingDocumentEntry,
  MissingRequirementEntry,
  ProfileStrength,
  ReadinessReport,
  ReadinessStatus,
  StoredRecommendations,
} from '@/types/analysis';
import type { Application } from '@/types/application';
import type { Document } from '@/types/document';
import type { Requirement } from '@/types/requirement';
import type { TimelineEventSummary, TimelineTask } from '@/types/timeline';

const KEY_DOCUMENT_TYPES: DocumentType[] = [
  DocumentType.Cv,
  DocumentType.AcademicTranscript,
  DocumentType.IeltsScore,
  DocumentType.ToeflScore,
];

async function assertApplicationOwnership(applicationId: string, userId: string): Promise<Application> {
  const { data: application, error } = await supabase
    .from('applications')
    .select(APPLICATION_COLUMNS)
    .eq('id', applicationId)
    .eq('user_id', userId)
    .single();

  if (error) throw new Error(error.message);
  return application as Application;
}

async function listTimelineTasks(applicationId: string): Promise<TimelineTask[]> {
  const { data, error } = await supabase
    .from('timeline_tasks')
    .select(TIMELINE_TASK_COLUMNS)
    .eq('application_id', applicationId)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);
  return (data ?? []) as TimelineTask[];
}

function buildStoredRecommendations(result: AnalysisResult): StoredRecommendations {
  return {
    summary: result.recommendations,
    improvement_suggestions: result.improvement_suggestions,
    recommended_next_steps: result.recommended_next_steps,
    missing_requirements: result.missing_requirements,
    document_evaluations: result.document_evaluations,
    uploaded_documents: result.uploaded_documents,
    checklist: result.checklist,
    timeline: result.timeline,
    applicant_info: result.applicant_info,
    profile_strength: result.profile_strength,
    scholarship_name: result.scholarship_name,
    eligibility_score: result.eligibility_score,
  };
}

function deriveReadinessStatus(score: number): ReadinessStatus {
  if (score >= 80) return 'Ready';
  if (score >= 60) return 'Moderate Readiness';
  if (score >= 40) return 'Needs Improvement';
  return 'Not Ready';
}

function mapRequirementComparisons(
  comparisons: StoredRecommendations['requirement_comparisons'],
): EligibilityComparisonRow[] {
  if (!comparisons) return [];
  return comparisons.map((row) => ({
    requirement_name: row.field,
    required_value: row.requirement,
    applicant_value: row.applicant,
    status: row.status,
    confidence: 0.75, // Default confidence for legacy data
    explanation: row.reason,
    suggested_action: null,
    // Legacy aliases
    requirement: row.field,
    requirement_value: row.requirement,
    reason: row.reason,
  }));
}

function parseStoredRecommendations(
  recommendations: Analysis['recommendations'],
): StoredRecommendations | null {
  if (!recommendations) return null;
  if (Array.isArray(recommendations)) {
    return {
      summary: recommendations,
      improvement_suggestions: [],
      recommended_next_steps: [],
      missing_requirements: [],
      document_evaluations: [],
      uploaded_documents: [],
      checklist: [],
      timeline: [],
      applicant_info: {
        name: '',
        email: '',
        phone: '',
        target_program: '',
        target_university: '',
      },
      profile_strength: 'Needs Improvement',
      scholarship_name: null,
      eligibility_score: 0,
    };
  }

  return recommendations;
}

export const AnalysisService = {
  async getLatestForApplication(applicationId: string): Promise<Analysis | null> {
    const userId = await requireUserId();
    await assertApplicationOwnership(applicationId, userId);

    const { data, error } = await supabase
      .from('ai_analysis')
      .select(AI_ANALYSIS_COLUMNS)
      .eq('application_id', applicationId)
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (error) throw new Error(error.message);
    return data as Analysis | null;
  },

  async runAnalysis(applicationId: string): Promise<AnalysisResult> {
    const userId = await requireUserId();
    await assertApplicationOwnership(applicationId, userId);

    try {
      await runBackendAnalysis(applicationId);
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Backend analysis failed: ${error.message}`);
      }
      throw new Error('Backend analysis failed: Unknown error');
    }

    const existing = await this.getLatestForApplication(applicationId);
    if (existing) {
      return this.analysisToResult(existing);
    }

    throw new Error('Analysis completed but results could not be loaded');
  },

  analysisToResult(analysis: Analysis): AnalysisResult {
    const stored = parseStoredRecommendations(analysis.recommendations);
    const report = stored?.readiness_report ?? null;
    const score =
      report?.overall_readiness.readiness_score ??
      stored?.eligibility_score ??
      analysis.readiness_score ??
      0;

    if (report) {
      return {
        applicant_info: stored?.applicant_info ?? {
          name: '',
          email: '',
          phone: '',
          target_program: '',
          target_university: '',
        },
        uploaded_documents: stored?.uploaded_documents ?? [],
        missing_documents: report.missing_documents as unknown as MissingDocumentEntry[],
        missing_requirements: report.missing_requirements as unknown as MissingRequirementEntry[],
        checklist: stored?.checklist ?? [],
        timeline: report.timeline,
        eligibility_score: report.overall_readiness.readiness_score,
        profile_strength: stored?.profile_strength ?? deriveProfileStrength(score),
        readiness_status: report.overall_readiness.status as ReadinessStatus,
        strengths: report.strengths,
        weaknesses: report.weaknesses,
        improvement_suggestions: [],
        recommended_next_steps: [],
        scholarship_name: stored?.scholarship_name ?? null,
        document_evaluations: stored?.document_evaluations ?? [],
        eligibility_comparison: report.eligibility_comparison,
        applicant_profile_summary: report.applicant_profile_summary,
        document_assessment: report.document_assessment,
        final_verdict: report.final_verdict,
        readiness_report: report,
        readiness_score: report.overall_readiness.readiness_score,
        recommendations: report.recommendations,
      };
    }

    return {
      applicant_info: stored?.applicant_info ?? {
        name: '',
        email: '',
        phone: '',
        target_program: '',
        target_university: '',
      },
      uploaded_documents: stored?.uploaded_documents ?? [],
      missing_documents: analysis.missing_documents ?? [],
      missing_requirements: stored?.missing_requirements ?? [],
      checklist: stored?.checklist ?? [],
      timeline: stored?.timeline ?? [],
      eligibility_score: score,
      profile_strength: stored?.profile_strength ?? deriveProfileStrength(score),
      readiness_status: stored?.readiness_status ?? deriveReadinessStatus(score),
      strengths: analysis.strengths ?? [],
      weaknesses: analysis.weaknesses ?? [],
      improvement_suggestions: stored?.improvement_suggestions ?? [],
      recommended_next_steps: stored?.recommended_next_steps ?? [],
      scholarship_name: stored?.scholarship_name ?? null,
      document_evaluations: stored?.document_evaluations ?? [],
      eligibility_comparison: mapRequirementComparisons(stored?.requirement_comparisons),
      applicant_profile_summary: null,
      document_assessment: [],
      final_verdict: stored?.final_verdict ?? null,
      readiness_report: null,
      readiness_score: score,
      recommendations: stored?.summary ?? [],
    };
  },
};

function hasDocumentForTypes(documents: Document[], types: DocumentType[]): boolean {
  return documents.some((doc) => doc.document_type && types.includes(doc.document_type));
}

function findDocumentForSlot(documents: Document[], slotKey: string) {
  const slot = APPLICATION_DOCUMENT_SLOTS.find((s) => s.key === slotKey);
  if (!slot) return undefined;
  return documents.find(
    (doc) => doc.document_type && slot.documentTypes.includes(doc.document_type),
  );
}

function mapTimelineTasks(tasks: TimelineTask[]): TimelineEventSummary[] {
  return tasks.map((task, index) => ({
    date: task.due_date ?? task.created_at.split('T')[0],
    event: task.completed ? `Completed milestone ${index + 1}` : `Upcoming milestone ${index + 1}`,
  }));
}

export function buildAnalysisResult(
  application: Application,
  documents: Document[],
  requirements: Requirement[],
  timelineTasks: TimelineTask[],
  profile: { full_name: string | null; email: string } | null,
): AnalysisResult {
  const scholarshipName = application.title ?? 'Scholarship Application';

  const document_evaluations: DocumentEvaluation[] = APPLICATION_DOCUMENT_SLOTS.map((slot) => {
    const doc = documents.find(
      (d) => d.document_type && slot.documentTypes.includes(d.document_type),
    );
    return {
      name: slot.label,
      status: doc ? 'present' : 'missing',
      notes: doc
        ? `Uploaded on ${doc.uploaded_at.split('T')[0]}`
        : `${slot.label} has not been uploaded yet`,
    };
  });

  const uploaded_documents: AnalysisDocumentEntry[] = documents.map((d) => ({
    name: DOCUMENT_TYPE_LABELS[d.document_type ?? DocumentType.Other] ?? d.file_name,
    status: 'complete',
    date: d.uploaded_at.split('T')[0],
  }));

  const missingFromSlots: MissingDocumentEntry[] = APPLICATION_DOCUMENT_SLOTS.filter(
    (slot) => !findDocumentForSlot(documents, slot.key),
  ).map((slot) => ({
    name: slot.label,
    priority:
      slot.key === 'cv' || slot.key === 'transcript' || slot.key === 'language'
        ? ('high' as const)
        : ('medium' as const),
  }));

  const missing_documents = dedupeMissingDocuments(missingFromSlots);

  const missing_requirements: MissingRequirementEntry[] = requirements
    .filter((req) => !req.is_fulfilled)
    .map((req) => ({
      name: req.title ?? req.category,
      category: req.category,
      priority: req.is_required ? ('high' as const) : ('medium' as const),
    }));

  const checklist: ChecklistEntry[] =
    requirements.length > 0
      ? requirements.map((req) => ({
          item: req.title ?? req.category,
          completed: Boolean(req.is_fulfilled),
        }))
      : APPLICATION_DOCUMENT_SLOTS.map((slot) => ({
          item: slot.label,
          completed: Boolean(findDocumentForSlot(documents, slot.key)),
        }));

  const slotCompletion =
    APPLICATION_DOCUMENT_SLOTS.filter((slot) => findDocumentForSlot(documents, slot.key)).length /
    APPLICATION_DOCUMENT_SLOTS.length;

  const requirementCompletion =
    requirements.length > 0
      ? requirements.filter((req) => req.is_fulfilled).length / requirements.length
      : slotCompletion;

  const keyDocBonus =
    [DocumentType.Cv, DocumentType.AcademicTranscript].filter((type) =>
      hasDocumentForTypes(documents, [type]),
    ).length * 5;

  const languageBonus = hasDocumentForTypes(documents, [DocumentType.IeltsScore, DocumentType.ToeflScore])
    ? 5
    : 0;

  const missingRequirementPenalty = Math.min(missing_requirements.length * 6, 36);

  const eligibility_score = clampScore(
    Math.round(requirementCompletion * 70 + keyDocBonus + languageBonus - missingRequirementPenalty),
  );

  const profile_strength = deriveProfileStrength(eligibility_score);

  const strengths = buildStrengths(documents, application, eligibility_score);
  const weaknesses = buildWeaknesses(missing_documents, missing_requirements, documents);
  const improvement_suggestions = buildImprovementSuggestions(missing_documents, application);
  const recommended_next_steps = buildRecommendedNextSteps(
    missing_documents,
    missing_requirements,
    application,
    timelineTasks,
  );

  const recommendations = [
    ...improvement_suggestions.slice(0, 2),
    ...recommended_next_steps.slice(0, 2),
  ];

  const applicant_info: ApplicantInfo = {
    name: profile?.full_name ?? 'Applicant',
    email: profile?.email ?? '',
    phone: '',
    target_program: application.title ?? scholarshipName,
    target_university: application.country ?? '',
  };

  return {
    applicant_info,
    uploaded_documents,
    missing_documents,
    missing_requirements,
    checklist,
    timeline: mapTimelineTasks(timelineTasks),
    eligibility_score,
    profile_strength,
    readiness_status: deriveReadinessStatus(eligibility_score),
    strengths,
    weaknesses,
    improvement_suggestions,
    recommended_next_steps,
    scholarship_name: scholarshipName,
    document_evaluations,
    eligibility_comparison: [],
    applicant_profile_summary: null,
    document_assessment: [],
    final_verdict: null,
    readiness_report: null,
    readiness_score: eligibility_score,
    recommendations,
  };
}

function dedupeMissingDocuments(items: MissingDocumentEntry[]): MissingDocumentEntry[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    const key = item.name.toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function deriveProfileStrength(score: number): ProfileStrength {
  if (score >= 80) return 'Strong';
  if (score >= 50) return 'Moderate';
  return 'Needs Improvement';
}

function buildStrengths(
  documents: Document[],
  application: Application,
  score: number,
): string[] {
  const strengths: string[] = [];

  if (hasDocumentForTypes(documents, [DocumentType.Cv])) {
    strengths.push('CV/Resume is uploaded and ready for review');
  }
  if (hasDocumentForTypes(documents, [DocumentType.AcademicTranscript])) {
    strengths.push('Academic transcript provided — supports eligibility verification');
  }
  if (hasDocumentForTypes(documents, [DocumentType.IeltsScore, DocumentType.ToeflScore])) {
    strengths.push('English proficiency certificate on file');
  }
  if (documents.length >= 4) {
    strengths.push(`Strong document portfolio with ${documents.length} files uploaded`);
  }
  if (application.title && score >= 60) {
    strengths.push(`Good alignment with ${application.title} requirements`);
  }
  if (strengths.length === 0) {
    strengths.push('Application started — upload documents to build your profile strength');
  }

  return strengths;
}

function buildWeaknesses(
  missingDocuments: MissingDocumentEntry[],
  missingRequirements: MissingRequirementEntry[],
  documents: Document[],
): string[] {
  const weaknesses: string[] = [];

  if (!hasDocumentForTypes(documents, KEY_DOCUMENT_TYPES)) {
    weaknesses.push('Core documents (CV, transcript, or language certificate) are incomplete');
  }
  if (missingDocuments.some((d) => d.name.toLowerCase().includes('recommendation'))) {
    weaknesses.push('Recommendation letter(s) not yet uploaded');
  }
  if (
    missingDocuments.some(
      (d) => d.name.toLowerCase().includes('statement') || d.name.toLowerCase().includes('purpose'),
    )
  ) {
    weaknesses.push('Statement of Purpose / Motivation letter is missing');
  }
  if (missingRequirements.some((r) => r.category === RequirementCategory.Language)) {
    weaknesses.push('Language proficiency requirement not yet satisfied');
  }
  if (missingRequirements.some((r) => r.category === RequirementCategory.Academic)) {
    weaknesses.push('Academic requirements need attention');
  }
  if (weaknesses.length === 0 && missingDocuments.length > 0) {
    weaknesses.push(`${missingDocuments.length} document(s) still required`);
  }

  return weaknesses;
}

function buildImprovementSuggestions(
  missingDocuments: MissingDocumentEntry[],
  application: Application,
): string[] {
  const suggestions: string[] = [];

  if (missingDocuments.some((d) => d.name.toLowerCase().includes('cv'))) {
    suggestions.push('Update your CV to highlight academic achievements and relevant experience');
  }
  if (missingDocuments.some((d) => d.name.toLowerCase().includes('transcript'))) {
    suggestions.push('Request official academic transcripts from your institution');
  }
  if (
    missingDocuments.some(
      (d) =>
        d.name.toLowerCase().includes('ielts') ||
        d.name.toLowerCase().includes('toefl') ||
        d.name.toLowerCase().includes('language'),
    )
  ) {
    suggestions.push('Schedule or upload your IELTS/TOEFL score report');
  }
  if (
    missingDocuments.some(
      (d) => d.name.toLowerCase().includes('statement') || d.name.toLowerCase().includes('purpose'),
    )
  ) {
    suggestions.push(
      `Draft a compelling Statement of Purpose tailored to ${application.title ?? 'the scholarship'}`,
    );
  }
  if (missingDocuments.some((d) => d.name.toLowerCase().includes('recommendation'))) {
    suggestions.push('Reach out to professors or employers for recommendation letters early');
  }
  if (suggestions.length === 0) {
    suggestions.push('Review all uploaded documents for accuracy and completeness before submission');
  }

  return suggestions;
}

function buildRecommendedNextSteps(
  missingDocuments: MissingDocumentEntry[],
  missingRequirements: MissingRequirementEntry[],
  application: Application,
  timelineTasks: TimelineTask[],
): string[] {
  const steps: string[] = [];

  const highPriority = missingDocuments.filter((d) => d.priority === 'high');
  if (highPriority.length > 0) {
    steps.push(`Upload high-priority documents: ${highPriority.map((d) => d.name).join(', ')}`);
  }
  if (missingRequirements.length > 0) {
    steps.push(`Address ${missingRequirements.length} outstanding requirement(s) listed below`);
  }

  const nextDeadline = timelineTasks.find((task) => task.due_date && !task.completed)?.due_date;
  if (nextDeadline) {
    steps.push(`Submit complete application before deadline: ${nextDeadline}`);
  }

  steps.push('Run a final review of all documents before submission');

  if (application.source_url) {
    steps.push('Verify requirements on the official scholarship website');
  }

  return steps;
}

/** Context for chat responses derived from real application data. */
export interface ApplicationContext {
  readinessScore: number | null;
  programName: string | null;
  deadline: string | null;
  missingDocuments: string[];
  uploadedDocuments: string[];
  daysUntilDeadline: number | null;
  actualGPA: string | null;
  actualIELTS: string | null;
  actualStrengths: string[];
  actualWeaknesses: string[];
  applicantProfile: any;
}

export async function getApplicationContext(applicationId: string): Promise<ApplicationContext | null> {
  const userId = await requireUserId();

  const { data: application } = await supabase
    .from('applications')
    .select('id,user_id,title,readiness_score')
    .eq('id', applicationId)
    .eq('user_id', userId)
    .maybeSingle();

  if (!application) return null;

  const documents = await DocumentService.listByApplication(applicationId);
  const requirements = await RequirementService.listByApplication(applicationId);
  const timelineTasks = await listTimelineTasks(applicationId);

  const docReqs = requirements.filter((r) => r.category === RequirementCategory.Documents);
  const uploadedDocuments = documents.map((d) => d.file_name);
  const missingDocuments = docReqs
    .filter((r) => !r.is_fulfilled)
    .map((r) => r.title ?? r.category);

  const nextDeadline = timelineTasks.find((task) => task.due_date && !task.completed)?.due_date ?? null;
  const daysUntilDeadline = nextDeadline
    ? Math.ceil((new Date(nextDeadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : null;

  return {
    readinessScore: application.readiness_score,
    programName: application.title,
    deadline: nextDeadline,
    missingDocuments,
    uploadedDocuments,
    daysUntilDeadline,
    actualGPA: null,
    actualIELTS: null,
    actualStrengths: [],
    actualWeaknesses: [],
    applicantProfile: null,
  };
}

export function generateChatResponse(message: string, context: ApplicationContext | null): string {
  const lower = message.toLowerCase();

  if (!context) {
    return 'I don\'t have an active application yet. Start a new application from the dashboard to get personalized guidance.';
  }

  // Use actual data from analysis/report if available
  const {
    actualGPA,
    actualIELTS,
    actualStrengths,
    actualWeaknesses,
    applicantProfile,
    readinessScore,
    programName,
    missingDocuments,
    uploadedDocuments,
    daysUntilDeadline,
    deadline,
  } = context;

  // GPA-specific responses with actual data
  if (lower.includes('gpa') || lower.includes('grade') || lower.includes('score')) {
    if (actualGPA) {
      const gpaNum = parseFloat(actualGPA);
      if (gpaNum >= 3.5) {
        return `Your GPA is ${actualGPA}, which is excellent for most scholarship applications. This competitive score will strengthen your application significantly.`;
      } else if (gpaNum >= 3.0) {
        return `Your GPA is ${actualGPA}, which is good and meets the requirements for many scholarships. Continue building on your academic achievements to further strengthen your profile.`;
      } else if (gpaNum >= 2.5) {
        return `Your GPA is ${actualGPA}. While this meets minimum requirements for some programs, consider highlighting your other strengths like research experience, publications, or leadership roles to make your application more competitive.`;
      } else {
        return `Your GPA is ${actualGPA}. You may want to focus on improving your academic performance or highlight exceptional achievements in other areas like research, projects, or extracurricular activities to compensate.`;
      }
    }
    if (applicantProfile?.academic_information?.gpa) {
      return `Based on your profile, your GPA is ${applicantProfile.academic_information.gpa}. This is a key factor in scholarship evaluations. Make sure your transcript is uploaded for accurate assessment.`;
    }
    return 'I don\'t have your GPA information from your uploaded documents. Please upload your academic transcript so I can provide a specific assessment of your academic performance.';
  }

  // IELTS-specific responses
  if (lower.includes('ielts') || lower.includes('english') || lower.includes('toefl') || lower.includes('language')) {
    if (actualIELTS) {
      const ieltsNum = parseFloat(actualIELTS);
      if (ieltsNum >= 7.5) {
        return `Your IELTS score is ${actualIELTS}, which is excellent and meets the requirements for most competitive programs. This strong language proficiency will be a significant advantage.`;
      } else if (ieltsNum >= 6.5) {
        return `Your IELTS score is ${actualIELTS}, which is good and meets the requirements for many programs. This score demonstrates solid English language proficiency.`;
      } else if (ieltsNum >= 6.0) {
        return `Your IELTS score is ${actualIELTS}. This meets minimum requirements for some programs, but consider retaking the test to improve your score for more competitive applications.`;
      } else {
        return `Your IELTS score is ${actualIELTS}. I recommend focusing on improving your English language skills and retaking the test to achieve a higher score for better scholarship opportunities.`;
      }
    }
    if (applicantProfile?.language_scores?.overall_score) {
      return `Based on your profile, your language test score is ${applicantProfile.language_scores.overall_score}. This is important for demonstrating your English proficiency.`;
    }
    return 'I don\'t have your language test scores from your uploaded documents. Please upload your IELTS/TOEFL score report so I can provide a specific assessment.';
  }

  // Strengths and weaknesses
  if (lower.includes('strength') || lower.includes('good') || lower.includes('strong')) {
    if (actualStrengths.length > 0) {
      return `Based on your analysis, your key strengths include: ${actualStrengths.slice(0, 3).join(', ')}. These are competitive advantages that make your application stand out.`;
    }
    return 'Based on your uploaded documents, I can provide specific feedback on your strengths. Upload your application documents for a detailed analysis.';
  }

  if (lower.includes('weakness') || lower.includes('bad') || lower.includes('improve')) {
    if (actualWeaknesses.length > 0) {
      return `Based on your analysis, areas for improvement include: ${actualWeaknesses.slice(0, 3).join(', ')}. Working on these will strengthen your application significantly.`;
    }
    return 'Based on your uploaded documents, I can provide specific feedback on areas needing improvement. Upload your application documents for a detailed analysis.';
  }

  // Document responses
  if (lower.includes('document') || lower.includes('missing')) {
    if (missingDocuments.length === 0) {
      return `You have uploaded ${uploadedDocuments.length} document(s) and no required documents appear to be missing. Great progress!`;
    }
    return `Based on your application, you still need: ${missingDocuments.join(', ')}. I recommend prioritizing these documents${daysUntilDeadline && daysUntilDeadline <= 14 ? ' as your deadline is approaching' : ''}.`;
  }

  // SOP responses
  if (lower.includes('sop') || lower.includes('statement') || lower.includes('motivation')) {
    return `Your Statement of Purpose should address your academic background, why ${programName ?? 'this program'}, your career goals, and how the program helps you achieve them. Focus on your unique strengths and academic achievements.`;
  }

  // Deadline responses
  if (lower.includes('deadline') || lower.includes('when')) {
    if (!deadline) {
      return 'No deadline is set for your current application yet. You can add one when creating or editing your application.';
    }
    const days = daysUntilDeadline ?? 0;
    if (days <= 0) {
      return `Your application deadline was ${new Date(deadline).toLocaleDateString()}. Submit any remaining documents as soon as possible.`;
    }
    return `Your application deadline is ${new Date(deadline).toLocaleDateString()} — ${days} day${days === 1 ? '' : 's'} remaining. Submit your documents promptly.`;
  }

  // Readiness score responses
  if (lower.includes('readiness') || lower.includes('score')) {
    const score = readinessScore ?? 0;
    const missing = missingDocuments.length;
    return `Your current readiness score is ${score}%. You have ${uploadedDocuments.length} document(s) uploaded${missing > 0 ? ` and ${missing} still required` : ''}.`;
  }

  // Contextual general responses
  const generalResponses = [
    `Based on your ${programName ?? 'application'} with a readiness score of ${readinessScore ?? 0}%, I can help with document review, requirement verification, or application strategy. What specific aspect would you like to discuss?`,
    `For your ${programName ?? 'application'}, I recommend focusing on ${missingDocuments.length > 0 ? `completing: ${missingDocuments.slice(0, 2).join(' and ')}` : 'document quality and completeness'}. How can I assist?`,
    `I can guide you through the ${programName ?? 'application'} process by reviewing your ${uploadedDocuments.length} uploaded documents and checking requirements. What would you like to know?`,
  ];

  return generalResponses[Math.floor(Math.random() * generalResponses.length)];
}
