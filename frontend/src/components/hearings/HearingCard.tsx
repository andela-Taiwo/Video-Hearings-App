// src/components/hearings/HearingCard.tsx

import React from 'react';
import { format } from 'date-fns';
import { Clock, MapPin, Users, Pencil, UserPlus, ChevronRight } from 'lucide-react';
import { Hearing } from '../../services/types.ts';

interface HearingCardProps {
  hearing: Hearing;
  onClick?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  onAddParticipants?: () => void;
}

const statusConfig: Record<string, { label: string; badge: string; bar: string; dot: string }> = {
  scheduled: {
    label: 'Scheduled',
    badge: 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200',
    bar: 'bg-blue-500',
    dot: 'bg-blue-500',
  },
  in_progress: {
    label: 'In Progress',
    badge: 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200',
    bar: 'bg-emerald-500',
    dot: 'bg-emerald-500',
  },
  completed: {
    label: 'Completed',
    badge: 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200',
    bar: 'bg-slate-400',
    dot: 'bg-slate-400',
  },
  cancelled: {
    label: 'Cancelled',
    badge: 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200',
    bar: 'bg-red-500',
    dot: 'bg-red-500',
  },
  postponed: {
    label: 'Postponed',
    badge: 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200',
    bar: 'bg-amber-400',
    dot: 'bg-amber-400',
  },
};

const hearingTypeLabel = (type: string) =>
  type ? type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : null;

export const HearingCard: React.FC<HearingCardProps> = ({
  hearing,
  onClick,
  onEdit,
  onAddParticipants,
}) => {
  const scheduledDate = new Date(hearing.scheduled_at);
  const participantCount = hearing.participants?.length || 0;
  const config = statusConfig[hearing.status] ?? statusConfig.scheduled;
  const typeLabel = hearingTypeLabel(hearing.hearing_type);

  return (
    <div
      className="group bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 cursor-pointer flex flex-col overflow-hidden"
      onClick={onClick}
    >
      <div className={`h-1 w-full ${config.bar}`} />
      <div className="p-5 flex flex-col flex-1">

        {/* Top row: status + type */}
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          <span className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full ${config.badge}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
            {config.label}
          </span>
          {typeLabel && (
            <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-slate-50 text-slate-500 ring-1 ring-inset ring-slate-200">
              {typeLabel}
            </span>
          )}
        </div>

        {/* Hearing name */}
        <h3 className="text-[15px] font-semibold text-slate-900 mb-4 line-clamp-2 leading-snug group-hover:text-indigo-700 transition-colors">
          {hearing.name}
        </h3>

        {/* Date block */}
        <div className="flex items-center gap-3 mb-4 bg-slate-50 rounded-xl px-3.5 py-2.5">
          <div className="text-center shrink-0">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 leading-none mb-0.5">
              {format(scheduledDate, 'MMM')}
            </p>
            <p className="text-2xl font-bold text-slate-800 leading-none">
              {format(scheduledDate, 'd')}
            </p>
            <p className="text-[10px] text-slate-400 leading-none mt-0.5">
              {format(scheduledDate, 'yyyy')}
            </p>
          </div>
          <div className="w-px h-10 bg-slate-200 shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-700">
              {format(scheduledDate, 'EEEE')}
            </p>
            <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
              <Clock className="w-3 h-3 shrink-0" />
              {format(scheduledDate, 'h:mm a')}
            </p>
          </div>
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-4 text-xs text-slate-500 flex-1">
          <span className="flex items-center gap-1.5 truncate">
            <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-400" />
            <span className="truncate">{hearing.courtroom_name || 'Courtroom'}</span>
          </span>
          <span className="flex items-center gap-1.5 shrink-0">
            <Users className="w-3.5 h-3.5 text-slate-400" />
            {participantCount} {participantCount === 1 ? 'person' : 'people'}
          </span>
        </div>

        {/* Actions */}
        <div
          className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center gap-1">
            <button
              onClick={onAddParticipants}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <UserPlus className="w-3.5 h-3.5" />
              Add
            </button>
            <button
              onClick={onEdit}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors"
            >
              <Pencil className="w-3.5 h-3.5" />
              Edit
            </button>
          </div>
          <span className="flex items-center gap-0.5 text-xs font-medium text-slate-400 group-hover:text-indigo-500 transition-colors">
            View <ChevronRight className="w-3.5 h-3.5" />
          </span>
        </div>
      </div>
    </div>
  );
};
