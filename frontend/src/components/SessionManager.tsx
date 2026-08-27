import React, { useState } from 'react';
import { Loader2, AlertTriangle, Save, FolderOpen, Check } from 'lucide-react';
import type { Session, WorkbookMetadata } from '../types';

interface FrontendState {
  currentStep: number;
  selectedJobNumbers: string[] | null;
  isMappingValid: boolean;
  excel1Meta?: WorkbookMetadata;
  excel2Meta?: WorkbookMetadata;
  excel3Meta?: WorkbookMetadata;
  customColumns?: import('../types').CustomColumnData[];
}

interface ProjectSummary {
  project_id: string;
  name: string;
  last_modified: string;
  evaluation_month?: string;
  excel1_filename?: string;
  excel2_filename?: string;
  excel3_filename?: string;
}

interface SessionManagerProps {
  sessionId: string | undefined;
  frontendState: FrontendState;
  onRestore: (session: Session, frontendState: FrontendState) => void;
}

export const SessionManager: React.FC<SessionManagerProps> = ({ sessionId, frontendState, onRestore }) => {
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [loadingProjectId, setLoadingProjectId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = async () => {
    setIsLoadingProjects(true);
    try {
      const response = await fetch('/api/projects');
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingProjects(false);
    }
  };

  const handleSave = async () => {
    if (!sessionId) return;
    setIsSaving(true);
    setError(null);
    try {
      // 1. Get current session export state
      const exportRes = await fetch(`/api/sessions/${sessionId}/export`);
      if (!exportRes.ok) throw new Error("Failed to capture session state");
      const exportData = await exportRes.json();
      exportData.frontend_state = frontendState;
      
      const projectName = `EIL Audit - ${frontendState.excel3Meta?.filename || sessionId.split('-')[0]}`;
      
      // 2. Save to backend
      const saveRes = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: projectName,
          session_export: exportData
        })
      });
      
      if (!saveRes.ok) throw new Error("Failed to save project");
      
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleOpenProject = async (projectId: string) => {
    setLoadingProjectId(projectId);
    setError(null);
    try {
      const res = await fetch(`/api/projects/${projectId}`);
      if (!res.ok) throw new Error("Failed to load project");
      
      const exportData = await res.json();
      
      const restoreRes = await fetch(`/api/sessions/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportData)
      });
      
      if (!restoreRes.ok) throw new Error("Failed to restore session on backend");
      
      const session = await restoreRes.json();
      onRestore(session, exportData.frontend_state || { currentStep: 1, selectedJobNumbers: null, isMappingValid: false });
      setIsModalOpen(false);
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoadingProjectId(null);
    }
  };

  return (
    <>
      <div className="flex items-center space-x-3">
        {error && !isModalOpen && (
          <div className="flex items-center text-red-600 bg-red-50 px-3 py-1 rounded border border-red-200 text-sm">
            <AlertTriangle className="w-4 h-4 mr-2" />
            {error}
          </div>
        )}
        <button 
          onClick={handleSave}
          disabled={isSaving || !sessionId}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded transition-colors text-sm font-medium shadow-sm disabled:opacity-50 border ${
            saveSuccess 
              ? 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
          }`}
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : saveSuccess ? (
            <Check className="w-4 h-4" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          <span>{saveSuccess ? 'Saved!' : 'Save Project'}</span>
        </button>
        
        <button 
          onClick={() => {
            fetchProjects();
            setIsModalOpen(true);
          }}
          className="flex items-center space-x-2 bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1.5 rounded hover:bg-blue-100 transition-colors text-sm font-medium shadow-sm"
        >
          <FolderOpen className="w-4 h-4" />
          <span>Open Project</span>
        </button>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full flex flex-col max-h-[80vh]">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-800 flex items-center">
                <FolderOpen className="w-6 h-6 mr-2 text-blue-600" /> Previous Projects
              </h2>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 font-bold"
              >
                ✕
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1">
              {error && isModalOpen && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 rounded border border-red-200 text-sm">
                  {error}
                </div>
              )}
              
              {isLoadingProjects ? (
                <div className="flex justify-center p-8">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                </div>
              ) : projects.length === 0 ? (
                <div className="text-center p-8 text-gray-500">
                  No previous projects found.
                </div>
              ) : (
                <div className="space-y-3">
                  {projects.map(p => (
                    <div key={p.project_id} className="border rounded-lg p-4 hover:border-blue-300 transition-colors bg-gray-50 flex justify-between items-center">
                      <div>
                        <h3 className="font-bold text-gray-800">{p.name}</h3>
                        <div className="text-xs text-gray-500 mt-1 space-y-1">
                          <p>Last Modified: {new Date(p.last_modified).toLocaleString()}</p>
                          {p.evaluation_month && <p>Eval Month: {p.evaluation_month}</p>}
                        </div>
                      </div>
                      <button
                        onClick={() => handleOpenProject(p.project_id)}
                        disabled={loadingProjectId !== null}
                        className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded font-semibold text-sm shadow flex items-center"
                      >
                        {loadingProjectId === p.project_id ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <FolderOpen className="w-4 h-4 mr-2" />}
                        Open
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
