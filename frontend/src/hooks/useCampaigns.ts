/**
 * Custom hook for campaign management
 */
import { useState, useCallback } from 'react';
import type { Campaign, CampaignDetail } from '../types/campaign';
import {
  listCampaigns as apiListCampaigns,
  getCampaign as apiGetCampaign,
  saveCampaign as apiSaveCampaign,
  updateCampaign as apiUpdateCampaign,
  deleteCampaign as apiDeleteCampaign,
} from '../api/campaigns';
import type { CampaignDraft } from '../api';

interface UseCampaignsReturn {
  campaigns: Campaign[];
  selectedCampaign: CampaignDetail | null;
  isLoading: boolean;
  error: string | null;
  fetchCampaigns: (statusFilter?: string) => Promise<void>;
  fetchCampaign: (id: string) => Promise<void>;
  saveCampaign: (name: string, draft: CampaignDraft) => Promise<Campaign>;
  updateCampaign: (id: string, updates: { name?: string; status?: string; objective?: string; budget_daily?: number }) => Promise<void>;
  removeCampaign: (id: string) => Promise<void>;
  clearSelected: () => void;
  clearError: () => void;
}

export function useCampaigns(): UseCampaignsReturn {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<CampaignDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCampaigns = useCallback(async (statusFilter?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiListCampaigns(statusFilter);
      setCampaigns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch campaigns');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchCampaign = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiGetCampaign(id);
      setSelectedCampaign(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch campaign');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveCampaign = useCallback(async (name: string, draft: CampaignDraft): Promise<Campaign> => {
    setIsLoading(true);
    setError(null);
    try {
      const campaign = await apiSaveCampaign({
        name,
        campaign_draft: draft as unknown as Record<string, unknown>,
      });
      setCampaigns(prev => [campaign, ...prev]);
      return campaign;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save campaign';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateCampaign = useCallback(async (
    id: string,
    updates: { name?: string; status?: string; objective?: string; budget_daily?: number }
  ) => {
    setIsLoading(true);
    setError(null);
    try {
      const updated = await apiUpdateCampaign(id, updates);
      setCampaigns(prev => prev.map(c => c.id === id ? updated : c));
      if (selectedCampaign?.id === id) {
        setSelectedCampaign(prev => prev ? { ...prev, ...updated } : null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update campaign');
    } finally {
      setIsLoading(false);
    }
  }, [selectedCampaign?.id]);

  const removeCampaign = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await apiDeleteCampaign(id);
      setCampaigns(prev => prev.filter(c => c.id !== id));
      if (selectedCampaign?.id === id) {
        setSelectedCampaign(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete campaign');
    } finally {
      setIsLoading(false);
    }
  }, [selectedCampaign?.id]);

  const clearSelected = useCallback(() => setSelectedCampaign(null), []);
  const clearError = useCallback(() => setError(null), []);

  return {
    campaigns,
    selectedCampaign,
    isLoading,
    error,
    fetchCampaigns,
    fetchCampaign,
    saveCampaign,
    updateCampaign,
    removeCampaign,
    clearSelected,
    clearError,
  };
}
