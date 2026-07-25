import { AppLayout } from "@/components/layout/app-layout";
import Logging from "@/pages/Logging";
import { Analyze } from "@/pages/analyze";
import { Apps } from "@/pages/apps";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { DigiBib } from "@/pages/digibib";
import { Help } from "@/pages/help";
import { Settings } from "@/pages/settings";
import { Status } from "@/pages/status";
import { Tools } from "@/pages/tools";
import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/digibib" element={<DigiBib />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/status" element={<Status />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/help" element={<Help />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/logs" element={<Logging />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
