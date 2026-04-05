'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, Loader2, RefreshCw, Server } from 'lucide-react'

interface GhidraInstance {
  id: string
  name: string
  mode: 'tcp' | 'uds'
  status: 'online' | 'offline'
}

interface GhidraInstancePickerProps {
  onConnect: (instanceId: string) => void
  connectedInstanceId?: string | null
}

export function GhidraInstancePicker({ onConnect, connectedInstanceId }: GhidraInstancePickerProps) {
  const [instances, setInstances] = useState<GhidraInstance[]>([])
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState<string | null>(null)

  const fetchInstances = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:10750/ghidra/instances')
      if (res.ok) {
        const data = await res.json()
        setInstances(data.instances || [])
      }
    } catch (err) {
      console.error('Failed to fetch Ghidra instances:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInstances()
  }, [])

  const handleConnect = async (instanceId: string) => {
    setConnecting(instanceId)
    try {
      const res = await fetch('http://localhost:10750/ghidra/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instance_id: instanceId })
      })
      if (res.ok) {
        onConnect(instanceId)
      }
    } catch (err) {
      console.error('Connect failed:', err)
    } finally {
      setConnecting(null)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-purple-500" />
            <CardTitle>Ghidra Instances</CardTitle>
          </div>
          <Button variant="ghost" size="icon" onClick={fetchInstances} disabled={loading}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <CardDescription>
          Select a running Ghidra process to begin analysis.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center py-6">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : instances.length === 0 ? (
          <p className="text-sm text-center py-4 text-muted-foreground">
            No active Ghidra instances found. Make sure Ghidra is running and the bridge plugin is started.
          </p>
        ) : (
          <div className="space-y-2">
            {instances.map((instance) => (
              <div
                key={instance.id}
                className={`flex items-center justify-between p-3 rounded-lg border bg-card/50 transition-colors ${
                  connectedInstanceId === instance.id ? 'border-purple-500/50 bg-purple-500/5' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${instance.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
                  <div>
                    <p className="text-sm font-medium">{instance.name}</p>
                    <p className="text-xs text-muted-foreground">ID: {instance.id} ({instance.mode.toUpperCase()})</p>
                  </div>
                </div>
                {connectedInstanceId === instance.id ? (
                  <Badge variant="outline" className="text-purple-500 border-purple-500/50 bg-purple-500/10 gap-1">
                    <Check className="w-3 h-3" /> Connected
                  </Badge>
                ) : (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleConnect(instance.id)}
                    disabled={!!connecting}
                  >
                    {connecting === instance.id ? (
                      <Loader2 className="w-3 h-3 animate-spin mr-2" />
                    ) : null}
                    Connect
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
