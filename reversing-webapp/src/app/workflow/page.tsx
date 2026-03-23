'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { GitBranch } from 'lucide-react'

export const dynamic = 'force-dynamic'

const REVERSED_APP_FLOWCHART = `
flowchart TD
  subgraph input["Input"]
    A[("Binary / Executable")]
  end

  subgraph loader["Loader (Webapp)"]
    B[Upload & validate]
    C[Select tools: Basic / PE / Ghidra]
    D[Run analysis pipeline]
  end

  subgraph static["Static analysis"]
    E[File metadata & type]
    F[Strings extraction]
    G[Entropy scan]
    H[PE/ELF parsing if applicable]
  end

  subgraph ghidra["Ghidra (optional)"]
    I[Import binary into project]
    J[Auto-analyze: symbols, xrefs]
    K[Decompile functions]
    L[Disassembly view]
  end

  subgraph annotate["Annotation & output"]
    M[Rename functions / labels]
    N[Add comments & bookmarks]
    O[Export: C pseudocode, report]
  end

  subgraph runtime["Runtime (optional)"]
    P[Frida script / hook targets]
    Q[Trace calls, patch in memory]
  end

  A --> B
  B --> C
  C --> D
  D --> E
  E --> F
  F --> G
  G --> H
  H --> I
  I --> J
  J --> K
  K --> L
  L --> M
  M --> N
  N --> O
  O -.->|"optional"| P
  P --> Q
`

export default function WorkflowPage() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const render = async () => {
      try {
        const mermaid = (await import('mermaid')).default
        mermaid.initialize({
          startOnLoad: false,
          theme: 'neutral',
          flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' }
        })
        const id = 'reversed-app-flowchart'
        const { svg } = await mermaid.render(id, REVERSED_APP_FLOWCHART)
        if (containerRef.current) {
          containerRef.current.innerHTML = svg
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to render diagram')
      }
    }

    render()
  }, [])

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/">
            <Button variant="outline" size="sm">Back to Home</Button>
          </Link>
        </div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <GitBranch className="w-6 h-6" />
          Reversed app workflow
        </h1>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>End-to-end reverse engineering flow</CardTitle>
          <CardDescription>
            From binary upload through static analysis, Ghidra decompilation, annotation, and optional runtime (Frida) steps. Follow the arrows; dashed line is optional.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            ref={containerRef}
            className="mermaid-container flex justify-center overflow-x-auto rounded-lg border bg-white p-4 min-h-[400px]"
          />
          {error && (
            <p className="text-destructive text-sm mt-2">{error}</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Legend</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm">
          <p><strong>Loader:</strong> Webapp Analyzer at <Link href="/loader" className="text-primary underline">/loader</Link> — upload binary, choose Basic / PE / Ghidra tools, then run.</p>
          <p><strong>Static:</strong> File type, strings, entropy, PE/ELF parsing (no Ghidra required).</p>
          <p><strong>Ghidra:</strong> Import, auto-analyze, decompile, disassembly (requires Ghidra + plugin).</p>
          <p><strong>Annotation:</strong> Rename symbols, add comments, export C or reports.</p>
          <p><strong>Runtime:</strong> Optional Frida scripting for live hooking and tracing.</p>
        </CardContent>
      </Card>
    </div>
  )
}
