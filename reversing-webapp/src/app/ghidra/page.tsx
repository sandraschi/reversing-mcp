'use client'

import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Code, ExternalLink, Server, Wrench } from 'lucide-react'

export const dynamic = 'force-dynamic'

export default function GhidraPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <Link href="/">
          <Button variant="outline" size="sm" className="mb-4">
            ← Back to Home
          </Button>
        </Link>
        <h1 className="text-3xl font-bold mb-2">Ghidra Integration</h1>
        <p className="text-muted-foreground mb-2">
          Professional decompilation and disassembly via the GhidraMCP plugin
        </p>
        <p className="text-sm text-muted-foreground/80 italic">
          NSA-grade binary archaeology. No agency endorsement implied.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 mb-8">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Server className="w-5 h-5 text-purple-500" />
              <CardTitle>How Reversing MCP Uses Ghidra</CardTitle>
            </div>
            <CardDescription>
              This server does not run or embed Ghidra. All ghidra_* tools talk to LaurieWired&apos;s
              <strong> GhidraMCP plugin</strong>, which runs inside Ghidra and exposes an HTTP API.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              <strong>Plugin URL (default):</strong>{' '}
              <code className="bg-muted px-1.5 py-0.5 rounded">http://127.0.0.1:8080/</code>
            </p>
            <p>
              You must have Ghidra running with a binary loaded and the GhidraMCP plugin server
              started. Then MCP tools (decompile, list functions, xrefs, etc.) send requests to
              that API.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Wrench className="w-5 h-5 text-green-500" />
              <CardTitle>Setup Steps</CardTitle>
            </div>
            <CardDescription>Get Ghidra tools working with this webapp and MCP</CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>Install Ghidra from ghidra-sre.org</li>
              <li>Install the GhidraMCP plugin (e.g. GhidraMCP.zip) into Ghidra</li>
              <li>Start Ghidra, create or open a project, import a binary, run analysis</li>
              <li>Start the GhidraMCP HTTP server from the plugin (default port 8080)</li>
              <li>Use ghidra_* MCP tools or this webapp; they will call the plugin</li>
            </ol>
            <p className="text-xs text-muted-foreground mt-3">
              For setup status and connectivity check, use the MCP tool <code>ghidra_setup_help()</code> in Claude/Cursor.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-amber-500" />
            <CardTitle>Headless</CardTitle>
          </div>
          <CardDescription>
            This integration requires the Ghidra GUI and the plugin. For headless (CI, batch, no display) use Ghidra&apos;s <code>analyzeHeadless</code> or a PyGhidra-based MCP (e.g. pyghidra-mcp). See <code>docs/GHIDRA.md</code> in the repo.
          </CardDescription>
        </CardHeader>
      </Card>

      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Code className="w-5 h-5 text-blue-500" />
            <CardTitle>Ghidra at a Glance</CardTitle>
          </div>
          <CardDescription>Open-source reverse engineering framework (NSA)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            Ghidra is a professional reverse engineering suite: decompiler, disassembler, and
            analysis engine. This project integrates with it via the community GhidraMCP plugin so
            you can drive Ghidra from natural language (MCP) and this web interface.
          </p>
          <div className="flex flex-wrap gap-2 mt-4">
            <Badge variant="secondary">Decompilation</Badge>
            <Badge variant="secondary">Disassembly</Badge>
            <Badge variant="secondary">90+ architectures</Badge>
            <Badge variant="secondary">HTTP API via plugin</Badge>
          </div>
          <Link
            href="https://ghidra-sre.org/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-primary hover:underline mt-4"
          >
            <ExternalLink className="w-4 h-4" />
            ghidra-sre.org
          </Link>
        </CardContent>
      </Card>

      <div className="flex gap-4">
        <Link href="/">
          <Button variant="outline">Home</Button>
        </Link>
        <Link href="/help">
          <Button variant="outline">Documentation</Button>
        </Link>
        <Link href="/settings">
          <Button>Settings</Button>
        </Link>
      </div>
    </div>
  )
}
