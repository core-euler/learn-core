import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const TelegramCallbackPage = () => {
  const navigate = useNavigate();
  const { checkAuth } = useAuth();
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      const query = window.location.search || '';
      if (!query || !query.includes('id=')) {
        setError('invalid_telegram_payload');
        return;
      }

      const backendBase = process.env.REACT_APP_BACKEND_URL || '';
      try {
        const response = await fetch(`${backendBase}/api/auth/telegram/callback${query}`, {
          method: 'GET',
          credentials: 'include',
        });

        if (!response.ok) {
          let detail = 'telegram_auth_failed';
          try {
            const data = await response.json();
            detail = data.detail || detail;
          } catch {
            // ignore
          }
          throw new Error(detail);
        }

        await checkAuth();
        navigate('/', { replace: true });
      } catch (err) {
        setError(err.message || 'telegram_auth_failed');
      }
    };

    run();
  }, [navigate, checkAuth]);

  return (
    <div className="min-h-screen bg-[#0d0d0d] flex items-center justify-center px-4">
      <div className="bg-[#141414] border border-[#222222] rounded-lg p-8 max-w-md w-full text-center">
        <h1 className="text-xl text-[#e5e5e5] mb-3">Telegram авторизация</h1>
        {!error ? (
          <p className="text-[#5a5a5a]">Выполняем вход...</p>
        ) : (
          <p className="text-red-400">Ошибка: {error}</p>
        )}
      </div>
    </div>
  );
};

export default TelegramCallbackPage;
