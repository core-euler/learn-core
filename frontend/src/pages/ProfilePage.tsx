import { useAuth } from '../contexts/AuthContext';

export function ProfilePage() {
  const { user } = useAuth();
  return (
    <section>
      <h1>Profile</h1>
      <p>ID: {user?.id}</p>
      <p>Name: {user?.first_name}</p>
      <p>Auth: {user?.auth_method}</p>
    </section>
  );
}
