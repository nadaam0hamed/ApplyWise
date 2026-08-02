'use client'

import { Clock, CheckCircle2, Zap, Brain } from 'lucide-react'

export function WhyChoose() {
  const reasons = [
    {
      icon: Clock,
      title: 'Save Time',
      description: 'Reduce application preparation from weeks to hours with AI-powered automation.',
    },
    {
      icon: CheckCircle2,
      title: 'Reduce Errors',
      description: 'Avoid costly mistakes with comprehensive document analysis and verification.',
    },
    {
      icon: Zap,
      title: 'Stay Organized',
      description: 'Keep track of all requirements, deadlines, and documents in one place.',
    },
    {
      icon: Brain,
      title: 'Powered by AI',
      description: 'Leverage cutting-edge artificial intelligence for intelligent insights.',
    },
  ]

  return (
    <section id="about" className="py-20 sm:py-32 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4">
            Why Choose ApplyWise
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            The smarter way to handle your application journey
          </p>
        </div>

        {/* Reasons Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {reasons.map((reason) => {
            const Icon = reason.icon
            return (
              <div
                key={reason.title}
                className="flex gap-6 p-8 rounded-2xl bg-gradient-to-br from-card/50 to-card/30 border border-primary/20 hover:shadow-lg hover:border-primary/40 hover:bg-gradient-to-br hover:from-card hover:to-card/50 transition-all"
              >
                {/* Icon */}
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                </div>

                {/* Content */}
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    {reason.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {reason.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
