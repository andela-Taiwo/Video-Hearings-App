
import React, { useState } from 'react';
import { Participant } from '../../services/types.ts';
import { Button } from '../common/Button.tsx';
import { Input } from '../common/Input.tsx';
import { Select } from '../common/Select.tsx';
import { UserMinus, Mail, Search, Users } from 'lucide-react';

interface ParticipantListProps {
  participants: Participant[];
  onRemoveParticipants: (participantIds: string[]) => Promise<void>;
  loading?: boolean;
}

const roleColors: Record<string, string> = {
  judge: 'bg-purple-50 text-purple-700 ring-purple-200',
  magistrate: 'bg-violet-50 text-violet-700 ring-violet-200',
  clerk: 'bg-blue-50 text-blue-700 ring-blue-200',
  defence_counsel: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
  prosecution_counsel: 'bg-red-50 text-red-700 ring-red-200',
  claimant_counsel: 'bg-orange-50 text-orange-700 ring-orange-200',
  defendant: 'bg-rose-50 text-rose-700 ring-rose-200',
  prosecutor: 'bg-pink-50 text-pink-700 ring-pink-200',
  witness: 'bg-gray-100 text-gray-600 ring-gray-200',
};

function getInitials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('');
}

export const ParticipantList: React.FC<ParticipantListProps> = ({
  participants = [],
  onRemoveParticipants,
  loading = false,
}) => {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const uniqueRoles = Array.from(new Set(participants.map((p) => p.role).filter(Boolean)));
  const roleOptions = [
    { value: '', label: 'All Roles' },
    ...uniqueRoles.map((r) => ({ value: r, label: r.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) })),
  ];

  const filtered = participants.filter((p) => {
    if (!p) return false;
    const name = (p.user_name || '').toLowerCase();
    const email = (p.user_email || '').toLowerCase();
    const term = searchTerm.toLowerCase();
    const matchesSearch = !term || name.includes(term) || email.includes(term);
    const matchesRole = !roleFilter || p.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const allSelected = filtered.length > 0 && filtered.every((p) => selectedIds.includes(p.id));

  const toggleAll = () =>
    setSelectedIds(allSelected ? [] : filtered.map((p) => p.id).filter(Boolean));

  const toggleOne = (pid: string) =>
    setSelectedIds((prev) =>
      prev.includes(pid) ? prev.filter((id) => id !== pid) : [...prev, pid]
    );

  const handleRemoveSelected = async () => {
    if (selectedIds.length > 0) {
      await onRemoveParticipants(selectedIds);
      setSelectedIds([]);
    }
  };

  if (participants.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-14 text-center">
        <div className="w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
          <Users className="w-7 h-7 text-gray-400" />
        </div>
        <h3 className="text-base font-semibold text-gray-800 mb-1">No Participants Yet</h3>
        <p className="text-sm text-gray-500">Add participants to this hearing using the button above.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">
          Participants
          <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-indigo-50 text-indigo-600 rounded-full">
            {participants.length}
          </span>
        </h3>
        {selectedIds.length > 0 && (
          <Button
            variant="danger"
            size="sm"
            onClick={handleRemoveSelected}
            loading={loading}
            icon={<UserMinus className="w-3.5 h-3.5" />}
          >
            Remove {selectedIds.length} selected
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
          <Input
            placeholder="Search by name or email…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select
          options={roleOptions}
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="w-44"
        />
      </div>

      {/* List */}
      <div className="divide-y divide-gray-100 rounded-xl border border-gray-100 overflow-hidden">
        {/* Select-all header */}
        <div className="flex items-center gap-3 px-4 py-2.5 bg-gray-50">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={toggleAll}
            disabled={filtered.length === 0}
            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          />
          <span className="text-xs font-medium text-gray-500">
            {filtered.length} participant{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>

        {filtered.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-400">
            No participants match your search.
          </div>
        ) : (
          filtered.map((p) => {
            if (!p?.id) return null;
            const initials = getInitials(p.user_name || p.user_email || '?');
            const roleClass = roleColors[p.role] ?? 'bg-gray-100 text-gray-600 ring-gray-200';
            const roleLabel = p.role
              ? p.role.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
              : 'Unknown';

            return (
              <div
                key={p.id}
                className={`flex items-center gap-3 px-4 py-3 transition-colors ${
                  selectedIds.includes(p.id) ? 'bg-indigo-50/50' : 'bg-white hover:bg-gray-50'
                }`}
              >
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedIds.includes(p.id)}
                  onChange={() => toggleOne(p.id)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 shrink-0"
                />

                {/* Avatar */}
                <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-semibold shrink-0">
                  {initials}
                </div>

                {/* Name + email — grows and truncates */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {p.user_name || '—'}
                  </p>
                  <p className="text-xs text-gray-400 flex items-center gap-1 truncate">
                    <Mail className="w-3 h-3 shrink-0" />
                    <span className="truncate">{p.user_email || '—'}</span>
                  </p>
                </div>

                {/* Role badge — fixed width, never hidden */}
                <span className={`shrink-0 px-2 py-0.5 text-xs font-semibold rounded-full ring-1 ring-inset ${roleClass}`}>
                  {roleLabel}
                </span>

                {/* Remove button — always visible */}
                <button
                  onClick={() => onRemoveParticipants([p.id])}
                  className="shrink-0 w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                  title="Remove participant"
                >
                  <UserMinus className="w-4 h-4" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
