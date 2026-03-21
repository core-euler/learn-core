import React, { useRef, useEffect } from 'react';

const ChatArea = ({ messages, isStreaming }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  const renderMessageContent = (content) => {
    if (!content) return null;

    // Simple markdown-like rendering
    const parts = content.split(/(\*\*.*?\*\*|`.*?`)/g);

    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={idx} className="font-semibold">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={idx}
            className="bg-[#0d0d0d] text-[#a5b4fc] px-1.5 py-0.5 rounded text-sm"
            style={{ fontFamily: '"Geist Mono", monospace' }}
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return <span key={idx}>{part}</span>;
    });
  };

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6" ref={scrollRef} data-testid="chat-area">
      {messages.map((message, idx) => {
        const isAI = message.role === 'assistant' || message.sender === 'ai';

        return (
          <div
            key={message.id || idx}
            className={`flex gap-4 animate-fade-up ${
              isAI ? 'justify-start' : 'justify-end'
            }`}
            data-testid={`message-${isAI ? 'ai' : 'user'}`}
          >
            {isAI && (
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#FA9042] to-[#8885FF] flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                LC
              </div>
            )}

            <div
              className={`
                max-w-[70%] px-4 py-3 leading-relaxed
                ${
                  isAI
                    ? 'bg-[#1c1c1c] text-[#e5e5e5] rounded-tl rounded-tr-xl rounded-br-xl rounded-bl-xl'
                    : 'bg-[#8885FF] text-white rounded-tl-xl rounded-tr rounded-br-xl rounded-bl-xl'
                }
              `}
            >
              <div className="text-sm whitespace-pre-wrap break-words">
                {renderMessageContent(message.content || message.text)}
              </div>
            </div>

            {!isAI && (
              <div className="w-8 h-8 rounded-full bg-[#1c1c1c] flex items-center justify-center text-[#5a5a5a] text-xs font-bold flex-shrink-0">
                U
              </div>
            )}
          </div>
        );
      })}

      {isStreaming && (
        <div className="flex gap-4 justify-start animate-fade-up">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#FA9042] to-[#8885FF] flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
            LC
          </div>
          <div className="bg-[#1c1c1c] px-4 py-3 rounded-tr-xl rounded-br-xl rounded-bl-xl">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-[#8885FF] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-[#8885FF] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-[#8885FF] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatArea;
