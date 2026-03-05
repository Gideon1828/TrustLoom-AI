import React, { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import { Bot, Sparkle, Trash2, X, Send } from "lucide-react";
import "./ChatBot.css";

const API_BASE_URL = "http://localhost:8000";

// ── Utility: render basic markdown (bold, italic, bullets, links) ────────
function renderMarkdown(text) {
  if (!text) return "";
  // Bold **text**
  let html = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Italic *text*
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, "<em>$1</em>");
  // Inline code `text`
  html = html.replace(/`(.+?)`/g, '<code class="chat-inline-code">$1</code>');
  // Links [text](url)
  html = html.replace(
    /\[(.+?)\]\((.+?)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  );
  // Line breaks
  html = html.replace(/\n/g, "<br/>");
  return html;
}

// ── Quick-action suggestion chips ────────────────────────────────────────
const QUICK_ACTIONS = [
  { label: "How does scoring work?", text: "How does the trust score work?" },
  { label: "Improve my score", text: "How can I improve my trust score?" },
  { label: "Download report", text: "How do I download a PDF report?" },
  { label: "Compare candidates", text: "How do I compare candidates?" },
];

// ── ChatBot Component ────────────────────────────────────────────────────
const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm **TrustLoom Assistant**. I can help you navigate the platform, explain features, and troubleshoot issues.\n\nHow can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(true);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const chatBodyRef = useRef(null);

  // Auto-scroll to latest message
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 200);
      setHasUnread(false);
    }
  }, [isOpen]);

  // ── Send message ───────────────────────────────────────────────────────
  const sendMessage = useCallback(
    async (text) => {
      const trimmed = (text || inputValue).trim();
      if (!trimmed || isTyping) return;

      const userMsg = {
        role: "user",
        content: trimmed,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInputValue("");
      setIsTyping(true);
      setShowQuickActions(false);

      // Build chat history for API (exclude timestamps)
      const history = [...messages, userMsg].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      try {
        const resp = await axios.post(`${API_BASE_URL}/api/chat/send`, {
          messages: history,
        });

        const reply = resp.data?.reply || "Sorry, I couldn't process that.";

        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: reply, timestamp: new Date() },
        ]);

        if (!isOpen) setHasUnread(true);
      } catch (err) {
        const fallback =
          err.response?.status === 503
            ? "The chat service is currently unavailable. Please try again later, or click your profile menu → **Report an Issue** for help."
            : "I'm having trouble connecting right now. Please try again in a moment.";
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: fallback, timestamp: new Date(), isError: true },
        ]);
      } finally {
        setIsTyping(false);
      }
    },
    [inputValue, isTyping, messages, isOpen]
  );

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleQuickAction = (text) => {
    sendMessage(text);
  };

  const clearChat = () => {
    setMessages([
      {
        role: "assistant",
        content:
          "Chat cleared! How can I help you?",
        timestamp: new Date(),
      },
    ]);
    setShowQuickActions(true);
  };

  // ── Time formatter ─────────────────────────────────────────────────────
  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <>
      {/* Floating Action Button */}
      <button
        className={`chatbot-fab ${isOpen ? "chatbot-fab-hidden" : ""} ${hasUnread ? "chatbot-fab-unread" : ""}`}
        onClick={() => setIsOpen(true)}
        aria-label="Open help chat"
      >
        <span className="chatbot-fab-bg-ring" />
        <span className="chatbot-fab-icon"><Bot size={28} /></span>
        <span className="chatbot-fab-sparkle chatbot-fab-sparkle-1"><Sparkle size={10} /></span>
        <span className="chatbot-fab-sparkle chatbot-fab-sparkle-2"><Sparkle size={10} /></span>
        <span className="chatbot-fab-sparkle chatbot-fab-sparkle-3"><Sparkle size={10} /></span>
        {hasUnread && <span className="chatbot-fab-badge" />}
        <span className="chatbot-fab-tooltip">Ask AI Assistant</span>
      </button>

      {/* Chat Window */}
      <div className={`chatbot-window ${isOpen ? "chatbot-window-open" : ""}`}>
        {/* Header */}
        <div className="chatbot-header">
          <div className="chatbot-header-accent" />
          <div className="chatbot-header-inner">
            <div className="chatbot-header-info">
              <div className="chatbot-avatar">
                <span className="chatbot-avatar-emoji"><Bot size={20} /></span>
              </div>
              <div>
                <h4 className="chatbot-header-title">TrustLoom AI</h4>
                <span className="chatbot-header-status">
                  <span className="chatbot-status-dot" />
                  Always ready to help
                </span>
              </div>
            </div>
            <div className="chatbot-header-actions">
              <button
                className="chatbot-header-btn"
                onClick={clearChat}
                title="Clear chat"
                aria-label="Clear chat history"
              >
                <Trash2 size={15} />
              </button>
              <button
                className="chatbot-header-btn chatbot-close-btn"
                onClick={() => setIsOpen(false)}
                title="Close"
                aria-label="Close chat"
              >
                <X size={16} strokeWidth={2.5} />
              </button>
            </div>
          </div>
        </div>

        {/* Message Body */}
        <div className="chatbot-body" ref={chatBodyRef}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`chatbot-msg ${msg.role === "user" ? "chatbot-msg-user" : "chatbot-msg-assistant"} ${msg.isError ? "chatbot-msg-error" : ""}`}
            >
              {msg.role === "assistant" && (
                <div className="chatbot-msg-avatar">
                  <span className="chatbot-msg-avatar-emoji"><Bot size={14} /></span>
                </div>
              )}
              <div className="chatbot-msg-content">
                <div
                  className="chatbot-msg-bubble"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                />
                <span className="chatbot-msg-time">{formatTime(msg.timestamp)}</span>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isTyping && (
            <div className="chatbot-msg chatbot-msg-assistant">
              <div className="chatbot-msg-avatar">
                <span className="chatbot-msg-avatar-emoji"><Bot size={14} /></span>
              </div>
              <div className="chatbot-msg-content">
                <div className="chatbot-typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        {showQuickActions && messages.length <= 2 && (
          <div className="chatbot-quick-actions">
            {QUICK_ACTIONS.map((action, idx) => (
              <button
                key={idx}
                className="chatbot-chip"
                onClick={() => handleQuickAction(action.text)}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="chatbot-input-area">
          <div className="chatbot-input-row">
            <textarea
              ref={inputRef}
              className="chatbot-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message…"
              rows={1}
              disabled={isTyping}
            />
            <button
              className="chatbot-send-btn"
              onClick={() => sendMessage()}
              disabled={!inputValue.trim() || isTyping}
              aria-label="Send message"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="chatbot-disclaimer">
            AI assistant — answers may not always be accurate
          </p>
        </div>
      </div>
    </>
  );
};

export default ChatBot;
