import React, { useState, useEffect } from 'react';
import type { JobReviewResult } from '../types';
import { sessionService } from '../services/api';
import { Loader2, AlertTriangle, CheckCircle2, XCircle, Search, Save, RotateCcw, ThumbsUp, ThumbsDown } from 'lucide-react';

interface ReviewDashboardProps {
  sessionId: string;
  selectedKeys: string[];
  evaluationMonth: string;
  onNext: () => void;
  customColumns?: import('../types').CustomColumnData[];
  setCustomColumns?: (cols: import('../types').CustomColumnData[]) => void;
}

type FilterStatus = 'ALL' | 'DRAFT' | 'WARNING' | 'BLOCKED' | 'APPROVED' | 'DELETED';

const isNonZero = (val: any) => val !== null && val !== undefined && val !== '' && Number(val) !== 0;

export const ReviewDashboard: React.FC<ReviewDashboardProps> = ({ sessionId, selectedKeys, evaluationMonth, onNext, customColumns = [], setCustomColumns = () => {} }) => {
  const [jobs, setJobs] = useState<JobReviewResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [filter, setFilter] = useState<FilterStatus>('ALL');
  const [search, setSearch] = useState('');
  const [newColumnHeading, setNewColumnHeading] = useState('');
  
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  
  // Pending override state for the currently expanded job
  const [pendingOverrides, setPendingOverrides] = useState<{ field: 'ocs_done' | 'others' | 'expediting' | 'meeting', value: string, reason: string } | null>(null);

  const fetchReviews = async () => {
    try {
      if (jobs.length === 0 && !loading) {
        setLoading(true);
      }
      const data = await sessionService.getReviewJobs(sessionId, { job_numbers: selectedKeys, evaluation_month: evaluationMonth });
      setJobs(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load review jobs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, evaluationMonth]); // removed selectedKeys to prevent refetch loop on delete

  const handleApplyOverride = async (jobId: string) => {
    if (!pendingOverrides) return;
    try {
      setError(null);
      const valStr = pendingOverrides.value.trim();
      const numValue = valStr === '' ? null : Number(valStr);
      
      await sessionService.overrideJob(sessionId, jobId, {
        field: pendingOverrides.field,
        value: numValue,
        reason: pendingOverrides.reason
      });
      
      setPendingOverrides(null);
      await fetchReviews();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to apply override");
    }
  };

  const handleResetOverrides = async (jobId: string) => {
    try {
      setError(null);
      await sessionService.resetJobOverrides(sessionId, jobId);
      await fetchReviews();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to reset overrides");
    }
  };

  
  const handleApproveAll = async () => {
    try {
      setError(null);
      setActionLoading('approve_all');
      await sessionService.approveAll(sessionId, { job_numbers: selectedKeys });
      await fetchReviews();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to approve all jobs");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteAll = async () => {
    try {
      setError(null);
      setActionLoading('delete_all');
      await sessionService.deleteAll(sessionId, { job_numbers: selectedKeys });
      await fetchReviews();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete all jobs");
    } finally {
      setActionLoading(null);
    }
  };

  const handleApprove = async (jobId: string, acknowledgeWarnings: boolean = false) => {
    try {
      setError(null);
      setActionLoading(jobId);
      await sessionService.approveJob(sessionId, jobId, { acknowledge_warnings: acknowledgeWarnings });
      await fetchReviews();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to approve job");
    } finally {
      setActionLoading(null);
    }
  };

  const handleUnapprove = async (jobId: string) => {
    try {
      setError(null);
      await sessionService.unapproveJob(sessionId, jobId);
      await fetchReviews();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to unapprove job");
    }
  };

  const handleDelete = async (jobId: string) => {
    try {
      setError(null);
      setActionLoading(jobId);
      await sessionService.deleteJob(sessionId, jobId);
      await fetchReviews();
      if (expandedJob === jobId) setExpandedJob(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete job");
    } finally {
      setActionLoading(null);
    }
  };

  const handleUndelete = async (jobId: string) => {
    try {
      setError(null);
      setActionLoading(jobId);
      await sessionService.undeleteJob(sessionId, jobId);
      await fetchReviews();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to undelete job");
    } finally {
      setActionLoading(null);
    }
  };

  const counts = {
    total: jobs.length,
    approved: jobs.filter(j => j.status === 'APPROVED').length,
    draft: jobs.filter(j => j.status === 'DRAFT').length,
    warning: jobs.filter(j => j.status === 'WARNING').length,
    blocked: jobs.filter(j => j.status === 'BLOCKED').length,
    deleted: jobs.filter(j => j.status === 'DELETED').length
  };

  const filteredJobs = jobs.filter(j => {
    if (filter !== 'ALL' && j.status !== filter) return false;
    if (search && !j.job_number.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 pb-4 border-b">
        <h2 className="text-xl font-bold text-gray-800 uppercase tracking-wider flex items-center">
          <span className="bg-indigo-600 text-white w-8 h-8 rounded-full flex items-center justify-center mr-3 shadow-md"><ThumbsUp className="w-4 h-4" /></span> 
          REVIEW & APPROVAL
        </h2>
        
        {/* SUMMARY BADGES */}
        <div className="flex gap-2 mt-4 md:mt-0 overflow-x-auto pb-2 md:pb-0">
          <div className="bg-gray-100 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-bold text-gray-700 whitespace-nowrap">
            Total: {counts.total}
          </div>
          <div className="bg-green-50 px-3 py-1.5 rounded-lg border border-green-200 text-xs font-bold text-green-700 whitespace-nowrap">
            Approved: {counts.approved}
          </div>
          <div className="bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-200 text-xs font-bold text-blue-700 whitespace-nowrap">
            Draft: {counts.draft}
          </div>
          <div className="bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200 text-xs font-bold text-amber-700 whitespace-nowrap">
            Warning: {counts.warning}
          </div>
          <div className="bg-red-50 px-3 py-1.5 rounded-lg border border-red-200 text-xs font-bold text-red-700 whitespace-nowrap">
            Blocked: {counts.blocked}
          </div>
          <div className="bg-red-100 px-3 py-1.5 rounded-lg border border-red-300 text-xs font-bold text-red-900 whitespace-nowrap">
            Deleted: {counts.deleted}
          </div>
        </div>
      </div>

      {error && <div className="p-4 bg-red-50 text-red-600 rounded mb-6 border border-red-200 shadow-sm">{error}</div>}

      {/* FILTERS */}
      <div className="flex flex-col md:flex-row justify-between gap-4 mb-6">
        <div className="flex space-x-2">
          {(['ALL', 'DRAFT', 'WARNING', 'BLOCKED', 'APPROVED', 'DELETED'] as FilterStatus[]).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-md text-xs font-bold transition-colors ${
                filter === f 
                  ? 'bg-indigo-600 text-white shadow-sm' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        
        <div className="relative flex items-center space-x-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input 
              type="text" 
              placeholder="Search Job No..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm w-full md:w-64 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => handleDeleteAll()}
              disabled={actionLoading === 'delete_all'}
              className="flex items-center space-x-2 px-4 py-2 bg-red-50 text-red-600 border border-red-200 rounded-lg hover:bg-red-100 font-bold text-sm shadow-sm"
            >
              <XCircle className="w-4 h-4" />
              <span>Delete All</span>
            </button>
            <button
              onClick={() => handleApproveAll()}
              disabled={actionLoading === 'approve_all'}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-bold text-sm shadow-sm"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Approve All</span>
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="p-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-indigo-500" /></div>
      ) : (
        <div className="overflow-x-auto border border-gray-200 rounded-lg shadow-sm mb-6">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-gray-100 text-gray-600 font-bold uppercase tracking-wider text-xs border-b">
              <tr>
                <th className="px-4 py-3">Job No.</th>
                <th className="px-4 py-3">FD</th>
                <th className="px-4 py-3">Running Orders</th>
                <th className="px-4 py-3">OCS Done</th>
                <th className="px-4 py-3">Expediting</th>
                <th className="px-4 py-3">Inspection</th>
                <th className="px-4 py-3">Others</th>
                <th className="px-4 py-3">Meeting</th>
                {customColumns.map((c, i) => (
                  <th key={i} className="px-4 py-3 relative group bg-indigo-50/20 text-indigo-900 border-l border-r border-indigo-100">
                    {c.heading}
                    <button 
                      onClick={() => setCustomColumns(customColumns.filter((_, idx) => idx !== i))}
                      className="absolute right-2 text-red-500 hidden group-hover:block top-1/2 -translate-y-1/2 bg-white rounded-full px-1.5 shadow"
                      title="Remove Column"
                    >
                      ×
                    </button>
                  </th>
                ))}
                <th className="px-4 py-3 text-indigo-700">Total</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredJobs.map(res => {
                const hasHighlight = isNonZero(res.fd) || isNonZero(res.running_orders) || isNonZero(res.ocs_done) || isNonZero(res.expediting) || isNonZero(res.inspection) || isNonZero(res.others) || isNonZero(res.meeting) || isNonZero(res.calculated_total);
                
                return (
                <tr key={res.job_number} data-test-id={`job-row-${res.job_number.toLowerCase()}`} className={`transition-colors ${expandedJob === res.job_number ? 'bg-indigo-50/50' : res.status === 'DELETED' ? 'bg-red-50 text-red-900 opacity-75' : res.status === 'APPROVED' ? 'bg-green-50/30' : hasHighlight ? 'bg-amber-50/50 hover:bg-amber-100/50' : 'hover:bg-gray-50'}`}>
                  <td className="px-4 py-3 font-black text-gray-800">{res.job_number}</td>
                  <td className={`px-4 py-3 text-gray-600 ${isNonZero(res.fd) ? 'bg-amber-100/50 font-semibold' : ''}`}>{res.fd}</td>
                  <td className={`px-4 py-3 text-gray-600 ${isNonZero(res.running_orders) ? 'bg-amber-100/50 font-semibold' : ''}`}>{res.running_orders}</td>
                  <td className={`px-4 py-3 font-medium ${isNonZero(res.ocs_done) ? 'bg-amber-100/50 font-semibold text-amber-900' : ''}`}>
                    {res.ocs_done !== null ? res.ocs_done : <span className="text-gray-400">—</span>}
                    {res.overrides['ocs_done']?.active && <span className="ml-2 text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded-full font-bold">OVR</span>}
                  </td>
                  <td className={`px-4 py-3 font-bold text-gray-700 ${isNonZero(res.expediting) ? 'bg-amber-100/50 text-amber-900' : ''}`}>{res.expediting !== null ? res.expediting : <span className="text-gray-400 italic">Blocked</span>}</td>
                  <td className={`px-4 py-3 font-bold text-gray-700 ${isNonZero(res.inspection) ? 'bg-amber-100/50 text-amber-900' : ''}`}>{res.inspection !== null ? res.inspection : <span className="text-gray-400 italic">Blocked</span>}</td>
                  <td className={`px-4 py-3 font-medium ${isNonZero(res.others) ? 'bg-amber-100/50 font-semibold text-amber-900' : ''}`}>
                    {res.others !== null ? res.others : <span className="text-gray-400">—</span>}
                    {res.overrides['others']?.active && <span className="ml-2 text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded-full font-bold">OVR</span>}
                  </td>
                  <td className={`px-4 py-3 font-medium ${isNonZero(res.meeting) ? 'bg-amber-100/50 font-semibold text-amber-900' : ''}`}>
                    {res.meeting !== null ? res.meeting : <span className="text-gray-400">—</span>}
                    {res.overrides['meeting']?.active && <span className="ml-2 text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded-full font-bold">OVR</span>}
                  </td>
                  {customColumns.map((col, i) => {
                    const isNumber = !isNaN(Number(col.data[res.job_number])) && col.data[res.job_number] !== '' && col.data[res.job_number] !== null && col.data[res.job_number] !== undefined;
                    const isNonZeroNum = isNumber && Number(col.data[res.job_number]) !== 0;
                    return (
                      <td key={i} className={`p-0 border-l border-r border-indigo-50 min-w-[120px] ${isNonZeroNum ? 'bg-amber-100/50' : ''}`}>
                        <input 
                          type="text" 
                          className="w-full h-full min-h-[44px] px-4 py-2 outline-none focus:bg-indigo-50 focus:ring-2 focus:ring-inset focus:ring-indigo-500 transition-colors bg-transparent"
                          value={col.data[res.job_number] || ''}
                          onChange={e => {
                            const newCols = [...customColumns];
                            newCols[i].data[res.job_number] = e.target.value;
                            setCustomColumns(newCols);
                          }}
                        />
                      </td>
                    );
                  })}
                  <td className={`px-4 py-3 font-black text-indigo-700 text-base ${isNonZero(res.calculated_total) ? 'bg-amber-100/50' : ''}`}>{res.calculated_total !== null ? res.calculated_total : <span className="text-gray-400 italic text-sm">Blocked</span>}</td>
                  <td className="px-4 py-3 text-center">
                    <div className={`inline-flex items-center font-bold px-2.5 py-1 rounded text-xs ${
                      res.status === 'BLOCKED' ? 'bg-red-100 text-red-700' :
                      res.status === 'DELETED' ? 'bg-red-200 text-red-900' :
                      res.status === 'WARNING' ? 'bg-amber-100 text-amber-700' : 
                      res.status === 'APPROVED' ? 'bg-green-100 text-green-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {res.status === 'BLOCKED' && <XCircle className="w-3 h-3 mr-1" />}
                      {res.status === 'DELETED' && <XCircle className="w-3 h-3 mr-1" />}
                      {res.status === 'WARNING' && <AlertTriangle className="w-3 h-3 mr-1" />}
                      {res.status === 'APPROVED' && <CheckCircle2 className="w-3 h-3 mr-1" />}
                      {res.status === 'DRAFT' && <RotateCcw className="w-3 h-3 mr-1" />}
                      {res.status}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end space-x-2">
                      <button 
                        data-test-id={`review-${res.job_number.toLowerCase()}`}
                        onClick={() => {
                          setExpandedJob(expandedJob === res.job_number ? null : res.job_number);
                          setPendingOverrides(null);
                        }}
                        className="text-indigo-600 hover:text-indigo-800 font-bold text-xs bg-indigo-50 px-2 py-1 rounded"
                      >
                        {expandedJob === res.job_number ? 'Close' : 'Review'}
                      </button>
                      
                      {res.status === 'APPROVED' ? (
                        <button 
                          onClick={() => handleUnapprove(res.job_number)}
                          disabled={actionLoading === res.job_number}
                          className="font-bold text-xs px-2 py-1 rounded bg-gray-200 text-gray-700 hover:bg-gray-300"
                        >
                          Undo Approve
                        </button>
                      ) : (
                        <button 
                          onClick={() => handleApprove(res.job_number, res.status === 'WARNING')}
                          disabled={res.status === 'BLOCKED' || res.status === 'DELETED' || actionLoading === res.job_number}
                          className={`font-bold text-xs px-2 py-1 rounded ${
                            (res.status === 'BLOCKED' || res.status === 'DELETED') ? 'bg-gray-100 text-gray-400 cursor-not-allowed' :
                            'bg-green-100 text-green-700 hover:bg-green-200'
                          }`}
                        >
                          Approve
                        </button>
                      )}
                      
                      {res.status === 'DELETED' ? (
                        <button 
                          onClick={() => handleUndelete(res.job_number)}
                          disabled={actionLoading === res.job_number}
                          className="font-bold text-xs px-2 py-1 rounded bg-gray-200 text-gray-700 hover:bg-gray-300"
                        >
                          Undo Delete
                        </button>
                      ) : (
                        <button 
                          onClick={() => handleDelete(res.job_number)}
                          disabled={actionLoading === res.job_number}
                          className="text-red-600 hover:text-red-800 font-bold text-xs bg-red-50 hover:bg-red-100 px-2 py-1 rounded"
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* EXPANDED DETAIL VIEW */}
      {expandedJob && (() => {
        const job = jobs.find(j => j.job_number === expandedJob);
        if (!job) return null;
        
        return (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 shadow-inner mb-6">
            <div className="flex justify-between items-start mb-6 border-b border-gray-200 pb-4">
              <h3 className="text-xl font-black text-gray-800 flex items-center">
                <span className="bg-gray-200 px-3 py-1 rounded-md mr-3">JOB: {job.job_number}</span>
                <div className={`inline-flex items-center font-bold px-3 py-1 rounded-lg text-sm ${
                      job.status === 'BLOCKED' ? 'bg-red-100 text-red-700' :
                      job.status === 'WARNING' ? 'bg-amber-100 text-amber-700' : 
                      job.status === 'APPROVED' ? 'bg-green-100 text-green-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                  {job.status}
                </div>
              </h3>
              
              <div className="flex gap-2">
                {Object.values(job.overrides).some(o => o.active) && (
                  <button 
                    onClick={() => handleResetOverrides(job.job_number)}
                    className="flex items-center text-xs font-bold bg-white text-gray-600 border border-gray-300 px-3 py-2 rounded hover:bg-gray-100 transition-colors shadow-sm"
                  >
                    <RotateCcw className="w-3 h-3 mr-2" /> Reset to Source
                  </button>
                )}
                
                {job.status === 'APPROVED' ? (
                  <button 
                    onClick={() => handleUnapprove(job.job_number)}
                    disabled={actionLoading === job.job_number}
                    className="flex items-center text-xs font-bold bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors shadow-sm"
                  >
                    <ThumbsDown className="w-3 h-3 mr-2" /> Unapprove Job
                  </button>
                ) : (
                  <button 
                    data-test-id={`approve-${job.job_number}`}
                    onClick={() => handleApprove(job.job_number, job.status === 'WARNING')}
                    disabled={job.status === 'BLOCKED' || job.status === 'DELETED' || actionLoading === job.job_number}
                    className={`flex items-center text-xs font-bold px-6 py-2 rounded transition-colors shadow-sm ${
                      (job.status === 'BLOCKED' || job.status === 'DELETED') ? 'bg-gray-300 text-gray-500 cursor-not-allowed' :
                      job.status === 'WARNING' ? 'bg-amber-500 hover:bg-amber-600 text-white' :
                      'bg-green-600 hover:bg-green-700 text-white'
                    }`}
                  >
                    {actionLoading === job.job_number ? <Loader2 className="w-3 h-3 animate-spin mr-2" /> : <ThumbsUp className="w-3 h-3 mr-2" />}
                    {job.status === 'WARNING' ? 'Acknowledge Warning & Approve' : 'Approve Job'}
                  </button>
                )}
                
                {job.status === 'DELETED' ? (
                  <button 
                    onClick={() => handleUndelete(job.job_number)}
                    disabled={actionLoading === job.job_number}
                    className="flex items-center text-xs font-bold bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors shadow-sm"
                  >
                    Undo Delete
                  </button>
                ) : (
                  <button 
                    onClick={() => handleDelete(job.job_number)}
                    disabled={actionLoading === job.job_number}
                    className="flex items-center text-xs font-bold bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors shadow-sm"
                  >
                    <XCircle className="w-3 h-3 mr-2" /> Delete
                  </button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              
              {/* SOURCE DATA */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest border-b pb-2">Source / Extracted Logic</h4>
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="mb-3"><span className="text-gray-500 text-xs">FD:</span> <span className="font-bold ml-2">{job.fd}</span></div>
                  <div className="mb-3"><span className="text-gray-500 text-xs">Running Orders:</span> <span className="font-bold ml-2">{job.running_orders}</span></div>
                </div>
                
                {job.warnings.length > 0 && (
                  <div className="bg-white p-4 rounded-lg border border-red-200 shadow-sm">
                    <h4 className="text-xs font-bold text-red-500 uppercase tracking-widest mb-2 flex items-center"><AlertTriangle className="w-3 h-3 mr-1"/> Issues</h4>
                    <ul className="text-xs text-red-700 list-disc pl-4 space-y-1">
                      {job.warnings.map((w, i) => <li key={i}>{w}</li>)}
                    </ul>
                  </div>
                )}
              </div>

              {/* EDITABLE INPUTS */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-widest border-b pb-2">Editable Inputs</h4>
                
                {/* OCS Done Edit */}
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-gray-700 text-sm">OCS Done</span>
                    {job.overrides['ocs_done'] ? (
                      <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Overridden</span>
                    ) : (
                      <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Source</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mb-3">
                    Source value: <span className="font-bold text-gray-800">{job.overrides['ocs_done']?.source_value ?? (job.ocs_done !== null ? job.ocs_done : 'Missing')}</span>
                  </div>
                  
                  <div className="flex gap-2">
                    <input 
                      type="text"
                      className="border border-gray-300 rounded px-2 py-1 text-sm w-20 focus:ring-2 focus:ring-indigo-500"
                      value={pendingOverrides?.field === 'ocs_done' ? pendingOverrides.value : (job.ocs_done !== null ? job.ocs_done : '')}
                      onChange={e => setPendingOverrides({ field: 'ocs_done', value: e.target.value, reason: pendingOverrides?.field === 'ocs_done' ? pendingOverrides.reason : '' })}
                    />
                    {pendingOverrides?.field === 'ocs_done' && (
                      <>
                        <input 
                          type="text"
                          placeholder="Reason for change..."
                          className="border border-gray-300 rounded px-2 py-1 text-sm flex-1 focus:ring-2 focus:ring-indigo-500"
                          value={pendingOverrides.reason}
                          onChange={e => setPendingOverrides({ ...pendingOverrides, reason: e.target.value })}
                        />
                        <button 
                          onClick={() => handleApplyOverride(job.job_number)}
                          className="bg-indigo-600 text-white rounded px-3 py-1 text-xs font-bold flex items-center hover:bg-indigo-700"
                        >
                          <Save className="w-3 h-3 mr-1" /> Save
                        </button>
                      </>
                    )}
                  </div>
                  
                  {job.overrides['ocs_done']?.reason && (
                    <div className="mt-2 text-[11px] text-gray-500 bg-gray-50 p-2 rounded">
                      <span className="font-bold">Reason:</span> {job.overrides['ocs_done'].reason}
                    </div>
                  )}
                </div>

                {/* Others Edit */}
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-gray-700 text-sm">Others</span>
                    {job.overrides['others'] ? (
                      <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Overridden</span>
                    ) : (
                      <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Source</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mb-3">
                    Source value: <span className="font-bold text-gray-800">{job.overrides['others']?.source_value ?? (job.others !== null ? job.others : 'Missing')}</span>
                  </div>
                  
                  <div className="flex gap-2">
                    <input 
                      type="text"
                      className="border border-gray-300 rounded px-2 py-1 text-sm w-20 focus:ring-2 focus:ring-indigo-500"
                      value={pendingOverrides?.field === 'others' ? pendingOverrides.value : (job.others !== null ? job.others : '')}
                      onChange={e => setPendingOverrides({ field: 'others', value: e.target.value, reason: pendingOverrides?.field === 'others' ? pendingOverrides.reason : '' })}
                    />
                    {pendingOverrides?.field === 'others' && (
                      <>
                        <input 
                          type="text"
                          placeholder="Reason for change..."
                          className="border border-gray-300 rounded px-2 py-1 text-sm flex-1 focus:ring-2 focus:ring-indigo-500"
                          value={pendingOverrides.reason}
                          onChange={e => setPendingOverrides({ ...pendingOverrides, reason: e.target.value })}
                        />
                        <button 
                          onClick={() => handleApplyOverride(job.job_number)}
                          className="bg-indigo-600 text-white rounded px-3 py-1 text-xs font-bold flex items-center hover:bg-indigo-700"
                        >
                          <Save className="w-3 h-3 mr-1" /> Save
                        </button>
                      </>
                    )}
                  </div>
                  
                  {job.overrides['others']?.reason && (
                    <div className="mt-2 text-[11px] text-gray-500 bg-gray-50 p-2 rounded">
                      <span className="font-bold">Reason:</span> {job.overrides['others'].reason}
                    </div>
                  )}
                </div>

                {/* Expediting Edit */}
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-gray-700 text-sm">Expediting</span>
                    {job.overrides['expediting'] ? (
                      <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Overridden</span>
                    ) : job.native_expediting_used ? (
                      <span className="text-[10px] bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Native Formula</span>
                    ) : (
                      <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Calculated</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mb-3">
                    Source value: <span className="font-bold text-gray-800">{job.overrides['expediting']?.source_value ?? (job.expediting !== null ? job.expediting : 'Missing')}</span>
                  </div>
                  
                  <div className="flex gap-2">
                    <input 
                      type="text"
                      className="border border-gray-300 rounded px-2 py-1 text-sm w-20 focus:ring-2 focus:ring-indigo-500"
                      value={pendingOverrides?.field === 'expediting' ? pendingOverrides.value : (job.expediting !== null ? job.expediting : '')}
                      onChange={e => setPendingOverrides({ field: 'expediting', value: e.target.value, reason: pendingOverrides?.field === 'expediting' ? pendingOverrides.reason : '' })}
                    />
                    {pendingOverrides?.field === 'expediting' && (
                      <>
                        <input 
                          type="text"
                          placeholder="Reason for change..."
                          className="border border-gray-300 rounded px-2 py-1 text-sm flex-1 focus:ring-2 focus:ring-indigo-500"
                          value={pendingOverrides.reason}
                          onChange={e => setPendingOverrides({ ...pendingOverrides, reason: e.target.value })}
                        />
                        <button 
                          onClick={() => handleApplyOverride(job.job_number)}
                          className="bg-indigo-600 text-white rounded px-3 py-1 text-xs font-bold flex items-center hover:bg-indigo-700"
                        >
                          <Save className="w-3 h-3 mr-1" /> Save
                        </button>
                      </>
                    )}
                  </div>
                  
                  {job.overrides['expediting']?.reason && (
                    <div className="mt-2 text-[11px] text-gray-500 bg-gray-50 p-2 rounded">
                      <span className="font-bold">Reason:</span> {job.overrides['expediting'].reason}
                    </div>
                  )}
                </div>

                {/* Meeting Edit */}
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-gray-700 text-sm">Meeting</span>
                    {job.overrides['meeting'] ? (
                      <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Overridden</span>
                    ) : (
                      <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Source</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mb-3">
                    Source value: <span className="font-bold text-gray-800">{job.overrides['meeting']?.source_value ?? (job.meeting !== null ? job.meeting : 'Missing')}</span>
                  </div>
                  
                  <div className="flex gap-2">
                    <input 
                      type="text"
                      className="border border-gray-300 rounded px-2 py-1 text-sm w-20 focus:ring-2 focus:ring-indigo-500"
                      value={pendingOverrides?.field === 'meeting' ? pendingOverrides.value : (job.meeting !== null ? job.meeting : '')}
                      onChange={e => setPendingOverrides({ field: 'meeting', value: e.target.value, reason: pendingOverrides?.field === 'meeting' ? pendingOverrides.reason : '' })}
                    />
                    {pendingOverrides?.field === 'meeting' && (
                      <>
                        <input 
                          type="text"
                          placeholder="Reason for change..."
                          className="border border-gray-300 rounded px-2 py-1 text-sm flex-1 focus:ring-2 focus:ring-indigo-500"
                          value={pendingOverrides.reason}
                          onChange={e => setPendingOverrides({ ...pendingOverrides, reason: e.target.value })}
                        />
                        <button 
                          onClick={() => handleApplyOverride(job.job_number)}
                          className="bg-indigo-600 text-white rounded px-3 py-1 text-xs font-bold flex items-center hover:bg-indigo-700"
                        >
                          <Save className="w-3 h-3 mr-1" /> Save
                        </button>
                      </>
                    )}
                  </div>
                  
                  {job.overrides['meeting']?.reason && (
                    <div className="mt-2 text-[11px] text-gray-500 bg-gray-50 p-2 rounded">
                      <span className="font-bold">Reason:</span> {job.overrides['meeting'].reason}
                    </div>
                  )}
                </div>
              </div>

              {/* CALCULATED RESULTS */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-green-400 uppercase tracking-widest border-b pb-2">Calculated Result</h4>
                <div className="bg-gray-800 p-5 rounded-lg border border-gray-700 shadow-sm text-white">
                  <div className="flex justify-between items-center mb-4 border-b border-gray-700 pb-4">
                    <span className="text-gray-400 text-sm">Expediting:</span>
                    <span className="font-black text-xl">{job.expediting !== null ? job.expediting : <span className="text-red-400 italic text-sm">Blocked</span>}</span>
                  </div>
                  <div className="flex justify-between items-center mb-4 border-b border-gray-700 pb-4">
                    <span className="text-gray-400 text-sm">Inspection:</span>
                    <span className="font-black text-xl">{job.inspection !== null ? job.inspection : <span className="text-red-400 italic text-sm">Blocked</span>}</span>
                  </div>
                  <div className="flex justify-between items-center text-green-400">
                    <span className="text-sm font-bold uppercase tracking-wider">Total Output:</span>
                    <span className="font-black text-3xl">{job.calculated_total !== null ? job.calculated_total : <span className="text-red-400 italic text-sm">Blocked</span>}</span>
                  </div>
                </div>
                
                <div className="bg-gray-800 text-green-400 p-4 rounded-lg shadow-inner font-mono text-[10px] overflow-x-auto border border-gray-700">
                  <div className="mb-2 text-gray-500 uppercase tracking-widest border-b border-gray-700 pb-1">Mathematical Evidence</div>
                  {job.evidence.map((line, i) => (
                    <div key={i} className={`whitespace-pre ${line === '---' ? 'my-2 text-gray-600' : ''}`}>
                      {line}
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        );
      })()}

      <div className="mt-8 mb-6 bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-bold text-gray-800 mb-1 uppercase tracking-wider">Custom Columns</h3>
        <p className="text-sm text-gray-500 mb-4">Add additional columns that will be injected into the final generated output for these jobs.</p>
        <div className="flex gap-2 mb-4">
          <input 
            type="text"
            placeholder="Column Heading"
            value={newColumnHeading}
            onChange={e => setNewColumnHeading(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 text-sm flex-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
          <button 
            onClick={() => {
              if (newColumnHeading.trim()) {
                setCustomColumns([...customColumns, { heading: newColumnHeading.trim(), data: {} }]);
                setNewColumnHeading('');
              }
            }}
            className="bg-gray-800 hover:bg-gray-900 text-white px-4 py-2 rounded text-sm font-bold shadow-sm transition-colors"
          >
            + Add Column
          </button>
        </div>
        

      </div>

      <div className="mt-4 pt-6 border-t border-gray-200 flex justify-end">
        <button
          onClick={onNext}
          disabled={counts.approved === 0}
          className={`px-8 py-3 rounded-lg font-bold text-sm shadow-md transition-all flex items-center space-x-2 ${
            counts.approved === 0
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white transform hover:scale-[1.02]'
          }`}
        >
          <span>Proceed to Output Generation ({counts.approved} Approved)</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
        </button>
      </div>
    </div>
  );
};
