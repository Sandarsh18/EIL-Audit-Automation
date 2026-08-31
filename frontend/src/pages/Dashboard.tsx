import React, { useState, useEffect } from 'react';
import type { Session, WorkbookMetadata } from '../types';
import { sessionService, excelService } from '../services/api';
import { UploadSlot } from '../components/UploadSlot';
import { WorkbookInspector } from '../components/WorkbookInspector';
import { MappingSection } from '../components/MappingSection';
import { JobNumberSelector } from '../components/JobNumberSelector';
import { Excel1AnalysisView } from '../components/Excel1AnalysisView';
import { Excel2AnalysisView } from '../components/Excel2AnalysisView';
import { CombinedCalculationView } from '../components/CombinedCalculationView';
import { ReviewDashboard } from '../components/ReviewDashboard';
import { OutputDashboard } from '../components/OutputDashboard';
import { SessionManager } from '../components/SessionManager';
import { ShieldCheck, Loader2, CheckCircle, Lock, Play } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [session, setSession] = useState<Session | null>(null);
  
  // App State
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [excel1Meta, setExcel1Meta] = useState<WorkbookMetadata | undefined>();
  const [excel2Meta, setExcel2Meta] = useState<WorkbookMetadata | undefined>();
  const [excel3Meta, setExcel3Meta] = useState<WorkbookMetadata | undefined>();
  const [customColumns, setCustomColumns] = useState<import('../types').CustomColumnData[]>([]);
  const [isMappingValid, setIsMappingValid] = useState(false);
  const [selectedJobNumbers, setSelectedJobNumbers] = useState<string[] | null>(null);
  const [activeInspector, setActiveInspector] = useState<WorkbookMetadata | null>(null);
  const [evaluationMonth, setEvaluationMonth] = useState<string>('2026-08');

  const [isInitializing, setIsInitializing] = useState(true);

  // Computed state
  const step1Complete = !!(excel1Meta && excel2Meta && excel3Meta);
  const step2Complete = isMappingValid;
  const step3Complete = !!(selectedJobNumbers && selectedJobNumbers.length > 0);
  
  // We'll manage navigation explicitly
  const canGoToStep = (step: number) => {
    if (step === 1) return true;
    if (step === 2) return step1Complete;
    if (step === 3) return step1Complete && step2Complete;
    if (step === 4) return step1Complete && step2Complete && step3Complete;
    if (step === 5) return step1Complete && step2Complete && step3Complete; // Assume they can go to Review after Analyze
    if (step === 6) return step1Complete && step2Complete && step3Complete; // Approve is part of Review practically, but we separate the view
    if (step === 7) return step1Complete && step2Complete && step3Complete;
    if (step === 8) return step1Complete && step2Complete && step3Complete; // Actually depends on generation output
    return false;
  };

  useEffect(() => {
    const initSession = async () => {
      try {
        const newSession = await sessionService.createSession();
        setSession(newSession);
      } catch (err) {
        console.error("Failed to initialize session", err);
      } finally {
        setIsInitializing(false);
      }
    };
    initSession();
  }, []);

  const handleRestoreSession = (restoredSession: Session, frontendState: any) => {
    setSession(restoredSession);
    setCurrentStep(frontendState.currentStep || 1);
    setSelectedJobNumbers(frontendState.selectedJobNumbers || null);
    setIsMappingValid(frontendState.isMappingValid || false);
    setExcel1Meta(frontendState.excel1Meta);
    setExcel2Meta(frontendState.excel2Meta);
    setExcel3Meta(frontendState.excel3Meta);
    setCustomColumns(frontendState.customColumns || []);
  };

  const removeFile = async (type: string) => {
    try {
      if (!session) return;
      await excelService.removeWorkbook(session.session_id, type);
      if (type === 'excel1') setExcel1Meta(undefined);
      if (type === 'excel2') setExcel2Meta(undefined);
      if (type === 'excel3') setExcel3Meta(undefined);
      setIsMappingValid(false);
      setSelectedJobNumbers(null);
    } catch (e) {
      console.error("Failed to remove workbook", e);
    }
  };

  const removeAllFiles = async () => {
    if (confirm("Are you sure you want to remove all files and reset the session mapping?")) {
      try {
        if (!session) return;
        await excelService.removeAllWorkbooks(session.session_id);
        setExcel1Meta(undefined);
        setExcel2Meta(undefined);
        setExcel3Meta(undefined);
        setIsMappingValid(false);
        setSelectedJobNumbers(null);
        setCurrentStep(1);
      } catch (e) {
        console.error("Failed to remove all workbooks", e);
      }
    }
  };

  const currentFrontendState = {
    currentStep,
    selectedJobNumbers,
    isMappingValid,
    excel1Meta,
    excel2Meta,
    excel3Meta,
    customColumns
  };

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 text-red-600 p-6">
        <h2 className="text-2xl font-bold mb-2">Service Unavailable</h2>
        <p>Could not connect to backend server. Please verify it is running.</p>
      </div>
    );
  }

  const renderStepper = () => {
    const steps = [
      { id: 1, label: "Upload" },
      { id: 2, label: "Map" },
      { id: 3, label: "Jobs" },
      { id: 4, label: "Analyze" },
      { id: 5, label: "Review & Approve" },
      { id: 6, label: "Output" }
    ];
    
    return (
      <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-200 mb-8 overflow-x-auto">
        {steps.map((step, idx) => {
          const isComplete = (step.id < currentStep) || 
                             (step.id === 1 && step1Complete) || 
                             (step.id === 2 && step2Complete) || 
                             (step.id === 3 && step3Complete);
          const isActive = currentStep === step.id;
          const isLocked = !canGoToStep(step.id);
          
          return (
            <div key={step.id} className="flex items-center min-w-max px-2">
              <button 
                onClick={() => setCurrentStep(step.id)}
                disabled={isLocked}
                className={`flex flex-col items-center ${isLocked ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 transition-colors ${
                  isActive ? 'bg-blue-600 text-white shadow-md' : 
                  isComplete ? 'bg-green-500 text-white' : 
                  'bg-gray-200 text-gray-500'
                }`}>
                  {isLocked ? <Lock className="w-4 h-4" /> : 
                   isComplete && !isActive ? <CheckCircle className="w-4 h-4" /> : 
                   <span className="font-bold text-sm">{step.id}</span>}
                </div>
                <span className={`text-xs font-semibold ${isActive ? 'text-blue-700' : 'text-gray-500'}`}>{step.label}</span>
              </button>
              {idx < steps.length - 1 && (
                <div className={`h-1 w-12 md:w-20 mx-2 rounded ${isComplete ? 'bg-green-500' : 'bg-gray-200'}`} />
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8 text-center md:text-left flex flex-col md:flex-row items-center justify-between border-b border-gray-200 pb-6">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center">
              EIL AUDIT AUTOMATION
            </h1>
            <p className="text-gray-500 mt-2 font-medium">End-to-End Excel Processing</p>
          </div>
          <div className="mt-4 md:mt-0 flex flex-col md:flex-row items-center gap-4">
            <div className="flex items-center space-x-2 text-sm text-gray-500 bg-white px-4 py-2 rounded-full border shadow-sm">
              <ShieldCheck className="w-5 h-5 text-green-500" />
              <span>Session: <span className="font-mono text-gray-700">{session.session_id.split('-')[0]}</span></span>
            </div>
            <SessionManager 
              sessionId={session.session_id} 
              frontendState={currentFrontendState} 
              onRestore={handleRestoreSession} 
            />
          </div>
        </header>

        {renderStepper()}

        {/* STEP 1: UPLOAD */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <h2 className="text-xl font-bold text-gray-800 uppercase flex items-center">
                <Play className="w-5 h-5 mr-2 text-blue-600" /> Step 1: Upload Source Workbooks
              </h2>
              {(excel1Meta || excel2Meta || excel3Meta) && (
                <button 
                  onClick={removeAllFiles}
                  className="px-4 py-2 text-sm font-bold text-red-600 bg-red-50 hover:bg-red-100 rounded-lg border border-red-200 transition-colors shadow-sm"
                >
                  Remove All Files
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <UploadSlot 
                title="[ Excel 1 ] CONSOLIDATED REPORT" 
                type="excel1" 
                sessionId={session.session_id}
                metadata={excel1Meta}
                onUploadSuccess={(meta) => { setExcel1Meta(meta); setIsMappingValid(false); }}
                onRemove={() => removeFile('excel1')}
              />
              <UploadSlot 
                title="[ Excel 2 ] INSPECTION CALL LOG" 
                type="excel2" 
                sessionId={session.session_id}
                metadata={excel2Meta}
                onUploadSuccess={(meta) => { setExcel2Meta(meta); setIsMappingValid(false); }}
                onRemove={() => removeFile('excel2')}
              />
              <UploadSlot 
                title="[ Excel 3 ] MASTER TEMPLATE" 
                type="excel3" 
                sessionId={session.session_id}
                metadata={excel3Meta}
                onUploadSuccess={(meta) => { setExcel3Meta(meta); setIsMappingValid(false); }}
                onRemove={() => removeFile('excel3')}
              />
            </div>
            {step1Complete && (
              <div className="flex justify-end mt-4">
                <button onClick={() => setCurrentStep(2)} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-bold shadow-md">
                  Proceed to Mapping →
                </button>
              </div>
            )}
          </div>
        )}

        {/* STEP 2: INSPECT & MAP */}
        {currentStep === 2 && step1Complete && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-gray-800 uppercase flex items-center">
              <Play className="w-5 h-5 mr-2 text-blue-600" /> Step 2: Inspect & Map Columns
            </h2>
            <div className="flex flex-wrap gap-4 mb-4">
              {[excel1Meta, excel2Meta, excel3Meta].map((meta, i) => meta && (
                <button 
                  key={meta.filename}
                  onClick={() => setActiveInspector(meta)}
                  className={`px-4 py-2 rounded-lg font-semibold border ${activeInspector === meta ? 'bg-blue-100 border-blue-300 text-blue-800' : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'}`}
                >
                  Inspect Excel {i+1}
                </button>
              ))}
            </div>
            {activeInspector && (
              <div className="mb-8">
                <WorkbookInspector 
                  key={activeInspector.filename} 
                  workbook={activeInspector} 
                  sessionId={session.session_id} 
                  onClose={() => setActiveInspector(null)}
                />
              </div>
            )}
            
            <MappingSection 
              key={`${excel1Meta.file_id}-${excel2Meta.file_id}-${excel3Meta.file_id}`}
              sessionId={session.session_id}
              excel1Meta={excel1Meta!}
              excel2Meta={excel2Meta!}
              excel3Meta={excel3Meta!}
              onSuccess={(result) => {
                if (result.valid) {
                  setIsMappingValid(true);
                  setCurrentStep(3);
                }
              }}
            />
          </div>
        )}

        {/* STEP 3: SELECT JOBS */}
        {currentStep === 3 && step2Complete && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-gray-800 uppercase flex items-center">
              <Play className="w-5 h-5 mr-2 text-blue-600" /> Step 3: Select Jobs
            </h2>
            <JobNumberSelector 
              sessionId={session.session_id}
              onSelectionComplete={(jobs) => {
                setSelectedJobNumbers(jobs);
                setCurrentStep(4);
              }}
            />
          </div>
        )}

        {/* STEP 4: ANALYZE */}
        {currentStep === 4 && step3Complete && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-gray-800 uppercase flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center"><Play className="w-5 h-5 mr-2 text-blue-600" /> Step 4: Rule Analysis</div>
              <div className="flex items-center gap-4">
                <div className="flex items-center text-sm text-blue-900 bg-blue-50 px-3 py-1.5 border border-blue-200 rounded shadow-sm">
                  <span className="font-semibold mr-2">Eval Month:</span>
                  <input 
                    type="month" 
                    value={evaluationMonth} 
                    onChange={async (e) => {
                      const newMonth = e.target.value;
                      setEvaluationMonth(newMonth);
                      try {
                        await sessionService.setEvaluationMonth(session.session_id, newMonth);
                      } catch (err) {
                        console.error("Failed to update evaluation month", err);
                      }
                    }}
                    className="bg-transparent outline-none font-mono"
                  />
                </div>
                <button onClick={() => setCurrentStep(5)} className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg font-bold shadow">
                  Proceed to Review →
                </button>
              </div>
            </h2>
            <div className="mt-6">
              <CombinedCalculationView sessionId={session.session_id} selectedKeys={selectedJobNumbers!} evaluationMonth={evaluationMonth} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              <Excel1AnalysisView sessionId={session.session_id} selectedKeys={selectedJobNumbers!} evaluationMonth={evaluationMonth} />
              <Excel2AnalysisView sessionId={session.session_id} selectedKeys={selectedJobNumbers!} evaluationMonth={evaluationMonth} />
            </div>
          </div>
        )}

        {/* STEP 5: REVIEW & APPROVE */}
        {currentStep === 5 && step3Complete && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-gray-800 uppercase flex items-center justify-between">
              <div className="flex items-center"><Play className="w-5 h-5 mr-2 text-blue-600" /> Step 5: Review & Approve</div>
              <button onClick={() => setCurrentStep(6)} className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg font-bold shadow">
                Proceed to Output →
              </button>
            </h2>
            <ReviewDashboard 
              sessionId={session.session_id} 
              selectedKeys={selectedJobNumbers!} 
              onNext={() => setCurrentStep(6)}
              evaluationMonth={evaluationMonth}
              customColumns={customColumns}
              setCustomColumns={setCustomColumns}
            />
          </div>
        )}

        {/* STEP 6: OUTPUT & DOWNLOAD */}
        {currentStep === 6 && step3Complete && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-gray-800 uppercase flex items-center">
              <Play className="w-5 h-5 mr-2 text-blue-600" /> Step 6: Generate Output
            </h2>
            <OutputDashboard sessionId={session.session_id} selectedKeys={selectedJobNumbers!} evaluationMonth={evaluationMonth} customColumns={customColumns} />
          </div>
        )}

      </div>
    </div>
  );
};
