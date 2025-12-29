'use client'

import Link from 'next/link'

// Force dynamic rendering
export const dynamic = 'force-dynamic'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Upload,
  Search,
  Settings,
  FileText,
  Github,
  Cpu,
  Shield,
  Code
} from 'lucide-react'

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Reversing MCP
        </h1>
        <p className="text-xl text-muted-foreground mb-6">
          Professional Binary Analysis with Ghidra MCP Integration
        </p>
        <div className="flex justify-center gap-2 mb-8">
          <Badge variant="secondary">FastMCP 2.13+</Badge>
          <Badge variant="secondary">Ghidra Integration</Badge>
          <Badge variant="secondary">React TypeScript</Badge>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-2">
              <Upload className="w-6 h-6 text-blue-600" />
            </div>
            <CardTitle className="text-lg">Load Binary</CardTitle>
            <CardDescription>
              Upload and analyze executable files
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
            <CardTitle className="text-lg">Ghidra Setup</CardTitle>
            <CardDescription>
              Setup Ghidra integration for decompilation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/settings">
              <Button variant="outline" className="w-full">
                Setup Ghidra
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
          Built with FastMCP 2.13+ • React TypeScript • Ghidra Plugin Integration
        </p>
      </div>
    </div>
  )
}