import React, { useState, useEffect } from 'react';
import type { MatchResult } from '../types';
import { sessionService } from '../services/api';
import { Loader2, AlertTriangle, ArrowLeft, ChevronRight } from 'lucide-react';

interface MatchResultsViewProps {
  sessionId: string;
  selectedKeys: string[];
  onBack: () => void;
}

export const MatchResultsView: React.FC<MatchResultsViewProps> = ({ sessionId, selectedKeys, onBack }) => {
  const [result, setResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    sessionService.matchJobNumbers(sessionId, selectedKeys)
      .then(data => {
        if (mounted) {
          setResult(data);
          setLoading(false);
        }
      })
      .catch(err => {
        if (mounted) {
          setError(err.response?.data?.detail || "Failed to load matches");
          setLoading(false);
        }
      });
    return () => { mounted = false; };
  }, [sessionId, selectedKeys]);

  const renderTable = (records: Record<string, any>[]) => {
    if (!records || records.length === 0) return null;
    const columns = Object.keys(records[0]);
    
    return (
      <div className="overflow-x-auto border border-gray-200 rounded-lg shadow-sm">
        <table className="w-full text-sm text-left text-gray-500 whitespace-nowrap">
          <thead className="text-xs text-gray-700 uppercase bg-gray-50">
            <tr>
              {columns.map(c => (
                <th key={c} className="px-4 py-3 border-b">{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((row, i) => (
              <tr key={i} className="bg-white border-b hover:bg-gray-50">
                {columns.map(c => (
                  <td key={c} className="px-4 py-2 border-r last:border-r-0">
                    {row[c] !== null && row[c] !== undefined ? String(row[c]) : <span className="text-gray-300 italic">Blank</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  if (loading) return <div className="p-12 flex flex-col items-center justify-center"><Loader2 className="w-10 h-10 animate-spin text-blue-500 mb-4" /><span className="text-gray-500">Extracting records...</span></div>;
  if (error) return <div className="p-4 bg-red-50 text-red-600 rounded mt-6 border border-red-200">{error}</div>;
  if (!result) return null;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <div className="flex items-center justify-between mb-8 border-b pb-4">
        <h2 className="text-xl font-bold text-gray-800 uppercase tracking-wider flex items-center">
          <span className="bg-green-600 text-white w-8 h-8 rounded-full flex items-center justify-center mr-3 shadow-md">✓</span> 
          Matched Records Preview
        </h2>
        <button onClick={onBack} className="flex items-center text-gray-600 hover:text-gray-900 transition-colors font-medium">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Selection
        </button>
      </div>

      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <button 
          onClick={() => {
            const event = new CustomEvent('analyzeExcel1', { detail: selectedKeys });
            window.dispatchEvent(event);
          }}
          className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-8 rounded-lg shadow-md transition-colors flex items-center justify-center"
        >
          Analyze Excel 1 <ChevronRight className="w-5 h-5 ml-2" />
        </button>
        <button 
          onClick={() => {
            const event = new CustomEvent('analyzeExcel2', { detail: selectedKeys });
            window.dispatchEvent(event);
          }}
          className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-8 rounded-lg shadow-md transition-colors flex items-center justify-center"
        >
          Analyze Excel 2 <ChevronRight className="w-5 h-5 ml-2" />
        </button>
        <button 
          onClick={() => {
            const event = new CustomEvent('calculateCombined', { detail: selectedKeys });
            window.dispatchEvent(event);
          }}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg shadow-md transition-colors flex items-center justify-center"
        >
          Review & Approve <ChevronRight className="w-5 h-5 ml-2" />
        </button>
      </div>

      <div className="space-y-12">
        {result.job_numbers.map(key => {
          const ex1 = result.excel1_records[key] || [];
          const ex2 = result.excel2_records[key] || [];
          
          return (
            <div key={key} className="bg-gray-50 p-4 rounded-xl border border-gray-200">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center bg-white p-3 rounded-lg shadow-sm border border-gray-100">
                Job Number Key: <span className="text-blue-600 ml-2 uppercase">{key}</span>
              </h3>
              
              <div className="mb-6">
                <h4 className="font-semibold text-gray-700 mb-2 uppercase text-sm tracking-wide">Excel 1 — {ex1.length} Record(s)</h4>
                {ex1.length > 0 ? renderTable(ex1) : (
                  <div className="p-4 bg-amber-50 text-amber-700 rounded border border-amber-200 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2" /> No records found in Excel 1.
                  </div>
                )}
              </div>

              <div>
                <h4 className="font-semibold text-gray-700 mb-2 uppercase text-sm tracking-wide">Excel 2 — {ex2.length} Record(s)</h4>
                {ex2.length > 0 ? renderTable(ex2) : (
                  <div className="p-4 bg-amber-50 text-amber-700 rounded border border-amber-200 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2" /> No inspection source records found in Excel 2.
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
