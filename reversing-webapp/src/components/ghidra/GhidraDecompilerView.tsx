'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Loader2, Code2, Copy, Terminal, ScrollText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

interface DecompilerResponse {
  function_name: string
  decompiled_code: string
  status: string
  error?: string
}

interface GhidraDecompilerViewProps {
  functionName: string | null
}

export function GhidraDecompilerView({ functionName }: GhidraDecompilerViewProps) {
  const [decompiledCode, setDecompiledCode] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!functionName) return

    const decompile = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`http://localhost:10750/ghidra/decompile?function_name=${encodeURIComponent(functionName)}`, {
          method: 'POST'
        })
        if (res.ok) {
          const data = await res.json()
          setDecompiledCode(data.decompiled_code)
        } else {
          const err = await res.json()
          setError(err.detail || 'Decompilation failed.')
        }
      } catch (err) {
        setError('Network error: Could not reach the API backend.')
      } finally {
        setLoading(false)
      }
    }

    decompile()
  }, [functionName])

  const copyToClipboard = () => {
    if (decompiledCode) {
      navigator.clipboard.writeText(decompiledCode)
    }
  }

  if (!functionName) {
    return (
      <Card className="h-full flex items-center justify-center border-dashed bg-muted/20">
        <div className="text-center p-8 flex flex-col items-center gap-4">
          <Terminal className="w-12 h-12 text-muted-foreground opacity-30" />
          <p className="text-muted-foreground">Select a function from the list to view decompiled code.</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="h-full flex flex-col bg-slate-950 text-slate-50 border-slate-800">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 py-3 px-4 border-b border-white/5">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-blue-400" />
            <CardTitle className="text-base font-mono">{functionName}</CardTitle>
          </div>
          <CardDescription className="text-xs text-slate-400">
            Decompiled C Code (Ghidra engine)
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          {loading && (
            <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-none animate-pulse">
              <Loader2 className="w-3 h-3 animate-spin mr-2" />
              Decompiling...
            </Badge>
          )}
          <Button variant="ghost" size="icon" onClick={copyToClipboard} className="h-8 w-8 hover:bg-slate-800">
            <Copy className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0 overflow-hidden relative">
        {error ? (
          <div className="flex items-center justify-center h-full text-red-400 text-sm p-4 text-center">
            {error}
          </div>
        ) : (
          <ScrollArea className="h-full w-full">
            <div className="p-4 bg-transparent font-mono text-[13px] leading-relaxed whitespace-pre">
              {decompiledCode || (loading ? 'Loading...' : '')}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}
