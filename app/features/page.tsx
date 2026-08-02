'use client'

import Link from 'next/link'
import { Navigation } from '@/components/navigation'
import { Zap, Upload, Brain, BarChart3, MessageCircle, FileText } from 'lucide-react'

export default function FeaturesPage() {
  const features = [
    {
      icon: Upload,
      title: 'Smart Document Upload',
      description: 'Drag and drop your documents with support for PDF, DOCX, images and more. Organize all your application materials in one place.',
    },
    {
      icon: Brain,
      title: 'AI-Powered Analysis',
      description: 'Get instant insights on your documents. Our AI identifies gaps, missing information, and provides actionable recommendations.',
    },
    {
      icon: BarChart3,
      title: 'Readiness Score',
      description: 'Track your application progress with a real-time readiness score. Know exactly what you need to complete.',
    },
    {
      icon: MessageCircle,
      title: '24/7 AI Assistant',
      description: 'Chat with our AI to ask questions, get writing help, and receive personalized guidance throughout your application.',
    },
    {
      icon: FileText,
      title: 'Professional Reports',
      description: 'Generate comprehensive application reports with all your details, timeline, and recommendations. Export as PDF.',
    },
    {
      icon: Zap,
      title: 'Timeline Management',
      description: 'Never miss a deadline. Automatic reminders and timeline visualization keep you on track.',
    },
  ]

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-16">
          {/* Header */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl sm:text-5xl font-bold text-foreground">Powerful Features</h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Everything you need to create a winning application. Powered by AI.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, idx) => {
              const Icon = feature.icon
              return (
                <div key={idx} className="glassmorphism rounded-xl p-8 border border-secondary/20 hover:border-secondary/40 transition group">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center mb-4 group-hover:scale-110 transition">
                    <Icon size={24} className="text-background" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              )
            })}
          </div>

          {/* CTA Section */}
          <div className="glassmorphism rounded-xl p-12 border border-secondary/20 text-center space-y-6">
            <h2 className="text-3xl font-bold text-foreground">Ready to apply smarter?</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Join thousands of students who have used ApplyWise to streamline their application process and reduce stress.
            </p>
            <Link
              href="/signup"
              className="inline-block px-8 py-3 bg-gradient-to-r from-primary to-secondary text-background rounded-lg font-semibold hover:shadow-lg hover:shadow-primary/20 transition"
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}
