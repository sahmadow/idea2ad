/**
 * Custom hook for Facebook OAuth flow
 */
import { useState, useEffect, useCallback } from 'react';
import type { FBStatusResponse, FBAuthMessage } from '../types/facebook';
import {
  getFBStatus,
  getOAuthUrl,
  getStoredSessionId,
  storeSessionId,
  clearSessionId,
  disconnectFacebook,
} from '../api/facebook';

interface UseFacebookAuthReturn {
  // State
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  status: FBStatusResponse | null;

  // Actions
  connect: () => void;
  disconnect: () => Promise<void>;
  refreshStatus: () => Promise<void>;
}

export function useFacebookAuth(): UseFacebookAuthReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<FBStatusResponse | null>(null);

  // Check status and update state
  const refreshStatus = useCallback(async (sid?: string) => {
    const targetSessionId = sid || sessionId || getStoredSessionId();
    setIsLoading(true);
    setError(null);

    try {
      const statusResponse = await getFBStatus(targetSessionId || undefined);
      setStatus(statusResponse);
      setIsConnected(statusResponse.connected);

      if (!statusResponse.connected && targetSessionId) {
        // Session invalid, clear it
        clearSessionId();
        setSessionId(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check status');
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Handle OAuth messages from popup
  useEffect(() => {
    const handleMessage = (event: MessageEvent<FBAuthMessage>) => {
      // Verify origin in production
      if (!event.data || typeof event.data !== 'object') return;

      if (event.data.type === 'FB_AUTH_SUCCESS') {
        const newSessionId = event.data.session_id;

        // CRITICAL: Clear old session before storing new one
        // This prevents session conflicts when switching Facebook accounts
        // Backend already deleted old DB sessions, but we need to clear frontend state
        clearSessionId();
        setSessionId(null);
        setIsConnected(false);
        setStatus(null);

        // Now store the new session
        storeSessionId(newSessionId);
        setSessionId(newSessionId);
        setError(null);

        // Refresh status with new session
        refreshStatus(newSessionId);
      } else if (event.data.type === 'FB_AUTH_ERROR') {
        setError(event.data.error);
        setIsConnected(false);
        setIsLoading(false);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [refreshStatus]);

  // Initial status check
  useEffect(() => {
    const storedId = getStoredSessionId();
    if (storedId) {
      setSessionId(storedId);
    }
    refreshStatus(storedId || undefined);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Open OAuth popup
  const connect = useCallback(() => {
    setError(null);
    const width = 600;
    const height = 700;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2;

    window.open(
      getOAuthUrl(),
      'fb_oauth',
      `width=${width},height=${height},left=${left},top=${top},popup=1`
    );
  }, []);

  // Disconnect and clear session
  const disconnect = useCallback(async () => {
    setIsLoading(true);
    try {
      await disconnectFacebook(sessionId || undefined);
      setSessionId(null);
      setIsConnected(false);
      setStatus(null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  return {
    isConnected,
    isLoading,
    error,
    sessionId,
    status,
    connect,
    disconnect,
    refreshStatus: () => refreshStatus(),
  };
}
