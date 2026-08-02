import { Navigation } from '@/components/navigation'
import { Hero } from '@/components/hero'
import { Features } from '@/components/features'
import { HowItWorks } from '@/components/how-it-works'
import { WhyChoose } from '@/components/why-choose'
import { Testimonials } from '@/components/testimonials'
import { FAQ } from '@/components/faq'
import { CTA } from '@/components/cta'
import { Footer } from '@/components/footer'

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <Navigation />
      <Hero />
      <Features />
      <HowItWorks />
      <WhyChoose />
      <Testimonials />
      <FAQ />
      <CTA />
      <Footer />
    </main>
  )
}
