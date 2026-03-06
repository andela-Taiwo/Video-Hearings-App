
import { useState, useEffect, useCallback } from 'react';
import { Hearing, HearingFilters, CreateHearingData, UpdateHearingData, AddParticipantData } from '../services/types.ts';
import { hearingService } from '../services/hearingService.ts';
import { useToast } from './useToast.ts';

export const useHearings = (initialFilters?: HearingFilters) => {
  const [hearings, setHearings] = useState<Hearing[]>([]);
  const [selectedHearing, setSelectedHearing] = useState<Hearing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<HearingFilters>(initialFilters || {});
  const { showToast } = useToast();

  const fetchHearings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await hearingService.getHearings(filters);
      setHearings(response.results);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch hearings');
      showToast('Failed to fetch hearings', 'error');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchHearing = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const hearing = await hearingService.getHearing(id);
      setSelectedHearing(hearing);
      return hearing;
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch hearing');
      showToast('Failed to fetch hearing details', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  const createHearing = useCallback(async (data: CreateHearingData) => {
    setLoading(true);
    try {
      const newHearing = await hearingService.createHearing(data);
      setHearings((prev) => [newHearing, ...prev]);
      showToast('Hearing created successfully', 'success');
      return newHearing;
    } catch (err: any) {
      const message = err.response?.data?.message || 'Failed to create hearing';
      showToast(message, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);


const updateHearing = useCallback(async (id: string, data: any) => {
  setLoading(true);
  try {
    // The data will now include postponement fields when status is 'postponed'
    const updated = await hearingService.updateHearing(id, data);
    setHearings((prev) => prev.map((h) => (h.id === id ? updated : h)));
    if (selectedHearing?.id === id) setSelectedHearing(updated);
    showToast('Hearing updated successfully', 'success');
    return updated;
  } catch (err: any) {
    const message = err.response?.data?.message || 
                    err.response?.data?.non_field_errors?.[0] || 
                    'Failed to update hearing';
    showToast(message, 'error');
    throw err;
  } finally {
    setLoading(false);
  }
}, [selectedHearing]);

  const deleteHearing = useCallback(async (id: string) => {
    setLoading(true);
    try {
      await hearingService.deleteHearing(id);
      setHearings((prev) => prev.filter((h) => h.id !== id));
      if (selectedHearing?.id === id) setSelectedHearing(null);
      showToast('Hearing deleted successfully', 'success');
    } catch (err: any) {
      const message = err.response?.data?.message || 'Failed to delete hearing';
      showToast(message, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [selectedHearing]);

  const addParticipants = useCallback(async (id: string, participants: AddParticipantData[]) => {
    setLoading(true);
    try {
      // Backend returns the full updated hearing object
      const updatedHearing = await hearingService.addParticipants(id, participants);
      setHearings((prev) =>
        prev.map((h) => (h.id === id ? updatedHearing : h))
      );
      if (selectedHearing?.id === id) {
        setSelectedHearing(updatedHearing);
      }
      showToast('Participants added successfully', 'success');
      return updatedHearing;
    } catch (err: any) {
      const message = err.response?.data?.message || 'Failed to add participants';
      showToast(message, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [selectedHearing]);

  const removeParticipants = useCallback(
    async (id: string, participantIds: string[]) => {
      setLoading(true);
      try {
        await hearingService.removeParticipants(id, participantIds);
        setHearings((prev) =>
          prev.map((h) =>
            h.id === id
              ? { ...h, participants: h.participants?.filter((p) => !participantIds.includes(p.id)) }
              : h
          )
        );
        if (selectedHearing?.id === id) {
          setSelectedHearing((prev) =>
            prev
              ? { ...prev, participants: prev.participants?.filter((p) => !participantIds.includes(p.id)) }
              : prev
          );
        }
        showToast('Participants removed successfully', 'success');
      } catch (err: any) {
        const message = err.response?.data?.message || 'Failed to remove participants';
        showToast(message, 'error');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [selectedHearing]
  );

  const rescheduleHearing = useCallback(async (id: string, scheduled_at: string, reason?: string) => {
    setLoading(true);
    try {
      const updated = await hearingService.rescheduleHearing(id, scheduled_at, reason);
      setHearings((prev) => prev.map((h) => (h.id === id ? updated : h)));
      if (selectedHearing?.id === id) setSelectedHearing(updated);
      showToast('Hearing rescheduled successfully', 'success');
      return updated;
    } catch (err: any) {
      const message = err.response?.data?.message || 'Failed to reschedule hearing';
      showToast(message, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [selectedHearing]);

  const cancelHearing = useCallback(async (id: string, reason?: string) => {
    setLoading(true);
    try {
      const updated = await hearingService.cancelHearing(id, reason);
      setHearings((prev) => prev.map((h) => (h.id === id ? updated : h)));
      if (selectedHearing?.id === id) setSelectedHearing(updated);
      showToast('Hearing cancelled successfully', 'success');
      return updated;
    } catch (err: any) {
      const message = err.response?.data?.message || 'Failed to cancel hearing';
      showToast(message, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [selectedHearing]);

  useEffect(() => {
    fetchHearings();
  }, [fetchHearings]);

  return {
    hearings,
    selectedHearing,
    loading,
    error,
    filters,
    setFilters,
    fetchHearings,
    fetchHearing,
    createHearing,
    updateHearing,
    deleteHearing,
    addParticipants,
    removeParticipants,
    rescheduleHearing,
    cancelHearing,
  };
};