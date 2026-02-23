import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function PrivateRoute() {
  const { user, bootstrapping } = useAuth();
  const location = useLocation();

  if (bootstrapping) return <p>Loading session...</p>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

export function PublicOnlyRoute() {
  const { user, bootstrapping } = useAuth();
  if (bootstrapping) return <p>Loading session...</p>;
  if (user) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
