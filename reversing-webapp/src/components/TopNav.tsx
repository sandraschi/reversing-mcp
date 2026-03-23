'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Upload, MessageSquare, Settings, FileText, Code, Wrench, HelpCircle, GitBranch } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV = [
  { href: '/', label: 'Home' },
  { href: '/loader', label: 'Analyze' },
  { href: '/results', label: 'Results' },
  { href: '/chat', label: 'Chat' },
  { href: '/ghidra', label: 'Ghidra' },
  { href: '/settings', label: 'Settings' },
  { href: '/workflow', label: 'Workflow' },
  { href: '/help', label: 'Help' },
] as const

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  '/': undefined,
  '/loader': Upload,
  '/results': FileText,
  '/chat': MessageSquare,
  '/ghidra': Code,
  '/settings': Settings,
  '/workflow': GitBranch,
  '/help': HelpCircle,
}

export function TopNav() {
  const pathname = usePathname()

  return (
    <nav className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2">
        <Link href="/" className="font-semibold text-foreground hover:underline">
          Reversing MCP
        </Link>
        <span className="text-muted-foreground">|</span>
        {NAV.filter(({ href }) => href !== '/').map(({ href, label }) => {
          const Icon = ICONS[href]
          const active = pathname === href || (href !== '/' && pathname.startsWith(href))
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-1.5 rounded px-2 py-1 text-sm',
                active ? 'bg-muted font-medium' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {Icon && <Icon className="h-4 w-4" />}
              {label}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
