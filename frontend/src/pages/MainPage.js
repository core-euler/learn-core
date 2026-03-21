import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import ChatArea from '../components/ChatArea';
import InputArea from '../components/InputArea';
import { modulesAPI, lessonsAPI, progressAPI, chatAPI } from '../utils/api';
import { streamChatLecture, streamConsultant } from '../utils/sse';
import { mockModules, mockLessonContent, delay } from '../utils/mockData';

const MainPage = () => {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const [modules, setModules] = useState([]);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [messages, setMessages] = useState([]);
  const [mode, setMode] = useState('lecture'); // 'lecture', 'exam', 'consultant'
  const [sessionId, setSessionId] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/login');
    }
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (user) {
      loadModules();
    }
  }, [user]);

  const loadModules = async () => {
    try {
      setLoading(true);
      
      // Try to fetch from backend
      try {
        const response = await modulesAPI.getAll();
        setModules(response.data);

        // Find first available lesson
        const firstActiveModule = response.data.find(
          (m) => m.status === 'active' || m.status === 'in_progress'
        );
        if (firstActiveModule?.lessons?.length) {
          const firstLesson = firstActiveModule.lessons.find((l) => !l.completed) || firstActiveModule.lessons[0];
          handleLessonSelect(firstLesson);
        }
      } catch (apiError) {
        // Fallback to mock data if backend not ready
        console.log('Using mock data for demonstration');
        await delay(500);
        setModules(mockModules);

        // Find first available lesson from mock data
        const firstActiveModule = mockModules.find(
          (m) => m.status === 'active' || m.status === 'in_progress'
        );
        if (firstActiveModule?.lessons?.length) {
          const firstLesson = firstActiveModule.lessons.find((l) => !l.completed) || firstActiveModule.lessons[0];
          handleLessonSelect(firstLesson);
        }
      }
    } catch (error) {
      console.error('Failed to load modules:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLessonSelect = async (lesson) => {
    try {
      setCurrentLesson(lesson);
      setMessages([]);
      setSessionId(null);
      setMode('lecture');

      // Try to load lesson content from backend
      try {
        const contentResponse = await lessonsAPI.getContent(lesson.id);
        const content = contentResponse.data;

        // Add initial AI message with lesson intro
        if (content.content) {
          setMessages([
            {
              id: 'intro',
              role: 'assistant',
              content: content.content.slice(0, 500) + '...\n\nЗадавайте вопросы по материалу!',
            },
          ]);
        }
      } catch (apiError) {
        // Fallback to mock data
        await delay(300);
        const mockContent = mockLessonContent[lesson.id];
        
        if (mockContent) {
          setMessages([
            {
              id: 'intro',
              role: 'assistant',
              content: mockContent.content + '\n\n📚 Задавайте вопросы по материалу!',
            },
          ]);
        } else {
          setMessages([
            {
              id: 'intro',
              role: 'assistant',
              content: `Добро пожаловать на урок: **${lesson.title}**\n\nЗадавайте вопросы, и я помогу разобраться в материале!`,
            },
          ]);
        }
      }
    } catch (error) {
      console.error('Failed to load lesson:', error);
      setMessages([
        {
          id: 'error',
          role: 'assistant',
          content: 'Не удалось загрузить урок. Попробуйте позже.',
        },
      ]);
    }
  };

  const handleModeChange = async (newMode) => {
    setMode(newMode);
    setMessages([]);
    setSessionId(null);

    if (newMode === 'exam' && currentLesson) {
      try {
        const response = await chatAPI.examStart(currentLesson.id);
        setSessionId(response.data.session_id);
        setMessages([
          {
            id: 'exam-start',
            role: 'assistant',
            content: response.data.message || 'Начинаем экзамен. Ответьте на следующие вопросы.',
          },
        ]);
      } catch (error) {
        console.error('Failed to start exam:', error);
      }
    } else if (newMode === 'consultant') {
      setMessages([
        {
          id: 'consultant-start',
          role: 'assistant',
          content: 'Здравствуйте! Я ваш консультант. Задавайте любые вопросы по курсу.',
        },
      ]);
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);

    try {
      if (mode === 'lecture' && currentLesson) {
        let fullResponse = '';
        const aiMessageId = `ai-${Date.now()}`;

        try {
          await streamChatLecture(
            currentLesson.id,
            text,
            sessionId,
            (chunk) => {
              if (chunk.content) {
                fullResponse += chunk.content;
                setMessages((prev) => {
                  const existing = prev.find((m) => m.id === aiMessageId);
                  if (existing) {
                    return prev.map((m) => (m.id === aiMessageId ? { ...m, content: fullResponse } : m));
                  } else {
                    return [...prev, { id: aiMessageId, role: 'assistant', content: fullResponse }];
                  }
                });
              }
              if (chunk.session_id && !sessionId) {
                setSessionId(chunk.session_id);
              }
            },
            () => {
              setIsStreaming(false);
            },
            (error) => {
              console.error('Streaming error:', error);
              throw error;
            }
          );
        } catch (streamError) {
          // Fallback to mock response
          await delay(1000);
          const mockResponse = `Отличный вопрос о **${currentLesson.title}**!\n\nВ контексте RAG-архитектуры это действительно важная тема. Чанкинг (разбиение документов) влияет на точность поиска и качество ответов.\n\nРекомендую обратить внимание на:\n- Размер чанка должен быть оптимальным для вашей модели\n- Используйте перекрытие (overlap) между чанками\n- Учитывайте семантические границы (параграфы, разделы)\n\nЕсть еще вопросы по этой теме?`;
          
          setMessages((prev) => [...prev, { id: aiMessageId, role: 'assistant', content: mockResponse }]);
          setIsStreaming(false);
        }
      } else if (mode === 'consultant') {
        let fullResponse = '';
        const aiMessageId = `ai-${Date.now()}`;

        try {
          await streamConsultant(
            text,
            sessionId,
            (chunk) => {
              if (chunk.content) {
                fullResponse += chunk.content;
                setMessages((prev) => {
                  const existing = prev.find((m) => m.id === aiMessageId);
                  if (existing) {
                    return prev.map((m) => (m.id === aiMessageId ? { ...m, content: fullResponse } : m));
                  } else {
                    return [...prev, { id: aiMessageId, role: 'assistant', content: fullResponse }];
                  }
                });
              }
              if (chunk.session_id && !sessionId) {
                setSessionId(chunk.session_id);
              }
            },
            () => {
              setIsStreaming(false);
            },
            (error) => {
              console.error('Streaming error:', error);
              throw error;
            }
          );
        } catch (streamError) {
          // Fallback to mock response
          await delay(1000);
          const mockResponse = `Хороший вопрос! В рамках курса по LLM-разработке могу помочь с:\n\n- Архитектурой RAG-систем\n- Промпт-инжинирингом\n- Выбором подходов к fine-tuning\n- Оптимизацией latency и costs\n\nЧто конкретно вас интересует?`;
          
          setMessages((prev) => [...prev, { id: aiMessageId, role: 'assistant', content: mockResponse }]);
          setIsStreaming(false);
        }
      } else if (mode === 'exam') {
        // Non-streaming exam finish
        try {
          const response = await chatAPI.examFinish(sessionId, text);
          setMessages((prev) => [
            ...prev,
            {
              id: `ai-${Date.now()}`,
              role: 'assistant',
              content: response.data.message || 'Ответ принят.',
            },
          ]);
        } catch (examError) {
          // Mock exam response
          await delay(1000);
          setMessages((prev) => [
            ...prev,
            {
              id: `ai-${Date.now()}`,
              role: 'assistant',
              content: `✅ Ваш ответ принят!\n\nЭто правильное направление мысли. В следующем уроке мы углубимся в детали этой темы.`,
            },
          ]);
        }
        setIsStreaming(false);
      }
    } catch (error) {
      console.error('Send message error:', error);
      setIsStreaming(false);
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'Ошибка отправки сообщения.',
        },
      ]);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-[#0d0d0d] flex items-center justify-center">
        <div className="text-[#8885FF] text-lg">Загрузка...</div>
      </div>
    );
  }

  const currentModule = modules.find((m) => m.lessons?.some((l) => l.id === currentLesson?.id));

  return (
    <div className="min-h-screen bg-[#0d0d0d] flex" data-testid="main-page">
      <Sidebar modules={modules} currentLesson={currentLesson} onLessonSelect={handleLessonSelect} />

      <div className="flex-1 ml-[264px] flex flex-col">
        <div
          className="h-16 border-b border-[#222222] bg-[#141414]/80 backdrop-blur-md flex items-center justify-between px-6"
          data-testid="topbar"
        >
          <div className="flex items-center gap-2 text-sm text-[#5a5a5a]">
            {currentModule && (
              <>
                <span style={{ fontFamily: '"Geist Mono", monospace' }}>
                  {String(currentModule.order || currentModule.id).padStart(2, '0')}
                </span>
                <span>·</span>
                <span>{currentLesson?.title || 'Выберите урок'}</span>
              </>
            )}
          </div>

          <div className="flex gap-2" data-testid="mode-switcher">
            <button
              onClick={() => handleModeChange('lecture')}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${
                  mode === 'lecture'
                    ? 'bg-[#8885FF] text-white'
                    : 'border border-[#222222] text-[#5a5a5a] hover:text-[#e5e5e5] hover:border-[#8885FF]'
                }
              `}
              data-testid="mode-lecture"
            >
              Лекция
            </button>
            <button
              onClick={() => handleModeChange('exam')}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${
                  mode === 'exam'
                    ? 'bg-[#8885FF] text-white'
                    : 'border border-[#222222] text-[#5a5a5a] hover:text-[#e5e5e5] hover:border-[#8885FF]'
                }
              `}
              data-testid="mode-exam"
            >
              Экзамен
            </button>
            <button
              onClick={() => handleModeChange('consultant')}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${
                  mode === 'consultant'
                    ? 'bg-[#8885FF] text-white'
                    : 'border border-[#222222] text-[#5a5a5a] hover:text-[#e5e5e5] hover:border-[#8885FF]'
                }
              `}
              data-testid="mode-consultant"
            >
              Консультант
            </button>
          </div>
        </div>

        <div
          className="flex-1 flex flex-col relative"
          style={{
            background:
              'linear-gradient(135deg, rgba(250, 144, 66, 0.03) 0%, rgba(136, 133, 255, 0.03) 100%), #141414',
          }}
        >
          <ChatArea messages={messages} isStreaming={isStreaming} />
          <InputArea
            mode={mode}
            onSendMessage={handleSendMessage}
            disabled={isStreaming || !currentLesson}
            currentLesson={currentLesson}
          />
        </div>
      </div>
    </div>
  );
};

export default MainPage;
