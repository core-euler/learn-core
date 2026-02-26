import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LectureModePage } from '../pages/LectureModePage';

const mockUseOutletContext = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useOutletContext: () => mockUseOutletContext(),
  };
});

describe('LectureModePage completion flow', () => {
  beforeEach(() => {
    mockUseOutletContext.mockReset();
  });

  it('shows success message when lesson completion succeeds', async () => {
    const onLessonCompleted = vi.fn().mockResolvedValue(undefined);
    mockUseOutletContext.mockReturnValue({ lessonId: 'lesson-1', onLessonCompleted });

    render(<LectureModePage />);

    await userEvent.click(screen.getByRole('button', { name: 'Завершить урок' }));

    expect(onLessonCompleted).toHaveBeenCalledTimes(1);
    expect(await screen.findByText('Урок отмечен как завершённый. Прогресс обновлён.')).toBeInTheDocument();
  });

  it('shows error message when lesson completion fails', async () => {
    const onLessonCompleted = vi.fn().mockRejectedValue(new Error('boom'));
    mockUseOutletContext.mockReturnValue({ lessonId: 'lesson-1', onLessonCompleted });

    render(<LectureModePage />);

    await userEvent.click(screen.getByRole('button', { name: 'Завершить урок' }));

    expect(onLessonCompleted).toHaveBeenCalledTimes(1);
    expect(await screen.findByText('Не удалось завершить урок. Попробуйте ещё раз.')).toBeInTheDocument();
  });
});
