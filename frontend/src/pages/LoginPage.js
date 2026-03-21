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
    const botUsername = process.env.REACT_APP_TELEGRAM_BOT_USERNAME || '';
    if (!botUsername) {
      setError('REACT_APP_TELEGRAM_BOT_USERNAME не задан');
      return;
    }
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
            className="w-full bg-[#0088cc] hover:bg-[#0077b3] text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            data-testid="telegram-login-button"
          >
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
