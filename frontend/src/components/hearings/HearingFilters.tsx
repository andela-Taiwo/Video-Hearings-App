// src/components/hearings/HearingFilters.tsx

import React, { useState } from 'react';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { Input } from '../common/Input.tsx';
import { HearingFilters as Filters } from '../../services/types.ts';

interface HearingFiltersProps {
  filters: Filters;
  onFilterChange: (filters: Filters) => void;
}

const STATUS_TABS = [
  { value: '', label: 'Active' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'postponed', label: 'Postponed' },
];

export const HearingFilters: React.FC<HearingFiltersProps> = ({ filters, onFilterChange }) => {
  const [showDateRange, setShowDateRange] = useState(false);
  const [localFilters, setLocalFilters] = useState<Filters>(filters);

  const hasDateFilter = !!(localFilters.date_from || localFilters.date_to);
  const hasAnyFilter = !!(localFilters.search || localFilters.status || hasDateFilter);

  const update = (patch: Partial<Filters>) => {
    const next = { ...localFilters, ...patch };
    setLocalFilters(next);
    onFilterChange(next);
  };

  const clearAll = () => {
    const empty: Filters = {};
    setLocalFilters(empty);
    onFilterChange(empty);
    setShowDateRange(false);
  };

  return (
    <div className="mb-7 space-y-3">
      {/* Search + date toggle row */}
      <div className="flex items-center gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search hearings by name…"
            value={localFilters.search || ''}
            onChange={(e) => update({ search: e.target.value })}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
          />
        </div>

        <button
          onClick={() => setShowDateRange(!showDateRange)}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium shadow-sm transition-colors shrink-0 ${
            showDateRange || hasDateFilter
              ? 'bg-indigo-600 border-indigo-600 text-white hover:bg-indigo-700'
              : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
          Date Range
          {hasDateFilter && <span className="w-1.5 h-1.5 rounded-full bg-white/70" />}
        </button>

        {hasAnyFilter && (
          <button
            onClick={clearAll}
            className="flex items-center gap-1.5 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 transition-colors whitespace-nowrap shrink-0"
          >
            <X className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>

      {/* Status pill tabs */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {STATUS_TABS.map(({ value, label }) => {
          const active = (localFilters.status ?? '') === value;
          return (
            <button
              key={value}
              onClick={() => update({ status: value as any })}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                active
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-200'
                  : 'bg-white text-slate-500 border border-slate-200 hover:border-indigo-300 hover:text-indigo-600'
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Date range panel */}
      {showDateRange && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              type="date"
              label="From Date"
              value={localFilters.date_from || ''}
              onChange={(e) => update({ date_from: e.target.value })}
            />
            <Input
              type="date"
              label="To Date"
              value={localFilters.date_to || ''}
              onChange={(e) => update({ date_to: e.target.value })}
            />
          </div>
        </div>
      )}
    </div>
  );
};
