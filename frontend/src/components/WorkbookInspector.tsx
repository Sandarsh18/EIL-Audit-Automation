import React, { useState, useEffect } from 'react';
import type { WorkbookMetadata, SheetMetadata } from '../types';
import { excelService } from '../services/api';
import { DataPreviewTable } from './DataPreviewTable';
import { Loader2, AlertCircle } from 'lucide-react';

interface WorkbookInspectorProps {
  workbook: WorkbookMetadata;
  sessionId: string;
  onClose: () => void;
}

export const WorkbookInspector: React.FC<WorkbookInspectorProps> = ({ workbook, sessionId, onClose }) => {
  const [activeSheet, setActiveSheet] = useState<string>(workbook.sheets[0]);
  const [sheetData, setSheetData] = useState<SheetMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (!activeSheet) return;
    
    const fetchSheet = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await excelService.getSheet(sessionId, workbook.workbook_type, activeSheet);
        setSheetData(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load sheet data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSheet();
  }, [activeSheet, workbook.workbook_type, sessionId]);

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b pb-4 mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-800">
            Workbook: <span className="font-semibold text-blue-600">{workbook.filename}</span>
          </h3>
          <p className="text-sm text-gray-500 mt-1 uppercase tracking-wider font-semibold">
            Type: {workbook.workbook_type}
          </p>
        </div>
        <button
          onClick={onClose}
          aria-label="Close inspection"
          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
        >
          <div className="w-6 h-6 flex items-center justify-center font-bold text-lg leading-none">X</div>
        </button>
      </div>

      <div className="mb-2 text-sm font-semibold text-gray-700">Sheets</div>
      <div className="flex flex-wrap gap-2 mb-6">
        {workbook.sheets.map(sheet => (
          <button
            key={sheet}
            onClick={() => setActiveSheet(sheet)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors border ${
              activeSheet === sheet 
                ? 'bg-blue-600 text-white border-blue-600 shadow-sm' 
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {sheet}
          </button>
        ))}
      </div>

      <div className="min-h-[300px]">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full text-blue-500 pt-10">
            <Loader2 className="w-10 h-10 animate-spin mb-4" />
            <p className="text-gray-500 font-medium">Inspecting worksheet...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center pt-10 text-red-500">
            <AlertCircle className="w-10 h-10 mb-2" />
            <p>{error}</p>
          </div>
        ) : sheetData ? (
          <DataPreviewTable sheet={sheetData} />
        ) : (
          <div className="text-center text-gray-500 pt-10">Select a sheet to view its contents</div>
        )}
      </div>
    </div>
  );
};
