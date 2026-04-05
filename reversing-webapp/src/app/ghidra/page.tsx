'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  ArrowLeft, 
  Binary, 
  CloudOff, 
  Cpu, 
  ExternalLink, 
  Info, 
  Layers, 
  Network, 
  Settings, 
  ShieldCheck, 
  Zap 
} from 'lucide-react'
import { GhidraInstancePicker } from '@/components/ghidra/GhidraInstancePicker'
import { GhidraFunctionList } from '@/components/ghidra/GhidraFunctionList'
import { GhidraDecompilerView } from '@/components/ghidra/GhidraDecompilerView'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

export default function GhidraPage() {
  const [status, setStatus] = useState<any>(null)
  const [connectedInstance, setConnectedInstance] = useState<string | null>(null)
  const [selectedFunctionName, setSelectedFunctionName] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:10750/ghidra/status')
      if (res.ok) {
        const data = await res.json()
        setStatus(data)
        if (data.connected_instance) {
          setConnectedInstance(data.connected_instance)
        }
      }
    } catch (err) {
      console.error('Failed to fetch Ghidra status:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const handleConnect = (instanceId: string) => {
    setConnectedInstance(instanceId)
    // Refresh status to confirm connection
    fetchStatus()
  }

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="border-b bg-white dark:bg-slate-900 sticky top-0 z-30">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <Zap className="h-6 w-6 text-yellow-500 fill-yellow-500" />
              <h1 className="text-xl font-bold tracking-tight">Ghidra Explorer</h1>
              <Badge variant="outline" className="ml-2 bg-blue-500/5 text-blue-500 border-blue-500/20">
                PRO BRIDGE
              </Badge>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {status?.bridge_running ? (
              <Badge variant="secondary" className="bg-green-500/10 text-green-500 border-green-500/20 gap-1.5 py-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Bridge Active
              </Badge>
            ) : (
              <Badge variant="destructive" className="gap-1.5 py-1">
                <CloudOff className="w-3.5 h-3.5" /> Bridge Offline
              </Badge>
            )}
            <Link href="/settings">
              <Button variant="ghost" size="icon">
                <Settings className="h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-4 py-6">
        {!status?.bridge_running && !loading ? (
          <div className="max-w-2xl mx-auto space-y-6 py-12">
            <Alert variant="destructive" className="border-2">
              <Info className="h-4 w-4" />
              <AlertTitle>Ghidra Bridge Connection Failed</AlertTitle>
              <AlertDescription>
                The WebApp could not establish a connection to the Ghidra MCP bridge on port 8089. 
                Please ensure the <code>ghidra-mcp</code> server is running.
              </AlertDescription>
            </Alert>
            
            <Card className="border-slate-200 dark:border-slate-800">
              <CardHeader>
                <CardTitle>How to start the bridge</CardTitle>
                <CardDescription>Follow these steps to enable live reversing</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="p-4 rounded-xl border bg-card/50 flex flex-col gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 font-bold mb-1">1</div>
                    <p className="text-sm font-semibold">Start Ghidra</p>
                    <p className="text-xs text-muted-foreground">Open your Ghidra project and open the CodeBrowser tool.</p>
                  </div>
                  <div className="p-4 rounded-xl border bg-card/50 flex flex-col gap-2">
                    <div className="w-8 h-8 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-500 font-bold mb-1">2</div>
                    <p className="text-sm font-semibold">Start MCP Bridge</p>
                    <p className="text-xs text-muted-foreground">In Ghidra, go to <code>Window -> MCP Bridge</code> and click "Start Server".</p>
                  </div>
                </div>
                <Button className="w-full mt-4" onClick={fetchStatus} disabled={loading}>
                  {loading ? 'Retrying...' : 'Check Bridge Connection Again'}
                </Button>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="grid grid-cols-12 gap-6 h-[calc(100vh-180px)]">
            {/* Sidebar: Instances & Functions */}
            <div className="col-span-12 lg:col-span-4 space-y-6 overflow-y-auto pr-2 custom-scrollbar">
              <GhidraInstancePicker 
                onConnect={handleConnect} 
                connectedInstanceId={connectedInstance} 
              />
              
              {connectedInstance ? (
                <GhidraFunctionList 
                  onSelect={setSelectedFunctionName} 
                  selectedFunctionName={selectedFunctionName} 
                />
              ) : (
                <Card className="border-dashed flex items-center justify-center p-12 text-center text-muted-foreground">
                  <div className="space-y-3">
                    <Network className="w-8 h-8 mx-auto opacity-20" />
                    <p className="text-sm font-medium">Connect to an instance to see functions.</p>
                  </div>
                </Card>
              )}
            </div>

            {/* Main Content: Decompiler */}
            <div className="col-span-12 lg:col-span-8 flex flex-col">
              <GhidraDecompilerView functionName={selectedFunctionName} />
            </div>
          </div>
        )}
      </main>

      {/* Footer Info */}
      <footer className="border-t bg-white dark:bg-slate-900 py-3 mt-auto">
        <div className="container mx-auto px-4 flex items-center justify-between text-[11px] text-muted-foreground uppercase tracking-widest font-semibold">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1"><Cpu className="w-3 h-3 text-blue-500" /> SOTA Reverse Engine</span>
            <span className="flex items-center gap-1"><Layers className="w-3 h-3 text-purple-500" /> Layered Analysis</span>
          </div>
          <div className="flex items-center gap-4">
             <span className="flex items-center gap-1 group cursor-pointer hover:text-white transition-colors">
               <Binary className="w-3 h-3" /> Artifact Verification
             </span>
             <Link href="https://ghidra-sre.org" target="_blank" className="flex items-center gap-1 hover:text-white transition-colors">
               Documentation <ExternalLink className="w-2.5 h-2.5" />
             </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
