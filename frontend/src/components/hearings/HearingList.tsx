// src/components/hearings/HearingList.tsx

import React from 'react';
import { Hearing } from '../../services/types.ts';
import { HearingCard } from './HearingCard.tsx';
import { Loader2, Scale } from 'lucide-react';

interface HearingListProps {
  hearings: Hearing[];
  loading?: boolean;
  onHearingClick?: (hearing: Hearing) => void;
  onEdit?: (hearing: Hearing) => void;
  onDelete?: (hearing: Hearing) => void;
  onAddParticipants?: (hearing: Hearing) => void;
}

export const HearingList: React.FC<HearingListProps> = ({
  hearings,
  loading = false,
  onHearingClick,
  onEdit,
  onDelete,
  onAddParticipants,
}) => {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <Loader2 className="w-7 h-7 animate-spin text-indigo-500" />
        <p className="text-sm text-slate-400">Loading hearings…</p>
      </div>
    );
  }

  if (hearings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-slate-100 to-indigo-50 flex items-center justify-center mb-5 shadow-sm">
          <Scale className="w-9 h-9 text-indigo-300" />
        </div>
        <h3 className="text-base font-semibold text-slate-800 mb-1.5">No hearings on the docket</h3>
        <p className="text-sm text-slate-400 max-w-xs">
          Schedule your first hearing to get started. Proceedings will appear here once created.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {hearings.map((hearing) => (
        <HearingCard
          key={hearing.id}
          hearing={hearing}
          onClick={() => onHearingClick?.(hearing)}
          onEdit={() => onEdit?.(hearing)}
          onDelete={() => onDelete?.(hearing)}
          onAddParticipants={() => onAddParticipants?.(hearing)}
        />
      ))}
    </div>
  );
};
