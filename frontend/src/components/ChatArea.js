import React, { useRef, useEffect } from 'react';

const ChatArea = ({ messages, isStreaming }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  const renderInlineMarkdown = (text) => {
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={idx} className="font-semibold text-[#e5e5e5]">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={idx}
            className="bg-[#0d0d0d] text-[#a5b4fc] px-1.5 py-0.5 rounded text-sm mx-0.5"
            style={{ fontFamily: '"Geist Mono", monospace' }}
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return <span key={idx}>{part}</span>;
    });
  };

  const renderMessageContent = (content) => {
    if (!content) return null;

    // Enhanced markdown rendering for full lesson content
    const lines = content.split('\n');
    const elements = [];

    lines.forEach((line, idx) => {
      // Headings
      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={idx} className="text-2xl font-bold mb-3 mt-6 first:mt-0">
            {line.slice(2)}
          </h1>
        );
      } else if (line.startsWith('## ')) {
        elements.push(
          <h2 key={idx} className="text-xl font-semibold mb-2 mt-4">
            {line.slice(3)}
          </h2>
        );
      } else if (line.startsWith('### ')) {
        elements.push(
          <h3 key={idx} className="text-lg font-semibold mb-2 mt-3">
            {line.slice(4)}
          </h3>
        );
      }
      // Horizontal rule
      else if (line.trim() === '---') {
        elements.push(<hr key={idx} className="border-[#222222] my-4" />);
      }
      // List items
      else if (line.match(/^[\-\*]\s/)) {
        elements.push(
          <div key={idx} className="flex gap-2 mb-1 ml-2">
            <span className="text-[#8885FF] flex-shrink-0">•</span>
            <span>{renderInlineMarkdown(line.slice(2))}</span>
          </div>
        );
      }
      // Numbered list
      else if (line.match(/^\d+\.\s/)) {
        const num = line.match(/^(\d+)\./)[1];
        elements.push(
          <div key={idx} className="flex gap-2 mb-1 ml-2">
            <span className="text-[#8885FF] flex-shrink-0 font-mono">{num}.</span>
            <span>{renderInlineMarkdown(line.replace(/^\d+\.\s/, ''))}</span>
          </div>
        );
      }
      // Regular paragraph
      else if (line.trim()) {
        elements.push(
          <p key={idx} className="mb-2">
            {renderInlineMarkdown(line)}
          </p>
        );
      }
      // Empty line
      else {
        elements.push(<div key={idx} className="h-2" />);
      }
    });

    return <div>{elements}</div>;
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
                px-4 py-3 leading-relaxed
                ${
                  isAI
                    ? message.id === 'lesson-content' 
                      ? 'max-w-[85%] bg-[#1c1c1c] text-[#e5e5e5] rounded-xl'
                      : 'max-w-[70%] bg-[#1c1c1c] text-[#e5e5e5] rounded-tl rounded-tr-xl rounded-br-xl rounded-bl-xl'
                    : 'max-w-[70%] bg-[#8885FF] text-white rounded-tl-xl rounded-tr rounded-br-xl rounded-bl-xl'
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
