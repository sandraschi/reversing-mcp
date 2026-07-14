import { getApiBase } from "@/common/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Bot, Download, Loader2, Send, Trash2, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const LS_KEY = "reversing-mcp-chat-history";
const PERS_KEY = "reversing-mcp-chat-personality";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const PERSONALITIES = [
  {
    id: "binary-analyst",
    label: "Binary Analyst",
    prompt: "You are a binary analysis expert. Use precise technical language.",
  },
  {
    id: "ghidra-specialist",
    label: "Ghidra Specialist",
    prompt: "You specialise in Ghidra workflows and decompilation.",
  },
  {
    id: "quick-summarizer",
    label: "Quick Summarizer",
    prompt: "Keep responses brief and to the point.",
  },
  { id: "custom", label: "Custom", prompt: "" },
];

const EXAMPLE_PROMPTS = [
  {
    group: "Analysis",
    items: [
      "Analyse this ELF binary's sections",
      "Find string references in a PE file",
      "Decompile function at address 0x401000",
    ],
  },
  {
    group: "Ghidra",
    items: [
      "How to set up Ghidra headless?",
      "Export decompiled code from Ghidra",
      "Run a Ghidra script on a binary",
    ],
  },
  {
    group: "Patterns",
    items: [
      "Identify obfuscated control flow",
      "Find hardcoded crypto keys",
      "Trace API calls in a malware sample",
    ],
  },
];

function loadHistory(): Message[] {
  try {
    const d = localStorage.getItem(LS_KEY);
    return d ? JSON.parse(d) : [];
  } catch {
    return [];
  }
}
function saveHistory(msgs: Message[]) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(msgs.slice(-100)));
  } catch {}
}
function loadPersonality(): string {
  try {
    return localStorage.getItem(PERS_KEY) || "binary-analyst";
  } catch {
    return "binary-analyst";
  }
}

const INITIAL_MSG: Message = {
  id: "0",
  role: "assistant",
  content:
    "Reversing assistant. I can help with binary analysis and Ghidra. Pick a model in Settings (Ollama) and ask.",
};

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    const h = loadHistory();
    return h.length > 0 ? h : [INITIAL_MSG];
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [personalityId, setPersonalityId] = useState(() => loadPersonality());
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  useEffect(() => {
    saveHistory(messages);
  }, [messages]);
  useEffect(() => {
    localStorage.setItem(PERS_KEY, personalityId);
  }, [personalityId]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    const userMsg: Message = {
      id: String(Date.now()),
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
          personality: personalityId,
        }),
      });
      const data = await res.json().catch(() => ({}));
      const reply =
        data?.reply ??
        "Backend or Ollama not reachable. Check Settings and run the backend (e.g. start-webapp.ps1).";
      setMessages((prev) => [
        ...prev,
        { id: String(Date.now() + 1), role: "assistant", content: reply },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          role: "assistant",
          content: "Request failed. Is the backend running?",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const exportChat = () => {
    const text = messages
      .map((m) => `${m.role === "user" ? "You" : "Assistant"}: ${m.content}`)
      .join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reversing-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className="flex h-[calc(100vh-8rem)] flex-col space-y-4"
      data-testid="chat-page"
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-white">
              AI Command
            </h2>
            <span
              className="text-xs text-blue-400 bg-blue-900/30 px-2 py-0.5 rounded border border-blue-800/50"
              data-testid="skill-badge"
            >
              reversing-mcp
            </span>
          </div>
          <p className="text-slate-400">Ollama chat (set model in Settings)</p>
        </div>
        <div className="flex items-center gap-2" data-testid="chat-controls">
          <span
            className={`inline-block w-2 h-2 rounded-full bg-green-500`}
            data-testid="backend-dot"
          />
          <select
            value={personalityId}
            onChange={(e) => setPersonalityId(e.target.value)}
            className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-200"
            data-testid="personality-select"
          >
            {PERSONALITIES.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={exportChat}
            disabled={messages.length === 0}
            className="h-8 text-xs gap-1"
            data-testid="chat-export"
          >
            <Download className="h-3 w-3" /> Export
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setMessages([INITIAL_MSG])}
            disabled={messages.length <= 1}
            className="h-8 text-xs gap-1 text-red-400 border-red-900/30 hover:bg-red-950/20"
            data-testid="chat-clear"
          >
            <Trash2 className="h-3 w-3" /> Clear
          </Button>
        </div>
      </div>

      <Card
        className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden"
        data-testid="dashboard"
      >
        <CardContent
          className="flex-1 overflow-y-auto p-4 space-y-4"
          data-testid="chat-messages"
        >
          {messages.map((m) => (
            <div key={m.id} className="flex gap-3">
              <div
                className={`h-8 w-8 shrink-0 rounded-full flex items-center justify-center border ${m.role === "user" ? "bg-slate-800 border-slate-700" : "bg-blue-900/20 border-blue-800"}`}
              >
                {m.role === "user" ? (
                  <User className="h-4 w-4 text-slate-400" />
                ) : (
                  <Bot className="h-4 w-4 text-blue-400" />
                )}
              </div>
              <div className="flex-1 space-y-1 min-w-0">
                <span className="text-sm font-medium text-slate-200">
                  {m.role === "user" ? "You" : "Assistant"}
                </span>
                <p className="text-sm text-slate-300 whitespace-pre-wrap break-words">
                  {m.content}
                </p>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-blue-900/20 border border-blue-800 flex items-center justify-center">
                <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />
              </div>
              <span className="text-sm text-slate-500">Thinking...</span>
            </div>
          )}
          <div ref={scrollRef} />
        </CardContent>
        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          <div
            className="mb-2 flex flex-wrap gap-1"
            data-testid="example-prompts"
          >
            {EXAMPLE_PROMPTS.map((g) =>
              g.items.map((p, i) => (
                <button
                  key={`${g.group}-${i}`}
                  type="button"
                  onClick={() => setInput(p)}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700 transition-colors"
                >
                  {p}
                </button>
              )),
            )}
          </div>
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              data-testid="chat-input"
            />
            <Button
              size="icon"
              className="bg-blue-600 hover:bg-blue-700 shrink-0"
              onClick={send}
              disabled={loading || !input.trim()}
              data-testid="chat-send"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
