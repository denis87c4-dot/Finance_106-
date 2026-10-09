import React, { useState, useRef, useEffect } from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Clock, Check } from 'lucide-react';

interface DatePickerWithInputProps {
  value: string; // YYYY-MM-DD
  onChange: (value: string) => void;
  label?: string;
  helperText?: string;
  className?: string;
  highlightDays?: number[]; // e.g. credit card closing/due days
  highlightLabel?: string;
}

export const DatePickerWithInput: React.FC<DatePickerWithInputProps> = ({
  value,
  onChange,
  label,
  helperText,
  className = '',
  highlightDays = [],
  highlightLabel
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Helper to convert YYYY-MM-DD to DD/MM/AAAA for typing
  const isoToBr = (iso: string): string => {
    if (!iso || !iso.includes('-')) return '';
    const parts = iso.split('-');
    if (parts.length === 3) {
      return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return iso;
  };

  // Helper to convert DD/MM/AAAA to YYYY-MM-DD
  const brToIso = (br: string): string | null => {
    const clean = br.trim();
    if (clean.includes('/')) {
      const parts = clean.split('/');
      if (parts.length === 3 && parts[0].length === 2 && parts[1].length === 2 && parts[2].length === 4) {
        return `${parts[2]}-${parts[1]}-${parts[0]}`;
      }
    } else if (clean.includes('-')) {
      const parts = clean.split('-');
      if (parts.length === 3 && parts[0].length === 4) {
        return clean;
      }
    }
    return null;
  };

  const [textInput, setTextInput] = useState<string>(() => isoToBr(value));

  // Sync when value prop changes from outside
  useEffect(() => {
    setTextInput(isoToBr(value));
  }, [value]);

  // Calendar view state (year and month 0-indexed)
  const [viewDate, setViewDate] = useState<Date>(() => {
    if (value && value.includes('-')) {
      const [y, m, d] = value.split('-').map(Number);
      return new Date(y, m - 1, d || 1);
    }
    return new Date();
  });

  // Close calendar popover on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Handle direct typing in the input
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let raw = e.target.value;
    setTextInput(raw);

    // If matches DD/MM/YYYY or YYYY-MM-DD, trigger onChange
    const iso = brToIso(raw);
    if (iso) {
      const d = new Date(iso + 'T00:00:00');
      if (!isNaN(d.getTime())) {
        onChange(iso);
        setViewDate(new Date(d.getFullYear(), d.getMonth(), 1));
      }
    }
  };

  // Select day from calendar grid
  const handleSelectDay = (day: number) => {
    const year = viewDate.getFullYear();
    const month = (viewDate.getMonth() + 1).toString().padStart(2, '0');
    const dayStr = day.toString().padStart(2, '0');
    const newIso = `${year}-${month}-${dayStr}`;

    onChange(newIso);
    setTextInput(isoToBr(newIso));
    setIsOpen(false);
  };

  // Calendar grid calculations
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth(); // 0-11
  const firstDayOfWeek = new Date(year, month, 1).getDay(); // 0 is Sunday
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();

  const monthNames = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];

  const weekDayNames = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

  // Parse currently selected value day/month/year
  const selectedYear = value ? parseInt(value.substring(0, 4), 10) : null;
  const selectedMonth = value ? parseInt(value.substring(5, 7), 10) - 1 : null;
  const selectedDay = value ? parseInt(value.substring(8, 10), 10) : null;

  const today = new Date();
  const isToday = (d: number) =>
    today.getDate() === d && today.getMonth() === month && today.getFullYear() === year;

  // Shortcuts
  const setQuickOffset = (days: number) => {
    const target = new Date();
    target.setDate(target.getDate() + days);
    const iso = target.toISOString().slice(0, 10);
    onChange(iso);
    setTextInput(isoToBr(iso));
    setViewDate(new Date(target.getFullYear(), target.getMonth(), 1));
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {label && (
        <label className="block text-xs uppercase font-semibold text-slate-400 mb-1.5 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <CalendarIcon className="w-3.5 h-3.5 text-emerald-400" />
            <span>{label}</span>
          </span>
          <span className="text-[10px] text-slate-500 font-normal">Digite ou use o calendário</span>
        </label>
      )}

      {/* Dual-Mode Input Field */}
      <div className="relative flex items-center">
        <input
          type="text"
          placeholder="DD/MM/AAAA ou AAAA-MM-DD"
          value={textInput}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-3.5 pr-10 py-2.5 text-sm text-white font-mono placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
        />

        {/* Toggle Calendar Button */}
        <button
          type="button"
          onClick={() => setIsOpen(prev => !prev)}
          className="absolute right-2 p-1.5 text-slate-400 hover:text-emerald-400 rounded-lg hover:bg-slate-800/80 transition-colors"
          title="Abrir calendário visual"
          tabIndex={-1}
        >
          <CalendarIcon className="w-4 h-4" />
        </button>
      </div>

      {helperText && (
        <span className="text-[11px] text-slate-500 mt-1 block">
          {helperText}
        </span>
      )}

      {/* Interactive Visual Calendar Popover */}
      {isOpen && (
        <div className="absolute left-0 top-full mt-2 z-50 w-80 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in-95">
          {/* Header with Month/Year Navigation */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs">
            <button
              type="button"
              onClick={() => setViewDate(new Date(year, month - 1, 1))}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <span className="font-bold text-white text-sm">
              {monthNames[month]} {year}
            </span>

            <button
              type="button"
              onClick={() => setViewDate(new Date(year, month + 1, 1))}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Shortcuts */}
          <div className="flex items-center justify-between gap-1 py-2 border-b border-slate-800/60 text-[11px]">
            <button
              type="button"
              onClick={() => setQuickOffset(0)}
              className="px-2 py-1 bg-slate-950 hover:bg-slate-800 text-slate-300 rounded-lg font-medium transition-colors"
            >
              Hoje
            </button>
            <button
              type="button"
              onClick={() => setQuickOffset(7)}
              className="px-2 py-1 bg-slate-950 hover:bg-slate-800 text-slate-300 rounded-lg font-medium transition-colors"
            >
              +7 dias
            </button>
            <button
              type="button"
              onClick={() => setQuickOffset(15)}
              className="px-2 py-1 bg-slate-950 hover:bg-slate-800 text-slate-300 rounded-lg font-medium transition-colors"
            >
              +15 dias
            </button>
            <button
              type="button"
              onClick={() => setQuickOffset(30)}
              className="px-2 py-1 bg-slate-950 hover:bg-slate-800 text-slate-300 rounded-lg font-medium transition-colors"
            >
              +30 dias
            </button>
          </div>

          {/* Weekday headers */}
          <div className="grid grid-cols-7 gap-1 text-center py-2 text-[10px] font-bold text-slate-500 uppercase">
            {weekDayNames.map(wd => (
              <span key={wd}>{wd}</span>
            ))}
          </div>

          {/* Days Grid */}
          <div className="grid grid-cols-7 gap-1 text-center text-xs">
            {/* Previous month muted filler */}
            {Array.from({ length: firstDayOfWeek }).map((_, i) => {
              const d = daysInPrevMonth - firstDayOfWeek + i + 1;
              return (
                <span key={`prev-${i}`} className="py-1.5 text-slate-700 select-none">
                  {d}
                </span>
              );
            })}

            {/* Current month days */}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const isSelected =
                selectedYear === year && selectedMonth === month && selectedDay === day;
              const isCurrentDay = isToday(day);
              const isHighlight = highlightDays.includes(day);

              return (
                <button
                  key={`cur-${day}`}
                  type="button"
                  onClick={() => handleSelectDay(day)}
                  className={`py-1.5 rounded-xl font-mono text-xs font-medium transition-all relative ${
                    isSelected
                      ? 'bg-emerald-600 text-white font-bold shadow-md shadow-emerald-600/30'
                      : isHighlight
                      ? 'bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/30 border border-indigo-500/40'
                      : isCurrentDay
                      ? 'bg-slate-800 text-emerald-400 font-bold border border-emerald-500/40'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  {day}
                  {isHighlight && !isSelected && (
                    <span className="w-1 h-1 rounded-full bg-indigo-400 absolute bottom-1 left-1/2 -translate-x-1/2"></span>
                  )}
                </button>
              );
            })}
          </div>

          {highlightLabel && (
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] text-indigo-300 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-indigo-400 inline-block"></span>
              <span>{highlightLabel}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
