import React, { useState } from 'react';
import { X, Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';

export interface ColumnDef {
  header: string;
  key: string;
  render?: (val: any, record: any, i?: number) => React.ReactNode;
}

export interface EvidenceModalProps {
  title: string;
  subtitle?: string;
  summaryStats: { label: string; value: React.ReactNode; colorClass?: string }[];
  records: any[];
  columns: ColumnDef[];
  isOpen: boolean;
  onClose: () => void;
  // Function to determine if a record matches current filter "All" | "Valid" | "Invalid" | "Warnings"
  filterRecord?: (record: any, filterType: string) => boolean;
  // Function to determine if a record matches a search term
  searchRecord?: (record: any, searchTerm: string) => boolean;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({
  title,
  subtitle,
  summaryStats,
  records,
  columns,
  isOpen,
  onClose,
  filterRecord,
  searchRecord
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('All');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  if (!isOpen) return null;

  let filteredRecords = records;
  
  if (filterRecord && filterType !== 'All') {
    filteredRecords = filteredRecords.filter(r => filterRecord(r, filterType));
  }

  if (searchRecord && searchTerm.trim() !== '') {
    filteredRecords = filteredRecords.filter(r => searchRecord(r, searchTerm));
  }

  const totalPages = Math.ceil(filteredRecords.length / pageSize) || 1;
  const currentRecords = filteredRecords.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 sm:p-6 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50/50">
          <div>
            <h2 className="text-xl font-bold text-gray-800 uppercase tracking-wider">{title}</h2>
            {subtitle && <p className="text-sm font-medium text-gray-500 mt-1">{subtitle}</p>}
          </div>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-700 hover:bg-gray-200 rounded-full transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Summary Stats */}
        <div className="px-6 py-4 bg-white border-b border-gray-100 flex flex-wrap gap-4 items-center">
          {summaryStats.map((stat, i) => (
            <div key={i} className="flex flex-col border-r pr-4 last:border-r-0">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">{stat.label}</span>
              <span className={`text-lg font-black ${stat.colorClass || 'text-gray-800'}`}>{stat.value}</span>
            </div>
          ))}
        </div>

        {/* Toolbar: Search & Filters */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200 flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input 
              type="text" 
              placeholder="Search records..." 
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          
          <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
            <Filter className="w-4 h-4 text-gray-400 mr-1" />
            {['All', 'Valid', 'Invalid', 'Warnings'].map(ft => (
              <button
                key={ft}
                onClick={() => { setFilterType(ft); setCurrentPage(1); }}
                className={`px-3 py-1.5 text-xs font-bold rounded-md transition-colors whitespace-nowrap ${
                  filterType === ft 
                    ? 'bg-indigo-600 text-white shadow-sm' 
                    : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-100'
                }`}
              >
                {ft}
              </button>
            ))}
          </div>
        </div>

        {/* Table Content */}
        <div className="flex-1 overflow-auto bg-white">
          <table className="w-full text-left border-collapse">
            <thead className="bg-white sticky top-0 z-10 shadow-sm border-b">
              <tr>
                {columns.map((c, i) => (
                  <th key={i} className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider bg-gray-50">
                    {c.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {currentRecords.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-6 py-12 text-center text-gray-500">
                    No records found matching criteria.
                  </td>
                </tr>
              ) : (
                currentRecords.map((record, rIdx) => (
                  <tr key={rIdx} className="hover:bg-gray-50/50 transition-colors">
                    {columns.map((c, cIdx) => (
                      <td key={cIdx} className="px-6 py-4 align-top">
                        {c.render ? c.render(record[c.key], record, (currentPage - 1) * pageSize + rIdx) : record[c.key]}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-6 py-3 border-t border-gray-200 bg-white flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-sm text-gray-500 font-medium">
            Showing <span className="font-bold text-gray-700">{filteredRecords.length === 0 ? 0 : (currentPage - 1) * pageSize + 1}</span> to <span className="font-bold text-gray-700">{Math.min(currentPage * pageSize, filteredRecords.length)}</span> of <span className="font-bold text-gray-700">{filteredRecords.length}</span> results
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">Rows per page:</span>
              <select 
                value={pageSize}
                onChange={(e) => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}
                className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
            
            <div className="flex items-center gap-1">
              <button 
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-1 rounded text-gray-500 hover:bg-gray-100 disabled:opacity-50 disabled:hover:bg-transparent"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="text-sm font-medium text-gray-700 mx-2">
                Page {currentPage} of {totalPages}
              </span>
              <button 
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-1 rounded text-gray-500 hover:bg-gray-100 disabled:opacity-50 disabled:hover:bg-transparent"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
