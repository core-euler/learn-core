import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  const handleTelegramLogin = () => {
    // Placeholder for Telegram OAuth
    const botUsername = process.env.REACT_APP_TELEGRAM_BOT_USERNAME || 'YourBot';
    const redirectUrl = `${window.location.origin}/auth/telegram/callback`;
    window.location.href = `https://t.me/${botUsername}?start=auth`;
  };

  return (
    <div className="min-h-screen bg-[#0d0d0d] flex items-center justify-center px-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] opacity-[0.03]">
          <div className="w-full h-full rounded-full bg-gradient-to-br from-[#FA9042] to-[#8885FF] blur-[120px]"></div>
        </div>
      </div>

      <div className="relative w-full max-w-md">
        <div className="bg-[#141414] border border-[#222222] rounded-lg p-8 shadow-2xl">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-2">
              <h1 className="text-3xl font-bold text-[#e5e5e5]" style={{ fontFamily: '"Geist", sans-serif' }}>
                LearnCore
              </h1>
              <div className="w-2 h-2 rounded-full bg-[#8885FF] animate-pulse"></div>
            </div>
            <p className="text-[#5a5a5a] text-sm">Войдите чтобы продолжить обучение</p>
          </div>

          <button
            onClick={handleTelegramLogin}
            className="w-full bg-[#0088cc] hover:bg-[#0077b3] text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 mb-4"
            data-testid="telegram-login-button"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18.717-1.969 9.27-2.566 11.799-.25 1.063-.742 1.42-1.219 1.455-1.035.095-1.822-.683-2.824-1.34-1.567-.999-2.451-1.621-3.975-2.597-1.763-1.127-.618-1.748.384-2.761.262-.263 4.818-4.418 4.905-4.794.011-.047.021-.223-.083-.316-.103-.093-.256-.061-.366-.036-.157.036-2.656 1.688-7.499 4.96-.709.487-1.35.724-1.925.711-.634-.014-1.853-.359-2.761-.653-.969-.307-1.738-.469-1.669-1.001.036-.277.431-.559 1.184-.849 4.636-2.021 7.726-3.354 9.271-3.999 4.416-1.839 5.32-2.16 5.916-2.171.131-.003.425.03.615.184.16.13.204.305.226.428.022.123.051.404.029.623z"/>
            </svg>
            Войти через Telegram
          </button>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#222222]"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-[#141414] text-[#5a5a5a]">или</span>
            </div>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#1c1c1c] border border-[#222222] text-[#e5e5e5] px-4 py-3 rounded-lg focus:outline-none focus:border-[#8885FF] focus:ring-1 focus:ring-[#8885FF] transition-colors"
                required
                data-testid="email-input"
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Пароль"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#1c1c1c] border border-[#222222] text-[#e5e5e5] px-4 py-3 rounded-lg focus:outline-none focus:border-[#8885FF] focus:ring-1 focus:ring-[#8885FF] transition-colors"
                required
                data-testid="password-input"
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-2 rounded-lg text-sm" data-testid="error-message">
                {error}
              </div>
            )}

            <div className="bg-[#8885FF]/10 border border-[#8885FF]/20 text-[#8885FF] px-3 py-2 rounded text-xs">
              💡 Демо: demo@learncore.dev / demo
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#8885FF] hover:bg-[#7774ee] disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors"
              data-testid="login-submit-button"
            >
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
