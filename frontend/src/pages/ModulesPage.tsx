import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { ModulesResponse } from '../types/api';

export function ModulesPage() {
  const [data, setData] = useState<ModulesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadModules = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.modules();
      setData(response);
    } catch {
      setError('Ошибка загрузки модулей');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadModules();
  }, []);

  if (loading) return <p>Loading modules...</p>;
  if (error) {
    return (
      <section>
        <p className="error">{error}</p>
        <button type="button" onClick={() => void loadModules()}>Повторить</button>
      </section>
    );
  }
  if (!data || data.modules.length === 0) return <p>Модули пока отсутствуют.</p>;

  return (
    <section>
      <h1>Modules</h1>
      <ul>
        {data.modules.map((m) => (
          <li key={m.id}>
            <Link to={`/modules/${m.id}`}>{m.title}</Link> ({m.lessons_count} lessons)
          </li>
        ))}
      </ul>
    </section>
  );
}
