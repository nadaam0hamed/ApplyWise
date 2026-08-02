'use client'

import { FileText, CheckCircle, ClipboardList, Calendar, Zap, TrendingUp } from 'lucide-react'

export function Features() {
  const features = [
    {
      icon: FileText,
      title: 'AI Document Analysis',
      description: 'Automatically extracts information from uploaded files.',
    },
    {
      icon: CheckCircle,
      title: 'Requirement Checker',
      description: 'Compares documents against official application requirements.',
    },
    {
      icon: ClipboardList,
      title: 'Smart Checklist',
      description: 'Generates a personalized checklist of missing documents.',
    },
    {
      icon: Calendar,
      title: 'Timeline Generator',
      description: 'Creates a step-by-step submission plan before deadlines.',
    },
    {
      icon: Zap,
      title: 'AI Assistant (RAG)',
      description: 'Answers questions using trusted official documents.',
    },
    {
      icon: TrendingUp,
      title: 'Readiness Score',
      description: 'Shows how ready the application is for submission.',
    },
  ]

  return (
    <section id="features" className="py-20 sm:py-32 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            const isEven = index % 2 === 0
            return (
              <div
                key={feature.title}
                className="group flex flex-col items-center text-center p-8 rounded-2xl border border-primary/20 bg-gradient-to-br from-card to-card/50 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 transition-all duration-300"
              >
                {/* Icon with gradient background */}
                <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${isEven ? 'from-primary/20 to-secondary/20' : 'from-secondary/20 to-primary/20'} flex items-center justify-center mb-6 group-hover:shadow-lg transition-all`}>
                  <Icon className={`w-8 h-8 ${isEven ? 'text-primary' : 'text-secondary'}`} />
                </div>

                {/* Content */}
                <h3 className="text-lg font-semibold text-foreground mb-3">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>


      </div>
    </section>
  )
}
