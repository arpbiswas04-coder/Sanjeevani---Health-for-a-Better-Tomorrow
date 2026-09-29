import React from 'react';

export const PlaceholderChart: React.FC<{ title: string }> = ({ title }) => {
  return (
    <div className="h-48 rounded-lg border border-dashed border-slate-700 flex flex-col items-center justify-center p-4 bg-slate-800/30">
      <span className="text-sm font-medium text-slate-400">{title}</span>
      <span className="text-xs text-slate-500 mt-1">Chart Component Placeholder</span>
    </div>
  );
};
