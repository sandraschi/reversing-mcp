import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { getApiBase } from "@/common/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "0",
      role: "assistant",
      content: "Reversing assistant. I can help with binary analysis and Ghidra. Pick a model in Settings (Ollama) and ask.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    const userMsg: Message = { id: String(Date.now()), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
        }),
      });
      const data = await res.json().catch(() => ({}));
      const reply =
        data?.reply ??
        "Backend or Ollama not reachable. Check Settings and run the backend (e.g. start-webapp.ps1).";
      setMessages((prev) => [...prev, { id: String(Date.now() + 1), role: "assistant", content: reply }]);
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

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">AI Command</h2>
        <p className="text-slate-400">Ollama chat (set model in Settings)</p>
      </div>

      <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m) => (
            <div key={m.id} className="flex gap-3">
              <div
                className={`h-8 w-8 shrink-0 rounded-full flex items-center justify-center border ${
                  m.role === "user" ? "bg-slate-800 border-slate-700" : "bg-blue-900/20 border-blue-800"
                }`}
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
                <p className="text-sm text-slate-300 whitespace-pre-wrap break-words">{m.content}</p>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-blue-900/20 border border-blue-800 flex items-center justify-center">
                <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />
              </div>
              <span className="text-sm text-slate-500">Thinking…</span>
            </div>
          )}
          <div ref={scrollRef} />
        </CardContent>
        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            />
            <Button
              size="icon"
              className="bg-blue-600 hover:bg-blue-700 shrink-0"
              onClick={send}
              disabled={loading || !input.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
