import React from 'react';
import type { SheetMetadata } from '../types';

interface DataPreviewTableProps {
  sheet: SheetMetadata;
}

export const DataPreviewTable: React.FC<DataPreviewTableProps> = ({ sheet }) => {
  return (
    <div className="mt-6">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-lg font-semibold text-gray-800">Sheet: {sheet.sheet_name}</h4>
        <div className="text-sm text-gray-600 font-medium">
          <span className="mr-4">Rows: {sheet.row_count}</span>
          <span>Columns: {sheet.column_count}</span>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-700 uppercase bg-gray-100 border-b">
            <tr>
              {sheet.columns.map((col) => (
                <th key={col.index} className="px-4 py-3 min-w-[150px]">
                  <div className="flex flex-col space-y-1">
                    <span className="font-semibold truncate" title={col.name}>{col.name}</span>
                    <span className="text-[10px] text-blue-600 font-medium bg-blue-50 px-2 py-0.5 rounded w-fit">
                      {col.data_type}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sheet.preview.map((row, rowIndex) => (
              <tr key={rowIndex} className="bg-white border-b hover:bg-gray-50 transition-colors">
                {sheet.columns.map((col) => (
                  <td key={`${rowIndex}-${col.index}`} className="px-4 py-2">
                    <div className="max-w-[200px] truncate text-gray-600" title={String(row[col.name] ?? '')}>
                      {row[col.name] !== null && row[col.name] !== undefined ? String(row[col.name]) : <span className="text-gray-300 italic">null</span>}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
            {sheet.preview.length === 0 && (
              <tr>
                <td colSpan={sheet.columns.length} className="px-4 py-8 text-center text-gray-500">
                  No preview data available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
