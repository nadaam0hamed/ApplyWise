'use client'

import { useState } from 'react'
import { Navigation } from '@/components/navigation'
import { Mail, Phone, MapPin, Send } from 'lucide-react'

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: '',
  })
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Simulate form submission
      await new Promise(resolve => setTimeout(resolve, 500))
      setSubmitted(true)
      setFormData({ name: '', email: '', message: '' })
    } finally {
      setLoading(false)
    }
  }

  const contactInfo = [
    {
      icon: Mail,
      title: 'Email',
      content: 'support@applywise.io',
      href: 'mailto:support@applywise.io',
    },
    {
      icon: Phone,
      title: 'Phone',
      content: '+1 (555) 123-4567',
      href: 'tel:+15551234567',
    },
    {
      icon: MapPin,
      title: 'Location',
      content: 'San Francisco, CA',
      href: '#',
    },
  ]

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto space-y-16">
          {/* Header */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl sm:text-5xl font-bold text-foreground">Get in Touch</h1>
            <p className="text-xl text-muted-foreground">
              Have questions? We'd love to hear from you
            </p>
          </div>

          {/* Contact Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {contactInfo.map((info, idx) => {
              const Icon = info.icon
              return (
                <a
                  key={idx}
                  href={info.href}
                  className="glassmorphism rounded-xl p-6 border border-secondary/20 hover:border-secondary/40 transition group"
                >
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center mb-4 group-hover:scale-110 transition">
                    <Icon size={24} className="text-background" />
                  </div>
                  <h3 className="font-semibold text-foreground mb-1">{info.title}</h3>
                  <p className="text-muted-foreground text-sm">{info.content}</p>
                </a>
              )
            })}
          </div>

          {/* Contact Form */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            {/* Form */}
            <div className="glassmorphism rounded-xl p-8 border border-secondary/20">
              <h2 className="text-2xl font-bold text-foreground mb-6">Send us a Message</h2>

              {submitted ? (
                <div className="space-y-4 py-8">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-r from-primary to-secondary mx-auto flex items-center justify-center">
                    <span className="text-2xl text-background">✓</span>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground text-center">Thank you!</h3>
                  <p className="text-muted-foreground text-center">
                    We've received your message and will get back to you soon.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      className="w-full px-4 py-2 rounded-lg bg-input border border-border text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition"
                      placeholder="John Doe"
                      required
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full px-4 py-2 rounded-lg bg-input border border-border text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition"
                      placeholder="you@example.com"
                      required
                    />
                  </div>

                  {/* Message */}
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Message
                    </label>
                    <textarea
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      rows={5}
                      className="w-full px-4 py-2 rounded-lg bg-input border border-border text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition resize-none"
                      placeholder="Tell us how we can help..."
                      required
                    ></textarea>
                  </div>

                  {/* Submit */}
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2 bg-gradient-to-r from-primary to-secondary text-background rounded-lg font-medium hover:shadow-lg hover:shadow-primary/20 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Send size={18} />
                    {loading ? 'Sending...' : 'Send Message'}
                  </button>
                </form>
              )}
            </div>

            {/* Info Section */}
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-4">Frequently Asked Questions</h2>
                <div className="space-y-4">
                  <div className="glassmorphism rounded-lg p-4 border border-secondary/20">
                    <h3 className="font-semibold text-foreground mb-2">Is ApplyWise free?</h3>
                    <p className="text-sm text-muted-foreground">Yes! We offer a free tier with essential features. Premium plans are available for advanced features.</p>
                  </div>
                  <div className="glassmorphism rounded-lg p-4 border border-secondary/20">
                    <h3 className="font-semibold text-foreground mb-2">How long does analysis take?</h3>
                    <p className="text-sm text-muted-foreground">Our AI typically analyzes documents within 1-2 minutes. Complex documents may take longer.</p>
                  </div>
                  <div className="glassmorphism rounded-lg p-4 border border-secondary/20">
                    <h3 className="font-semibold text-foreground mb-2">Is my data secure?</h3>
                    <p className="text-sm text-muted-foreground">Yes, all your documents are encrypted and stored securely. We never share your data with third parties.</p>
                  </div>
                </div>
              </div>

              <div className="glassmorphism rounded-xl p-8 border border-secondary/20">
                <h3 className="text-lg font-bold text-foreground mb-3">Response Times</h3>
                <p className="text-sm text-muted-foreground mb-4">We typically respond to inquiries within 24 hours during business days.</p>
                <p className="text-xs text-muted-foreground">Business Hours: Monday - Friday, 9 AM - 5 PM PST</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
