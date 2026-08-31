import React, { useState, useEffect } from 'react';
import { Loader2, AlertTriangle, Save, FolderOpen, Check, Trash2 } from 'lucide-react';
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
  const [isModalOpen, setIsModalOpen] = useState(false); // Open projects modal
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false); // Save project modal
  const [saveProjectName, setSaveProjectName] = useState("");
  const [showReplaceConfirm, setShowReplaceConfirm] = useState(false);
  
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [loadingProjectId, setLoadingProjectId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
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

  useEffect(() => {
    if (isSaveModalOpen) {
      fetchProjects(); // Need this to check for duplicates
      if (!saveProjectName) {
        setSaveProjectName(`EIL Audit - ${frontendState.excel3Meta?.filename || sessionId?.split('-')[0]}`);
      }
    }
  }, [isSaveModalOpen]);

  const executeSave = async () => {
    if (!sessionId || !saveProjectName.trim()) return;
    setIsSaving(true);
    setError(null);
    try {
      const exportRes = await fetch(`/api/sessions/${sessionId}/export`);
      if (!exportRes.ok) throw new Error("Failed to capture session state");
      const exportData = await exportRes.json();
      exportData.frontend_state = frontendState;
      
      const saveRes = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: saveProjectName.trim(),
          session_export: exportData
        })
      });
      
      if (!saveRes.ok) throw new Error("Failed to save project");
      
      setSaveSuccess(true);
      setIsSaveModalOpen(false);
      setShowReplaceConfirm(false);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveClick = () => {
    const trimmed = saveProjectName.trim();
    if (!trimmed) {
      setError("Project name cannot be empty.");
      return;
    }
    const exists = projects.some(p => p.name === trimmed);
    if (exists) {
      setShowReplaceConfirm(true);
    } else {
      executeSave();
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

  const handleDeleteProject = async (projectId: string) => {
    setIsDeleting(true);
    setError(null);
    try {
      const res = await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error("Failed to delete project");
      
      setProjects(projects.filter(p => p.project_id !== projectId));
      setDeleteConfirmId(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div className="flex items-center space-x-3">
        {error && !isModalOpen && !isSaveModalOpen && (
          <div className="flex items-center text-red-600 bg-red-50 px-3 py-1 rounded border border-red-200 text-sm">
            <AlertTriangle className="w-4 h-4 mr-2" />
            {error}
          </div>
        )}
        <button 
          onClick={() => {
            setError(null);
            setIsSaveModalOpen(true);
            setShowReplaceConfirm(false);
          }}
          disabled={!sessionId}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded transition-colors text-sm font-medium shadow-sm disabled:opacity-50 border ${
            saveSuccess 
              ? 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
          }`}
        >
          {saveSuccess ? (
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
            setError(null);
          }}
          className="flex items-center space-x-2 bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1.5 rounded hover:bg-blue-100 transition-colors text-sm font-medium shadow-sm"
        >
          <FolderOpen className="w-4 h-4" />
          <span>Open Project</span>
        </button>
      </div>

      {isSaveModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-800 flex items-center mb-4">
              <Save className="w-5 h-5 mr-2 text-blue-600" /> Save Project
            </h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 rounded border border-red-200 text-sm">
                {error}
              </div>
            )}
            
            {!showReplaceConfirm ? (
              <>
                <div className="mb-4">
                  <label className="block text-sm font-bold text-gray-700 mb-1">Project Name</label>
                  <input
                    type="text"
                    value={saveProjectName}
                    onChange={(e) => setSaveProjectName(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    placeholder="Enter project name..."
                    autoFocus
                  />
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button 
                    onClick={() => setIsSaveModalOpen(false)}
                    className="px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={handleSaveClick}
                    disabled={isSaving || !saveProjectName.trim()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-bold transition-colors shadow-sm disabled:opacity-50 flex items-center"
                  >
                    {isSaving && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                    Save Project
                  </button>
                </div>
              </>
            ) : (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start mb-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-bold text-yellow-800">Project already exists. Replace it?</h3>
                    <p className="text-sm text-yellow-700 mt-1">A project named "{saveProjectName}" already exists. Replacing it will overwrite its saved state completely.</p>
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-4">
                  <button 
                    onClick={() => setShowReplaceConfirm(false)}
                    className="px-4 py-2 text-gray-600 bg-white border border-gray-300 hover:bg-gray-50 rounded font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={executeSave}
                    disabled={isSaving}
                    className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded font-bold transition-colors shadow-sm disabled:opacity-50 flex items-center"
                  >
                    {isSaving && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                    Replace
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full flex flex-col max-h-[80vh]">
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
              {error && (
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
                    <div key={p.project_id} className="border rounded-lg p-4 hover:border-blue-300 transition-colors bg-gray-50 flex flex-col md:flex-row md:items-center justify-between gap-4">
                      {deleteConfirmId === p.project_id ? (
                        <div className="w-full bg-red-50 border border-red-200 rounded p-3">
                          <h3 className="font-bold text-red-800 mb-1 flex items-center">
                            <AlertTriangle className="w-4 h-4 mr-1" /> Delete Project?
                          </h3>
                          <p className="text-xs text-red-700 mb-3">This will permanently delete the saved project, including its uploaded Excel files, saved workflow state, and generated output.</p>
                          <div className="flex justify-end space-x-2">
                            <button 
                              onClick={() => setDeleteConfirmId(null)}
                              className="px-3 py-1 bg-white border border-gray-300 rounded text-xs font-bold text-gray-700"
                            >
                              Cancel
                            </button>
                            <button 
                              onClick={() => handleDeleteProject(p.project_id)}
                              disabled={isDeleting}
                              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs font-bold flex items-center disabled:opacity-50"
                            >
                              {isDeleting && <Loader2 className="w-3 h-3 animate-spin mr-1" />}
                              Delete Project
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div>
                            <h3 className="font-bold text-gray-800">{p.name}</h3>
                            <div className="text-xs text-gray-500 mt-1 space-y-1">
                              <p>Last Modified: {new Date(p.last_modified).toLocaleString()}</p>
                              {p.evaluation_month && <p>Eval Month: {p.evaluation_month}</p>}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2 shrink-0">
                            <button
                              onClick={() => setDeleteConfirmId(p.project_id)}
                              disabled={loadingProjectId !== null}
                              className="flex items-center text-red-500 hover:text-red-700 hover:bg-red-50 px-3 py-2 rounded text-sm font-semibold transition-colors disabled:opacity-50"
                            >
                              <Trash2 className="w-4 h-4 mr-1" />
                              Delete
                            </button>
                            <button
                              onClick={() => handleOpenProject(p.project_id)}
                              disabled={loadingProjectId !== null}
                              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded font-semibold text-sm shadow flex items-center transition-colors"
                            >
                              {loadingProjectId === p.project_id ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <FolderOpen className="w-4 h-4 mr-2" />}
                              Open
                            </button>
                          </div>
                        </>
                      )}
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

