export type LessonStatus = 'locked' | 'available' | 'completed';
export type ModuleStatus = 'locked' | 'available' | 'completed';

export type UserMe = {
  id: string;
  email: string | null;
  first_name: string;
  auth_method: 'email' | 'telegram';
};

export type ProgressLesson = {
  lesson_id: string;
  status: LessonStatus;
  exam_score: number | null;
  exam_attempts: number;
  completed_at: string | null;
};

export type ProgressModule = {
  module_id: string;
  status: ModuleStatus;
  completed_at: string | null;
  lessons: ProgressLesson[];
};

export type ProgressResponse = {
  overall_percent: number;
  next_lesson_id: string | null;
  consultant_unlocked: boolean;
  modules: ProgressModule[];
};

export type ModulesResponse = {
  modules: Array<{
    id: string;
    title: string;
    description: string | null;
    order_index: number;
    lessons_count: number;
  }>;
};

export type ModuleDetailsResponse = {
  id: string;
  title: string;
  description: string | null;
  order_index: number;
  lessons: Array<{
    id: string;
    module_id: string;
    title: string;
    description: string | null;
    order_index: number;
  }>;
};

export type LessonContentResponse = {
  lesson_id: string;
  title: string;
  content: string;
};

export type LectureJsonResponse = {
  session_id: string;
  reply: string;
};

export type ExamStartResponse = {
  session_id: string;
  questions: Array<{ id: string; type: string; text: string; options?: string[] }>;
  provider: string;
  fallback_reason: string;
};

export type ExamFinishResponse = {
  session_id: string;
  score: number;
  passed: boolean;
  lesson_completed: boolean;
  answers: Array<{ question_id: string; is_correct: boolean; comment: string }>;
};

export type ConsultantResponse = {
  session_id: string;
  reply: string;
  source: string;
  retrieval: {
    citations: Array<{ source?: string; title?: string; chunk_id?: string }>;
  };
};
