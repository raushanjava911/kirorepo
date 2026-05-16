import React, { useState, useRef, useEffect } from "react";

const API_URL = process.env.REACT_APP_API_URL || "";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", content: input.trim() };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updatedMessages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      const data = await response.json();

      if (response.ok) {
        const assistantMsg = {
          role: "assistant",
          content: data.reply,
          toolsUsed: data.tools_used || [],
        };
        setMessages([...updatedMessages, assistantMsg]);
      } else {
        setMessages([
          ...updatedMessages,
          { role: "assistant", content: `Error: ${data.error}`, toolsUsed: [] },
        ]);
      }
    } catch (err) {
      setMessages([
        ...updatedMessages,
        { role: "assistant", content: `Error: ${err.message}`, toolsUsed: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>AI Agent</h1>
        <p className="header-subtitle">
          Weather · Calculator · Wikipedia · HR Policy
        </p>
      </header>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Ask me anything! I can:</p>
            <ul>
              <li>Tell you the current date/time in any timezone</li>
              <li>Get live weather for any city</li>
              <li>Do math calculations</li>
              <li>Look up facts on Wikipedia</li>
              <li>Answer questions about your HR policies</li>
            </ul>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <span className="message-role">
              {msg.role === "user" ? "You" : "Agent"}
            </span>
            <p className="message-content">{msg.content}</p>
            {msg.toolsUsed && msg.toolsUsed.length > 0 && (
              <details className="tools-used">
                <summary>
                  🔧 Used {msg.toolsUsed.length} agent{msg.toolsUsed.length > 1 ? "s" : ""}
                </summary>
                <ul>
                  {msg.toolsUsed.map((tool, j) => (
                    <li key={j}>
                      <strong>{tool.tool}</strong>
                      <span className="tool-task">: {tool.args.task}</span>
                      <pre>{tool.result}</pre>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <span className="message-role">Agent</span>
            <p className="message-content typing">Thinking... 🤔</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about HR policy, weather, facts..."
          disabled={loading}
          aria-label="Chat message input"
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;
