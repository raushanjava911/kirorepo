import React, { useState, useRef, useEffect } from "react";

// When running behind nginx proxy, use relative path; for local dev use localhost:5000
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
        body: JSON.stringify({ messages: updatedMessages }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessages([...updatedMessages, { role: "assistant", content: data.reply }]);
      } else {
        setMessages([...updatedMessages, { role: "assistant", content: `Error: ${data.error}` }]);
      }
    } catch (err) {
      setMessages([...updatedMessages, { role: "assistant", content: `Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>Chat with OpenAI</h1>
      </header>

      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="empty-state">Send a message to start chatting.</p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <span className="message-role">{msg.role === "user" ? "You" : "Assistant"}</span>
            <p className="message-content">{msg.content}</p>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <span className="message-role">Assistant</span>
            <p className="message-content typing">Thinking...</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
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
