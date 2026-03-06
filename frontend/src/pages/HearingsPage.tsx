
import React, { useState, useEffect,  useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { HearingList } from '../components/hearings/HearingList.tsx';
import { HearingForm } from '../components/hearings/HearingForm.tsx';
import { HearingFilters } from '../components/hearings/HearingFilters.tsx';
import { AddParticipantsModal } from '../components/hearings/AddParticipantsModal.tsx';
import { Modal } from '../components/common/Modal.tsx';
import { ConfirmDialog } from '../components/common/ConfirmDialog.tsx';
import { Plus, Scale, CalendarClock, Activity, CheckCircle2, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { useHearings } from '../hooks/useHearings.ts';
import { Hearing, CreateHearingData, AddParticipantData, Courtroom } from '../services/types.ts';
import { courtService } from '../services/courtService.ts';
import { hearingService } from '../services/hearingService.ts';

export const HearingsPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    hearings,
    loading,
    error, // ✅ This is the key - now we'll use it!
    filters,
    setFilters,
    fetchHearings,
    createHearing,
    deleteHearing,
    addParticipants,
  } = useHearings();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddParticipantsModal, setShowAddParticipantsModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedHearing, setSelectedHearing] = useState<Hearing | null>(null);
  const [creating, setCreating] = useState(false);
  const [courtrooms, setCourtrooms] = useState<Courtroom[]>([]);
  const [statusCounts, setStatusCounts] = useState({ scheduled: 0, in_progress: 0, completed: 0, cancelled: 0 });
  const [statsError, setStatsError] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);

  const fetchStatusCounts = useCallback(async () => {
    setStatsLoading(true);
    setStatsError(false);
    try {
      const [scheduledRes, inProgressRes, completedRes, cancelledRes] = await Promise.all([
        hearingService.getHearings({ status: 'scheduled' }),
        hearingService.getHearings({ status: 'in_progress' }),
        hearingService.getHearings({ status: 'completed' }),
        hearingService.getHearings({ status: 'cancelled' }),
      ]);
      
      setStatusCounts({
        scheduled: scheduledRes.count,
        in_progress: inProgressRes.count,
        completed: completedRes.count,
        cancelled: cancelledRes.count,
      });
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      setStatsError(true);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    courtService.getCourtrooms()
      .then(setCourtrooms)
      .catch(() => {});
    fetchStatusCounts();
  }, [fetchStatusCounts]);

  const refreshStats = () => fetchStatusCounts();

  const handleCreateHearing = async (data: CreateHearingData) => {
    setCreating(true);
    try {
      await createHearing(data);
      setShowCreateModal(false);
      refreshStats();
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteHearing = async () => {
    if (selectedHearing) {
      await deleteHearing(selectedHearing.id);
      setShowDeleteConfirm(false);
      setSelectedHearing(null);
      refreshStats();
    }
  };

  const handleAddParticipants = async (participants: AddParticipantData[]) => {
    if (selectedHearing) {
      await addParticipants(selectedHearing.id, participants);
      setShowAddParticipantsModal(false);
      setSelectedHearing(null);
      fetchHearings();
    }
  };

  const handleRetry = () => {
    fetchHearings();
    refreshStats();
  };

  // ✅ SHOW ERROR STATE
  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Failed to Load Hearings</h2>
          <p className="text-gray-600 mb-6">
            {error}
          </p>
          <button
            onClick={handleRetry}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const { scheduled, in_progress: inProgress, completed, cancelled } = statusCounts;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero banner */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 relative overflow-hidden">
        {/* Decorative rings */}
        <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full border border-white/5" />
        <div className="absolute -top-10 -right-10 w-56 h-56 rounded-full border border-white/5" />
        <div className="absolute bottom-0 left-0 w-64 h-64 rounded-full border border-white/5 -translate-x-1/2 translate-y-1/2" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-0">
          {/* Top row */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-5 mb-8">
            <div>
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-9 h-9 rounded-xl bg-white/10 backdrop-blur flex items-center justify-center ring-1 ring-white/20">
                  <Scale className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-semibold text-indigo-300 uppercase tracking-widest">
                  Case Docket
                </span>
              </div>
              <h1 className="text-4xl font-bold text-white tracking-tight leading-tight">
                Court Hearings
              </h1>
              <p className="mt-1.5 text-sm text-slate-400">
                Schedule, manage, and track all court proceedings in one place.
              </p>
            </div>

            <button
              onClick={() => setShowCreateModal(true)}
              className="shrink-0 inline-flex items-center gap-2 px-5 py-2.5 bg-white text-slate-900 text-sm font-semibold rounded-xl shadow-lg hover:bg-indigo-50 active:scale-95 transition-all"
            >
              <Plus className="w-4 h-4" />
              Schedule Hearing
            </button>
          </div>

          {/* Stat strip with loading/error states */}
          {statsError ? (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-8 flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-800">
                <AlertCircle className="w-5 h-5" />
                <span>Unable to load statistics</span>
              </div>
              <button
                onClick={refreshStats}
                className="text-sm text-amber-800 hover:text-amber-900 underline"
              >
                Retry
              </button>
            </div>
          ) : statsLoading ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center gap-3 rounded-xl px-4 py-3 ring-1 bg-white/5 ring-white/10 animate-pulse">
                  <div className="w-5 h-5 bg-white/10 rounded" />
                  <div className="flex-1">
                    <div className="h-3 bg-white/10 rounded w-16 mb-1" />
                    <div className="h-6 bg-white/10 rounded w-8" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pb-8">
              {[
                { label: 'Upcoming', value: scheduled, icon: CalendarClock, color: 'text-blue-300', bg: 'bg-blue-500/10 ring-blue-500/20' },
                { label: 'In Progress', value: inProgress, icon: Activity, color: 'text-emerald-300', bg: 'bg-emerald-500/10 ring-emerald-500/20' },
                { label: 'Completed', value: completed, icon: CheckCircle2, color: 'text-slate-300', bg: 'bg-white/5 ring-white/10' },
                { label: 'Cancelled', value: cancelled, icon: XCircle, color: 'text-rose-300', bg: 'bg-rose-500/10 ring-rose-500/20' },
              ].map(({ label, value, icon: Icon, color, bg }) => (
                <div key={label} className={`flex items-center gap-3 rounded-xl px-4 py-3 ring-1 ${bg}`}>
                  <Icon className={`w-5 h-5 shrink-0 ${color}`} />
                  <div>
                    <p className="text-[11px] font-medium text-slate-400 leading-none mb-1">{label}</p>
                    <p className="text-2xl font-bold text-white leading-none">{value}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <HearingFilters filters={filters} onFilterChange={setFilters} />

        <HearingList
          hearings={filters.status ? hearings : hearings.filter(h => h.status !== 'cancelled')}
          loading={loading}
          onHearingClick={(h) => navigate(`/hearings/${h.id}`)}
          onEdit={(h) => navigate(`/hearings/${h.id}/edit`)}
          onDelete={(h) => { setSelectedHearing(h); setShowDeleteConfirm(true); }}
          onAddParticipants={(h) => { setSelectedHearing(h); setShowAddParticipantsModal(true); }}
        />
      </div>

      {/* Create Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Schedule New Hearing" size="xl">
        <HearingForm
          onSubmit={handleCreateHearing}
          onCancel={() => setShowCreateModal(false)}
          loading={creating}
        />
      </Modal>

      {/* Add Participants Modal */}
      <AddParticipantsModal
        isOpen={showAddParticipantsModal}
        onClose={() => { setShowAddParticipantsModal(false); setSelectedHearing(null); }}
        onAdd={handleAddParticipants}
        loading={loading}
        courtId={
          courtrooms.find(
            (c) => c.id === (selectedHearing?.courtroom || selectedHearing?.courtroom_id)
          )?.court
        }
      />

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => { setShowDeleteConfirm(false); setSelectedHearing(null); }}
        onConfirm={handleDeleteHearing}
        title="Delete Hearing"
        message={`Are you sure you want to delete "${selectedHearing?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        type="danger"
      />
    </div>
  );
};