'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

export function FAQ() {
  const [openIndex, setOpenIndex] = useState(0)

  const faqs = [
    {
      question: 'What types of applications can ApplyWise help with?',
      answer: 'ApplyWise can assist with university admissions, scholarship applications, visa applications, passport renewals, residency permit applications, and other official procedures that require document verification.',
    },
    {
      question: 'How secure are my documents?',
      answer: 'Your documents are encrypted and stored securely. We use enterprise-grade security with automatic deletion after processing. Your data is never shared with third parties.',
    },
    {
      question: 'Can ApplyWise handle documents in different languages?',
      answer: 'Yes! Our AI supports multiple languages including English, Spanish, French, German, Chinese, and more. The system automatically detects and processes documents regardless of language.',
    },
    {
      question: 'How long does the analysis take?',
      answer: 'Most applications are analyzed within minutes. The timeline depends on the number and complexity of documents, but typically you\'ll get results within 5-10 minutes.',
    },
    {
      question: 'Is there a free trial available?',
      answer: 'Yes! You can start with our free tier which includes analysis for up to 3 applications. Premium plans offer unlimited applications, priority support, and advanced features.',
    },
    {
      question: 'Can I export my checklist and timeline?',
      answer: 'Absolutely! You can export your checklist, timeline, and analysis report as PDF or Word documents. This makes it easy to share with advisors or keep for your records.',
    },
  ]

  return (
    <section className="py-20 sm:py-32 bg-background">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4">
            Frequently Asked Questions
          </h2>
          <p className="text-lg text-muted-foreground">
            Everything you need to know about ApplyWise
          </p>
        </div>

        {/* FAQ Accordion */}
        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="border border-primary/20 bg-gradient-to-r from-card/50 to-card/30 rounded-xl overflow-hidden hover:border-primary/40 hover:bg-gradient-to-r hover:from-card hover:to-card/50 transition-all"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? -1 : index)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-primary/5 transition-colors"
              >
                <span className="text-lg font-semibold text-foreground text-left">
                  {faq.question}
                </span>
                <ChevronDown
                  className={`flex-shrink-0 w-5 h-5 text-primary transition-transform duration-200 ${
                    openIndex === index ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {openIndex === index && (
                <div className="px-6 py-4 bg-primary/5 border-t border-primary/20">
                  <p className="text-muted-foreground leading-relaxed">
                    {faq.answer}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
