import React, { useState, useEffect } from 'react';
import type { CombinedJobSummary, ManualInputs } from '../types';
import { sessionService } from '../services/api';
import { Loader2, Calculator, Lock, GitMerge } from 'lucide-react';

interface CombinedCalculationViewProps {
  sessionId: string;
  selectedKeys: string[];
  evaluationMonth: string;
}

export const CombinedCalculationView: React.FC<CombinedCalculationViewProps> = ({ sessionId, selectedKeys, evaluationMonth }) => {
  const [results, setResults] = useState<CombinedJobSummary[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobSummary, setJobSummary] = useState<any>(null);
  
  // Track manual overrides and config
  const [manualInputs, setManualInputs] = useState<Record<string, ManualInputs>>({});

  const fetchCalculations = async () => {
    try {
      setLoading(true);
      
      // Fetch job summary reconciliation
      const summary = await sessionService.getJobNumbers(sessionId);
      setJobSummary(summary);

      const data = await sessionService.calculateCombined(sessionId, {
        job_numbers: selectedKeys,
        evaluation_month: evaluationMonth,
        manual_inputs: manualInputs
      });
      setResults(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to calculate combined rules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        await fetchCalculations();
      } catch (err: any) {
        setError(err.response?.data?.detail || "Failed to initialize calculations");
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, selectedKeys, evaluationMonth]);



  const handleManualInputChange = (job: string, field: keyof ManualInputs, value: string) => {
    const numValue = value.trim() === '' ? null : Number(value);
    
    // Only update if it's a valid number or null
    if (value.trim() !== '' && isNaN(Number(value))) return;

    setManualInputs(prev => ({
      ...prev,
      [job]: {
        ...prev[job],
        [field]: numValue
      }
    }));
  };

  const applyManualInputs = async () => {
    try {
      fetchCalculations();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update calculations");
    }
  };

  if (error) return <div className="p-4 bg-red-50 text-red-600 rounded mt-6 border border-red-200 shadow-sm">{error}</div>;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <div className="flex items-center justify-between mb-8 border-b pb-4">
        <h2 className="text-xl font-bold text-gray-800 uppercase tracking-wider flex items-center">
          <span className="bg-indigo-600 text-white w-8 h-8 rounded-full flex items-center justify-center mr-3 shadow-md"><Calculator className="w-4 h-4" /></span> 
          COMBINED CALCULATION PREVIEW
        </h2>
        <div className="text-xs font-bold text-gray-400 flex items-center">
          <Lock className="w-3 h-3 mr-1" /> EXCEL 3 IS NOT MODIFIED
        </div>
      </div>
      
      {loading && !results && (
        <div className="p-12 flex flex-col items-center justify-center"><Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-4" /><span className="text-gray-500 font-medium">Executing Combined Engine...</span></div>
      )}

      {jobSummary && (
        <div className="mb-8 p-5 bg-gray-50 rounded-lg border border-gray-200">
          <h3 className="text-sm font-bold text-gray-700 uppercase mb-4 flex items-center">
            <GitMerge className="w-4 h-4 mr-2 text-indigo-500" />
            Job Universe Reconciliation
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="p-3 bg-white border rounded shadow-sm">
              <div className="text-xs text-gray-500 font-bold">TOTAL JOBS EXTRACTED</div>
              <div className="text-xl font-black text-indigo-700">{jobSummary.total_valid_job_numbers}</div>
            </div>
            <div className="p-3 bg-white border rounded shadow-sm border-green-200">
              <div className="text-xs text-gray-500 font-bold">MATCHED ALL 3</div>
              <div className="text-xl font-black text-green-600">
                {jobSummary.options.filter((o: any) => o.intersection_status === 'MATCHED').length}
              </div>
            </div>
            <div className="p-3 bg-white border rounded shadow-sm border-amber-200">
              <div className="text-xs text-gray-500 font-bold">MISSING EXCEL 3</div>
              <div className="text-xl font-black text-amber-600">
                {jobSummary.options.filter((o: any) => o.intersection_status === 'MISSING IN EXCEL 3').length}
              </div>
            </div>
            <div className="p-3 bg-white border rounded shadow-sm border-red-200">
              <div className="text-xs text-gray-500 font-bold">EXCEL 3 ONLY</div>
              <div className="text-xl font-black text-red-600">
                {jobSummary.options.filter((o: any) => o.intersection_status === 'EXCEL 3 ONLY').length}
              </div>
            </div>
          </div>
        </div>
      )}

      {results && (
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
            <span className="text-sm text-blue-800 font-medium flex-1">
              If a calculation is <span className="font-bold">BLOCKED</span> due to missing values, you can manually enter them below and hit recalculate.
            </span>
            <div className="flex items-center gap-3">
              <button 
                onClick={applyManualInputs}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-bold shadow transition-colors flex items-center disabled:opacity-50 shrink-0"
              >
                {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Calculator className="w-4 h-4 mr-2" />}
                Recalculate
              </button>
            </div>
          </div>

          <div className="overflow-x-auto border border-gray-200 rounded-lg shadow-sm">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-gray-100 text-gray-600 font-bold uppercase tracking-wider text-xs border-b">
                <tr>
                  <th className="px-4 py-3">Job No.</th>
                  <th className="px-4 py-3" title="FD / Orders for FD f/">FD / Orders for FD f/</th>
                  <th className="px-4 py-3">Running Orders</th>
                  <th className="px-4 py-3">OCS Done</th>
                  <th className="px-4 py-3">Expediting</th>
                  <th className="px-4 py-3">Inspection</th>
                  <th className="px-4 py-3">Others</th>
                  <th className="px-4 py-3">Calc. Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {results.map(res => {

                  const manualValues = manualInputs[res.job_number] || {};
                  
                  // Compute effective values (manual override takes precedence)
                  const effFd = manualValues.fd !== undefined ? manualValues.fd : res.fd;
                  const effRo = manualValues.running_orders !== undefined ? manualValues.running_orders : res.running_orders;
                  const effOcs = manualValues.ocs_done !== undefined ? manualValues.ocs_done : res.ocs_done;
                  const effExp = manualValues.expediting !== undefined ? manualValues.expediting : (
                    res.native_expediting_used 
                      ? res.expediting 
                      : (effRo !== null && effOcs !== null ? (effRo + effOcs) * 2 : null)
                  );
                  const effInsp = manualValues.inspection !== undefined ? manualValues.inspection : res.inspection;
                  const effOthers = manualValues.others !== undefined ? manualValues.others : res.others;
                  
                  // Local calc total calculation matching backend EXACTLY: Total = Expediting + Inspection + Others
                  const localTotal = (effExp !== null && effInsp !== null && effOthers !== null)
                    ? (effExp + effInsp + effOthers)
                    : null;
                  
                  // Formatting helpers for inputs
                  const formatVal = (val: any) => val === null ? '' : String(val);
                  const isOverride = (field: keyof ManualInputs) => manualValues[field] !== undefined;
                  
                  // Base input class
                  const inputClass = (field: keyof ManualInputs) => 
                    `w-20 px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-center transition-colors ${isOverride(field) ? 'border-amber-400 bg-amber-50 text-amber-900 font-bold' : 'border-gray-300 text-gray-700'}`;

                  return (
                    <React.Fragment key={res.job_number}>
                      <tr className={`transition-colors ${res.status === 'BLOCKED' ? 'bg-red-50/30' : res.status === 'WARNING' ? 'bg-amber-50/30' : 'hover:bg-gray-50'}`}>
                        <td className="px-4 py-3 font-black text-gray-800">{res.job_number}</td>
                        
                        {/* FD Input */}
                        <td className="px-4 py-2">
                          <input 
                            type="text" value={formatVal(effFd)}
                            onChange={(e) => handleManualInputChange(res.job_number, 'fd', e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') applyManualInputs(); }}
                            placeholder="0" className={inputClass('fd')}
                          />
                        </td>
                        
                        {/* Running Orders Input */}
                        <td className="px-4 py-2">
                          <input 
                            type="text" value={formatVal(effRo)}
                            onChange={(e) => handleManualInputChange(res.job_number, 'running_orders', e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') applyManualInputs(); }}
                            placeholder="0" className={inputClass('running_orders')}
                          />
                        </td>
                        
                        {/* OCS Done Input */}
                        <td className="px-4 py-2">
                          <input 
                            type="text" value={formatVal(effOcs)}
                            onChange={(e) => handleManualInputChange(res.job_number, 'ocs_done', e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') applyManualInputs(); }}
                            placeholder="Pending" className={inputClass('ocs_done')}
                          />
                        </td>
                        
                        {/* Expediting Input */}
                        <td className="px-4 py-2 relative group">
                          <input 
                            type="text" value={formatVal(effExp)}
                            onChange={(e) => handleManualInputChange(res.job_number, 'expediting', e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') applyManualInputs(); }}
                            placeholder="Blocked" className={inputClass('expediting')}
                          />
                          {isOverride('expediting') && <div className="hidden group-hover:block absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">Manual Override</div>}
                        </td>
                        
                        {/* Inspection Input */}
                        <td className="px-4 py-2 relative group">
                          <input 
                            type="text" value={formatVal(effInsp)}
                            onChange={(e) => handleManualInputChange(res.job_number, 'inspection', e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') applyManualInputs(); }}
                            placeholder="Missing" className={inputClass('inspection')}
                          />
                          {isOverride('inspection') && <div className="hidden group-hover:block absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">Manual Override</div>}
                        </td>
                        
                        {/* Others Input */}
                        <td className="px-4 py-2 relative group">
                          <input 
                            type="text" value={formatVal(effOthers)}
                            onChange={(e) => handleManualInputChange(res.job_number, 'others', e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') applyManualInputs(); }}
                            placeholder="Pending" className={inputClass('others')}
                          />
                          {isOverride('others') && <div className="hidden group-hover:block absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">Manual Override</div>}
                        </td>
                        
                        {/* Calc Total (Read-Only) */}
                        <td className="px-4 py-3 font-black text-gray-700 text-base">
                          {localTotal !== null ? localTotal : <span className="text-gray-400 italic text-sm">Blocked</span>}
                          {localTotal !== res.calculated_total && (
                            <span className="ml-2 text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-bold">Preview</span>
                          )}
                        </td>
                      </tr>
                      

                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
