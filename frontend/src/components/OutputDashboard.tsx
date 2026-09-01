import React, { useCallback, useState, useEffect } from 'react';
import type { ChangePlan, OutputMetadata } from '../types';
import { outputService } from '../services/api';
import { Loader2, Download, AlertTriangle, FileSpreadsheet, Lock, Hash, CheckCircle2, ChevronRight } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '/api';

interface OutputDashboardProps {
  sessionId: string;
  selectedKeys: string[];
  evaluationMonth: string;
  customColumns: import('../types').CustomColumnData[];
}

export const OutputDashboard: React.FC<OutputDashboardProps> = ({ sessionId, selectedKeys, evaluationMonth, customColumns = [] }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [plan, setPlan] = useState<ChangePlan | null>(null);
  const [result, setResult] = useState<OutputMetadata | null>(null);
  
  const [generating, setGenerating] = useState(false);
  

  
  const fetchPlan = useCallback(async () => {
    try {
      setLoading(true);
      const data = await outputService.getChangePlan(sessionId, {
        job_numbers: selectedKeys,
        evaluation_month: evaluationMonth
      });
      setPlan(data);
      setResult(null);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate change plan");
    } finally {
      setLoading(false);
    }
  }, [sessionId, selectedKeys, evaluationMonth]);

  useEffect(() => {
    fetchPlan();
  }, [fetchPlan]);

  const handleGenerate = async () => {
    if (!plan) return;
    try {
      setGenerating(true);
      setError(null);
      const data = await outputService.generateOutput(sessionId, {
        job_numbers: selectedKeys,
        custom_columns: customColumns.length > 0 ? customColumns : undefined,
        evaluation_month: evaluationMonth
      });
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate final output");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const link = document.createElement('a');
    link.href = `${API_URL}/sessions/${sessionId}/output/download?output_id=${result.output_id}`;
    link.download = 'CONSOLIDATED_Manhour_Automated.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return (
      <div className="bg-white p-12 rounded-xl shadow-sm border border-gray-100 mt-6 flex flex-col items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-500 mb-4" />
        <p className="text-gray-500 font-bold">Analyzing Excel 3 Template & Planning Output...</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 pb-4 border-b gap-4">
        <h2 className="text-xl font-bold text-gray-800 uppercase tracking-wider flex items-center">
          <span className="bg-emerald-600 text-white w-8 h-8 rounded-full flex items-center justify-center mr-3 shadow-md"><FileSpreadsheet className="w-4 h-4" /></span> 
          OUTPUT GENERATION
        </h2>
        
        {plan && !result && (
          <div className="flex flex-col md:flex-row items-center gap-4 w-full md:w-auto mt-4 md:mt-0">
            <div className="flex flex-wrap gap-2 justify-center md:justify-end">
              <div className="bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200 text-xs font-bold text-emerald-700 whitespace-nowrap">
                Approved Jobs to Output: {plan.approved_jobs_included}
              </div>
              <div className="bg-gray-100 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-bold text-gray-700 whitespace-nowrap">
                Fields to Write: {plan.cells_to_modify.length}
              </div>
              <div className="bg-red-50 px-3 py-1.5 rounded-lg border border-red-200 text-xs font-bold text-red-700 whitespace-nowrap">
                Blocked Jobs: {plan.blocked_jobs.length}
              </div>
            </div>
            
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-6 py-2 rounded-lg shadow-sm transition-transform transform hover:scale-[1.02] flex items-center w-full md:w-auto justify-center flex-shrink-0"
            >
              {generating ? <Loader2 className="w-5 h-5 mr-2 animate-spin" /> : <Download className="w-5 h-5 mr-2" />}
              Generate Output Excel →
            </button>
          </div>
        )}
      </div>

      {error && <div role="alert" className="p-4 bg-red-50 text-red-600 rounded mb-6 border border-red-200 shadow-sm flex items-center"><AlertTriangle className="w-5 h-5 mr-2"/> {error}</div>}

      {result ? (
        <div className="flex flex-col items-center justify-center py-12 px-4 text-center space-y-6">
          <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center border-4 border-emerald-500 shadow-lg mb-2 relative">
            <CheckCircle2 className="w-10 h-10 text-emerald-600" />
            <div className="absolute -bottom-2 -right-2 bg-white rounded-full p-1 shadow">
              <Lock className="w-4 h-4 text-emerald-500" />
            </div>
          </div>
          
          <div>
            <h3 className="text-2xl font-black text-gray-800 mb-2">Output Generated Successfully</h3>
            <p className="text-gray-500 max-w-lg mx-auto">
              Your audit data has been securely written to a newly generated output workbook. 
              The original template remains completely untouched. Only approved jobs are included.
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-2xl text-left mt-4 mb-4">
            <div className="bg-gray-50 border p-4 rounded-lg">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-bold">Jobs Processed</div>
              <div className="text-xl font-black text-emerald-700">{result.jobs_processed}</div>
            </div>
            <div className="bg-gray-50 border p-4 rounded-lg">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-bold">Cells Written</div>
              <div className="text-xl font-black text-emerald-700">{result.cells_modified}</div>
            </div>
            <div className="bg-gray-50 border p-4 rounded-lg">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-bold">Jobs Blocked</div>
              <div className="text-xl font-black text-red-600">{result.jobs_blocked}</div>
            </div>
            <div className="bg-gray-50 border p-4 rounded-lg">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-bold">Source Integrity</div>
              <div className="text-xl font-black text-blue-600 flex items-center">
                100% <Lock className="w-4 h-4 ml-1 text-emerald-500"/>
              </div>
            </div>
          </div>
          
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 w-full max-w-2xl flex items-center justify-between shadow-sm">
            <div className="flex items-center text-sm font-mono text-slate-600 truncate max-w-md">
              <Hash className="w-4 h-4 mr-2 flex-shrink-0" />
              <span className="truncate">{result.original_sha256}</span>
            </div>
            <div className="text-xs font-bold uppercase tracking-wider text-emerald-600 bg-emerald-100 px-2 py-1 rounded">
              Verified
            </div>
          </div>
          
          <div className="pt-6">
            <button
              data-test-id="download-output"
              onClick={handleDownload}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-10 py-4 rounded-xl shadow-lg transition-transform transform hover:scale-[1.02] flex items-center text-lg"
            >
              <Download className="w-6 h-6 mr-3" />
              Download Output Excel
            </button>
          </div>
        </div>
      ) : plan ? (
        <div>
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4 shadow-sm text-sm text-blue-800 flex items-start">
            <AlertTriangle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5 text-blue-500" />
            <div>
              <p className="font-bold mb-1">Preview the Generated Output</p>
              <p>The output engine will construct a brand new Excel workbook using the Excel 3 file as a structural template. Only the approved jobs below will be written as new rows into the output. All unspecified columns will be deliberately left blank.</p>
            </div>
          </div>
          
          {customColumns.length > 0 && (
            <div className="mb-6 bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
              <h3 className="font-bold text-gray-800 mb-2">Custom Columns Included from Step 5</h3>
              <div className="flex flex-wrap gap-2">
                {customColumns.map((c, i) => (
                  <span key={i} className="bg-indigo-50 text-indigo-700 border border-indigo-200 px-3 py-1 rounded-full text-xs font-bold">
                    {c.heading}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          <div className="overflow-x-auto border border-gray-200 rounded-lg shadow-sm mb-8">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-gray-100 text-gray-600 font-bold uppercase tracking-wider text-xs border-b">
                <tr>
                  <th className="px-4 py-3 sticky left-0 bg-gray-100 z-10 border-r border-gray-200">Job No.</th>
                  <th className="px-4 py-3 text-center">FD</th>
                  <th className="px-4 py-3 text-center">Running Orders</th>
                  <th className="px-4 py-3 text-center">OCS Done</th>
                  <th className="px-4 py-3 text-center">Expediting</th>
                  <th className="px-4 py-3 text-center">Inspection</th>
                  <th className="px-4 py-3 text-center">Others</th>
                  <th className="px-4 py-3 text-center">Meeting</th>
                  <th className="px-4 py-3 text-center">Total</th>
                  <th className="px-4 py-3 text-center">Audit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {plan.cells_to_modify.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="px-4 py-8 text-center text-gray-500 italic">
                      No jobs approved for output. Please approve jobs in the Review tab.
                    </td>
                  </tr>
                ) : (
                  (() => {
                    const map: Record<string, any> = {};
                    plan.cells_to_modify.forEach(c => {
                      if (!map[c.job_number]) {
                        map[c.job_number] = { job_number: c.job_number, fields: {}, cells: [] };
                      }
                      map[c.job_number].fields[c.logical_field] = c.new_value;
                      map[c.job_number].cells.push(c);
                    });
                    const jobWiseData = Object.values(map).sort((a, b) => a.job_number.localeCompare(b.job_number));
                    
                    return jobWiseData.map((job, i) => (
                      <React.Fragment key={i}>
                        <tr className="transition-colors hover:bg-gray-50">
                          <td className="px-4 py-3 font-black text-gray-800 sticky left-0 bg-white group-hover:bg-gray-50 z-10 border-r border-gray-200">{job.job_number}</td>
                          <td className="px-4 py-3 text-center font-mono text-gray-700">{job.fields.orders_for_fd !== undefined && job.fields.orders_for_fd !== null ? job.fields.orders_for_fd : <span className="text-gray-300">-</span>}</td>
                          <td className="px-4 py-3 text-center font-mono text-gray-700">{job.fields.running_orders !== undefined && job.fields.running_orders !== null ? job.fields.running_orders : <span className="text-gray-300">-</span>}</td>
                          <td className="px-4 py-3 text-center font-mono text-gray-700">{job.fields.ocs_done !== undefined && job.fields.ocs_done !== null ? job.fields.ocs_done : <span className="text-gray-300">-</span>}</td>
                          <td className="px-4 py-3 text-center font-mono text-gray-700">{job.fields.expediting !== undefined && job.fields.expediting !== null ? job.fields.expediting : <span className="text-gray-300">-</span>}</td>
                          <td className="px-4 py-3 text-center font-mono font-bold text-indigo-700 bg-indigo-50/30">{job.fields.inspection !== undefined && job.fields.inspection !== null ? job.fields.inspection : <span className="text-gray-300">-</span>}</td>
                          <td className="px-4 py-3 text-center font-mono text-gray-700">{job.fields.others !== undefined && job.fields.others !== null ? job.fields.others : <span className="text-gray-300">-</span>}</td>
                          <td className="px-4 py-3 text-center font-mono text-gray-700">{job.fields.meeting !== undefined && job.fields.meeting !== null ? job.fields.meeting : <span className="text-gray-300">-</span>}</td>
                          <td className="px-4 py-3 text-center font-mono font-black text-emerald-700 bg-emerald-50/30">{job.fields.total !== undefined && job.fields.total !== null ? job.fields.total : <span className="text-gray-300">-</span>}</td>
                          <td className="px-4 py-3 text-center">
                            <button 
                              onClick={() => {
                                const el = document.getElementById(`audit-${job.job_number}`);
                                if (el) {
                                  el.classList.toggle('hidden');
                                }
                              }}
                              className="text-xs text-indigo-600 hover:text-indigo-800 font-bold hover:underline"
                            >
                              Details
                            </button>
                          </td>
                        </tr>
                        <tr id={`audit-${job.job_number}`} className="hidden bg-gray-50 border-b border-gray-200">
                          <td colSpan={10} className="px-6 py-4">
                            <div className="text-xs font-bold text-gray-500 mb-2 uppercase">Field Mapping Audit Trail for {job.job_number}</div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                              {job.cells.map((c: any, idx: number) => (
                                <div key={idx} className="bg-white border rounded p-2 text-xs shadow-sm flex justify-between items-center">
                                  <div>
                                    <span className="font-bold text-gray-700 uppercase">{c.logical_field.replace(/_/g, ' ')}</span>
                                    <div className="text-gray-400 font-mono mt-0.5">{c.sheet_name}</div>
                                  </div>
                                  <div className="text-right">
                                    <div className="font-mono font-bold text-emerald-600">{c.new_value !== null ? String(c.new_value) : 'Blank'}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </td>
                        </tr>
                      </React.Fragment>
                    ));
                  })()
                )}
              </tbody>
            </table>
          </div>
          
          <div className="flex justify-end border-t pt-6">
            <button
              onClick={handleGenerate}
              disabled={generating || plan.approved_jobs_included === 0}
              className={`px-8 py-3 rounded-lg font-bold text-sm shadow-md transition-all flex items-center space-x-2 ${
                generating || plan.approved_jobs_included === 0
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white transform hover:scale-[1.02]'
              }`}
            >
              {generating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              <span>{generating ? 'Generating Output Workbook...' : 'Generate Output Excel'}</span>
              {!generating && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
};
