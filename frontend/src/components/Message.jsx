import ReactMarkdown from "react-markdown";

export default function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
          isUser ? "bg-gray-700 text-gray-300" : "bg-blue-600 text-white"
        }`}
      >
        {isUser ? "You" : "AI"}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-2xl flex flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}
      >
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : message.error
                ? "bg-red-900/40 text-red-300 border border-red-800 rounded-tl-sm"
                : "bg-gray-800 text-gray-100 rounded-tl-sm"
          }`}
        >
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <ReactMarkdown
              components={{
                p: ({ children }) => (
                  <p className="mb-2 last:mb-0">{children}</p>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-white">
                    {children}
                  </strong>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside mb-2 space-y-1">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside mb-2 space-y-1">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="text-gray-300">{children}</li>
                ),
                code: ({ children }) => (
                  <code className="bg-gray-900 px-1.5 py-0.5 rounded text-blue-300 text-xs font-mono">
                    {children}
                  </code>
                ),
                h1: ({ children }) => (
                  <h1 className="text-base font-bold text-white mb-2">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-sm font-bold text-white mb-2">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-semibold text-gray-200 mb-1">
                    {children}
                  </h3>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Tool calls badge */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {[...new Set(message.toolCalls)].map((tool, i) => (
              <span
                key={i}
                className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-500 border border-gray-700"
              >
                🔧 {tool}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
