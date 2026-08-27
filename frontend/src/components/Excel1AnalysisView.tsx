import React, { useState, useEffect } from 'react';
import type { JobCalculationResult } from '../types';
import { sessionService } from '../services/api';
import { Loader2, AlertTriangle, CheckCircle2, FileSpreadsheet } from 'lucide-react';
import { EvidenceModal } from './EvidenceModal';

interface Excel1AnalysisViewProps {
  sessionId: string;
  selectedKeys: string[];
  evaluationMonth: string;
}

export const Excel1AnalysisView: React.FC<Excel1AnalysisViewProps> = ({ sessionId, selectedKeys, evaluationMonth }) => {
  const [results, setResults] = useState<JobCalculationResult[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    sessionService.calculateExcel1(sessionId, selectedKeys, evaluationMonth)
      .then(data => {
        if (mounted) {
          setResults(data);
          setLoading(false);
        }
      })
      .catch(err => {
        if (mounted) {
          setError(err.response?.data?.detail || "Failed to calculate business rules");
          setLoading(false);
        }
      });
    return () => { mounted = false; };
  }, [sessionId, selectedKeys, evaluationMonth]);

  const openModal = (job: string) => {
    setActiveJob(job);
  };
  
  const closeModal = () => {
    setActiveJob(null);
  };

  if (loading) return <div className="p-12 flex flex-col items-center justify-center"><Loader2 className="w-10 h-10 animate-spin text-purple-500 mb-4" /><span className="text-gray-500 font-medium">Executing Business Rule Engine...</span></div>;
  if (error) return <div className="p-4 bg-red-50 text-red-600 rounded mt-6 border border-red-200 shadow-sm">{error}</div>;
  if (!results) return null;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <div className="flex items-center justify-between mb-8 border-b pb-4">
        <h2 className="text-xl font-bold text-gray-800 uppercase tracking-wider flex items-center">
          <span className="bg-purple-600 text-white w-8 h-8 rounded-full flex items-center justify-center mr-3 shadow-md"><FileSpreadsheet className="w-4 h-4" /></span> 
          EXCEL 1 ANALYSIS
        </h2>
        <div className="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full text-xs font-bold shadow-inner border border-indigo-100">
          Evaluation Month: {evaluationMonth}
        </div>
      </div>

      <div className="space-y-6">
        {results.map(res => {
          
          return (
            <div key={res.job_number} className={`border rounded-xl shadow-sm transition-all duration-200 ${res.status === 'WARNING' ? 'border-amber-200 bg-amber-50/30' : 'border-gray-200 bg-white'}`}>
              <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex-1">
                  <h3 className="text-xl font-black text-gray-800 tracking-wide uppercase mb-1">
                    {res.job_number}
                  </h3>
                  <p className="text-sm text-gray-500 font-medium mt-2">
                    Source Records: <span className="font-bold text-gray-700">{res.source_record_count}</span> | 
                    Eligible: <span className="font-bold text-green-700 ml-1">{res.eligible_record_count}</span> | 
                    Excluded by OCS Date: <span className="font-bold text-amber-700 ml-1">{res.excluded_record_count}</span>
                  </p>
                </div>
                
                <div className="flex flex-1 items-center justify-between gap-6 px-4">
                  <div className="text-center">
                    <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">FD</div>
                    <div className="text-2xl font-black text-blue-600">{res.fd}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Running Orders</div>
                    <div className="text-2xl font-black text-purple-600">{res.running_orders}</div>
                  </div>
                </div>
                
                <div className="flex-1 flex flex-col items-end justify-center">
                  <div className={`flex items-center font-bold px-3 py-1.5 rounded-full text-sm ${res.status === 'WARNING' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
                    {res.status === 'WARNING' ? <AlertTriangle className="w-4 h-4 mr-1.5" /> : <CheckCircle2 className="w-4 h-4 mr-1.5" />}
                    {res.status}
                  </div>
                  
                  <button 
                    onClick={() => openModal(res.job_number)}
                    className="mt-3 flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg border border-blue-200"
                  >
                    View Evidence
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {activeJob && results?.find(r => r.job_number === activeJob) && (
        <EvidenceModal
          isOpen={true}
          onClose={closeModal}
          title="Excel 1 Calculation Evidence"
          subtitle={`Job: ${activeJob}`}
          summaryStats={[
            { label: "Source Records", value: results.find(r => r.job_number === activeJob)?.source_record_count },
            { label: "Eligible Records", value: results.find(r => r.job_number === activeJob)?.eligible_record_count, colorClass: "text-green-600" },
            { label: "Excluded (OCS Date)", value: results.find(r => r.job_number === activeJob)?.excluded_record_count, colorClass: "text-amber-600" },
            { label: "FD", value: results.find(r => r.job_number === activeJob)?.fd, colorClass: "text-blue-600" },
            { label: "Running Orders", value: results.find(r => r.job_number === activeJob)?.running_orders, colorClass: "text-purple-600" },
            { label: "Status", value: results.find(r => r.job_number === activeJob)?.status, colorClass: results.find(r => r.job_number === activeJob)?.status === 'WARNING' ? 'text-amber-600' : 'text-green-600' }
          ]}
          records={results.find(r => r.job_number === activeJob)?.evidence || []}
          columns={[
            { header: "#", key: "_index", render: (_, __, i) => i !== undefined ? i + 1 : '-' },
            { header: "Balance Quantity", key: "balance_quantity_raw", render: (val, row) => (
              <span className={row.is_balance_invalid || row.is_balance_blank ? 'text-amber-600 font-bold' : 'font-medium text-gray-800'}>
                {row.is_balance_blank ? 'blank' : String(val)}
              </span>
            )},
            { header: "OCS Date", key: "ocs_date_raw", render: (val, row) => (
              <span className={row.is_ocs_invalid ? 'text-amber-600 font-bold' : 'font-medium text-gray-800'}>
                {row.is_ocs_blank ? 'blank' : String(val)}
              </span>
            )},
            { header: "Classification", key: "contribution", render: (val) => {
              if (val === 'FD') return <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded">FD Condition Matched</span>;
              if (val === 'Running Order') return <span className="bg-purple-100 text-purple-700 text-xs font-bold px-2 py-1 rounded">Running Order</span>;
              if (val === 'Excluded') return <span className="bg-amber-100 text-amber-700 text-xs font-bold px-2 py-1 rounded">Excluded from Analysis</span>;
              return <span className="bg-gray-100 text-gray-500 text-xs font-bold px-2 py-1 rounded">Neither FD nor Running Order</span>;
            }},
            { header: "Eligibility", key: "eligibility", render: (val) => {
              if (val === 'INCLUDED') return <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded border border-green-200">INCLUDED</span>;
              if (val === 'EXCLUDED') return <span className="bg-amber-100 text-amber-700 text-xs font-bold px-2 py-1 rounded border border-amber-200">EXCLUDED</span>;
              if (val === 'BLANK_OCS') return <span className="bg-gray-100 text-gray-600 text-xs font-bold px-2 py-1 rounded border border-gray-200">BLANK OCS</span>;
              return null;
            }},
            { header: "Warnings", key: "notes", render: (val) => val && val.length > 0 ? (
              <div className="text-xs text-amber-600 font-medium flex flex-col gap-1">
                {val.map((n: string, i: number) => <span key={i} className="flex items-center"><AlertTriangle className="w-3 h-3 mr-1" /> {n}</span>)}
              </div>
            ) : null }
          ]}
          filterRecord={(record, ft) => {
            if (ft === 'Warnings') return record.notes && record.notes.length > 0;
            if (ft === 'Valid') return !record.is_balance_invalid && !record.is_ocs_invalid;
            if (ft === 'Invalid') return record.is_balance_invalid || record.is_ocs_invalid;
            return true;
          }}
          searchRecord={(record, term) => {
            const t = term.toLowerCase();
            return (
              String(record.balance_quantity_raw || '').toLowerCase().includes(t) ||
              String(record.ocs_date_raw || '').toLowerCase().includes(t) ||
              String(record.contribution || '').toLowerCase().includes(t) ||
              String(record.eligibility || '').toLowerCase().includes(t) ||
              String(record.exclusion_reason || '').toLowerCase().includes(t)
            );
          }}
        />
      )}
    </div>
  );
};
