import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ApiError } from '../utils/http';

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await register(email, password);
      navigate('/login');
    } catch (err) {
      if (err instanceof ApiError && err.detail === 'email_exists') setError('Email уже зарегистрирован');
      else setError('Не удалось зарегистрироваться');
    }
  }

  return (
    <section className="auth">
      <h1>Register</h1>
      <form onSubmit={onSubmit}>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" minLength={8} required />
        <button type="submit">Create account</button>
      </form>
      {error && <p className="error">{error}</p>}
      <p>
        Уже есть аккаунт? <Link to="/login">Login</Link>
      </p>
    </section>
  );
}
