'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, FileText, Search, Clock } from 'lucide-react'
import Link from 'next/link'

// Force dynamic rendering
export const dynamic = 'force-dynamic'

interface AnalysisResult {
  id: string
  fileName: string
  fileSize: string
  analysisDate: string
  status: 'completed' | 'processing' | 'failed'
  toolCount: number
  hasGhidra: boolean
}

export default function ResultsPage() {
  const [results, setResults] = useState<AnalysisResult[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading results - in real app, this would fetch from API
    const mockResults: AnalysisResult[] = [
      {
        id: '1',
        fileName: 'Setup.exe',
        fileSize: '2.4 MB',
        analysisDate: '2025-12-29 14:30',
        status: 'completed',
        toolCount: 5,
        hasGhidra: true
      },
      {
        id: '2',
        fileName: 'notepad.dll',
        fileSize: '1.1 MB',
        analysisDate: '2025-12-29 13:15',
        status: 'completed',
        toolCount: 4,
        hasGhidra: false
      }
    ]

    setTimeout(() => {
      setResults(mockResults)
      setLoading(false)
    }, 1000)
  }, [])

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-100 text-green-800">Completed</Badge>
      case 'processing':
        return <Badge variant="secondary">Processing</Badge>
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <Link href="/">
            <Button variant="outline" size="sm">
              ← Back to Home
            </Button>
          </Link>
          <h1 className="text-3xl font-bold">Analysis Results</h1>
        </div>
        <p className="text-muted-foreground">
          Browse and review previous binary analysis results
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-muted-foreground">Loading results...</span>
        </div>
      ) : results.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Results Found</h3>
            <p className="text-muted-foreground mb-4">
              You haven't analyzed any files yet. Upload a binary to get started.
            </p>
            <Link href="/loader">
              <Button>
                <FileText className="w-4 h-4 mr-2" />
                Upload Binary
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {results.map((result) => (
            <Card key={result.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{result.fileName}</CardTitle>
                    <CardDescription className="flex items-center gap-4 mt-1">
                      <span className="flex items-center gap-1">
                        <FileText className="w-3 h-3" />
                        {result.fileSize}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {result.analysisDate}
                      </span>
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {result.hasGhidra && (
                      <Badge variant="outline" className="text-xs">
                        Ghidra
                      </Badge>
                    )}
                    {getStatusBadge(result.status)}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    {result.toolCount} analysis tools used
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Search className="w-4 h-4 mr-1" />
                      View Details
                    </Button>
                    <Button size="sm">
                      Download Report
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="mt-8 text-center text-muted-foreground">
        <p className="text-sm">
          Results are stored locally and automatically cleaned up after 30 days.
        </p>
      </div>
    </div>
  )
}