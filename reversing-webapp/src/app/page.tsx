'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

// Force dynamic rendering
export const dynamic = 'force-dynamic'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { API_BASE } from '@/app/api/config'
import {
  Upload,
  Search,
  Settings,
  FileText,
  Github,
  Cpu,
  Shield,
  Code,
  MessageSquare,
  GitBranch
} from 'lucide-react'

export default function HomePage() {
  const [ghidraStatus, setGhidraStatus] = useState<{
    installed: boolean
    pluginRunning: boolean
  } | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/ghidra/status`)
      .then((r) => r.json())
      .then((d) =>
        setGhidraStatus({
          installed: d?.installed === true,
          pluginRunning: d?.http_server_running === true,
        })
      )
      .catch(() => setGhidraStatus({ installed: false, pluginRunning: false }))
  }, [])

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Reversing MCP
        </h1>
        <p className="text-xl text-muted-foreground mb-2">
          Professional Binary Analysis with Ghidra MCP Integration
        </p>
        <p className="text-sm text-muted-foreground/80 italic mb-6">
          NSA-grade binary archaeology. No agency endorsement implied.
        </p>
        <div className="flex justify-center flex-wrap gap-2 mb-8">
          <Badge variant="secondary">FastMCP 3.1</Badge>
          <Badge variant="secondary">Ghidra Integration</Badge>
          <Badge variant="secondary">Ollama Chat</Badge>
          {ghidraStatus === null && (
            <Badge variant="outline">Ghidra: checking...</Badge>
          )}
          {ghidraStatus && !ghidraStatus.installed && (
            <Badge variant="destructive">Ghidra: not found</Badge>
          )}
          {ghidraStatus && ghidraStatus.installed && !ghidraStatus.pluginRunning && (
            <Badge className="bg-amber-600 hover:bg-amber-700">
              Ghidra: found, plugin not running
            </Badge>
          )}
          {ghidraStatus && ghidraStatus.installed && ghidraStatus.pluginRunning && (
            <Badge className="bg-green-600 hover:bg-green-700">Ghidra: found</Badge>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-2">
              <Upload className="w-6 h-6 text-blue-600" />
            </div>
            <CardTitle className="text-lg">Analyzer</CardTitle>
            <CardDescription>
              Load binary, run analysis (file / PE / strings / Ghidra)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/loader">
              <Button className="w-full">
                Start Analysis
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-2">
              <Search className="w-6 h-6 text-green-600" />
            </div>
            <CardTitle className="text-lg">View Results</CardTitle>
            <CardDescription>
              Browse previous analysis results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/results">
              <Button variant="outline" className="w-full">
                View Results
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-2">
              <Settings className="w-6 h-6 text-purple-600" />
            </div>
            <CardTitle className="text-lg">Ghidra</CardTitle>
            <CardDescription>
              Ghidra integration and plugin setup
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/ghidra">
              <Button variant="outline" className="w-full">
                Ghidra
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center mb-2">
              <MessageSquare className="w-6 h-6 text-amber-600" />
            </div>
            <CardTitle className="text-lg">Chat</CardTitle>
            <CardDescription>
              Talk to local LLM (Ollama). Set model in Settings.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/chat">
              <Button variant="outline" className="w-full">
                Open Chat
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mb-2">
              <Settings className="w-6 h-6 text-slate-600" />
            </div>
            <CardTitle className="text-lg">Settings</CardTitle>
            <CardDescription>
              Ollama model list/select, Ghidra and backend
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/settings">
              <Button variant="outline" className="w-full">
                Settings
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-2">
              <FileText className="w-6 h-6 text-orange-600" />
            </div>
            <CardTitle className="text-lg">Documentation</CardTitle>
            <CardDescription>
              Help and advanced features
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/help">
              <Button variant="outline" className="w-full">
                View Docs
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 bg-cyan-100 rounded-lg flex items-center justify-center mb-2">
              <GitBranch className="w-6 h-6 text-cyan-600" />
            </div>
            <CardTitle className="text-lg">Workflow</CardTitle>
            <CardDescription>
              Reversed-app flowchart (Mermaid)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/workflow">
              <Button variant="outline" className="w-full">
                View Flowchart
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Features Overview */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold mb-6 text-center">Analysis Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Cpu className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Multi-Tool Analysis</h3>
            <p className="text-muted-foreground">
              Comprehensive analysis using file, strings, entropy, and PE parsing tools
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Code className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Ghidra Integration</h3>
            <p className="text-muted-foreground">
              Professional decompilation and disassembly with Ghidra's advanced analysis engine
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Shield className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Security Analysis</h3>
            <p className="text-muted-foreground">
              Detect obfuscation, identify PDB files, and analyze malware characteristics
            </p>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="bg-muted/50 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold mb-4">Supported Analysis</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">15+</div>
            <div className="text-sm text-muted-foreground">File Types</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">25+</div>
            <div className="text-sm text-muted-foreground">Ghidra Tools</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">5</div>
            <div className="text-sm text-muted-foreground">Analysis Engines</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">100%</div>
            <div className="text-sm text-muted-foreground">Open Source</div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-muted-foreground">
        <div className="flex justify-center gap-4 mb-4">
          <Link href="https://github.com/NationalSecurityAgency/ghidra" className="flex items-center gap-2 hover:text-foreground">
            <Github className="w-4 h-4" />
            Ghidra NSA
          </Link>
          <Link href="https://github.com/sandraschi/reversing-mcp" className="flex items-center gap-2 hover:text-foreground">
            <Github className="w-4 h-4" />
            Reversing MCP
          </Link>
        </div>
        <p className="text-sm">
          Built with FastMCP 3.1 • React TypeScript • Ollama • Ghidra Plugin
        </p>
      </div>
    </div>
  )
}