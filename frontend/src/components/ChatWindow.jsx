import { useState, useRef, useEffect } from "react";
import axios from "axios";
import Message from "./Message";

const API = "https://web-production-3d94.up.railway.app";

const SUGGESTED_QUESTIONS = [
  "What was the total revenue?",
  "What are the main risk factors?",
  "Summarize the management discussion section",
  "What was the year-over-year growth?",
];

export default function ChatWindow({
  messages,
  setMessages,
  sessionId,
  documents,
}) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await axios.post(`${API}/query`, {
        message: userMsg,
        session_id: sessionId,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.data.answer,
          toolCalls: res.data.tool_calls_made,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen">
      {/* Top Bar */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white">
            Financial Analysis Chat
          </h2>
          <p className="text-xs text-gray-500">
            {documents.length > 0
              ? `${documents.length} document${documents.length > 1 ? "s" : ""} loaded`
              : "Upload a PDF to get started"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-gray-500">Agent ready</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-4">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-6 text-center">
            <div>
              <p className="text-4xl mb-3">📊</p>
              <h3 className="text-lg font-semibold text-white mb-1">
                Ask anything about your documents
              </h3>
              <p className="text-sm text-gray-500 max-w-sm">
                Upload a financial PDF on the left, then ask questions. The
                agent will search, reason, and cite its sources.
              </p>
            </div>
            {documents.length > 0 && (
              <div className="flex flex-col gap-2 w-full max-w-md">
                <p className="text-xs text-gray-500 uppercase tracking-wider">
                  Try asking
                </p>
                <div className="grid grid-cols-1 gap-2">
                  {SUGGESTED_QUESTIONS.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(q)}
                      className="text-left px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 transition-colors border border-gray-700 hover:border-gray-600"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <Message key={i} message={msg} />
            ))}
            {loading && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold flex-shrink-0">
                  AI
                </div>
                <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1 items-center h-5">
                    <span
                      className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    />
                    <span
                      className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    />
                    <span
                      className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-800 bg-gray-900 px-6 py-4">
        <div className="flex gap-3 items-end max-w-4xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              documents.length === 0
                ? "Upload a document first..."
                : "Ask about revenues, risks, growth, comparisons..."
            }
            disabled={documents.length === 0 || loading}
            rows={1}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            style={{ minHeight: "48px", maxHeight: "120px" }}
            onInput={(e) => {
              e.target.style.height = "auto";
              e.target.style.height =
                Math.min(e.target.scrollHeight, 120) + "px";
            }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading || documents.length === 0}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl px-4 py-3 text-sm font-medium transition-colors flex-shrink-0"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-600 text-center mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
