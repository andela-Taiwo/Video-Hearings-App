// src/pages/HearingDetailPage.tsx

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import {
  Calendar,
  Clock,
  MapPin,
  Users,
  Edit,
  Trash2,
  CalendarClock,
  XCircle,
  UserPlus,
  ArrowLeft,
  FileText,
  Tag,
} from 'lucide-react';
import { useHearings } from '../hooks/useHearings.ts';
import { Button } from '../components/common/Button.tsx';
import { ParticipantList } from '../components/hearings/ParticipantList.tsx';
import { AddParticipantsModal } from '../components/hearings/AddParticipantsModal.tsx';
import { ConfirmDialog } from '../components/common/ConfirmDialog.tsx';
import { Courtroom } from '../services/types.ts';
import { courtService } from '../services/courtService.ts';

const statusConfig: Record<string, { label: string; badge: string; bar: string }> = {
  scheduled: {
    label: 'Scheduled',
    badge: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200',
    bar: 'from-blue-500 to-indigo-600',
  },
  in_progress: {
    label: 'In Progress',
    badge: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
    bar: 'from-emerald-500 to-teal-600',
  },
  completed: {
    label: 'Completed',
    badge: 'bg-gray-100 text-gray-600 ring-1 ring-gray-200',
    bar: 'from-gray-400 to-gray-500',
  },
  cancelled: {
    label: 'Cancelled',
    badge: 'bg-red-50 text-red-700 ring-1 ring-red-200',
    bar: 'from-red-500 to-rose-600',
  },
  postponed: {
    label: 'Postponed',
    badge: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
    bar: 'from-amber-400 to-orange-500',
  },
};

export const HearingDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    selectedHearing,
    loading,
    fetchHearing,
    deleteHearing,
    addParticipants,
    removeParticipants,
    rescheduleHearing,
    cancelHearing,
  } = useHearings();

  const [showAddParticipants, setShowAddParticipants] = useState(false);
  const [showReschedule, setShowReschedule] = useState(false);
  const [showCancel, setShowCancel] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [newDate, setNewDate] = useState('');
  const [newTime, setNewTime] = useState('');
  const [reason, setReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [courtrooms, setCourtrooms] = useState<Courtroom[]>([]);

  useEffect(() => {
    if (id) fetchHearing(id);
  }, [id, fetchHearing]);

  useEffect(() => {
    courtService.getCourtrooms().then(setCourtrooms).catch(() => {});
  }, []);

  if (loading && !selectedHearing) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (!selectedHearing) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900">Hearing not found</h2>
        <p className="mt-2 text-gray-600">The hearing you're looking for doesn't exist.</p>
        <Button className="mt-4" onClick={() => navigate('/hearings')}>Back to Hearings</Button>
      </div>
    );
  }

  const scheduledDate = new Date(selectedHearing.scheduled_at);
  const courtroomUUID = selectedHearing.courtroom || selectedHearing.courtroom_id;
  const hearingCourtroom = courtrooms.find((c) => c.id === courtroomUUID);
  const hearingCourtId = hearingCourtroom?.court;
  const status = statusConfig[selectedHearing.status] ?? statusConfig.scheduled;

  const handleAddParticipants = async (participants: any[]) => {
    setActionLoading(true);
    try {
      await addParticipants(selectedHearing.id, participants);
      setShowAddParticipants(false);
      if (id) fetchHearing(id);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveParticipants = async (participantIds: string[]) => {
    setActionLoading(true);
    try {
      await removeParticipants(selectedHearing.id, participantIds);
      if (id) fetchHearing(id);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReschedule = async () => {
    if (!newDate || !newTime) return;
    setActionLoading(true);
    try {
      await rescheduleHearing(selectedHearing.id, `${newDate}T${newTime}:00`, reason);
      setShowReschedule(false);
      setNewDate('');
      setNewTime('');
      setReason('');
      if (id) fetchHearing(id);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    setActionLoading(true);
    try {
      await cancelHearing(selectedHearing.id, reason);
      setShowCancel(false);
      setReason('');
      if (id) fetchHearing(id);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    setActionLoading(true);
    try {
      await deleteHearing(selectedHearing.id);
      navigate('/hearings');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Back */}
        <button
          onClick={() => navigate('/hearings')}
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Hearings
        </button>

        {/* Hero Header Card */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden mb-6">
          {/* Colour bar */}
          <div className={`h-1.5 w-full bg-gradient-to-r ${status.bar}`} />
          <div className="px-7 py-6">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              {/* Title + meta */}
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ring-inset ${status.badge}`}>
                    {status.label}
                  </span>
                  <span className="text-xs text-gray-400 font-mono bg-gray-50 px-2 py-0.5 rounded-md">
                    #{selectedHearing.id.slice(0, 8)}
                  </span>
                </div>
                <h1 className="text-2xl font-bold text-gray-900 leading-tight mb-1">
                  {selectedHearing.name}
                </h1>
                <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mt-2">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    {format(scheduledDate, 'EEEE, MMMM d, yyyy')}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    {format(scheduledDate, 'h:mm a')}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5" />
                    {selectedHearing.courtroom_name || 'Courtroom'}
                  </span>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex flex-wrap gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/hearings/${id}/edit`)}
                  icon={<Edit className="w-3.5 h-3.5" />}
                >
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAddParticipants(true)}
                  icon={<UserPlus className="w-3.5 h-3.5" />}
                  disabled={courtrooms.length === 0}
                >
                  Add Participants
                </Button>
                {selectedHearing.status === 'scheduled' && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowReschedule(true)}
                      icon={<CalendarClock className="w-3.5 h-3.5" />}
                    >
                      Reschedule
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowCancel(true)}
                      icon={<XCircle className="w-3.5 h-3.5" />}
                    >
                      Cancel
                    </Button>
                  </>
                )}
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => setShowDelete(true)}
                  icon={<Trash2 className="w-3.5 h-3.5" />}
                >
                  Delete
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Sidebar */}
          <div className="space-y-5">

            {/* Info card */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">
                Hearing Details
              </h2>
              <div className="space-y-3.5">
                {[
                  { icon: Tag, label: 'Type', value: selectedHearing.hearing_type?.replace(/_/g, ' ') || '—' },
                  { icon: MapPin, label: 'Courtroom', value: selectedHearing.courtroom_name || '—' },
                  { icon: Users, label: 'Participants', value: `${selectedHearing.participants?.length || 0} added` },
                ].map(({ icon: Icon, label, value }) => (
                  <div key={label} className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
                      <Icon className="w-4 h-4 text-indigo-500" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs text-gray-400">{label}</p>
                      <p className="text-sm font-medium text-gray-800 capitalize truncate">{value}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Description */}
            {selectedHearing.description && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-4 h-4 text-gray-400" />
                  <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Description</h2>
                </div>
                <p className="text-sm text-gray-600 leading-relaxed">{selectedHearing.description}</p>
              </div>
            )}

            {/* Metadata */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
              <div className="flex items-center gap-2 mb-3">
                <Clock className="w-4 h-4 text-gray-400" />
                <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Timeline</h2>
              </div>
              <dl className="space-y-2">
                {selectedHearing.created_at && (
                  <div className="flex justify-between">
                    <dt className="text-xs text-gray-400">Created</dt>
                    <dd className="text-xs text-gray-700">{format(new Date(selectedHearing.created_at), 'MMM d, yyyy')}</dd>
                  </div>
                )}
                {selectedHearing.updated_at && (
                  <div className="flex justify-between">
                    <dt className="text-xs text-gray-400">Last Updated</dt>
                    <dd className="text-xs text-gray-700">{format(new Date(selectedHearing.updated_at), 'MMM d, yyyy')}</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>

          {/* Participants panel */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <ParticipantList
                participants={selectedHearing.participants || []}
                onRemoveParticipants={handleRemoveParticipants}
                loading={actionLoading}
              />
            </div>
          </div>
        </div>

        {/* Modals */}
        <AddParticipantsModal
          isOpen={showAddParticipants}
          onClose={() => setShowAddParticipants(false)}
          onAdd={handleAddParticipants}
          loading={actionLoading}
          courtId={hearingCourtId}
        />

        <ConfirmDialog
          isOpen={showReschedule}
          onClose={() => { setShowReschedule(false); setNewDate(''); setNewTime(''); setReason(''); }}
          onConfirm={handleReschedule}
          title="Reschedule Hearing"
          confirmText="Reschedule"
          cancelText="Cancel"
          type="info"
        >
          <div className="space-y-4 mt-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">New Date</label>
              <input
                type="date"
                value={newDate}
                onChange={(e) => setNewDate(e.target.value)}
                min={format(new Date(), 'yyyy-MM-dd')}
                className="block w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">New Time</label>
              <input
                type="time"
                value={newTime}
                onChange={(e) => setNewTime(e.target.value)}
                className="block w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Reason (Optional)</label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
                className="block w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                placeholder="Enter reason for rescheduling"
              />
            </div>
          </div>
        </ConfirmDialog>

        <ConfirmDialog
          isOpen={showCancel}
          onClose={() => { setShowCancel(false); setReason(''); }}
          onConfirm={handleCancel}
          title="Cancel Hearing"
          message="Are you sure you want to cancel this hearing?"
          confirmText="Cancel Hearing"
          cancelText="Go Back"
          type="warning"
        >
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Reason for Cancellation</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              className="block w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              placeholder="Enter reason for cancellation"
            />
          </div>
        </ConfirmDialog>

        <ConfirmDialog
          isOpen={showDelete}
          onClose={() => setShowDelete(false)}
          onConfirm={handleDelete}
          title="Delete Hearing"
          message={`Are you sure you want to delete "${selectedHearing.name}"? This action cannot be undone.`}
          confirmText="Delete"
          cancelText="Cancel"
          type="danger"
        />
      </div>
    </div>
  );
};
