import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow.jsx";

function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [sessionId] = useState(() => `session_${Date.now()}`);

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-sans">
      <Sidebar documents={documents} setDocuments={setDocuments} />
      <ChatWindow
        messages={messages}
        setMessages={setMessages}
        sessionId={sessionId}
        documents={documents}
      />
    </div>
  );
}

export default App;
