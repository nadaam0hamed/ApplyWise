'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { useApplication } from '@/hooks/useApplication'
import { ProgramService } from '@/services/program.service'
import { RequirementService } from '@/services/requirement.service'
import {
  ApplicationType,
  ApplicationStatus,
  RequirementSource,
  APPLICATION_TYPE_LABELS,
  APPLICATION_TYPE_ICONS,
  APPLICATION_TYPES,
} from '@/constants/applicationStatus'
import type { Program } from '@/types/program'
import {
  ChevronRight,
  Search,
  FileUp,
  FileText,
  Type,
  CheckCircle,
  ArrowLeft,
  Loader2,
} from 'lucide-react'

type WizardStep = 1 | 2 | 3

export default function StartApplicationPage() {
  const router = useRouter()
  const { createApplication } = useApplication()

  const [step, setStep] = useState<WizardStep>(1)
  const [applicationType, setApplicationType] = useState<ApplicationType | ''>('')
  const [requirementSource, setRequirementSource] = useState<RequirementSource | ''>('')
  const [title, setTitle] = useState('')
  const [country, setCountry] = useState('')
  const [websiteUrl, setWebsiteUrl] = useState('')
  const [manualNotes, setManualNotes] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null)
  const [programs, setPrograms] = useState<Program[]>([])
  const [programsLoading, setProgramsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    if (requirementSource !== RequirementSource.Program) return

    let mounted = true
    setProgramsLoading(true)

    ProgramService.list()
      .then((list) => {
        if (mounted) setPrograms(list)
      })
      .catch(() => {
        if (mounted) setPrograms([])
      })
      .finally(() => {
        if (mounted) setProgramsLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [requirementSource])

  const filteredPrograms = programs.filter(
    (prog) =>
      prog.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prog.country.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const handleApplicationTypeSelect = (type: ApplicationType) => {
    setApplicationType(type)
    setStep(2)
  }

  const handleRequirementSourceSelect = (source: RequirementSource) => {
    setRequirementSource(source)
    setSelectedProgram(null)
    setWebsiteUrl('')
    setManualNotes('')
    if (source !== RequirementSource.Program) {
      setSearchQuery('')
    }
  }

  const handleSelectProgram = (program: Program) => {
    setSelectedProgram(program)
    setTitle(program.scholarship_name || program.name)
    setCountry(program.country)
    setStep(3)
  }

  const handleProceedToReview = () => {
    if (!title.trim()) {
      setSubmitError('Please enter an application title')
      return
    }
    if (!country.trim()) {
      setSubmitError('Please enter a country')
      return
    }
    setSubmitError(null)
    setStep(3)
  }

  const handleCreateApplication = async () => {
    if (!applicationType) return
    if (!title.trim() || !country.trim()) {
      setSubmitError('Title and country are required')
      return
    }

    setIsSubmitting(true)
    setSubmitError(null)

    try {
      const created = await createApplication({
        application_type: applicationType,
        title: title.trim(),
        country: country.trim(),
        status: ApplicationStatus.InProgress,
        source_url: requirementSource === RequirementSource.Url ? websiteUrl.trim() || null : null,
      })

      if (selectedProgram) {
        await RequirementService.createDefaultCategories(created.id)
      }

      router.push(`/applications/${created.id}`)
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to create application')
      setIsSubmitting(false)
    }
  }

  const handleBack = () => {
    setSubmitError(null)
    if (step === 3) {
      setStep(2)
      return
    }
    if (step === 2) {
      setRequirementSource('')
      setSelectedProgram(null)
      setWebsiteUrl('')
      setManualNotes('')
      setTitle('')
      setCountry('')
      setSearchQuery('')
      setStep(1)
      setApplicationType('')
    }
  }

  const stepLabels: Record<WizardStep, string> = {
    1: 'Choose Application Type',
    2: 'Application Details',
    3: 'Review & Create',
  }

  return (
    <>
      <Navigation />
      <div className="premium-dashboard-bg min-h-screen">
        <div className="noise-texture" />
        <div className="subtle-grid" />
        <div className="floating-light-emerald" style={{ top: '15%', left: '-10%' }} />
        <div className="floating-light-cyan" style={{ top: '50%', right: '-5%' }} />
        <div className="floating-light-blue" style={{ bottom: '10%', left: '5%' }} />

        <div className="relative z-20 py-8 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto space-y-8">
            {/* Header */}
            <div className="premium-card card-animate-in overflow-hidden">
              <div className="p-8 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-4xl font-bold text-foreground">Start New Application</h1>
                    <p className="text-sm text-muted-foreground mt-2">
                      Step {step} of 3 • {stepLabels[step]}
                    </p>
                  </div>
                  {step > 1 && (
                    <button
                      type="button"
                      onClick={handleBack}
                      disabled={isSubmitting}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-secondary hover:bg-secondary/10 transition-colors disabled:opacity-50"
                    >
                      <ArrowLeft size={18} />
                      Back
                    </button>
                  )}
                </div>
                <div className="animated-gradient-line mt-4" />
              </div>
            </div>

            {submitError && (
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                {submitError}
              </div>
            )}

            {/* Step 1: Choose Application Type */}
            {step === 1 && (
              <div className="premium-card p-8 card-animate-in">
                <h2 className="text-xl font-bold text-foreground mb-6">
                  What type of application are you preparing?
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {APPLICATION_TYPES.map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => handleApplicationTypeSelect(type)}
                      className="p-6 rounded-xl border-2 border-secondary/20 hover:border-secondary hover:bg-secondary/10 transition-all group text-left"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-2xl mb-2">{APPLICATION_TYPE_ICONS[type]}</p>
                          <h3 className="font-semibold text-foreground group-hover:text-secondary transition-colors">
                            {APPLICATION_TYPE_LABELS[type]}
                          </h3>
                        </div>
                        <ChevronRight
                          size={20}
                          className="text-secondary/50 group-hover:text-secondary transition-colors"
                        />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 2: Details & Requirement Source */}
            {step === 2 && applicationType && (
              <div className="premium-card p-8 card-animate-in space-y-8">
                <div>
                  <h2 className="text-xl font-bold text-foreground mb-2">Application Details</h2>
                  <p className="text-sm text-muted-foreground">
                    {APPLICATION_TYPE_ICONS[applicationType]}{' '}
                    {APPLICATION_TYPE_LABELS[applicationType]}
                  </p>
                </div>

                {/* Required fields */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs text-muted-foreground uppercase tracking-wide mb-2">
                      Application Title *
                    </label>
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="e.g. Erasmus Mundus Master's Program"
                      className="w-full px-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground placeholder-muted-foreground focus:border-secondary focus:outline-none transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-muted-foreground uppercase tracking-wide mb-2">
                      Country *
                    </label>
                    <input
                      type="text"
                      value={country}
                      onChange={(e) => setCountry(e.target.value)}
                      placeholder="e.g. Germany"
                      className="w-full px-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground placeholder-muted-foreground focus:border-secondary focus:outline-none transition-colors"
                    />
                  </div>
                </div>

                {/* Optional requirement source */}
                <div>
                  <h3 className="font-semibold text-foreground mb-2">
                    How do you want to provide requirements? (optional)
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Choose a method to import application requirements, or skip to create with
                    title and country only.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { id: RequirementSource.Program, icon: '📚', label: 'Popular Program', desc: 'Select from scholarship programs' },
                      { id: RequirementSource.Url, icon: '🔗', label: 'Website URL', desc: 'Save an official requirements URL' },
                      { id: RequirementSource.Pdf, icon: '📄', label: 'Requirement PDF', desc: 'Note a PDF source (upload coming soon)' },
                      { id: RequirementSource.Manual, icon: '✏️', label: 'Manual Text', desc: 'Enter requirements in your own words' },
                    ].map((source) => (
                      <button
                        key={source.id}
                        type="button"
                        onClick={() => handleRequirementSourceSelect(source.id)}
                        className={`p-6 rounded-xl border-2 transition-all text-left ${
                          requirementSource === source.id
                            ? 'border-secondary bg-secondary/10'
                            : 'border-secondary/20 hover:border-secondary hover:bg-secondary/5'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <p className="text-3xl">{source.icon}</p>
                          <CheckCircle
                            size={20}
                            className={
                              requirementSource === source.id
                                ? 'text-secondary'
                                : 'text-secondary/20'
                            }
                          />
                        </div>
                        <h3 className="font-semibold text-foreground mb-1">{source.label}</h3>
                        <p className="text-xs text-muted-foreground">{source.desc}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Source-specific inputs */}
                {requirementSource === RequirementSource.Url && (
                  <div className="p-6 rounded-xl bg-secondary/5 border border-secondary/20 space-y-4">
                    <h3 className="font-semibold text-foreground">Official Website URL</h3>
                    <input
                      type="url"
                      placeholder="https://example.com/requirements"
                      value={websiteUrl}
                      onChange={(e) => setWebsiteUrl(e.target.value)}
                      className="w-full px-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground placeholder-muted-foreground focus:border-secondary focus:outline-none transition-colors"
                    />
                  </div>
                )}

                {requirementSource === RequirementSource.Pdf && (
                  <div className="p-6 rounded-xl bg-secondary/5 border border-secondary/20 space-y-2">
                    <h3 className="font-semibold text-foreground">Requirement PDF</h3>
                    <p className="text-sm text-muted-foreground">
                      Document upload is not available yet. You can create the application now
                      and add documents later.
                    </p>
                  </div>
                )}

                {requirementSource === RequirementSource.Manual && (
                  <div className="p-6 rounded-xl bg-secondary/5 border border-secondary/20 space-y-4">
                    <h3 className="font-semibold text-foreground">Requirements (optional notes)</h3>
                    <textarea
                      value={manualNotes}
                      onChange={(e) => setManualNotes(e.target.value)}
                      rows={4}
                      placeholder="Describe the application requirements..."
                      className="w-full px-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground placeholder-muted-foreground focus:border-secondary focus:outline-none transition-colors resize-none"
                    />
                  </div>
                )}

                {requirementSource === RequirementSource.Program && (
                  <div className="space-y-4">
                    <h3 className="font-semibold text-foreground">Search Programs</h3>
                    <div className="relative">
                      <Search
                        size={18}
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground"
                      />
                      <input
                        type="text"
                        placeholder="Search programs..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground placeholder-muted-foreground focus:border-secondary focus:outline-none transition-colors"
                      />
                    </div>

                    {programsLoading ? (
                      <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground">
                        <Loader2 className="animate-spin" size={20} />
                        Loading programs...
                      </div>
                    ) : filteredPrograms.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-6">
                        No programs found. You can still create your application with the title
                        and country above.
                      </p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {filteredPrograms.map((program) => (
                          <button
                            key={program.id}
                            type="button"
                            onClick={() => handleSelectProgram(program)}
                            className={`p-4 rounded-lg border-2 transition-all text-left ${
                              selectedProgram?.id === program.id
                                ? 'border-secondary bg-secondary/10'
                                : 'border-secondary/20 hover:border-secondary hover:bg-secondary/5'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div>
                                <p className="text-2xl mb-1">{program.icon ?? '📚'}</p>
                                <h4 className="font-semibold text-foreground text-sm">
                                  {program.name}
                                </h4>
                                <p className="text-xs text-muted-foreground mt-1">
                                  {program.country}
                                </p>
                              </div>
                              <ChevronRight size={18} className="text-secondary/50" />
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Continue without program selection */}
                {requirementSource !== RequirementSource.Program && (
                  <button
                    type="button"
                    onClick={handleProceedToReview}
                    disabled={!title.trim() || !country.trim()}
                    className="w-full px-6 py-3 btn-gradient-primary text-background rounded-lg font-semibold hover:shadow-lg hover:shadow-primary/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <CheckCircle size={18} />
                    Continue to Review
                  </button>
                )}

                {requirementSource === RequirementSource.Program && !selectedProgram && (
                  <button
                    type="button"
                    onClick={handleProceedToReview}
                    disabled={!title.trim() || !country.trim()}
                    className="w-full px-6 py-3 rounded-lg border border-secondary/30 text-secondary hover:bg-secondary/10 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Skip program selection & continue
                  </button>
                )}
              </div>
            )}

            {/* Step 3: Review & Create */}
            {step === 3 && applicationType && (
              <div className="space-y-6 card-animate-in">
                <div className="premium-card p-8 space-y-6">
                  <h2 className="text-2xl font-bold text-foreground">Review Application</h2>

                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-secondary/5 border border-secondary/20">
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                        Application Type
                      </p>
                      <p className="text-lg font-semibold text-foreground">
                        {APPLICATION_TYPE_ICONS[applicationType]}{' '}
                        {APPLICATION_TYPE_LABELS[applicationType]}
                      </p>
                    </div>

                    <div className="p-4 rounded-lg bg-secondary/5 border border-secondary/20">
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                        Title
                      </p>
                      <p className="text-lg font-semibold text-foreground">{title}</p>
                    </div>

                    <div className="p-4 rounded-lg bg-secondary/5 border border-secondary/20">
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                        Country
                      </p>
                      <p className="text-lg font-semibold text-foreground">{country}</p>
                    </div>

                    {selectedProgram && (
                      <div className="p-4 rounded-lg bg-secondary/5 border border-secondary/20">
                        <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                          Selected Program
                        </p>
                        <p className="text-sm text-foreground">{selectedProgram.name}</p>
                        {selectedProgram.required_documents.length > 0 && (
                          <div className="mt-3 space-y-1">
                            <p className="text-xs text-muted-foreground uppercase tracking-wide">
                              Required Documents
                            </p>
                            {selectedProgram.required_documents.map((doc) => (
                              <div key={doc} className="flex items-center gap-2 text-sm text-foreground">
                                <CheckCircle size={14} className="text-secondary flex-shrink-0" />
                                {doc}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {requirementSource === RequirementSource.Url && websiteUrl && (
                      <div className="p-4 rounded-lg bg-secondary/5 border border-secondary/20">
                        <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                          Source URL
                        </p>
                        <p className="text-sm text-foreground break-all">{websiteUrl}</p>
                      </div>
                    )}

                    {requirementSource === RequirementSource.Manual && manualNotes && (
                      <div className="p-4 rounded-lg bg-secondary/5 border border-secondary/20">
                        <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                          Notes
                        </p>
                        <p className="text-sm text-foreground whitespace-pre-wrap">{manualNotes}</p>
                      </div>
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleCreateApplication}
                  disabled={isSubmitting}
                  className="w-full px-6 py-4 btn-gradient-primary text-background rounded-lg font-semibold text-lg hover:shadow-lg hover:shadow-primary/30 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      Creating Application...
                    </>
                  ) : (
                    <>
                      <CheckCircle size={20} />
                      Create Application
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
