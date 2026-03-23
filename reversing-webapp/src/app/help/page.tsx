'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  FileText,
  Search,
  Settings,
  Cpu,
  Code,
  Shield,
  Github,
  Book,
  HelpCircle,
  Zap,
  Target
} from 'lucide-react'
import Link from 'next/link'

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function HelpPage() {
  const [activeTab, setActiveTab] = useState('getting-started')

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <Link href="/">
            <Button variant="outline" size="sm">
              ← Back to Home
            </Button>
          </Link>
          <h1 className="text-3xl font-bold">Documentation & Help</h1>
        </div>
        <p className="text-muted-foreground">
          Complete guide to using Reversing MCP for professional binary analysis
        </p>
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 mt-4">
          <p className="text-sm text-slate-700 font-medium mb-2">
            💡 <strong>Reverse Engineering Ethics:</strong> This toolkit serves defensive security (malware analysis), digital preservation (reviving old software), and research purposes.
          </p>
          <div className="text-xs text-slate-600 space-y-1">
            <div>• <strong>✅ Permitted:</strong> Security research, malware analysis, software preservation, education</div>
            <div>• <strong>📚 Example (Planned):</strong> Our Directmedia-MCP project will reverse engineer the DKI format to preserve philosophical texts from bankrupt vendor&#39;s abandoned software. <em>Note: Application reverse engineering may be simpler than data format cracking which involves copyrighted content. Current repo has mock tools (get_toc, export_book, etc.) that will be replaced with real implementations.</em></div>
            <div>• <strong>❌ Prohibited:</strong> Software cracking, IP theft, unauthorized testing</div>
            <div className="font-medium mt-1">Always ensure compliance with applicable laws and licenses. <em>Note: Even defunct vendors&#39; software remains protected by copyright.</em></div>
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="getting-started">Getting Started</TabsTrigger>
          <TabsTrigger value="analysis">Analysis Tools</TabsTrigger>
          <TabsTrigger value="ghidra">Ghidra Setup</TabsTrigger>
          <TabsTrigger value="troubleshooting">Troubleshooting</TabsTrigger>
        </TabsList>

        <TabsContent value="getting-started" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Quick Start Guide
              </CardTitle>
              <CardDescription>
                Get up and running with Reversing MCP in minutes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-blue-800 font-medium">
                  🔍 <strong>Note:</strong> This webapp focuses on static analysis (strings, entropy,
                  PE). For decompilation and xrefs, add <strong>ReVa</strong> MCP in Cursor or
                  Claude and use Ghidra there.
                </p>
              </div>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="mt-0.5">1</Badge>
                  <div>
                    <h4 className="font-semibold">Launch the Webapp</h4>
                    <p className="text-sm text-muted-foreground">
                      Run <code className="bg-muted px-1 py-0.5 rounded">.\start-webapp.ps1</code> to start both frontend and backend servers.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="mt-0.5">2</Badge>
                  <div>
                    <h4 className="font-semibold">Upload a Binary</h4>
                    <p className="text-sm text-muted-foreground">
                      Click "Load Binary" and select an executable file (.exe, .dll) for analysis.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="mt-0.5">3</Badge>
                  <div>
                    <h4 className="font-semibold">Setup Ghidra (ReVa MCP)</h4>
                    <p className="text-sm text-muted-foreground">
                      <strong>For decompilation:</strong> Install Ghidra, add the ReVa extension,
                      then register ReVa in your MCP client. This webapp does not proxy Ghidra MCP.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="mt-0.5">4</Badge>
                  <div>
                    <h4 className="font-semibold">Analyze & Review</h4>
                    <p className="text-sm text-muted-foreground">
                      View comprehensive analysis results: strings, entropy, PE structure, and Ghidra-powered decompilation.
                    </p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  See the <Link href="/workflow" className="text-primary underline">Reversed app workflow</Link> flowchart for the full pipeline (loader, static, Ghidra, annotation, optional Frida).
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                What You Can Analyze
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">Supported File Types</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Windows Executables (.exe, .dll)</li>
                    <li>• Linux Binaries (ELF)</li>
                    <li>• Raw Binaries</li>
                    <li>• Firmware Images</li>
                    <li className="text-orange-600 font-medium">• <strong>Note:</strong> Focus on Ghidra-powered analysis. IDA Pro's monopoly was destroyed by NSA's Ghidra release - no excuse for $3,000+ pricing anymore</li>
                  </ul>
                </div>

                <div className="space-y-2">
                  <h4 className="font-semibold text-sm">Analysis Types</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Static Analysis</li>
                    <li>• String Extraction</li>
                    <li>• Entropy Analysis</li>
                    <li>• PE File Parsing</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Analysis Tools Overview</CardTitle>
              <CardDescription>
                Professional reverse engineering tools available in Reversing MCP
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <FileText className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold">File Analysis</h4>
                      <p className="text-sm text-muted-foreground">Detect file types, permissions, metadata</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <Search className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold">String Extraction</h4>
                      <p className="text-sm text-muted-foreground">Find printable strings in binaries</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                      <Shield className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold">Entropy Analysis</h4>
                      <p className="text-sm text-muted-foreground">Detect compression and encryption</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                      <Cpu className="w-5 h-5 text-orange-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold">PE File Analysis</h4>
                      <p className="text-sm text-muted-foreground">Windows executable structure analysis</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                      <Code className="w-5 h-5 text-red-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold">Ghidra Integration</h4>
                      <p className="text-sm text-muted-foreground">Professional decompilation and disassembly</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                      <Zap className="w-5 h-5 text-yellow-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold">Directmedia Decompression</h4>
                      <p className="text-sm text-muted-foreground">Extract text from 1990s e-book formats</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ghidra" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Ghidra Integration Setup</CardTitle>
              <CardDescription>
                Enable professional-grade reverse engineering with NSA's Ghidra
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <h4 className="font-semibold mb-2 text-orange-800">🐉 Ghidra via ReVa MCP</h4>
                <p className="text-sm text-orange-800">
                  <strong>Static analysis</strong> runs in this webapp and the core reversing-mcp
                  server. <strong>Interactive Ghidra</strong> (decompile, xrefs, rename) is provided
                  by the separate <strong>ReVa</strong> MCP server in your IDE — not the old
                  LaurieWired HTTP bridge.
                </p>
                <p className="text-sm text-orange-800 mt-2">
                  <strong>Why Ghidra over IDA Pro?</strong> The NSA destroyed IDA Pro's monopoly in 2019. IDA Pro's $3,000+ pricing was somewhat understandable when it had no competition, but Ghidra provides 95%+ of IDA Pro's functionality for FREE. IDA Pro now requires torrent downloads of cracked versions (security risks, malware, legal issues).
                </p>
                <p className="text-sm text-orange-800 mt-2">
                  <strong>The monopoly is permanently broken.</strong> Thanks to the NSA, professional reverse engineering is now accessible to everyone, not just those willing to pay extortionate prices or risk malware infections.
                </p>
              </div>

              <div className="bg-muted p-4 rounded-lg">
                <h4 className="font-semibold mb-2 text-orange-600">⚠️ Architecture</h4>
                <p className="text-sm">
                  The LaurieWired <code>bridge_mcp_ghidra.py</code> integration was removed. Use{' '}
                  <strong>ReVa</strong> (<code>reverse-engineering-assistant</code>) for Ghidra MCP.
                  See <code>docs/GHIDRA.md</code> in the repo.
                </p>
              </div>

              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <Badge variant="outline">1</Badge>
                  <div>
                    <h4 className="font-semibold">Install Ghidra</h4>
                    <p className="text-sm text-muted-foreground">
                      Download from <a href="https://ghidra-sre.org" className="text-blue-600 hover:underline">ghidra-sre.org</a>
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Badge variant="outline">2</Badge>
                  <div>
                    <h4 className="font-semibold">Install ReVa extension</h4>
                    <p className="text-sm text-muted-foreground">
                      Download the release zip that matches your Ghidra version from the ReVa GitHub
                      releases; install via File → Install Extensions.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Badge variant="outline">3</Badge>
                  <div>
                    <h4 className="font-semibold">Add ReVa to your MCP client</h4>
                    <p className="text-sm text-muted-foreground">
                      Configure streamable HTTP or <code>mcp-reva</code> (Ghidra 12+) in Cursor or
                      Claude Desktop.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Badge variant="outline">4</Badge>
                  <div>
                    <h4 className="font-semibold">Load binary in Ghidra</h4>
                    <p className="text-sm text-muted-foreground">
                      Open your program in Ghidra, then use ReVa tools from the IDE.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="troubleshooting" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Common Issues & Solutions</CardTitle>
              <CardDescription>
                Fix common problems with Reversing MCP
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div className="border-l-4 border-red-500 pl-4">
                  <h4 className="font-semibold text-red-600">Webapp Shows White Screen</h4>
                  <p className="text-sm text-muted-foreground mb-2">
                    Frontend routes not working (like /results or /help)
                  </p>
                  <p className="text-sm">
                    <strong>Solution:</strong> These pages have been created. Try refreshing the page or restart the webapp.
                  </p>
                </div>

                <div className="border-l-4 border-orange-500 pl-4">
                  <h4 className="font-semibold text-orange-600">No decompilation in the browser</h4>
                  <p className="text-sm text-muted-foreground mb-2">
                    The webapp does not call Ghidra for decompilation.
                  </p>
                  <p className="text-sm">
                    <strong>Solution:</strong> Install Ghidra + ReVa, add ReVa to your MCP client,
                    and analyze from Cursor or Claude. Use this site for static metadata and strings.
                  </p>
                </div>

                <div className="border-l-4 border-blue-500 pl-4">
                  <h4 className="font-semibold text-blue-600">Analysis Takes Too Long</h4>
                  <p className="text-sm text-muted-foreground mb-2">
                    File analysis seems to hang or takes very long
                  </p>
                  <p className="text-sm">
                    <strong>Solution:</strong> Large files may take time. Try smaller test files first (under 10MB).
                  </p>
                </div>

                <div className="border-l-4 border-green-500 pl-4">
                  <h4 className="font-semibold text-green-600">Cannot Upload Files</h4>
                  <p className="text-sm text-muted-foreground mb-2">
                    File upload fails or shows errors
                  </p>
                  <p className="text-sm">
                    <strong>Solution:</strong> Ensure backend server is running on port 11112 and check browser console for errors.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Getting Help</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Github className="w-5 h-5 text-gray-600" />
                  <div>
                    <h4 className="font-semibold">GitHub Issues</h4>
                    <p className="text-sm text-muted-foreground">
                      Report bugs and request features on GitHub
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Book className="w-5 h-5 text-gray-600" />
                  <div>
                    <h4 className="font-semibold">Documentation</h4>
                    <p className="text-sm text-muted-foreground">
                      Check the README.md and GHIDRA_PLUGIN_SETUP.md files
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <HelpCircle className="w-5 h-5 text-gray-600" />
                  <div>
                    <h4 className="font-semibold">Command Line Help</h4>
                    <p className="text-sm text-muted-foreground">
                      Run <code className="bg-muted px-1 py-0.5 rounded">python -m reversing_mcp.server --help</code>
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="mt-8 text-center text-muted-foreground">
        <p className="text-sm">
          Built with FastMCP 2.13+ • React TypeScript • Ghidra Plugin Integration
        </p>
      </div>
    </div>
  )
}