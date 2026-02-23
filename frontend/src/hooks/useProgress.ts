import { useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';
import type { ProgressResponse } from '../types/api';

export function useProgress() {
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await api.progress());
    } catch {
      setError('Не удалось загрузить прогресс');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload };
}
