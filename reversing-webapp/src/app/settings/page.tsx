'use client'

import { useState, useEffect } from 'react'

// Force dynamic rendering
export const dynamic = 'force-dynamic'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { checkTools } from '@/lib/mcp/client'
import {
  Settings,
  Play,
  Square,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  Github,
  FileText,
  Download,
  Upload
} from 'lucide-react'

export default function SettingsPage() {
  const [toolsStatus, setToolsStatus] = useState<any>(null)
  const [isChecking, setIsChecking] = useState(false)
  const [ghidraStatus, setGhidraStatus] = useState<any>(null)
  const [isStartingGhidra, setIsStartingGhidra] = useState(false)

  const handleStartGhidra = async () => {
    setIsStartingGhidra(true)
    try {
      // Call the start Ghidra endpoint
      const response = await fetch('http://localhost:3001/start_ghidra', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })

      if (!response.ok) {
        throw new Error(`Failed to start Ghidra: ${response.statusText}`)
      }

      // Wait a moment for Ghidra to start
      setTimeout(async () => {
        await handleCheckStatus()
        setIsStartingGhidra(false)
      }, 3000)
    } catch (error) {
      console.error('Failed to start Ghidra:', error)
      setIsStartingGhidra(false)
      alert(`Failed to start Ghidra: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const handleCheckStatus = async () => {
    setIsChecking(true)
    try {
      const status = await checkTools()
      setToolsStatus(status)

      // Also check Ghidra status
      try {
        const response = await fetch('http://localhost:3001/ghidra/status')
        if (response.ok) {
          const ghidraData = await response.json()
          setGhidraStatus(ghidraData)
        }
      } catch (ghidraError) {
        console.warn('Failed to check Ghidra status:', ghidraError)
        setGhidraStatus({ available: false, error: 'Failed to check status' })
      }
    } catch (error) {
      console.error('Failed to check tools status:', error)
    } finally {
      setIsChecking(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Ghidra Setup & Status</h1>
        <p className="text-muted-foreground">
          Setup Ghidra integration, manage plugins, and monitor analysis capabilities
        </p>
      </div>

      {/* Status Overview */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            System Status
          </CardTitle>
          <CardDescription>
            Current status of MCP server and Ghidra integration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* MCP Server Status */}
            <div className="space-y-4">
              <h4 className="font-medium">MCP Server</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">FastMCP Server</span>
                  <Badge variant="default">Running</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Tools Loaded</span>
                  <Badge variant="secondary">25+ Ghidra Tools</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Version</span>
                  <span className="text-sm text-muted-foreground">2.14.1</span>
                </div>
              </div>
            </div>

            {/* Ghidra Status */}
            <div className="space-y-4">
              <h4 className="font-medium">Ghidra Integration</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Ghidra MCP</span>
                  {ghidraStatus?.available ? (
                    <Badge variant="default">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Available
                    </Badge>
                  ) : (
                    <Badge variant="destructive">
                      <XCircle className="w-3 h-3 mr-1" />
                      Unavailable
                    </Badge>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">HTTP Server</span>
                  {ghidraStatus?.http_server_running ? (
                    <Badge variant="default">Port {ghidraStatus.http_port || 8080}</Badge>
                  ) : (
                    <Badge variant="secondary">Not Running</Badge>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Plugin Version</span>
                  <span className="text-sm text-muted-foreground">1.2</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 mt-6">
            <Button onClick={handleCheckStatus} disabled={isChecking}>
              {isChecking ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Settings className="w-4 h-4 mr-2" />
              )}
              Check Status
            </Button>

            <Button
              onClick={handleStartGhidra}
              disabled={isStartingGhidra || ghidraStatus?.available}
              variant="outline"
            >
              {isStartingGhidra ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              Start Ghidra
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Ghidra Installation & Setup */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Ghidra Installation</CardTitle>
          <CardDescription>
            Install and configure Ghidra for MCP integration
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Installation Steps */}
          <div className="space-y-4">
            <h4 className="font-medium">Installation Steps</h4>

            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 border rounded-lg">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-blue-600">1</span>
                </div>
                <div>
                  <h5 className="font-medium">Download Ghidra</h5>
                  <p className="text-sm text-muted-foreground mb-2">
                    Download the latest Ghidra release from the official NSA website.
                  </p>
                  <Button variant="outline" size="sm" asChild>
                    <a
                      href="https://ghidra-sre.org/"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Github className="w-3 h-3 mr-1" />
                      Download Ghidra
                    </a>
                  </Button>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 border rounded-lg">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-blue-600">2</span>
                </div>
                <div>
                  <h5 className="font-medium">Install MCP Plugin</h5>
                  <p className="text-sm text-muted-foreground mb-2">
                    Install the GhidraMCP plugin to enable HTTP server functionality.
                  </p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled>
                      <Download className="w-3 h-3 mr-1" />
                      GhidraMCP.zip (Included)
                    </Button>
                    <Button variant="outline" size="sm" asChild>
                      <a
                        href="https://github.com/LaurieWired/GhidraMCP"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Github className="w-3 h-3 mr-1" />
                        Plugin Source
                      </a>
                    </Button>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 border rounded-lg">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-blue-600">3</span>
                </div>
                <div>
                  <h5 className="font-medium">Enable Plugin</h5>
                  <p className="text-sm text-muted-foreground">
                    In Ghidra: File → Configure → Developer → Enable GhidraMCP HTTP Server
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 border rounded-lg">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-blue-600">4</span>
                </div>
                <div>
                  <h5 className="font-medium">Start Ghidra</h5>
                  <p className="text-sm text-muted-foreground">
                    Launch Ghidra normally - the plugin will start the HTTP server automatically.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Plugin Details */}
          <div className="border-t pt-6">
            <h4 className="font-medium mb-4">Plugin Details</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Plugin Name:</span>
                  <span className="text-sm font-mono">GhidraMCP</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Version:</span>
                  <span className="text-sm">1.2</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">HTTP Port:</span>
                  <span className="text-sm">8080</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Endpoints:</span>
                  <span className="text-sm">25+ REST APIs</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Java Version:</span>
                  <span className="text-sm">Compatible</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">License:</span>
                  <span className="text-sm">Apache 2.0</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Settings */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Analysis Settings</CardTitle>
          <CardDescription>
            Configure default analysis options and behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Default Tools */}
          <div>
            <h4 className="font-medium mb-3">Default Analysis Tools</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[
                { name: 'File Analysis', enabled: true },
                { name: 'String Extraction', enabled: true },
                { name: 'Entropy Analysis', enabled: true },
                { name: 'PE Analysis', enabled: true },
                { name: 'Ghidra Decompilation', enabled: true },
                { name: 'Cross References', enabled: false },
              ].map((tool) => (
                <div key={tool.name} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id={tool.name.toLowerCase().replace(' ', '-')}
                    defaultChecked={tool.enabled}
                    className="rounded"
                  />
                  <label
                    htmlFor={tool.name.toLowerCase().replace(' ', '-')}
                    className="text-sm"
                  >
                    {tool.name}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Analysis Options */}
          <div>
            <h4 className="font-medium mb-3">Analysis Options</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Timeout (seconds)</label>
                  <p className="text-xs text-muted-foreground">Maximum analysis time per tool</p>
                </div>
                <input
                  type="number"
                  defaultValue={300}
                  className="w-20 px-2 py-1 border rounded text-sm"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">String Min Length</label>
                  <p className="text-xs text-muted-foreground">Minimum characters for string detection</p>
                </div>
                <input
                  type="number"
                  defaultValue={4}
                  className="w-20 px-2 py-1 border rounded text-sm"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Entropy Block Size</label>
                  <p className="text-xs text-muted-foreground">Bytes per entropy calculation block</p>
                </div>
                <input
                  type="number"
                  defaultValue={256}
                  className="w-20 px-2 py-1 border rounded text-sm"
                />
              </div>
            </div>
          </div>

          {/* Save Settings */}
          <div className="flex justify-end pt-4 border-t">
            <Button>
              <Settings className="w-4 h-4 mr-2" />
              Save Settings
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Advanced Configuration</CardTitle>
          <CardDescription>
            Expert settings for power users and custom deployments
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* MCP Server Config */}
          <div>
            <h4 className="font-medium mb-3">MCP Server Configuration</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Server Host</label>
                  <p className="text-xs text-muted-foreground">MCP server bind address</p>
                </div>
                <input
                  type="text"
                  defaultValue="localhost"
                  className="w-32 px-2 py-1 border rounded text-sm"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Server Port</label>
                  <p className="text-xs text-muted-foreground">MCP server port</p>
                </div>
                <input
                  type="number"
                  defaultValue={3001}
                  className="w-20 px-2 py-1 border rounded text-sm"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Ghidra Host</label>
                  <p className="text-xs text-muted-foreground">Ghidra HTTP server address</p>
                </div>
                <input
                  type="text"
                  defaultValue="127.0.0.1"
                  className="w-32 px-2 py-1 border rounded text-sm"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Ghidra Port</label>
                  <p className="text-xs text-muted-foreground">Ghidra HTTP server port</p>
                </div>
                <input
                  type="number"
                  defaultValue={8080}
                  className="w-20 px-2 py-1 border rounded text-sm"
                />
              </div>
            </div>
          </div>

          {/* Danger Zone */}
          <div className="border-t pt-6">
            <h4 className="font-medium mb-3 text-red-600">Danger Zone</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 border border-red-200 rounded-lg">
                <div>
                  <h5 className="font-medium text-red-600">Reset Configuration</h5>
                  <p className="text-sm text-muted-foreground">
                    Reset all settings to default values
                  </p>
                </div>
                <Button variant="destructive" size="sm">
                  Reset
                </Button>
              </div>

              <div className="flex items-center justify-between p-3 border border-red-200 rounded-lg">
                <div>
                  <h5 className="font-medium text-red-600">Clear Cache</h5>
                  <p className="text-sm text-muted-foreground">
                    Clear all cached analysis results
                  </p>
                </div>
                <Button variant="destructive" size="sm">
                  Clear Cache
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}