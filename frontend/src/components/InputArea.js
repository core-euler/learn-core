import React, { useState, useRef, useEffect } from 'react';

const InputArea = ({ mode, onSendMessage, disabled, currentLesson }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  const getModeHint = () => {
    switch (mode) {
      case 'lecture':
        return `Режим лекции: задавайте вопросы по материалу урока "${currentLesson?.title || ''}"`;
      case 'exam':
        return 'Режим экзамена: отвечайте на вопросы LearnCore, чтобы проверить знания';
      case 'consultant':
        return 'Режим консультанта: свободный диалог по любым темам курса';
      default:
        return 'Введите ваше сообщение';
    }
  };

  const getPlaceholder = () => {
    switch (mode) {
      case 'exam':
        return 'Введите ваш ответ...';
      case 'consultant':
        return 'Задайте вопрос консультанту...';
      default:
        return 'Задайте вопрос...';
    }
  };

  const handleSubmit = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [message]);

  return (
    <div className="border-t border-[#222222] bg-[#141414]/80 backdrop-blur-md" data-testid="input-area">
      <div className="max-w-4xl mx-auto px-6 py-4">
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={getPlaceholder()}
              disabled={disabled}
              className="
                w-full bg-[#1c1c1c] border border-[#222222] text-[#e5e5e5] 
                px-4 py-3 rounded-lg resize-none
                focus:outline-none focus:border-[#8885FF] focus:ring-1 focus:ring-[#8885FF]
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all
              "
              rows={1}
              style={{ minHeight: '48px', maxHeight: '120px' }}
              data-testid="chat-input"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={!message.trim() || disabled}
            className="
              bg-[#8885FF] hover:bg-[#7774ee] disabled:opacity-50 disabled:cursor-not-allowed
              text-white p-3 rounded-lg transition-all flex items-center justify-center
              shadow-lg hover:shadow-[#8885FF]/20
            "
            style={{ minWidth: '48px', minHeight: '48px' }}
            data-testid="send-button"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>

        <div className="mt-2 text-xs text-[#5a5a5a] px-1">{getModeHint()}</div>
      </div>
    </div>
  );
};

export default InputArea;
