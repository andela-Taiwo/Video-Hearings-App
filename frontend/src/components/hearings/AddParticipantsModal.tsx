// src/components/hearings/AddParticipantsModal.tsx

import React, { useState } from 'react';
import { Modal } from '../common/Modal.tsx';
import { Button } from '../common/Button.tsx';
import { Input } from '../common/Input.tsx';
import { Select } from '../common/Select.tsx';
import { Plus, X } from 'lucide-react';
import { AddParticipantData } from '../../services/types.ts';

interface AddParticipantsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (participants: AddParticipantData[]) => Promise<void>;
  loading?: boolean;
  /** Parent court UUID derived from the hearing's courtroom — auto-set on each participant */
  courtId?: string;
}

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
];

const BAR_NUMBER_ROLES = new Set([
  'defence_counsel',
  'prosecution_counsel',
  'claimant_counsel',
]);

const COURT_ID_ROLES = new Set(['judge', 'magistrate', 'clerk']);

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const isValidEmail = (email: string) => EMAIL_RE.test(email.trim());

const emptyParticipant = (): AddParticipantData => ({
  email: '',
  role: '',
  send_invite: true,
});

export const AddParticipantsModal: React.FC<AddParticipantsModalProps> = ({
  isOpen,
  onClose,
  onAdd,
  loading = false,
  courtId,
}) => {
  const [participants, setParticipants] = useState<AddParticipantData[]>([emptyParticipant()]);
  const [emailErrors, setEmailErrors] = useState<Record<number, string>>({});

  const handleAddParticipant = () => {
    setParticipants([...participants, emptyParticipant()]);
  };

  const handleRemoveParticipant = (index: number) => {
    setParticipants(participants.filter((_, i) => i !== index));
    setEmailErrors((prev) => {
      const next = { ...prev };
      delete next[index];
      return next;
    });
  };

  const handleParticipantChange = (index: number, field: keyof AddParticipantData, value: any) => {
    const updated = [...participants];
    updated[index] = { ...updated[index], [field]: value };
    setParticipants(updated);
    if (field === 'email') {
      setEmailErrors((prev) => ({
        ...prev,
        [index]: value && !isValidEmail(value) ? 'Enter a valid email address' : '',
      }));
    }
  };

  const isValid = (p: AddParticipantData, index: number) => {
    const requiresBarNumber = BAR_NUMBER_ROLES.has(p.role);
    return (
      !!p.email &&
      isValidEmail(p.email) &&
      !!p.role &&
      !!p.first_name &&
      !!p.last_name &&
      (!requiresBarNumber || !!p.bar_number) &&
      !emailErrors[index]
    );
  };

  const handleSubmit = async () => {
    const validParticipants = participants
      .filter((p, i) => isValid(p, i))
      .map((p) => {
        const needsCourt = COURT_ID_ROLES.has(p.role);
        if (needsCourt && !courtId) {
          console.warn('court_id required for role', p.role, 'but courtId prop is missing');
        }
        return {
          ...p,
          send_invite: true,
          ...(needsCourt && courtId ? { court_id: courtId } : {}),
        };
      });

    if (validParticipants.length > 0) {
      await onAdd(validParticipants);
      setParticipants([emptyParticipant()]);
      setEmailErrors({});
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Participants"
      size="lg"
      footer={
        <div className="flex justify-end space-x-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            loading={loading}
            disabled={!participants.some((p, i) => isValid(p, i))}
          >
            {(() => {
              const count = participants.filter((p, i) => isValid(p, i)).length;
              return `Add ${count} Participant${count !== 1 ? 's' : ''}`;
            })()}
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Add participants to this hearing. All fields marked with * are required.
        </p>

        {participants.map((participant, index) => {
          const requiresBarNumber = BAR_NUMBER_ROLES.has(participant.role);
          return (
            <div key={index} className="bg-gray-50 border border-gray-100 p-4 rounded-xl relative">
              {participants.length > 1 && (
                <button
                  onClick={() => handleRemoveParticipant(index)}
                  className="absolute top-3 right-3 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Input
                  label="First Name *"
                  value={participant.first_name || ''}
                  onChange={(e) => handleParticipantChange(index, 'first_name', e.target.value)}
                  placeholder="First name"
                />
                <Input
                  label="Last Name *"
                  value={participant.last_name || ''}
                  onChange={(e) => handleParticipantChange(index, 'last_name', e.target.value)}
                  placeholder="Last name"
                />
                <Input
                  label="Email *"
                  type="email"
                  value={participant.email}
                  onChange={(e) => handleParticipantChange(index, 'email', e.target.value)}
                  placeholder="participant@example.com"
                  error={emailErrors[index] || undefined}
                  required
                />
                <Select
                  label="Role *"
                  options={roleOptions}
                  value={participant.role}
                  onChange={(e) => handleParticipantChange(index, 'role', e.target.value)}
                  required
                />
                <Input
                  label="Phone Number"
                  value={participant.phone_number || ''}
                  onChange={(e) => handleParticipantChange(index, 'phone_number', e.target.value)}
                  placeholder="Phone number"
                />
                {requiresBarNumber && (
                  <Input
                    label="Bar Number *"
                    value={participant.bar_number || ''}
                    onChange={(e) => handleParticipantChange(index, 'bar_number', e.target.value)}
                    placeholder="e.g. 12345"
                    helper="Required for counsel roles"
                  />
                )}
              </div>
            </div>
          );
        })}

        <Button
          type="button"
          variant="outline"
          onClick={handleAddParticipant}
          icon={<Plus className="w-4 h-4" />}
          fullWidth
        >
          Add Another Participant
        </Button>
      </div>
    </Modal>
  );
};