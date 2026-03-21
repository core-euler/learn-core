import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import ChatArea from '../components/ChatArea';
import InputArea from '../components/InputArea';
import { modulesAPI, lessonsAPI, progressAPI, chatAPI } from '../utils/api';
import { streamChatLecture } from '../utils/sse';

const buildMessageId = () => `msg-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const normalizeModules = (modulesData, progressData, moduleDetailsById) => {
  const progressModules = progressData?.modules || [];

  return (modulesData?.modules || []).map((module) => {
    const moduleProgress = progressModules.find((pm) => pm.module_id === module.id);
    const moduleDetails = moduleDetailsById[module.id] || { lessons: [] };
    const lessonProgressList = moduleProgress?.lessons || [];

    return {
      id: module.id,
      order: module.order_index,
      title: module.title,
      description: module.description,
      status: moduleProgress?.status || 'locked',
      lessons: (moduleDetails.lessons || []).map((lesson) => {
        const lessonProgress = lessonProgressList.find((lp) => lp.lesson_id === lesson.id);
        const status = lessonProgress?.status || 'locked';
        return {
          id: lesson.id,
          title: lesson.title,
          description: lesson.description,
          status,
          completed: status === 'completed',
        };
      }),
    };
  });
};

const MainPage = () => {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const [modules, setModules] = useState([]);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [messages, setMessages] = useState([]);
  const [mode, setMode] = useState('lecture');
  const [sessionId, setSessionId] = useState(null);
  const [examQuestions, setExamQuestions] = useState([]);
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
    // `loadModules` is intentionally omitted to avoid reloading loop on function recreation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const loadModules = async () => {
    try {
      setLoading(true);

      const [modulesRes, progressRes] = await Promise.all([modulesAPI.getAll(), progressAPI.get()]);
      const moduleList = modulesRes.data?.modules || [];

      const moduleDetailsEntries = await Promise.all(
        moduleList.map(async (module) => {
          try {
            const details = await modulesAPI.getOne(module.id);
            return [module.id, details.data];
          } catch {
            return [module.id, { lessons: [] }];
          }
        })
      );

      const moduleDetailsById = Object.fromEntries(moduleDetailsEntries);
      const normalized = normalizeModules(modulesRes.data, progressRes.data, moduleDetailsById);
      setModules(normalized);

      const nextLessonId = progressRes.data?.next_lesson_id;
      let targetLesson = null;

      if (nextLessonId) {
        targetLesson = normalized.flatMap((m) => m.lessons).find((l) => l.id === nextLessonId) || null;
      }

      if (!targetLesson) {
        targetLesson = normalized.flatMap((m) => m.lessons).find((l) => l.status === 'available') || null;
      }

      if (targetLesson) {
        await handleLessonSelect(targetLesson);
      }
    } catch (error) {
      console.error('Failed to load modules:', error);
      setMessages([
        {
          id: 'load-error',
          role: 'assistant',
          content: 'Не удалось загрузить курс с сервера. Проверьте backend и авторизацию.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleLessonSelect = async (lesson) => {
    try {
      setCurrentLesson(lesson);
      setMessages([]);
      setSessionId(null);
      setExamQuestions([]);
      setMode('lecture');

      const contentResponse = await lessonsAPI.getContent(lesson.id);
      const content = contentResponse.data;

      setMessages([
        {
          id: 'lesson-content',
          role: 'assistant',
          content: `${content.content}\n\n---\n\n💬 Прочитали материал? Задавайте вопросы!`,
        },
      ]);
    } catch (error) {
      console.error('Failed to load lesson:', error);
      setMessages([
        {
          id: 'lesson-error',
          role: 'assistant',
          content: 'Не удалось загрузить контент урока. Возможно урок заблокирован или недоступен.',
        },
      ]);
    }
  };

  const handleModeChange = async (newMode) => {
    if (newMode === 'lecture' && currentLesson) {
      await handleLessonSelect(currentLesson);
      return;
    }

    setMode(newMode);
    setMessages([]);
    setSessionId(null);
    setExamQuestions([]);

    if (newMode === 'exam' && currentLesson) {
      try {
        const response = await chatAPI.examStart(currentLesson.id);
        const questions = response.data?.questions || [];
        setExamQuestions(questions);
        setSessionId(response.data?.session_id || null);

        const questionText = questions.length
          ? questions
              .map((q, idx) => `${idx + 1}. ${q.text}${q.options?.length ? `\n   ${q.options.join(' / ')}` : ''}`)
              .join('\n\n')
          : 'Вопросы не получены от сервера.';

        setMessages([
          {
            id: 'exam-start',
            role: 'assistant',
            content: `Начинаем экзамен. Ответьте на вопросы:\n\n${questionText}`,
          },
        ]);
      } catch (error) {
        console.error('Failed to start exam:', error);
        setMessages([
          {
            id: 'exam-error',
            role: 'assistant',
            content: 'Не удалось запустить экзамен.',
          },
        ]);
      }
    } else if (newMode === 'consultant') {
      setMessages([
        {
          id: 'consultant-start',
          role: 'assistant',
          content: 'Режим консультанта активирован. Задавайте вопросы по пройденным модулям.',
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

        await streamChatLecture(
          currentLesson.id,
          text,
          buildMessageId(),
          sessionId,
          (chunk) => {
            if (!chunk.content) return;
            fullResponse += chunk.content;
            setMessages((prev) => {
              const exists = prev.some((m) => m.id === aiMessageId);
              if (exists) {
                return prev.map((m) => (m.id === aiMessageId ? { ...m, content: fullResponse } : m));
              }
              return [...prev, { id: aiMessageId, role: 'assistant', content: fullResponse }];
            });
          },
          () => {
            setIsStreaming(false);
          },
          (error) => {
            throw error;
          }
        );
      } else if (mode === 'consultant') {
        const response = await chatAPI.consultant(text, buildMessageId(), sessionId);
        const reply = response.data?.reply || 'Пустой ответ консультанта.';

        if (!sessionId && response.data?.session_id) {
          setSessionId(response.data.session_id);
        }

        setMessages((prev) => [
          ...prev,
          {
            id: `ai-${Date.now()}`,
            role: 'assistant',
            content: reply,
          },
        ]);
        setIsStreaming(false);
      } else if (mode === 'exam') {
        if (!sessionId) {
          throw new Error('exam_session_missing');
        }

        const answers = (examQuestions.length ? examQuestions : [{ id: '1' }]).map((question) => ({
          question_id: question.id,
          answer: text,
        }));

        const response = await chatAPI.examFinish(sessionId, answers);
        const body = response.data || {};

        setMessages((prev) => [
          ...prev,
          {
            id: `ai-${Date.now()}`,
            role: 'assistant',
            content: `Результат экзамена: ${body.score ?? 0}%\nСтатус: ${body.passed ? 'сдан' : 'не сдан'}\nУрок завершён: ${body.lesson_completed ? 'да' : 'нет'}`,
          },
        ]);

        if (body.lesson_completed) {
          await loadModules();
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
          content: 'Ошибка отправки сообщения на backend.',
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
                  {String(currentModule.order || '00').padStart(2, '0')}
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
