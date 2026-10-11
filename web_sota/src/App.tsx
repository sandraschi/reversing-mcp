import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { useZoom } from "@/hooks/useZoom";
import { Analyze } from "@/pages/analyze";
import { Apps } from "@/pages/apps";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { DigiBib } from "@/pages/digibib";
import { Help } from "@/pages/help";
import { Inbox } from "@/pages/inbox";
import Logging from "@/pages/Logging";
import { Settings } from "@/pages/settings";
import { Skills } from "@/pages/skills";
import { Status } from "@/pages/status";
import { Tools } from "@/pages/tools";

function App() {
  const { zoom, reset } = useZoom();
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/digibib" element={<DigiBib />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/status" element={<Status />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/help" element={<Help />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/logs" element={<Logging />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <button
          type="button"
          onClick={reset}
          title="Reset zoom (Ctrl+0). Ctrl+Scroll zooms."
          className="fixed bottom-2 right-2 z-50 rounded bg-slate-900/90 border border-slate-800 px-2 py-0.5 text-sm text-slate-400 hover:text-slate-200"
        >
          {Math.round(zoom * 100)}%
        </button>
      </AppLayout>
    </Router>
  );
}

export default App;
