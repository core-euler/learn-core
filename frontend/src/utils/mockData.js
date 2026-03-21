// Mock data for demonstrating LearnCore UI when backend is not fully connected

export const mockModules = [
  {
    id: 1,
    order: 1,
    title: 'Основы LLM',
    status: 'completed',
    lessons: [
      { id: 101, title: 'Что такое языковая модель', completed: true },
      { id: 102, title: 'Токены и контекстное окно', completed: true },
      { id: 103, title: 'Архитектура трансформера', completed: true },
    ],
  },
  {
    id: 2,
    order: 2,
    title: 'Промпт-инжиниринг',
    status: 'completed',
    lessons: [
      { id: 201, title: 'Chain-of-Thought', completed: true },
      { id: 202, title: 'Few-shot примеры', completed: true },
      { id: 203, title: 'Системные промпты', completed: true },
      { id: 204, title: 'Антипаттерны промптов', completed: true },
    ],
  },
  {
    id: 3,
    order: 3,
    title: 'RAG-архитектура',
    status: 'active',
    lessons: [
      { id: 301, title: 'Эмбеддинги и векторы', completed: true },
      { id: 302, title: 'Пайплайн индексации', completed: false },
      { id: 303, title: 'Retrieval стратегии', completed: false },
      { id: 304, title: 'Hybrid search', completed: false },
    ],
  },
  {
    id: 4,
    order: 4,
    title: 'Агенты и инструменты',
    status: 'locked',
    lessons: [
      { id: 401, title: 'Введение в агентов', completed: false },
      { id: 402, title: 'Tool calling', completed: false },
      { id: 403, title: 'ReAct паттерн', completed: false },
    ],
  },
  {
    id: 5,
    order: 5,
    title: 'Fine-tuning моделей',
    status: 'locked',
    lessons: [
      { id: 501, title: 'Подготовка данных', completed: false },
      { id: 502, title: 'LoRA и QLoRA', completed: false },
      { id: 503, title: 'Оценка качества', completed: false },
    ],
  },
  {
    id: 6,
    order: 6,
    title: 'Продакшн-деплой',
    status: 'locked',
    lessons: [
      { id: 601, title: 'Мониторинг и логирование', completed: false },
      { id: 602, title: 'Оптимизация latency', completed: false },
      { id: 603, title: 'Стратегии кэширования', completed: false },
    ],
  },
];

export const mockLessonContent = {
  302: {
    title: 'Пайплайн индексации',
    content: `**Пайплайн индексации в RAG**

Пайплайн индексации — это процесс подготовки документов для последующего поиска. Он состоит из нескольких ключевых этапов:

1. **Загрузка документов**: Чтение исходных файлов (PDF, MD, TXT)
2. **Чанкинг (разбиение)**: Разделение на небольшие фрагменты
3. **Эмбеддинг**: Преобразование текста в векторы
4. **Индексация**: Сохранение в векторную БД

**Оптимальный размер чанка**

Размер чанка зависит от задачи:
- Для вопросов-ответов: 256-512 токенов
- Для длинного контекста: 1024-2048 токенов
- Учитывайте перекрытие (overlap) 10-20%

Важно балансировать между точностью поиска и сохранением контекста.`,
  },
};

export const mockUser = {
  id: 1,
  email: 'demo@learncore.dev',
  full_name: 'Демо Пользователь',
};

// Simulate API delay
export const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
