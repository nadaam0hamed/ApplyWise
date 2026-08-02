'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { Navigation } from '@/components/navigation'

/** Legacy route — applications are created in the wizard and redirect to dashboard. */
export default function ScholarshipAnalysisPage() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/dashboard/start-application')
  }, [router])

  return (
    <>
      <Navigation />
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-secondary" size={32} />
      </div>
    </>
  )
}
