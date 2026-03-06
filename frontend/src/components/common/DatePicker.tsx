import React from 'react';
import ReactDatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { Calendar } from 'lucide-react';

interface DatePickerProps {
  selected: Date | null;
  onChange: (date: Date | null) => void;
  label?: string;
  error?: string;
  minDate?: Date;
  maxDate?: Date;
  showTimeSelect?: boolean;
  placeholderText?: string;
}

export const DatePicker: React.FC<DatePickerProps> = ({
  selected,
  onChange,
  label,
  error,
  minDate,
  maxDate,
  showTimeSelect = true,
  placeholderText = "Select date and time",
}) => {
  const handleChange = (date: Date | null) => {
    if (date && minDate && date < minDate) {
      // User picked a time before selecting a date — the library defaulted to today.
      // Preserve the chosen time but snap the date forward to minDate.
      const corrected = new Date(minDate);
      corrected.setHours(date.getHours(), date.getMinutes(), 0, 0);
      onChange(corrected);
    } else {
      onChange(date);
    }
  };

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          {label}
        </label>
      )}
      <div className="relative">
        <ReactDatePicker
          selected={selected}
          onChange={handleChange}
          minDate={minDate}
          maxDate={maxDate}
          openToDate={minDate}
          showTimeSelect={showTimeSelect}
          dateFormat="MMMM d, yyyy h:mm aa"
          placeholderText={placeholderText}
          className={`
            block w-full rounded-xl border px-3.5 py-2.5 pl-10 text-sm text-gray-900
            placeholder:text-gray-400 shadow-sm transition
            focus:outline-none focus:ring-2 focus:border-transparent
            ${error ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-indigo-500'}
          `}
        />
        <Calendar className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>
      {error && <p className="mt-1.5 text-xs text-red-600">{error}</p>}
    </div>
  );
};