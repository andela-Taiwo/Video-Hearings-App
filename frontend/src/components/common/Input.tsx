import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helper?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helper, className = '', id, ...props }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1.5">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`
            block w-full rounded-xl border px-3.5 py-2.5 text-sm text-gray-900
            placeholder:text-gray-400 shadow-sm transition
            focus:outline-none focus:ring-2 focus:border-transparent
            ${error
              ? 'border-red-300 focus:ring-red-500'
              : 'border-gray-200 focus:ring-indigo-500'
            }
            ${className}
          `}
          {...props}
        />
        {error && <p className="mt-1.5 text-xs text-red-600">{error}</p>}
        {helper && !error && <p className="mt-1.5 text-xs text-gray-500">{helper}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';