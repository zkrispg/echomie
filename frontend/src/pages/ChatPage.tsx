import { useState, useRef, useEffect } from "react";
import { apiChat, apiGetChatHistory, apiClearChatHistory } from "../api/client";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const GREETING = "你好呀，我是 EchoMie 治愈小助手 🌸\n有什么想说的，都可以告诉我～";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: GREETING },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiGetChatHistory()
      .then((res) => {
        if (res.items.length > 0) {
          const history = res.items.map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
          }));
          setMessages([{ role: "assistant", content: GREETING }, ...history]);
        }
      })
      .catch(() => {})
      .finally(() => setHistoryLoaded(true));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await apiChat(text);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "抱歉，暂时无法回应，但我一直在这里陪着你 🌸" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (!confirm("确定清空所有聊天记录吗？")) return;
    try {
      await apiClearChatHistory();
      setMessages([{ role: "assistant", content: GREETING }]);
    } catch {}
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-page">
      <div className="chat-header">
        <span className="chat-header-icon">💬</span>
        <h2>AI 治愈陪伴</h2>
        {historyLoaded && messages.length > 1 && (
          <button className="chat-clear-btn" onClick={handleClear} title="清空记录">
            🗑️
          </button>
        )}
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.role === "assistant" && (
              <span className="bubble-avatar">🌸</span>
            )}
            <div className="bubble-content">
              {msg.content.split("\n").map((line, j) => (
                <p key={j}>{line}</p>
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble assistant">
            <span className="bubble-avatar">🌸</span>
            <div className="bubble-content typing">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-bar">
        <textarea
          className="chat-input"
          placeholder="说点什么吧…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          发送
        </button>
      </div>
    </div>
  );
}
