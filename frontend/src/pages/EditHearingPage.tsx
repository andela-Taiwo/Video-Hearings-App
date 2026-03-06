
// In src/pages/EditHearingPage.tsx - Add postponement handling

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Loader2, CalendarClock } from 'lucide-react';
import { useHearings } from '../hooks/useHearings.ts';
import { Button } from '../components/common/Button.tsx';
import { Input } from '../components/common/Input.tsx';
import { Select } from '../components/common/Select.tsx';
import { DatePicker } from '../components/common/DatePicker.tsx';
import { Hearing, Courtroom, Case } from '../services/types.ts';
import { courtService } from '../services/courtService.ts';
import { caseService } from '../services/caseService.ts';

const tomorrow = (() => {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(0, 0, 0, 0);
  return d;
})();

const statusOptions = [
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'postponed', label: 'Postponed' },
];

const hearingTypeOptions = [
  { value: '', label: 'Select hearing type' },
  { value: 'arraignment', label: 'Arraignment' },
  { value: 'bail', label: 'Bail Hearing' },
  { value: 'trial', label: 'Trial' },
  { value: 'sentencing', label: 'Sentencing' },
  { value: 'case_management', label: 'Case Management' },
  { value: 'plea', label: 'Plea Hearing' },
  { value: 'appeal', label: 'Appeal' },
  { value: 'directions', label: 'Directions Hearing' },
];

export const EditHearingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedHearing, loading, fetchHearing, updateHearing } = useHearings();

  const [formData, setFormData] = useState({
    name: '',
    case_id: '',
    courtroom_id: '',
    scheduled_at: null as Date | null,
    hearing_type: '',
    status: 'scheduled' as Hearing['status'],
    description: '',
    // Fields for special status transitions
    new_scheduled_at: null as Date | null,
    postponement_reason: '',
    cancellation_reason: '',
    completion_notes: '',
  });

  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [showPostponementFields, setShowPostponementFields] = useState(false);
  const [courtrooms, setCourtrooms] = useState<Courtroom[]>([]);
  const [cases, setCases] = useState<Case[]>([]);

  useEffect(() => {
    if (id) {
      fetchHearing(id);
    }
  }, [id, fetchHearing]);

  useEffect(() => {
    if (selectedHearing) {
      setFormData({
        name: selectedHearing.name || '',
        case_id: selectedHearing.case.id || '',
        courtroom_id: (selectedHearing as any).courtroom || selectedHearing.courtroom_id || '',
        scheduled_at: selectedHearing.scheduled_at ? new Date(selectedHearing.scheduled_at) : null,
        hearing_type: selectedHearing.hearing_type || '',
        status: selectedHearing.status || 'scheduled',
        description: selectedHearing.description || '',
        new_scheduled_at: null,
        postponement_reason: '',
        cancellation_reason: '',
        completion_notes: '',
      });
    }
  }, [selectedHearing]);

  useEffect(() => {
    courtService.getCourtrooms().then(setCourtrooms).catch(() => {});
    caseService.getCases().then(setCases).catch(() => {});
  }, []);

  // Show postponement fields when status changes to postponed
  useEffect(() => {
    setShowPostponementFields(formData.status === 'postponed');
  }, [formData.status]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.name) newErrors.name = 'Hearing name is required';
    if (!formData.case_id) newErrors.case_id = 'Case ID is required';
    if (!formData.courtroom_id) newErrors.courtroom_id = 'Courtroom ID is required';
    if (!formData.scheduled_at) newErrors.scheduled_at = 'Scheduled date is required';
    if (!formData.hearing_type) newErrors.hearing_type = 'Hearing type is required';
    
    // Additional validation for postponement
    if (formData.status === 'postponed') {
      if (!formData.new_scheduled_at) {
        newErrors.new_scheduled_at = 'New scheduled time is required when postponing a hearing';
      }
      if (!formData.postponement_reason) {
        newErrors.postponement_reason = 'Reason for postponement is required';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);

    if (!validateForm() || !id) return;

    setSaving(true);
    try {
      const updateData: any = {
        name: formData.name,
        case_id: formData.case_id,
        courtroom_id: formData.courtroom_id,
        hearing_type: formData.hearing_type,
        description: formData.description,
        status: formData.status,
      };

      if (formData.status !== 'postponed') {
        updateData.scheduled_at = formData.scheduled_at?.toISOString();
      }

      if (formData.status === 'postponed') {
        updateData.new_scheduled_at = formData.new_scheduled_at?.toISOString();
        updateData.postponement_reason = formData.postponement_reason;
      }

      if (formData.status === 'cancelled' && formData.cancellation_reason) {
        updateData.cancellation_reason = formData.cancellation_reason;
      }

      if (formData.status === 'completed' && formData.completion_notes) {
        updateData.completion_notes = formData.completion_notes;
      }

      await updateHearing(id, updateData);
      navigate(`/hearings/${id}`);
    } catch (error: any) {
      const data = error?.response?.data;
      if (data) {
        // Surface field-level errors into the existing errors map
        const fieldErrors: Record<string, string> = {};
        let generalMessage = '';

        Object.entries(data).forEach(([key, val]) => {
          const msg = Array.isArray(val) ? val.join(' ') : String(val);
          if (key === 'non_field_errors' || key === 'error' || key === 'detail') {
            generalMessage = generalMessage ? `${generalMessage} ${msg}` : msg;
          } else {
            fieldErrors[key] = msg;
          }
        });

        if (Object.keys(fieldErrors).length) setErrors((prev) => ({ ...prev, ...fieldErrors }));
        if (generalMessage) setApiError(generalMessage);
      } else {
        setApiError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-7 h-7 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!selectedHearing && !loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-16">
          <h2 className="text-xl font-semibold text-gray-900">Hearing not found</h2>
          <p className="mt-2 text-sm text-gray-500">The hearing you're trying to edit doesn't exist.</p>
          <Button className="mt-5" onClick={() => navigate('/hearings')}>
            Back to Hearings
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <div className="mb-7">
          <button
            onClick={() => navigate(`/hearings/${id}`)}
            className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Hearing Details
          </button>

          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Edit Hearing</h1>
          <p className="mt-1 text-sm text-gray-500">Update the hearing information below</p>
        </div>

        {/* Edit Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-7 space-y-7">
          {/* Basic Information */}
          <div className="space-y-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest border-b border-gray-100 pb-3">
              Basic Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Hearing Name *"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                error={errors.name}
                placeholder="Enter hearing name"
              />
              <Select
                label="Case *"
                options={[
                  { value: '', label: cases.length === 0 ? 'Loading…' : 'Select case' },
                  ...cases.map((c) => ({ value: c.id, label: `${c.case_number} — ${c.title}` })),
                ]}
                value={formData.case_id}
                onChange={(e) => setFormData({ ...formData, case_id: e.target.value })}
                error={errors.case_id}
              />
              <Select
                label="Courtroom *"
                options={[
                  { value: '', label: courtrooms.length === 0 ? 'Loading…' : 'Select courtroom' },
                  ...courtrooms.map((r) => ({ value: r.id, label: r.name })),
                ]}
                value={formData.courtroom_id}
                onChange={(e) => setFormData({ ...formData, courtroom_id: e.target.value })}
                error={errors.courtroom_id}
              />
              <DatePicker
                label="Scheduled Date & Time *"
                selected={formData.scheduled_at}
                onChange={(date) => setFormData({ ...formData, scheduled_at: date })}
                error={errors.scheduled_at}
                minDate={tomorrow}
              />
              <Select
                label="Hearing Type *"
                options={hearingTypeOptions}
                value={formData.hearing_type}
                onChange={(e) => setFormData({ ...formData, hearing_type: e.target.value })}
                error={errors.hearing_type}
              />
              <Select
                label="Status"
                options={statusOptions}
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as Hearing['status'] })}
              />
            </div>
          </div>

          {/* Postponement Fields */}
          {showPostponementFields && (
            <div className="space-y-4 bg-amber-50 border border-amber-200 p-5 rounded-2xl">
              <h2 className="text-sm font-semibold text-amber-800 flex items-center gap-2">
                <CalendarClock className="w-4 h-4" />
                Postponement Details
              </h2>
              <div className="grid grid-cols-1 gap-4">
                <DatePicker
                  label="New Scheduled Date & Time *"
                  selected={formData.new_scheduled_at}
                  onChange={(date) => setFormData({ ...formData, new_scheduled_at: date })}
                  error={errors.new_scheduled_at}
                  minDate={tomorrow}
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Reason for Postponement *
                  </label>
                  <textarea
                    value={formData.postponement_reason}
                    onChange={(e) => setFormData({ ...formData, postponement_reason: e.target.value })}
                    rows={3}
                    className={`block w-full rounded-xl border px-3.5 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 shadow-sm transition focus:outline-none focus:ring-2 focus:border-transparent resize-none ${
                      errors.postponement_reason
                        ? 'border-red-300 focus:ring-red-500'
                        : 'border-gray-200 focus:ring-indigo-500'
                    }`}
                    placeholder="Enter reason for postponement"
                  />
                  {errors.postponement_reason && (
                    <p className="mt-1.5 text-xs text-red-600">{errors.postponement_reason}</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Cancellation Fields */}
          {formData.status === 'cancelled' && (
            <div className="space-y-4 bg-red-50 border border-red-200 p-5 rounded-2xl">
              <h2 className="text-sm font-semibold text-red-800">Cancellation Details</h2>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Reason for Cancellation
                </label>
                <textarea
                  value={formData.cancellation_reason}
                  onChange={(e) => setFormData({ ...formData, cancellation_reason: e.target.value })}
                  rows={3}
                  className="block w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 shadow-sm transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                  placeholder="Enter reason for cancellation"
                />
              </div>
            </div>
          )}

          {/* Completion Fields */}
          {formData.status === 'completed' && (
            <div className="space-y-4 bg-emerald-50 border border-emerald-200 p-5 rounded-2xl">
              <h2 className="text-sm font-semibold text-emerald-800">Completion Details</h2>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Completion Notes
                </label>
                <textarea
                  value={formData.completion_notes}
                  onChange={(e) => setFormData({ ...formData, completion_notes: e.target.value })}
                  rows={3}
                  className="block w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 shadow-sm transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                  placeholder="Enter completion notes"
                />
              </div>
            </div>
          )}

          {/* Description */}
          <div className="space-y-3">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest border-b border-gray-100 pb-3">
              Additional Information
            </h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Description (Optional)
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
                className="block w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 shadow-sm transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                placeholder="Enter hearing description"
              />
            </div>
          </div>

          {/* API Error Banner */}
          {apiError && (
            <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 flex items-start gap-3">
              <span className="mt-0.5 shrink-0 text-red-500">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.75-11.25a.75.75 0 011.5 0v4.5a.75.75 0 01-1.5 0v-4.5zm.75 7.5a.75.75 0 100-1.5.75.75 0 000 1.5z" clipRule="evenodd" />
                </svg>
              </span>
              <p className="text-sm text-red-700">{apiError}</p>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate(`/hearings/${id}`)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              loading={saving}
              icon={<Save className="w-4 h-4" />}
            >
              Save Changes
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};