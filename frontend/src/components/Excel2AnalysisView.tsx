import React, { useState, useEffect } from 'react';
import type { InspectionJobResult } from '../types';
import { sessionService } from '../services/api';
import { Loader2, AlertTriangle, CheckCircle2, Calendar } from 'lucide-react';
import { EvidenceModal } from './EvidenceModal';

interface Excel2AnalysisViewProps {
  sessionId: string;
  selectedKeys: string[];
  evaluationMonth: string;
}

export const Excel2AnalysisView: React.FC<Excel2AnalysisViewProps> = ({ sessionId, selectedKeys, evaluationMonth }) => {
  const [results, setResults] = useState<InspectionJobResult[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    // Setting the evaluation month on the session is handled by the parent/Dashboard
    sessionService.calculateInspection(sessionId, selectedKeys, evaluationMonth)
      .then(data => {
        if (mounted) {
          setResults(data);
          setLoading(false);
        }
      })
      .catch(err => {
        if (mounted) {
          setError(err.response?.data?.detail || err.message || "Failed to calculate inspection days");
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

  if (loading) return <div className="p-12 flex flex-col items-center justify-center"><Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-4" /><span className="text-gray-500 font-medium">Executing Inspection Engine...</span></div>;
  if (error) return <div className="p-4 bg-red-50 text-red-600 rounded mt-6 border border-red-200 shadow-sm">{error}</div>;
  if (!results) return null;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <div className="flex items-center justify-between mb-8 border-b pb-4">
        <h2 className="text-xl font-bold text-gray-800 uppercase tracking-wider flex items-center">
          <span className="bg-indigo-600 text-white w-8 h-8 rounded-full flex items-center justify-center mr-3 shadow-md"><Calendar className="w-4 h-4" /></span> 
          EXCEL 2 INSPECTION ANALYSIS
        </h2>
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
                    Evaluation Month: <span className="font-bold text-gray-700">{res.evaluation_month_str || 'N/A'}</span>
                  </p>
                  <p className="text-sm text-gray-500 font-medium">
                    Source Records: <span className="font-bold text-gray-700">{res.records_analyzed}</span>
                  </p>
                  <p className="text-sm text-gray-500 font-medium">
                    Qualifying {res.evaluation_month_str || 'Current'} Records: <span className="font-bold text-indigo-700">{res.valid_records}</span>
                  </p>
                </div>
                
                <div className="flex flex-1 items-center justify-center gap-6 px-4">
                  <div className="text-center">
                    <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Current Month Inspection Days</div>
                    <div className="text-3xl font-black text-indigo-600">{res.total_inspection_days}</div>
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
                    View Records
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
          title="Excel 2 Inspection Records"
          subtitle={`Job: ${activeJob}`}
          summaryStats={[
            { label: "Evaluation Month", value: results.find(r => r.job_number === activeJob)?.evaluation_month_str || 'N/A' },
            { label: "Source Records", value: results.find(r => r.job_number === activeJob)?.records_analyzed },
            { label: "Qualifying Records", value: results.find(r => r.job_number === activeJob)?.valid_records, colorClass: 'text-indigo-600' },
            { label: "Inspection Days", value: results.find(r => r.job_number === activeJob)?.total_inspection_days, colorClass: 'text-indigo-600' }
          ]}
          records={results.find(r => r.job_number === activeJob)?.evidence || []}
          columns={[
            { header: "#", key: "_index", render: (_, __, i) => i !== undefined ? i + 1 : '-' },
            { header: "From", key: "from_date_parsed", render: (val, row) => (
              <span className={!val ? 'text-amber-600 font-bold' : 'font-medium text-gray-800'}>
                {val ? val : (row.from_date_raw === null || row.from_date_raw === '' ? '—' : String(row.from_date_raw))}
              </span>
            )},
            { header: "Upto", key: "upto_date_parsed", render: (val, row) => (
              <span className={!val ? 'text-amber-600 font-bold' : 'font-medium text-gray-800'}>
                {val ? val : (row.upto_date_raw === null || row.upto_date_raw === '' ? '—' : String(row.upto_date_raw))}
              </span>
            )},
            { header: "Duration", key: "days", render: (val) => val !== null ? (
              <span className="bg-indigo-100 text-indigo-700 text-xs font-bold px-2 py-1 rounded">{val} days</span>
            ) : <span className="bg-gray-100 text-gray-500 text-xs font-bold px-2 py-1 rounded">—</span>},
            { header: "Source Days", key: "source_no_of_days", render: (val, row) => val !== null && val !== undefined ? (
              <div className={`text-[11px] font-bold px-2 py-0.5 rounded inline-flex items-center ${row.diagnostic_match ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
                {String(val)} 
                {row.diagnostic_match ? <CheckCircle2 className="w-3 h-3 ml-1" /> : <AlertTriangle className="w-3 h-3 ml-1" />}
              </div>
            ) : null},
            { header: "Others", key: "others_contribution", render: (val, row) => val !== null && val !== undefined ? (
              <span className="bg-purple-100 text-purple-700 text-[11px] font-bold px-2 py-0.5 rounded inline-flex flex-col items-start">
                <span>{val}</span>
                <span className="text-[9px] text-purple-500 font-medium uppercase tracking-wider leading-none mt-0.5">{row.others_selected_source || 'Unknown'}</span>
              </span>
            ) : <span className="bg-gray-100 text-gray-500 text-xs font-bold px-2 py-1 rounded">—</span>},
            { header: "Status", key: "status", render: (val) => (
              <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${val === 'VALID' ? 'bg-green-100 text-green-700' : val === 'EXCLUDED' ? 'bg-gray-200 text-gray-600' : 'bg-red-100 text-red-700'}`}>
                {val}
              </span>
            )},
            { header: "Warnings", key: "warnings", render: (val) => val && val.length > 0 ? (
              <div className="text-[11px] text-amber-600 font-bold flex flex-col gap-1">
                {val.map((w: string, wi: number) => <span key={wi} className="flex items-center"><AlertTriangle className="w-3 h-3 mr-1" /> {w}</span>)}
              </div>
            ) : null}
          ]}
          filterRecord={(record, ft) => {
            if (ft === 'Valid') return record.status === 'VALID';
            if (ft === 'Invalid') return record.status === 'INVALID';
            if (ft === 'Warnings') return record.warnings && record.warnings.length > 0;
            return true;
          }}
          searchRecord={(record, term) => {
            const t = term.toLowerCase();
            return (
              String(record.from_date_parsed || record.from_date_raw || '').toLowerCase().includes(t) ||
              String(record.upto_date_parsed || record.upto_date_raw || '').toLowerCase().includes(t) ||
              String(record.status || '').toLowerCase().includes(t) ||
              (record.warnings || []).some((w: string) => w.toLowerCase().includes(t))
            );
          }}
        />
      )}
    </div>
  );
};
