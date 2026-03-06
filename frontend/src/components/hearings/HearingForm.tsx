// src/components/hearings/HearingForm.tsx

import React, { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '../common/Input.tsx';
import { Select } from '../common/Select.tsx';
import { DatePicker } from '../common/DatePicker.tsx';
import { Button } from '../common/Button.tsx';
import { Plus, Trash2, UserPlus } from 'lucide-react';
import { CreateHearingData, AddParticipantData, Courtroom, Case } from '../../services/types.ts';
import { courtService } from '../../services/courtService.ts';
import { caseService } from '../../services/caseService.ts';

const participantSchema = z.object({
  email: z.string().email('Invalid email address'),
  role: z.string().min(1, 'Role is required'),
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  bar_number: z.string().optional(),
  court_id: z.string().optional(),
  phone_number: z.string().optional(),
  send_invite: z.boolean().default(true),
});

const hearingSchema = z.object({
  case_id: z.string().min(1, 'Case ID is required'),
  courtroom_id: z.string().min(1, 'Courtroom ID is required'),
  scheduled_at: z.date({ required_error: 'Scheduled date is required' }),
  name: z.string().min(1, 'Hearing name is required'),
  description: z.string().optional(),
  hearing_type: z.string().min(1, 'Hearing type is required'),
  participants: z.array(participantSchema).min(1, 'At least one participant is required'),
});

type HearingFormData = z.infer<typeof hearingSchema>;

const tomorrow = (() => {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(0, 0, 0, 0);
  return d;
})();

interface HearingFormProps {
  initialData?: Partial<HearingFormData>;
  onSubmit: (data: CreateHearingData) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

const BAR_NUMBER_ROLES = ['defence_counsel', 'prosecution_counsel', 'claimant_counsel'];

const roleOptions = [
  { value: '', label: 'Select a role' },
  { value: 'judge', label: 'Judge' },
  { value: 'magistrate', label: 'Magistrate' },
  { value: 'clerk', label: 'Clerk' },
  { value: 'defence_counsel', label: 'Defence Counsel' },
  { value: 'prosecution_counsel', label: 'Prosecution Counsel' },
  { value: 'claimant_counsel', label: 'Claimant Counsel' },
  { value: 'defendant', label: 'Defendant' },
  { value: 'prosecutor', label: 'Prosecutor' },
  { value: 'witness', label: 'Witness' },
  { value: 'juror', label: 'Juror' },
  { value: 'public', label: 'Public' },
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

export const HearingForm: React.FC<HearingFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  loading = false,
}) => {
  const [showParticipantForm, setShowParticipantForm] = useState(false);
  const [currentParticipant, setCurrentParticipant] = useState<Partial<AddParticipantData>>({});
  const [courtrooms, setCourtrooms] = useState<Courtroom[]>([]);
  const [cases, setCases] = useState<Case[]>([]);

  const {
    register,
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<HearingFormData>({
    resolver: zodResolver(hearingSchema),
    defaultValues: {
      participants: initialData?.participants || [],
      ...initialData,
      scheduled_at: initialData?.scheduled_at ? new Date(initialData.scheduled_at) : undefined,
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'participants',
  });

  const scheduledDate = watch('scheduled_at');
  const selectedCourtroomId = watch('courtroom_id');

  useEffect(() => {
    courtService.getCourtrooms().then(setCourtrooms).catch(() => {});
    caseService.getCases().then(setCases).catch(() => {});
  }, []);

  const handleAddParticipant = () => {
    if (currentParticipant.email && currentParticipant.role) {
      const selectedCourtroom = courtrooms.find((r) => r.id === selectedCourtroomId);
      const participantData: AddParticipantData = {
        ...currentParticipant as AddParticipantData,
        court_id: selectedCourtroom?.court || undefined,
        send_invite: true,
      };
      append(participantData);
      setCurrentParticipant({});
      setShowParticipantForm(false);
    }
  };

  const handleRemoveParticipant = (index: number) => {
    remove(index);
  };

  const onSubmitForm = async (data: HearingFormData) => {
    await onSubmit({
      ...data,
      scheduled_at: data.scheduled_at.toISOString(),
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmitForm)} className="space-y-6">
      {/* Basic Information */}
      <div className="bg-gray-50/60 border border-gray-100 p-5 rounded-2xl">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">Basic Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label="Case"
            options={[
              { value: '', label: cases.length === 0 ? 'Loading…' : 'Select case' },
              ...cases.map((c) => ({ value: c.id, label: `${c.case_number} — ${c.title}` })),
            ]}
            {...register('case_id')}
            error={errors.case_id?.message}
          />
          <Select
            label="Courtroom"
            options={[
              { value: '', label: courtrooms.length === 0 ? 'Loading…' : 'Select courtroom' },
              ...courtrooms.map((r) => ({ value: r.id, label: r.name })),
            ]}
            {...register('courtroom_id')}
            error={errors.courtroom_id?.message}
          />
          <Input
            label="Hearing Name"
            {...register('name')}
            error={errors.name?.message}
            placeholder="Enter hearing name"
          />
          <Select
            label="Hearing Type"
            options={hearingTypeOptions}
            {...register('hearing_type')}
            error={errors.hearing_type?.message}
          />
          <div className="md:col-span-2">
            <DatePicker
              label="Scheduled Date & Time"
              selected={scheduledDate}
              onChange={(date) => setValue('scheduled_at', date as Date)}
              error={errors.scheduled_at?.message}
              minDate={tomorrow}
            />
          </div>
          <div className="md:col-span-2">
            <Input
              label="Description (Optional)"
              {...register('description')}
              error={errors.description?.message}
              placeholder="Enter hearing description"
            />
          </div>
        </div>
      </div>

      {/* Participants */}
      <div className="bg-gray-50/60 border border-gray-100 p-5 rounded-2xl">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Participants</h3>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowParticipantForm(true)}
            icon={<UserPlus className="w-4 h-4" />}
          >
            Add Participant
          </Button>
        </div>

        {errors.participants && (
          <p className="text-sm text-red-600 mb-2">{errors.participants.message}</p>
        )}

        {/* Participant List */}
        <div className="space-y-2 mb-4">
          {fields.map((field, index) => (
            <div key={field.id} className="flex items-center gap-3 bg-white border border-gray-100 px-4 py-3 rounded-xl">
              <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-x-4 gap-y-0.5">
                <div className="text-sm text-gray-700">
                  <span className="text-xs text-gray-400 block">Email</span>
                  {field.email}
                </div>
                <div className="text-sm text-gray-700">
                  <span className="text-xs text-gray-400 block">Role</span>
                  {field.role}
                </div>
                {field.first_name && (
                  <div className="text-sm text-gray-700">
                    <span className="text-xs text-gray-400 block">Name</span>
                    {field.first_name} {field.last_name}
                  </div>
                )}
                {field.bar_number && (
                  <div className="text-sm text-gray-700">
                    <span className="text-xs text-gray-400 block">Bar #</span>
                    {field.bar_number}
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={() => handleRemoveParticipant(index)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Add Participant Form */}
        {showParticipantForm && (() => {
          const requiresBarNumber = BAR_NUMBER_ROLES.includes(currentParticipant.role || '');
          const canAdd =
            !!currentParticipant.email &&
            !!currentParticipant.role &&
            !!currentParticipant.first_name &&
            !!currentParticipant.last_name &&
            (!requiresBarNumber || !!currentParticipant.bar_number);

          return (
            <div className="bg-white p-5 rounded-xl border border-gray-200">
              <h4 className="text-sm font-semibold text-gray-700 mb-4">New Participant</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Email *"
                  type="email"
                  value={currentParticipant.email || ''}
                  onChange={(e) => setCurrentParticipant({ ...currentParticipant, email: e.target.value })}
                  placeholder="participant@example.com"
                />
                <Select
                  label="Role *"
                  options={roleOptions}
                  value={currentParticipant.role || ''}
                  onChange={(e) => setCurrentParticipant({ ...currentParticipant, role: e.target.value })}
                />
                <Input
                  label="First Name *"
                  value={currentParticipant.first_name || ''}
                  onChange={(e) => setCurrentParticipant({ ...currentParticipant, first_name: e.target.value })}
                  placeholder="First name"
                />
                <Input
                  label="Last Name *"
                  value={currentParticipant.last_name || ''}
                  onChange={(e) => setCurrentParticipant({ ...currentParticipant, last_name: e.target.value })}
                  placeholder="Last name"
                />
                <Input
                  label={requiresBarNumber ? 'Bar Number *' : 'Bar Number'}
                  value={currentParticipant.bar_number || ''}
                  onChange={(e) => setCurrentParticipant({ ...currentParticipant, bar_number: e.target.value })}
                  placeholder={requiresBarNumber ? 'Required for this role' : 'For lawyers'}
                  helper={requiresBarNumber ? 'Required for counsel roles' : undefined}
                  error={
                    requiresBarNumber && currentParticipant.bar_number === ''
                      ? undefined
                      : undefined
                  }
                />
                <Input
                  label="Phone Number"
                  type="tel"
                  value={currentParticipant.phone_number || ''}
                  onChange={(e) => setCurrentParticipant({ ...currentParticipant, phone_number: e.target.value })}
                  placeholder="Optional"
                />
              </div>
              <div className="flex justify-end gap-2 mt-4">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowParticipantForm(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={handleAddParticipant}
                  disabled={!canAdd}
                >
                  Add
                </Button>
              </div>
            </div>
          );
        })()}
      </div>

      {/* Form Actions */}
      <div className="flex justify-end gap-3 pt-1">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          {initialData ? 'Update Hearing' : 'Create Hearing'}
        </Button>
      </div>
    </form>
  );
};