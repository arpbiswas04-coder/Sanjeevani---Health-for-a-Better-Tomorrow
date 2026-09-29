import React from 'react';

export const PlaceholderMap: React.FC<{ label?: string }> = ({ label = 'Supply Chain & Facility Geospatial Map' }) => {
  return (
    <div className="h-64 rounded-lg border border-dashed border-slate-700 flex flex-col items-center justify-center p-4 bg-slate-800/30">
      <span className="text-sm font-medium text-slate-400">{label}</span>
      <span className="text-xs text-slate-500 mt-1">Geospatial Map Placeholder</span>
    </div>
  );
};
