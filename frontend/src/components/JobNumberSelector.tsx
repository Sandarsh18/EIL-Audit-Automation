import React, { useState, useEffect, useMemo } from 'react';
import type { JobNumberSummary } from '../types';
import { sessionService } from '../services/api';
import { Loader2, Search, CheckSquare, Square, AlertTriangle } from 'lucide-react';

interface JobNumberSelectorProps {
  sessionId: string;
  onSelectionComplete: (selectedKeys: string[]) => void;
}

export const JobNumberSelector: React.FC<JobNumberSelectorProps> = ({ sessionId, onSelectionComplete }) => {
  const [summary, setSummary] = useState<JobNumberSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    let mounted = true;
    sessionService.getJobNumbers(sessionId)
      .then(data => {
        if (mounted) {
          setSummary(data);
          setLoading(false);
        }
      })
      .catch(err => {
        if (mounted) {
          setError(err.response?.data?.detail || "Failed to load Job Numbers");
          setLoading(false);
        }
      });
    return () => { mounted = false; };
  }, [sessionId]);

  const filteredOptions = useMemo(() => {
    if (!summary) return [];
    return summary.options.filter(o => 
      o.original_value.toLowerCase().includes(search.toLowerCase())
    );
  }, [summary, search]);

  const toggleSelect = (key: string) => {
    const next = new Set(selected);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setSelected(next);
  };

  const selectAll = () => {
    setSelected(new Set(filteredOptions.map(o => o.normalized_key)));
  };

  const clearAll = () => {
    setSelected(new Set());
  };

  if (loading) return <div className="p-8 flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>;
  if (error) return <div className="p-4 bg-red-50 text-red-600 rounded">{error}</div>;
  if (!summary) return null;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <h2 className="text-xl font-bold text-gray-800 mb-2 uppercase tracking-wider flex items-center">
        <span className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center mr-3 shadow-md">4</span> 
        Job Number Selection
      </h2>
      <p className="text-gray-500 mb-6 ml-11">
        {summary.total_valid_job_numbers} valid Job Numbers found. 
        {summary.blank_job_numbers > 0 && <span className="text-amber-600 ml-2">({summary.blank_job_numbers} rows had no Job Number).</span>}
      </p>

      <div className="flex flex-col md:flex-row gap-4 mb-4">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
            placeholder="Search Job Numbers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex space-x-2">
          <button onClick={selectAll} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors text-sm font-medium">Select All</button>
          <button onClick={clearAll} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors text-sm font-medium">Clear All</button>
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg overflow-hidden flex flex-col h-96">
        <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 grid grid-cols-12 gap-4 font-semibold text-gray-600 text-sm">
          <div className="col-span-1 text-center">Select</div>
          <div className="col-span-4">Job Number</div>
          <div className="col-span-3 text-center">Excel 1 Records</div>
          <div className="col-span-4 text-center">Excel 2 Status</div>
        </div>
        
        <div className="overflow-y-auto flex-1">
          {filteredOptions.length === 0 ? (
            <div className="p-8 text-center text-gray-500 italic">No job numbers match your search.</div>
          ) : (
            filteredOptions.map(opt => (
              <div 
                key={opt.normalized_key} 
                className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-gray-100 items-center hover:bg-blue-50 cursor-pointer"
                onClick={() => toggleSelect(opt.normalized_key)}
              >
                <div className="col-span-1 flex justify-center">
                  {selected.has(opt.normalized_key) ? (
                    <CheckSquare className="w-5 h-5 text-blue-600" />
                  ) : (
                    <Square className="w-5 h-5 text-gray-400" />
                  )}
                </div>
                <div className="col-span-4 font-medium text-gray-800 break-all">{opt.original_value}</div>
                <div className="col-span-3 text-center">
                  <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                    {opt.excel1_count}
                  </span>
                </div>
                <div className="col-span-4 text-center flex justify-center items-center">
                  {opt.excel2_found ? (
                    <span className="bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                      Found ({opt.excel2_count})
                    </span>
                  ) : (
                    <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center">
                      <AlertTriangle className="w-3 h-3 mr-1" /> Not Found
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <div className="text-gray-600 font-medium">
          Selected: <span className="text-blue-600 font-bold">{selected.size}</span> Job Number(s)
        </div>
        <button 
          onClick={() => onSelectionComplete(Array.from(selected))}
          disabled={selected.size === 0}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg shadow-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          View Matching Records
        </button>
      </div>
    </div>
  );
};
