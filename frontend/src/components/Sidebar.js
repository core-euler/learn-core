import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const Sidebar = ({ modules, currentLesson, onLessonSelect }) => {
  const { user, logout } = useAuth();
  const [expandedModules, setExpandedModules] = useState(new Set());

  const toggleModule = (moduleId) => {
    setExpandedModules((prev) => {
      const next = new Set(prev);
      if (next.has(moduleId)) {
        next.delete(moduleId);
      } else {
        next.add(moduleId);
      }
      return next;
    });
  };

  const getModuleStatus = (module) => {
    if (module.status === 'completed') return 'completed';
    if (module.status === 'available') return 'active';
    if (module.status === 'active' || module.status === 'in_progress') return 'active';
    if (module.status === 'locked') return 'locked';
    return 'locked';
  };

  const getLessonStatus = (lesson) => {
    if (lesson.status === 'completed') return 'done';
    if (lesson.status === 'available' && currentLesson?.id !== lesson.id) return 'upcoming';
    if (lesson.status === 'locked') return 'upcoming';
    if (lesson.completed) return 'done';
    if (currentLesson?.id === lesson.id) return 'current';
    return 'upcoming';
  };

  const getUserInitials = () => {
    const sourceName = user?.full_name || user?.first_name || user?.email || '';
    if (!sourceName) return 'U';
    return sourceName
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  React.useEffect(() => {
    // Auto-expand active modules
    const activeModuleIds = modules
      .filter((m) => getModuleStatus(m) === 'active')
      .map((m) => m.id);
    setExpandedModules(new Set(activeModuleIds));
  }, [modules]);

  return (
    <aside className="w-[264px] bg-[#111111] h-screen flex flex-col fixed left-0 top-0" data-testid="sidebar">
      <div className="p-6 border-b border-[#222222]">
        <div className="flex items-center gap-2 mb-1">
          <h1 className="text-xl font-bold text-[#e5e5e5]" style={{ fontFamily: '"Geist", sans-serif' }}>
            LearnCore
          </h1>
          <div className="w-2 h-2 rounded-full bg-[#8885FF] animate-pulse"></div>
        </div>
        <p className="text-xs text-[#5a5a5a]">LLM-Driven Development</p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-xs text-[#5a5a5a] uppercase tracking-wide mb-3 px-2">Модули курса</h2>
          <div className="space-y-1" data-testid="modules-list">
            {modules.map((module) => {
              const status = getModuleStatus(module);
              const isExpanded = expandedModules.has(module.id);
              const isLocked = status === 'locked';

              return (
                <div key={module.id} className="module-group" data-testid={`module-${module.id}`}>
                  <div
                    className={`
                      flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer
                      transition-colors relative
                      ${
                        status === 'active'
                          ? 'bg-[#8885FF]/10 hover:bg-[#8885FF]/15'
                          : status === 'completed'
                          ? 'hover:bg-[#1c1c1c]'
                          : 'opacity-40 cursor-not-allowed'
                      }
                    `}
                    onClick={() => !isLocked && toggleModule(module.id)}
                    data-testid={`module-header-${module.id}`}
                  >
                    {status === 'active' && <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-[#8885FF]"></div>}
                    {status === 'completed' && <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-[#22c55e]"></div>}

                    <span
                      className="text-xs text-[#5a5a5a] font-mono flex-shrink-0"
                      style={{ fontFamily: '"Geist Mono", monospace' }}
                    >
                      {String(module.order || module.id).padStart(2, '0')}
                    </span>

                    <span className="flex-1 text-sm text-[#e5e5e5] truncate">{module.title}</span>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {status === 'completed' && <span className="text-[#22c55e] text-sm">✓</span>}
                      {status === 'active' && <span className="text-[#8885FF] text-sm">●</span>}
                      {status === 'locked' && <span className="text-[#5a5a5a] text-xs">🔒</span>}
                      {!isLocked && (
                        <span className={`text-[#5a5a5a] text-xs transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
                          ►
                        </span>
                      )}
                    </div>
                  </div>

                  {isExpanded && module.lessons && (
                    <div className="ml-6 mt-1 space-y-0.5 border-l border-[#222222] pl-3" data-testid={`lessons-${module.id}`}>
                      {module.lessons.map((lesson) => {
                        const lessonStatus = getLessonStatus(lesson);
                        return (
                          <div
                            key={lesson.id}
                            className={`
                              flex items-center gap-2 px-3 py-2 rounded cursor-pointer
                              transition-colors text-sm
                              ${
                                lessonStatus === 'current'
                                  ? 'bg-[#8885FF]/10 text-[#e5e5e5]'
                                  : lessonStatus === 'done'
                                  ? 'text-[#5a5a5a] hover:text-[#e5e5e5] hover:bg-[#1c1c1c]'
                                  : 'text-[#333333]'
                              }
                            `}
                            onClick={() => onLessonSelect(lesson)}
                            data-testid={`lesson-${lesson.id}`}
                          >
                            <div
                              className={`
                              w-1.5 h-1.5 rounded-full flex-shrink-0
                              ${
                                lessonStatus === 'done'
                                  ? 'bg-[#22c55e]'
                                  : lessonStatus === 'current'
                                  ? 'bg-[#8885FF] animate-pulse'
                                  : 'bg-[#333333]'
                              }
                            `}
                            ></div>
                            <span className="truncate">{lesson.title}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-[#222222]">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full bg-gradient-to-br from-[#FA9042] to-[#8885FF] flex items-center justify-center text-white text-sm font-bold"
            data-testid="user-avatar"
          >
            {getUserInitials()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm text-[#e5e5e5] truncate">{user?.full_name || user?.first_name || user?.email || 'User'}</div>
            <button
              onClick={logout}
              className="text-xs text-[#5a5a5a] hover:text-[#8885FF] transition-colors"
              data-testid="logout-button"
            >
              Выйти
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
