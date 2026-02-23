import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';
import { AuthProvider } from '../contexts/AuthContext';

function renderApp() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>,
  );
}

describe('frontend smoke', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('redirects unauthorized private route to login', async () => {
    window.history.pushState({}, '', '/dashboard');
    vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'missing_access' }), { status: 401, headers: { 'Content-Type': 'application/json' } }));

    renderApp();
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Login' })).toBeInTheDocument());
  });

  it('renders dashboard with continue CTA', async () => {
    window.history.pushState({}, '', '/dashboard');
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 'u1', email: 'a@b.c', first_name: 'A', auth_method: 'email' }), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ overall_percent: 33, next_lesson_id: 'lesson-42', consultant_unlocked: false, modules: [] }),
          { status: 200 },
        ),
      );

    renderApp();

    await waitFor(() => expect(screen.getByText('Общий прогресс: 33%')).toBeInTheDocument());
    expect(screen.getByRole('link', { name: 'Продолжить' })).toHaveAttribute('href', '/lessons/lesson-42/lecture');
  });
});
