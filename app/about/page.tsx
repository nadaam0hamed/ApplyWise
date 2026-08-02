'use client'

import Link from 'next/link'
import { Navigation } from '@/components/navigation'
import { Heart, Users, Lightbulb, Target } from 'lucide-react'

export default function AboutPage() {
  const values = [
    {
      icon: Heart,
      title: 'Student-First',
      description: 'We put students at the center of everything we do. Our mission is to make the application process less stressful.',
    },
    {
      icon: Lightbulb,
      title: 'Innovation',
      description: 'We leverage the latest AI technology to provide intelligent, actionable insights for your applications.',
    },
    {
      icon: Users,
      title: 'Community',
      description: 'We believe in supporting students globally. ApplyWise connects students from 60+ countries.',
    },
    {
      icon: Target,
      title: 'Excellence',
      description: 'We are committed to helping you achieve your dreams through superior tools and support.',
    },
  ]

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto space-y-16">
          {/* Header */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl sm:text-5xl font-bold text-foreground">About ApplyWise</h1>
            <p className="text-xl text-muted-foreground">
              Empowering students to apply smarter and stress less
            </p>
          </div>

          {/* Mission Statement */}
          <div className="glassmorphism rounded-xl p-12 border border-secondary/20 text-center space-y-4">
            <h2 className="text-3xl font-bold text-foreground">Our Mission</h2>
            <p className="text-lg text-muted-foreground leading-relaxed">
              ApplyWise was founded with a simple mission: to make the university application process less overwhelming and more successful. We believe that every student deserves access to intelligent tools and personalized guidance that help them put their best foot forward.
            </p>
          </div>

          {/* Our Values */}
          <div className="space-y-8">
            <h2 className="text-3xl font-bold text-foreground text-center">Our Values</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {values.map((value, idx) => {
                const Icon = value.icon
                return (
                  <div key={idx} className="glassmorphism rounded-xl p-8 border border-secondary/20">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center mb-4">
                      <Icon size={24} className="text-background" />
                    </div>
                    <h3 className="text-lg font-bold text-foreground mb-2">{value.title}</h3>
                    <p className="text-muted-foreground">{value.description}</p>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Impact */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glassmorphism rounded-xl p-8 border border-secondary/20 text-center">
              <p className="text-4xl font-bold text-secondary mb-2">2,500+</p>
              <p className="text-muted-foreground">Students Helped</p>
            </div>
            <div className="glassmorphism rounded-xl p-8 border border-secondary/20 text-center">
              <p className="text-4xl font-bold text-secondary mb-2">60+</p>
              <p className="text-muted-foreground">Countries</p>
            </div>
            <div className="glassmorphism rounded-xl p-8 border border-secondary/20 text-center">
              <p className="text-4xl font-bold text-secondary mb-2">98%</p>
              <p className="text-muted-foreground">Success Rate</p>
            </div>
          </div>

          {/* Story */}
          <div className="glassmorphism rounded-xl p-12 border border-secondary/20 space-y-4">
            <h2 className="text-2xl font-bold text-foreground">Our Story</h2>
            <p className="text-foreground leading-relaxed">
              ApplyWise was born from the frustrations of students struggling with university applications. Our team noticed that many capable students were overwhelmed by the process and didn't have access to professional guidance.
            </p>
            <p className="text-foreground leading-relaxed">
              We decided to build an intelligent assistant that could provide the insights and support that students need, powered by artificial intelligence and designed with student feedback. Today, ApplyWise helps thousands of students navigate their applications with confidence.
            </p>
          </div>

          {/* CTA */}
          <div className="text-center space-y-6">
            <h2 className="text-3xl font-bold text-foreground">Join Our Community</h2>
            <Link
              href="/signup"
              className="inline-block px-8 py-3 bg-gradient-to-r from-primary to-secondary text-background rounded-lg font-semibold hover:shadow-lg hover:shadow-primary/20 transition"
            >
              Start Your Application Journey
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}
