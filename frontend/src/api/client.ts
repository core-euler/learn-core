import type {
  ConsultantResponse,
  ExamFinishResponse,
  ExamStartResponse,
  LessonContentResponse,
  ModuleDetailsResponse,
  ModulesResponse,
  ProgressResponse,
  UserMe,
} from '../types/api';
import { http } from '../utils/http';

export const api = {
  me: () => http<UserMe>('/api/auth/me'),
  login: (email: string, password: string) =>
    http<{ ok: boolean }>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string) =>
    http('/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),
  logout: () => http<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),
  progress: () => http<ProgressResponse>('/api/progress'),
  modules: () => http<ModulesResponse>('/api/modules'),
  moduleById: (id: string) => http<ModuleDetailsResponse>(`/api/modules/${id}`),
  lessonContent: (id: string) => http<LessonContentResponse>(`/api/lessons/${id}/content`),
  completeLesson: (id: string) => http<{ ok: boolean }>(`/api/progress/lessons/${id}/complete`, { method: 'POST' }),
  lectureJson: (lessonId: string, message: string, messageId: string) =>
    http<{ session_id: string; reply: string }>('/api/chat/lecture', {
      method: 'POST',
      body: JSON.stringify({ lesson_id: lessonId, message, message_id: messageId }),
    }),
  examStart: (lessonId: string) =>
    http<ExamStartResponse>('/api/chat/exam/start', {
      method: 'POST',
      body: JSON.stringify({ lesson_id: lessonId }),
    }),
  examFinish: (sessionId: string, answers: Array<{ question_id: string; answer: string }>) =>
    http<ExamFinishResponse>('/api/chat/exam/finish', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, answers }),
    }),
  consultant: (message: string, messageId: string) =>
    http<ConsultantResponse>('/api/chat/consultant', {
      method: 'POST',
      body: JSON.stringify({ message, message_id: messageId }),
    }),
};
