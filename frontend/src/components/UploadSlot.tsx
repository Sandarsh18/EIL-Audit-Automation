import React, { useState } from 'react';
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle, Loader2, X } from 'lucide-react';
import { excelService } from '../services/api';
import type { WorkbookMetadata } from '../types';

interface UploadSlotProps {
  title: string;
  type: string;
  sessionId: string;
  onUploadSuccess: (metadata: WorkbookMetadata) => void;
  onRemove: () => void;
  metadata?: WorkbookMetadata;
}

export const UploadSlot: React.FC<UploadSlotProps> = ({ title, type, sessionId, onUploadSuccess, onRemove, metadata }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx')) {
      setError('Please upload a valid .xlsx file.');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await excelService.uploadWorkbook(sessionId, type, file);
      onUploadSuccess(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An unexpected error occurred during upload.');
    } finally {
      setIsUploading(false);
      if (e.target) {
        e.target.value = '';
      }
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center space-y-4 text-center transition-all hover:shadow-md">
      <h3 className="font-semibold text-lg text-gray-800">{title}</h3>
      
      {!metadata ? (
        <div className="w-full">
          <label className={`
            flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer
            ${error ? 'border-red-300 bg-red-50 hover:bg-red-100' : 'border-blue-300 bg-blue-50 hover:bg-blue-100'}
          `}>
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              {isUploading ? (
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-2" />
              ) : (
                <Upload className={`w-8 h-8 mb-2 ${error ? 'text-red-500' : 'text-blue-500'}`} />
              )}
              <p className="text-sm text-gray-500 font-medium">
                {isUploading ? 'Uploading...' : `Click to upload ${type}`}
              </p>
            </div>
            <input type="file" className="hidden" accept=".xlsx" onChange={handleFileChange} disabled={isUploading} />
          </label>
          
          {error && (
            <div className="mt-3 flex items-center justify-center text-red-600 text-sm">
              <AlertCircle className="w-4 h-4 mr-1" />
              {error}
            </div>
          )}
          <div className="mt-4 text-sm text-gray-500 flex items-center justify-center">
             Status: <span className="ml-1 font-semibold text-gray-700">Not uploaded</span>
          </div>
        </div>
      ) : (
        <div className="w-full p-4 border border-green-200 bg-green-50 rounded-lg relative flex flex-col items-center">
          <button 
            onClick={onRemove}
            className="absolute top-2 right-2 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
            title="Remove File"
          >
            <X className="w-4 h-4" />
          </button>
          
          <div className="flex items-center justify-center space-x-2 text-green-700 mb-2">
            <CheckCircle className="w-6 h-6" />
            <span className="font-semibold">Uploaded</span>
          </div>
          <div className="flex items-center justify-center space-x-2 text-sm text-gray-700 mb-2">
            <FileSpreadsheet className="w-4 h-4 text-gray-500 flex-shrink-0" />
            <span className="truncate max-w-[180px]" title={metadata.filename}>{metadata.filename}</span>
          </div>
          <div className="text-xs text-gray-500 mb-4">
            {metadata.sheets.length} sheets • {(metadata.size / 1024).toFixed(1)} KB
          </div>
          
          {type === 'excel3' && (
            <label className="cursor-pointer bg-white border border-blue-300 text-blue-700 hover:bg-blue-50 px-4 py-1.5 rounded-lg text-xs font-bold transition-colors shadow-sm w-full text-center">
              {isUploading ? (
                <span className="flex items-center justify-center"><Loader2 className="w-3 h-3 animate-spin mr-1"/> Uploading...</span>
              ) : (
                "Replace Master Template"
              )}
              <input type="file" className="hidden" accept=".xlsx" onChange={(e) => {
                if (window.confirm("Replacing the Master Template will invalidate generated output and require re-mapping. Continue?")) {
                  handleFileChange(e);
                } else {
                  e.target.value = '';
                }
              }} disabled={isUploading} />
            </label>
          )}
        </div>
      )}
    </div>
  );
};
