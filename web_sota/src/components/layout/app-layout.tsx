import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

// import { Toaster } from '@/components/ui/toaster';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();

  // Persist sidebar state
  useEffect(() => {
    const stored = localStorage.getItem("sidebar-collapsed");
    if (stored !== null) setCollapsed(stored === "true");
  }, []);

  // Fleet shortcuts: Ctrl+L Logs, Ctrl+H Help (inputs keep their keys).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!e.ctrlKey || e.shiftKey || e.altKey || e.metaKey) return;
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) return;
      if (e.key === "l" || e.key === "L") {
        e.preventDefault();
        navigate("/logs");
      } else if (e.key === "h" || e.key === "H") {
        e.preventDefault();
        navigate("/help");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navigate]);

  const handleToggle = () => {
    const newState = !collapsed;
    setCollapsed(newState);
    localStorage.setItem("sidebar-collapsed", String(newState));
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-50 font-sans selection:bg-emerald-500/30">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar collapsed={collapsed} onToggle={handleToggle} />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Topbar />
          <main className="flex-1 overflow-y-auto p-6 scroll-smooth">
            <div className="mx-auto max-w-7xl animate-in fade-in duration-500">
              {children}
            </div>
          </main>
        </div>
      </div>
      {/* <Toaster /> */}
    </div>
  );
}
