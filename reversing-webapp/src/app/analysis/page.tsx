'use client'

import { useState, useEffect } from 'react'

// Force dynamic rendering
export const dynamic = 'force-dynamic'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAnalysisState, useToolsStatus } from '@/lib/mcp/hooks'
import { formatFileSize, formatEntropy, getEntropyDescription, calculateAnalysisScore, getAnalysisSummary } from '@/lib/utils'
import {
  FileText,
  Code,
  BarChart3,
  Shield,
  Cpu,
  Database,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  Download,
  Settings
} from 'lucide-react'

export default function AnalysisPage() {
  const router = useRouter()
  const { state } = useAnalysisState()
  const [ghidraStatus, setGhidraStatus] = useState<any>(null)
  const [analysisProgress, setAnalysisProgress] = useState(0)

  // Redirect if no analysis results
  useEffect(() => {
    if (!state.analysis_results && !state.current_file) {
      router.push('/loader')
    }
  }, [state, router])

  // Check Ghidra status
  useEffect(() => {
    const checkGhidraStatus = async () => {
      try {
        const response = await fetch('http://localhost:3001/ghidra/status')
        if (response.ok) {
          const status = await response.json()
          setGhidraStatus(status)
        }
      } catch (error) {
        console.warn('Failed to check Ghidra status:', error)
      }
    }

    checkGhidraStatus()
  }, [])

  // Simulate analysis progress
  useEffect(() => {
    if (state.analysis_results) {
      const timer = setInterval(() => {
        setAnalysisProgress(prev => {
          if (prev >= 100) {
            clearInterval(timer)
            return 100
          }
          return prev + 10
        })
      }, 200)
      return () => clearInterval(timer)
    }
  }, [state.analysis_results])

  if (!state.analysis_results || !state.current_file) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading analysis...</p>
        </div>
      </div>
    )
  }

  const { analysis_results, current_file } = state

  // Use the analysis score and other metrics from the API response
  const analysisScore = analysis_results?.analysis_score || 0
  const languageHint = analysis_results?.language_hint || 'Unknown'
  const entropyScore = analysis_results?.entropy_score || 0.0
  const functionsCount = analysis_results?.functions || 0
  const stringsCount = analysis_results?.strings || 0
  const hasPdb = analysis_results?.has_pdb || false
  const isObfuscated = analysis_results?.is_obfuscated || false

  const summary = {
    functions: functionsCount,
    strings: stringsCount,
    entropy_score: entropyScore,
    language_hint: languageHint,
    has_pdb: hasPdb,
    is_obfuscated: isObfuscated
  }

  // Ghidra action handlers
  const handleDecompileFunctions = async () => {
    if (!current_file) return

    try {
      const response = await fetch('http://localhost:3001/ghidra/decompile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ function_name: 'main' }) // Start with main function
      })

      if (response.ok) {
        const result = await response.json()
        alert(`Decompiled main function:\n\n${result.decompiled_code?.substring(0, 500)}...`)
      } else {
        throw new Error(`Failed to decompile: ${response.statusText}`)
      }
    } catch (error) {
      console.error('Decompilation failed:', error)
      alert(`Decompilation failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const handleStartGhidra = async () => {
    try {
      const response = await fetch('http://localhost:3001/start_ghidra', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: current_file?.name })
      })

      if (response.ok) {
        alert('Ghidra GUI started successfully!')
        // Refresh Ghidra status
        const statusResponse = await fetch('http://localhost:3001/ghidra/status')
        if (statusResponse.ok) {
          setGhidraStatus(await statusResponse.json())
        }
      } else {
        throw new Error(`Failed to start Ghidra: ${response.statusText}`)
      }
    } catch (error) {
      console.error('Failed to start Ghidra:', error)
      alert(`Failed to start Ghidra: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Analysis Results</h1>
            <p className="text-muted-foreground">
              Comprehensive reverse engineering analysis of {current_file.name}
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/results">
              <Button variant="outline">
                <FileText className="w-4 h-4 mr-2" />
                View All Results
              </Button>
            </Link>
            <Link href="/settings">
              <Button variant="outline">
                <Settings className="w-4 h-4 mr-2" />
                Ghidra Settings
              </Button>
            </Link>
          </div>
        </div>

        {/* Analysis Progress */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Analysis Progress</span>
              <span className="text-sm text-muted-foreground">{analysisProgress}%</span>
            </div>
            <Progress value={analysisProgress} className="w-full" />
          </CardContent>
        </Card>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">File Size</p>
                <p className="text-2xl font-bold">{formatFileSize(current_file.size)}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Analysis Score</p>
                <p className="text-2xl font-bold">{analysisScore}%</p>
              </div>
              <BarChart3 className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Functions Found</p>
                <p className="text-2xl font-bold">{summary.functions}</p>
              </div>
              <Code className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Strings Found</p>
                <p className="text-2xl font-bold">{summary.strings}</p>
              </div>
              <Database className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Analysis Tabs */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="technical">Technical</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="ghidra">Ghidra</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>What is this executable?</CardTitle>
              <CardDescription>
                Basic identification and classification
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-2">File Information</h4>
                  <dl className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Name:</dt>
                      <dd className="font-mono">{current_file.name}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Size:</dt>
                      <dd>{formatFileSize(current_file.size)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Type:</dt>
                      <dd>{analysis_results.results.file?.file_type || 'Unknown'}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Language:</dt>
                      <dd>
                        <Badge variant={languageHint !== 'Unknown' ? 'default' : 'secondary'}>
                          {languageHint}
                        </Badge>
                      </dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Analysis Summary</h4>
                  <dl className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Tools Used:</dt>
                      <dd>{analysis_results.tools_used.join(', ')}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Entropy:</dt>
                      <dd>{formatEntropy(entropyScore)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Functions:</dt>
                      <dd>{functionsCount}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Strings:</dt>
                      <dd>{stringsCount}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>How does it work?</CardTitle>
              <CardDescription>
                Functional analysis and capabilities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">Entropy Analysis</span>
                      <span className="text-sm text-muted-foreground">
                        {getEntropyDescription(entropyScore)}
                      </span>
                    </div>
                    <Progress value={(entropyScore / 8) * 100} className="h-2" />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-blue-600 mb-1">
                      {functionsCount}
                    </div>
                    <div className="text-sm text-muted-foreground">Functions</div>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-green-600 mb-1">
                      {stringsCount}
                    </div>
                    <div className="text-sm text-muted-foreground">Strings</div>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-purple-600 mb-1">
                      {analysisScore}%
                    </div>
                    <div className="text-sm text-muted-foreground">Completeness</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Technical Tab */}
        <TabsContent value="technical" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Technical Details</CardTitle>
              <CardDescription>
                Low-level analysis and binary structure
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="strings">
                <TabsList>
                  <TabsTrigger value="strings">Strings</TabsTrigger>
                  <TabsTrigger value="entropy">Entropy</TabsTrigger>
                  <TabsTrigger value="hexdump">Hex Dump</TabsTrigger>
                </TabsList>

                <TabsContent value="strings" className="space-y-4">
                  <div className="max-h-96 overflow-y-auto border rounded p-4 bg-muted/20">
                    {analysis_results.results.strings?.map((str: any, index: number) => (
                      <div key={index} className="font-mono text-sm mb-2">
                        <span className="text-muted-foreground">
                          {str.offset.toString(16).padStart(8, '0')}:
                        </span>
                        <span className="ml-4">{str.string}</span>
                      </div>
                    )) || <p className="text-muted-foreground">No strings found</p>}
                  </div>
                </TabsContent>

                <TabsContent value="entropy" className="space-y-4">
                  <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Overall Entropy</span>
                    <Badge variant="outline">
                      {formatEntropy(entropyScore)}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {getEntropyDescription(entropyScore)}
                  </p>

                    {analysis_results.results.entropy?.compressed_regions && analysis_results.results.entropy.compressed_regions.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Compressed Regions</h4>
                        <div className="space-y-2">
                          {analysis_results.results.entropy.compressed_regions.map((region: any, index: number) => (
                            <div key={index} className="flex items-center justify-between p-2 border rounded">
                              <span className="text-sm">Offset: 0x{region.offset.toString(16)}</span>
                              <Badge variant="secondary">Entropy: {region.entropy.toFixed(2)}</Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="hexdump" className="space-y-4">
                  <div className="font-mono text-sm bg-muted/20 p-4 rounded border max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap">
                      {analysis_results.results.hexdump || 'Hex dump not available'}
                    </pre>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Security Analysis</CardTitle>
              <CardDescription>
                Malware detection and security assessment
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* PDB Detection */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  {hasPdb ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600" />
                  )}
                  <div>
                    <h4 className="font-medium">PDB Debug Symbols</h4>
                    <p className="text-sm text-muted-foreground">
                      {hasPdb
                        ? 'Debug symbols found - likely legitimate software'
                        : 'No debug symbols - could indicate malware or stripped binary'
                      }
                    </p>
                  </div>
                </div>
                <Badge variant={hasPdb ? 'default' : 'destructive'}>
                  {hasPdb ? 'Present' : 'Missing'}
                </Badge>
              </div>

              {/* Obfuscation Detection */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  {isObfuscated ? (
                    <AlertTriangle className="w-5 h-5 text-orange-600" />
                  ) : (
                    <Shield className="w-5 h-5 text-green-600" />
                  )}
                  <div>
                    <h4 className="font-medium">Obfuscation Analysis</h4>
                    <p className="text-sm text-muted-foreground">
                      {isObfuscated
                        ? 'Signs of obfuscation detected - potential malware'
                        : 'No obfuscation detected - appears to be clean'
                      }
                    </p>
                  </div>
                </div>
                <Badge variant={isObfuscated ? 'destructive' : 'default'}>
                  {isObfuscated ? 'Obfuscated' : 'Clean'}
                </Badge>
              </div>

              {/* Entropy Analysis */}
              <div className="p-4 border rounded-lg">
                <h4 className="font-medium mb-2">Entropy Analysis</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Overall Entropy</span>
                    <span>{formatEntropy(entropyScore)}</span>
                  </div>
                  <Progress value={(entropyScore / 8) * 100} className="h-2" />
                  <p className="text-xs text-muted-foreground">
                    {getEntropyDescription(entropyScore)}
                  </p>
                </div>
              </div>

              {/* Security Recommendations */}
              <div className="p-4 bg-muted/50 rounded-lg">
                <h4 className="font-medium mb-2">Security Recommendations</h4>
                <ul className="text-sm space-y-1">
                  {!hasPdb && (
                    <li className="text-orange-600">⚠️ No debug symbols - verify legitimacy</li>
                  )}
                  {isObfuscated && (
                    <li className="text-red-600">⚠️ Obfuscation detected - potential malware</li>
                  )}
                  {entropyScore > 7.0 && (
                    <li className="text-orange-600">⚠️ High entropy - possible encryption</li>
                  )}
                  {stringsCount < 5 && (
                    <li className="text-orange-600">⚠️ Very few strings - suspicious</li>
                  )}
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Ghidra Tab */}
        <TabsContent value="ghidra" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Ghidra Analysis</CardTitle>
              <CardDescription>
                Professional decompilation and disassembly
              </CardDescription>
            </CardHeader>
            <CardContent>
              {ghidraStatus?.available ? (
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2 text-green-700">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-sm">Ghidra MCP is available and ready</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Button className="h-auto p-4" onClick={handleDecompileFunctions}>
                      <div className="text-left">
                        <div className="font-medium">Decompile Functions</div>
                        <div className="text-sm text-muted-foreground">View C code from binary</div>
                      </div>
                    </Button>

                    <Button variant="outline" className="h-auto p-4">
                      <div className="text-left">
                        <div className="font-medium">Cross References</div>
                        <div className="text-sm text-muted-foreground">Find function calls</div>
                      </div>
                    </Button>

                    <Button variant="outline" className="h-auto p-4" onClick={handleStartGhidra}>
                      <div className="text-left">
                        <div className="font-medium">Start Ghidra GUI</div>
                        <div className="text-sm text-muted-foreground">Manual analysis</div>
                      </div>
                    </Button>

                    <Button variant="outline" className="h-auto p-4">
                      <div className="text-left">
                        <div className="font-medium">Export Analysis</div>
                        <div className="text-sm text-muted-foreground">Save results</div>
                      </div>
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center gap-2 text-yellow-700">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm">
                      Ghidra MCP not available. Please install Ghidra plugin and start Ghidra.
                    </span>
                  </div>
                  <Link href="/settings">
                    <Button variant="outline" className="mt-3">
                      Configure Ghidra
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Export Tab */}
        <TabsContent value="export" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Export Analysis Results</CardTitle>
              <CardDescription>
                Download or share your analysis results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button className="h-auto p-4">
                  <div className="text-left">
                    <Download className="w-4 h-4 mr-2" />
                    <div className="font-medium">JSON Report</div>
                    <div className="text-sm text-muted-foreground">Complete analysis data</div>
                  </div>
                </Button>

                <Button variant="outline" className="h-auto p-4">
                  <div className="text-left">
                    <FileText className="w-4 h-4 mr-2" />
                    <div className="font-medium">PDF Report</div>
                    <div className="text-sm text-muted-foreground">Formatted document</div>
                  </div>
                </Button>

                <Button variant="outline" className="h-auto p-4">
                  <div className="text-left">
                    <Code className="w-4 h-4 mr-2" />
                    <div className="font-medium">Raw Data</div>
                    <div className="text-sm text-muted-foreground">For other tools</div>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}