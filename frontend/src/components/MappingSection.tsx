import React, { useState, useEffect } from 'react';
import type { WorkbookMetadata, SheetMetadata, MappingConfiguration, ValidationResult } from '../types';
import { excelService, sessionService } from '../services/api';
import { CheckCircle, AlertTriangle, Info } from 'lucide-react';

interface MappingSectionProps {
  sessionId: string;
  excel1Meta: WorkbookMetadata;
  excel2Meta: WorkbookMetadata;
  excel3Meta: WorkbookMetadata;
  onSuccess: (result: ValidationResult) => void;
}

export const MappingSection: React.FC<MappingSectionProps> = ({ 
  sessionId, 
  excel1Meta, 
  excel2Meta, 
  excel3Meta,
  onSuccess 
}) => {
  // Sheets selection
  const getDefaultSheet3 = () => {
    if (excel3Meta.sheet_summaries) {
      const candidates = excel3Meta.sheet_summaries.filter(s => s.is_candidate);
      const mar26 = candidates.find(s => s.name === "ConsolidatedMHrequirementMar26");
      if (mar26) return mar26.name;
      if (candidates.length > 0) return candidates[candidates.length - 1].name;
    }
    return excel3Meta.sheets[0];
  };

  const [sheet1, setSheet1] = useState(excel1Meta.sheets[0]);
  const [sheet2, setSheet2] = useState(excel2Meta.sheets[0]);
  const [sheet3, setSheet3] = useState(getDefaultSheet3());
  
  const [pendingSheet3, setPendingSheet3] = useState<string | null>(null);
  const [showSheetChangeWarning, setShowSheetChangeWarning] = useState(false);

  // Loaded sheet data (for columns and preview)
  const [data1, setData1] = useState<SheetMetadata | null>(null);
  const [data2, setData2] = useState<SheetMetadata | null>(null);
  const [data3, setData3] = useState<SheetMetadata | null>(null);

  // Mappings
  const [mapping1, setMapping1] = useState<Record<string, string>>({});
  const [mapping2, setMapping2] = useState<Record<string, string>>({});
  const [mapping3, setMapping3] = useState<Record<string, string>>({});

  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);

  const autoMapFromCanonical = (
    data: SheetMetadata | null,
    currentMapping: Record<string, string>,
    setMapping: (m: Record<string, string>) => void,
    fieldMap: Record<string, string> // maps canonical name from backend to logicalField in frontend
  ) => {
    if (!data) return;
    const newMapping = { ...currentMapping };
    let changed = false;
    
    for (const [canonicalName, logicalField] of Object.entries(fieldMap)) {
      if (!newMapping[logicalField]) {
        const match = data.columns.find(c => c.canonical === canonicalName);
        if (match) {
          newMapping[logicalField] = match.name;
          changed = true;
        }
      }
    }
    
    if (changed) setMapping(newMapping);
  };

  useEffect(() => {
    excelService.getSheet(sessionId, 'excel1', sheet1).then(d => {
      setData1(d);
      autoMapFromCanonical(d, mapping1, setMapping1, {
        'JOB_NUMBER': 'job_number',
        'BALANCE_QUANTITY': 'balance_quantity',
        'OCS_DATE': 'ocs_date'
      });
    }).catch(console.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sheet1, sessionId]);

  useEffect(() => {
    excelService.getSheet(sessionId, 'excel2', sheet2).then(d => {
      setData2(d);
      autoMapFromCanonical(d, mapping2, setMapping2, {
        'JOB_NUMBER': 'job_number',
        'INSPECTION_FROM': 'inspection_from',
        'INSPECTION_UPTO': 'inspection_upto',
        'DATE_RECEIVED': 'date_received',
        'QAP_APPL': 'qap_appl',
        'NO_OF_WORKING_DAYS': 'no_of_working_days'
      });
    }).catch(console.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sheet2, sessionId]);

  // Watch for Excel 3 workbook change to reset mapping and sheet selection
  useEffect(() => {
    // When excel3Meta changes, it means a new workbook was uploaded or state was reset
    const defaultSheet = getDefaultSheet3();
    setSheet3(defaultSheet);
    setMapping3({});
    setPendingSheet3(null);
    setShowSheetChangeWarning(false);
  }, [excel3Meta.filename, excel3Meta.sheets]);

  useEffect(() => {
    excelService.getSheet(sessionId, 'excel3', sheet3).then(d => {
      setData3(d);
      autoMapFromCanonical(d, mapping3, setMapping3, {
        'JOB_NUMBER': 'job_number',
        'RUNNING_ORDERS': 'running_orders',
        'ORDERS_FOR_FD_FOLLOWUP': 'orders_for_fd',
        'OCS_DONE': 'ocs_done',
        'EXPEDITING': 'expediting',
        'INSPECTION_SOURCE': 'inspection',
        'OTHERS': 'others',
        'TOTAL': 'total'
      });
    }).catch(console.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sheet3, sessionId, excel3Meta.filename]);

  const handleValidate = async () => {
    setError(null);
    setValidationResult(null);
    
    // Basic frontend check for missing fields
    const req1 = ['job_number', 'balance_quantity', 'ocs_date'];
    const req2 = ['job_number', 'inspection_from', 'inspection_upto', 'date_received'];
    const req3 = ['job_number', 'running_orders', 'expediting', 'inspection', 'others', 'total'];
    
    if (req1.some(k => !mapping1[k]) || req2.some(k => !mapping2[k]) || req3.some(k => !mapping3[k])) {
      setError("All fields must be mapped before validating.");
      return;
    }

    const config: MappingConfiguration = {
      excel1: { sheet: sheet1, columns: mapping1 as any },
      excel2: { sheet: sheet2, columns: mapping2 as any },
      excel3: { sheet: sheet3, columns: mapping3 as any }
    };

    setIsValidating(true);
    try {
      const result = await sessionService.validateAndSaveMapping(sessionId, config);
      setValidationResult(result);
      if (result.valid) {
        onSuccess(result);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Validation failed.");
    } finally {
      setIsValidating(false);
    }
  };

  const getPreview = (data: SheetMetadata | null, colName: string) => {
    if (!data || !colName) return null;
    const values = data.preview.slice(0, 3).map(r => r[colName]).filter(v => v !== null && v !== undefined);
    if (values.length === 0) return "No preview values";
    return values.join(", ") + (data.preview.length > 3 ? "..." : "");
  };

  const handleSheet3Change = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSheet = e.target.value;
    if (Object.values(mapping3).some(v => v !== '')) {
      setPendingSheet3(newSheet);
      setShowSheetChangeWarning(true);
    } else {
      setSheet3(newSheet);
    }
  };

  const confirmSheet3Change = () => {
    if (pendingSheet3) {
      setMapping3({}); // Reset mappings that might be incompatible
      setSheet3(pendingSheet3);
    }
    setShowSheetChangeWarning(false);
    setPendingSheet3(null);
  };

  const cancelSheet3Change = () => {
    setShowSheetChangeWarning(false);
    setPendingSheet3(null);
  };

  const renderFieldMapping = (
    label: string, 
    logicalField: string, 
    data: SheetMetadata | null, 
    mapping: Record<string, string>, 
    setMapping: (m: Record<string, string>) => void,
    optional: boolean = false,
    expectedCanonical?: string
  ) => {
    // If an expectedCanonical is given, check if any column actually has it.
    // If not, and it's optional, return the Not Available UI.
    const isAvailable = !expectedCanonical || (data?.columns.some(c => c.canonical === expectedCanonical) ?? false);
    
    if (optional && !isAvailable) {
      return (
        <div className="flex flex-col mb-4 bg-gray-50 p-3 rounded-lg border border-gray-200 opacity-70">
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-2">
            <label className="font-semibold text-gray-500 w-1/3 line-through">{label}</label>
            <div className="w-full md:w-2/3 mt-2 md:mt-0 p-2 text-sm text-gray-500 italic bg-gray-100 rounded border border-gray-200">
              NOT AVAILABLE IN SELECTED SHEET
            </div>
          </div>
        </div>
      );
    }
    
    const selectedCol = mapping[logicalField] || '';
    const warnings = validationResult?.warnings?.filter(w => w.logical_field === logicalField) || [];

    return (
      <div className="flex flex-col mb-4 bg-gray-50 p-3 rounded-lg border border-gray-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-2">
          <label className="font-semibold text-gray-700 w-1/3">{label}</label>
          <select 
            name={logicalField}
            value={selectedCol} 
            onChange={e => setMapping({ ...mapping, [logicalField]: e.target.value })}
            className="w-full md:w-2/3 mt-2 md:mt-0 p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">-- Select Source Column --</option>
            {data?.columns.map(c => (
              <option key={c.name} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>
        
        {selectedCol && (
          <div className="flex items-center text-xs text-gray-500 bg-white p-2 rounded border border-gray-100">
            <Info className="w-3 h-3 mr-1 text-blue-500" />
            <span className="font-medium mr-2">Preview:</span> 
            <span className="truncate italic">{getPreview(data, selectedCol)}</span>
          </div>
        )}

        {warnings.length > 0 && (
          <div className="mt-2 text-xs text-amber-700 bg-amber-50 p-2 rounded border border-amber-200 flex items-start">
            <AlertTriangle className="w-4 h-4 mr-1 shrink-0 mt-0.5" />
            <div>
              {warnings.map((w, i) => <div key={i}>{w.message}</div>)}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <h2 className="text-xl font-bold text-gray-800 mb-6 uppercase tracking-wider flex items-center">
        <span className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center mr-3 shadow-md">3</span> 
        Configure Column Mapping
      </h2>

      {/* Excel 1 */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-gray-800 border-b pb-2 mb-4">EXCEL 1 — {excel1Meta.filename}</h3>
        <div className="flex items-center space-x-4 mb-6 bg-gray-50 p-3 rounded">
          <label className="font-semibold text-gray-700">Sheet:</label>
          <select value={sheet1} onChange={e => setSheet1(e.target.value)} className="p-2 border rounded">
            {excel1Meta.sheets.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="space-y-2">
          {renderFieldMapping("Job Number", "job_number", data1, mapping1, setMapping1)}
          {renderFieldMapping("Balance Quantity", "balance_quantity", data1, mapping1, setMapping1)}
          {renderFieldMapping("OCS Date", "ocs_date", data1, mapping1, setMapping1)}
        </div>
      </div>

      {/* Excel 2 */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-gray-800 border-b pb-2 mb-4">EXCEL 2 — {excel2Meta.filename}</h3>
        <div className="flex items-center space-x-4 mb-6 bg-gray-50 p-3 rounded">
          <label className="font-semibold text-gray-700">Sheet:</label>
          <select value={sheet2} onChange={e => setSheet2(e.target.value)} className="p-2 border rounded">
            {excel2Meta.sheets.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="space-y-2">
          {renderFieldMapping("Job Number", "job_number", data2, mapping2, setMapping2)}
          {renderFieldMapping("Inspection Attended From", "inspection_from", data2, mapping2, setMapping2)}
          {renderFieldMapping("Inspection Attended Upto", "inspection_upto", data2, mapping2, setMapping2)}
          {renderFieldMapping("Date Received", "date_received", data2, mapping2, setMapping2)}
          {renderFieldMapping("QAP Appl.", "qap_appl", data2, mapping2, setMapping2, true)}
          {renderFieldMapping("No. of Working Days", "no_of_working_days", data2, mapping2, setMapping2, true)}
        </div>
      </div>

      {/* Excel 3 */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-gray-800 border-b pb-2 mb-4">EXCEL 3 — {excel3Meta.filename}</h3>
        <div className="flex flex-col space-y-4 mb-6 bg-gray-50 p-4 rounded border border-gray-200">
          <div className="flex items-center space-x-4">
            <label className="font-semibold text-gray-700">Source Sheet for Evaluation:</label>
            <select value={sheet3} onChange={handleSheet3Change} className="p-2 border rounded w-full max-w-md focus:ring-blue-500 focus:border-blue-500 bg-white">
              {excel3Meta.sheet_summaries ? (
                excel3Meta.sheet_summaries.map(s => (
                  <option key={s.name} value={s.name}>
                    {s.name} {!s.is_candidate ? '(Not a candidate source sheet)' : ''}
                  </option>
                ))
              ) : (
                excel3Meta.sheets.map(s => <option key={s} value={s}>{s}</option>)
              )}
            </select>
          </div>
          
          {excel3Meta.sheet_summaries && excel3Meta.sheet_summaries.find(s => s.name === sheet3) && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mt-4 bg-white p-4 rounded shadow-sm border border-gray-100">
              {(() => {
                const s = excel3Meta.sheet_summaries.find(x => x.name === sheet3)!;
                return (
                  <>
                    <div>
                      <span className="text-gray-500 block text-xs uppercase tracking-wider">Rows</span>
                      <span className="font-semibold text-gray-800">{s.row_count}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-xs uppercase tracking-wider">Detected Fields</span>
                      <span className="font-semibold text-gray-800">{data3?.columns.length || 0}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-xs uppercase tracking-wider">Schema</span>
                      <span className="font-semibold text-gray-800 capitalize">{s.schema_type}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-xs uppercase tracking-wider">Job Column</span>
                      <span className="font-semibold text-gray-800">{data3?.columns.find(c => c.canonical === 'JOB_NUMBER')?.name || 'Unknown'}</span>
                    </div>
                  </>
                );
              })()}
            </div>
          )}
        </div>
        <div className="space-y-2">
          {renderFieldMapping("Job Number", "job_number", data3, mapping3, setMapping3, false, 'JOB_NUMBER')}
          {renderFieldMapping("Running Orders", "running_orders", data3, mapping3, setMapping3, false, 'RUNNING_ORDERS')}
          {renderFieldMapping("Orders for FD f/", "orders_for_fd", data3, mapping3, setMapping3, false, 'ORDERS_FOR_FD_FOLLOWUP')}
          {renderFieldMapping("OCS Done", "ocs_done", data3, mapping3, setMapping3, false, 'OCS_DONE')}
          {renderFieldMapping("Expediting", "expediting", data3, mapping3, setMapping3, false, 'EXPEDITING')}
          {renderFieldMapping("Inspn", "inspection", data3, mapping3, setMapping3, false, 'INSPECTION_SOURCE')}
          {renderFieldMapping("Others", "others", data3, mapping3, setMapping3, false, 'OTHERS')}
          {renderFieldMapping("Total", "total", data3, mapping3, setMapping3, false, 'TOTAL')}
        </div>
      </div>

      {error && (
        <div className="mb-4 text-red-600 bg-red-50 p-4 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {validationResult?.valid && (
        <div className="mb-4 text-green-700 bg-green-50 p-4 rounded-lg border border-green-200 flex items-center">
          <CheckCircle className="w-5 h-5 mr-2" />
          Mapping validation successful! Configurations stored.
        </div>
      )}

      <div className="flex justify-end">
        <button 
          onClick={handleValidate}
          disabled={isValidating}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg shadow-md transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isValidating ? 'Validating...' : 'Validate and Proceed'}
        </button>
      </div>

      {/* Sheet Change Warning Modal */}
      {showSheetChangeWarning && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-start mb-4">
              <div className="bg-amber-100 p-2 rounded-full mr-3 text-amber-600">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Change Source Sheet?</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Changing the source sheet will reload its columns and reset mappings that are not available in the new sheet.
                </p>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button 
                onClick={cancelSheet3Change}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={confirmSheet3Change}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Change Sheet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
