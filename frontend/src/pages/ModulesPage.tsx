import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { ModulesResponse } from '../types/api';

export function ModulesPage() {
  const [data, setData] = useState<ModulesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.modules().then(setData).catch(() => setError('Ошибка загрузки модулей'));
  }, []);

  if (error) return <p>{error}</p>;
  if (!data) return <p>Loading modules...</p>;

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
