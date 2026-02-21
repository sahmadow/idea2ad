import { Navigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { auth } = useAppContext();

  if (auth.isLoading) return null; // wait for auth check
  if (!auth.isAuthenticated) return <Navigate to="/" replace />;

  return <>{children}</>;
}
