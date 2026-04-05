'use client'

import { useState, useEffect, useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Search, Loader2, FunctionSquare } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'

interface GhidraFunction {
  name: string
  address: string
  signature: string
  is_entry_point: boolean
}

interface GhidraFunctionListProps {
  onSelect: (functionName: string) => void
  selectedFunctionName?: string | null
}

export function GhidraFunctionList({ onSelect, selectedFunctionName }: GhidraFunctionListProps) {
  const [functions, setFunctions] = useState<GhidraFunction[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    const fetchFunctions = async () => {
      setLoading(true)
      try {
        const res = await fetch('http://localhost:10750/ghidra/functions')
        if (res.ok) {
          const data = await res.json()
          setFunctions(data.functions || [])
        }
      } catch (err) {
        console.error('Failed to fetch Ghidra functions:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchFunctions()
  }, [])

  const filteredFunctions = useMemo(() => {
    return functions.filter((f) => 
      f.name.toLowerCase().includes(search.toLowerCase()) || 
      f.address.toLowerCase().includes(search.toLowerCase())
    )
  }, [functions, search])

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <FunctionSquare className="w-5 h-5 text-blue-500" />
          <CardTitle>Functions</CardTitle>
        </div>
        <CardDescription>
          {loading ? 'Fetching function definitions...' : `Found ${functions.length} functions.`}
        </CardDescription>
        <div className="relative mt-2">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or address..."
            className="pl-8"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0 border-t">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Retrieving large function list...</p>
          </div>
        ) : filteredFunctions.length === 0 ? (
          <div className="flex items-center justify-center py-20 text-muted-foreground italic text-sm">
            {search ? 'No matches found.' : 'No functions available.'}
          </div>
        ) : (
          <ScrollArea className="h-full">
            <div className="p-2 space-y-1">
              {filteredFunctions.map((f) => (
                <button
                  key={`${f.address}-${f.name}`}
                  className={`w-full text-left px-3 py-2 rounded-md transition-colors flex items-center justify-between group ${
                    selectedFunctionName === f.name
                      ? 'bg-blue-500/10 text-blue-500 border border-blue-500/20'
                      : 'hover:bg-accent text-sm'
                  }`}
                  onClick={() => onSelect(f.name)}
                >
                  <div className="flex flex-col overflow-hidden">
                    <span className="font-mono font-medium truncate">{f.name}</span>
                    <span className="text-[10px] opacity-50 font-mono">{f.address}</span>
                  </div>
                  {f.is_entry_point && (
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500" title="Entry Point" />
                  )}
                </button>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}
