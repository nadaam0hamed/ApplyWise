'use client'

import { Star } from 'lucide-react'

export function Testimonials() {
  const testimonials = [
    {
      name: 'Sarah Johnson',
      role: 'University Applicant',
      content: 'ApplyWise saved me so much time! The AI analysis caught issues I would have missed. Highly recommended!',
      rating: 5,
    },
    {
      name: 'Michael Chen',
      role: 'Visa Applicant',
      content: 'The timeline feature helped me organize everything perfectly. The checklist made sure I didn\'t forget anything crucial.',
      rating: 5,
    },
    {
      name: 'Emma Rodriguez',
      role: 'Scholarship Seeker',
      content: 'I couldn\'t have navigated the scholarship application without ApplyWise. It\'s like having an expert advisor 24/7.',
      rating: 5,
    },
  ]

  return (
    <section className="py-20 sm:py-32 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4">
            Loved by Applicants
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            See what users say about their ApplyWise experience
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((testimonial) => (
            <div
              key={testimonial.name}
              className="p-8 rounded-2xl bg-gradient-to-br from-card to-card/50 border border-primary/20 hover:shadow-lg hover:border-primary/40 transition-all flex flex-col"
            >
              {/* Rating */}
              <div className="flex gap-1 mb-4">
                {Array.from({ length: testimonial.rating }).map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>

              {/* Quote */}
              <p className="text-foreground mb-6 flex-grow leading-relaxed">
                &quot;{testimonial.content}&quot;
              </p>

              {/* Author */}
              <div className="border-t border-border pt-4">
                <p className="font-semibold text-foreground">{testimonial.name}</p>
                <p className="text-sm text-muted-foreground">{testimonial.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
