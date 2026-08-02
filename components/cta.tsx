'use client'

import { ArrowRight } from 'lucide-react'

export function CTA() {
  return (
    <section className="py-20 sm:py-32 bg-gradient-to-br from-background via-primary/10 to-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Content */}
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-6 text-balance">
          Ready to simplify your application journey?
        </h2>

        <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
          Join thousands of successful applicants who have simplified their process with ApplyWise.
        </p>

        {/* CTA Button */}
        <button className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-primary to-secondary text-background rounded-xl font-semibold hover:shadow-lg hover:shadow-primary/30 transition-all transform hover:scale-105">
          Get Started
          <ArrowRight size={20} />
        </button>

        {/* Trust Badge */}
        <div className="mt-16 pt-12 border-t border-border">
          <p className="text-muted-foreground text-sm font-medium mb-4">Trusted by applicants worldwide</p>
          <div className="flex items-center justify-center gap-8 flex-wrap">
            <span className="text-foreground font-semibold">50K+ Users</span>
            <span className="text-muted-foreground/50">•</span>
            <span className="text-foreground font-semibold">98% Success Rate</span>
            <span className="text-muted-foreground/50">•</span>
            <span className="text-foreground font-semibold">100+ Countries</span>
          </div>
        </div>
      </div>
    </section>
  )
}
