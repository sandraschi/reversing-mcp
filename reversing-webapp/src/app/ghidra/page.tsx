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
        <h1 className="text-3xl font-bold mb-2">Ghidra + ReVa MCP</h1>
        <p className="text-muted-foreground mb-2">
          Decompilation and listings run through ReVa in your MCP client, not this webapp
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
              <CardTitle>How this fits together</CardTitle>
            </div>
            <CardDescription>
              <strong>reversing-mcp</strong> (this repo) exposes static analysis and Directmedia
              tools. <strong>ReVa</strong> (reverse-engineering-assistant) exposes Ghidra as MCP.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              Add ReVa to <strong>Cursor</strong> or <strong>Claude Desktop</strong>. Use assistant
              mode (Ghidra GUI + extension) or <code className="bg-muted px-1 rounded">mcp-reva</code>{' '}
              headless on Ghidra 12+ per ReVa docs.
            </p>
            <p>
              The Next.js webapp talks to the FastAPI backend for uploads and static metrics only; it
              does not proxy Ghidra MCP.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Wrench className="w-5 h-5 text-green-500" />
              <CardTitle>Setup (short)</CardTitle>
            </div>
            <CardDescription>Install Ghidra, ReVa, then wire MCP</CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>Install Ghidra from ghidra-sre.org</li>
              <li>Install ReVa extension zip matching your Ghidra version</li>
              <li>Register ReVa in your MCP client (see docs/GHIDRA.md in the repo)</li>
              <li>Use ReVa tools from the IDE; use this webapp for strings / entropy / PE</li>
            </ol>
            <p className="text-xs text-muted-foreground mt-3">
              Legacy LaurieWired GhidraMCP + <code>bridge_mcp_ghidra.py</code> were removed from
              reversing-mcp.
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
            For batch analysis without the GUI, use Ghidra&apos;s{' '}
            <code className="bg-muted px-1 rounded">analyzeHeadless</code> or ReVa headless mode when
            supported. See <code>docs/GHIDRA.md</code>.
          </CardDescription>
        </CardHeader>
      </Card>

      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Code className="w-5 h-5 text-blue-500" />
            <CardTitle>Ghidra at a glance</CardTitle>
          </div>
          <CardDescription>Open-source reverse engineering framework (NSA)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            Ghidra is a professional reverse engineering suite: decompiler, disassembler, and
            analysis engine. ReVa turns that into MCP tools for agents; this project no longer
            bundles the old HTTP plugin bridge.
          </p>
          <div className="flex flex-wrap gap-2 mt-4">
            <Badge variant="secondary">Decompilation</Badge>
            <Badge variant="secondary">Disassembly</Badge>
            <Badge variant="secondary">90+ architectures</Badge>
            <Badge variant="secondary">MCP via ReVa</Badge>
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
