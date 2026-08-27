import axios from 'axios';
import type { Session, WorkbookMetadata, SheetMetadata, MappingConfiguration, ValidationResult, OutputGenerateRequest } from '../types';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
});

// Global interceptor to handle HTML error pages and parsing failures
api.interceptors.response.use(
  (response) => {
    // If the server returns 200 OK but the content is actually HTML (e.g. proxy fallback)
    if (typeof response.data === 'string' && response.data.trim().startsWith('<')) {
      return Promise.reject(new Error("Received unexpected HTML response from server instead of JSON data."));
    }
    return response;
  },
  (error) => {
    if (error.response && typeof error.response.data === 'string' && error.response.data.trim().startsWith('<')) {
      error.response.data = { detail: `Server returned an unexpected error page (Status: ${error.response.status}). Please verify the backend is running properly.` };
    } else if (error.message && error.message.includes("Unexpected token '<'")) {
       error.response = error.response || {};
       error.response.data = { detail: "Failed to parse server response. The server might have returned an HTML error page." };
    }
    return Promise.reject(error);
  }
);


export const sessionService = {
  createSession: async (): Promise<Session> => {
    const response = await api.post<Session>('/sessions');
    return response.data;
  },
  getSession: async (sessionId: string): Promise<Session> => {
    const response = await api.get<Session>(`/sessions/${sessionId}`);
    return response.data;
  },
  setEvaluationMonth: async (sessionId: string, evaluationMonth: string): Promise<Session> => {
    const response = await api.post<Session>(`/sessions/${sessionId}/evaluation-month`, { evaluation_month: evaluationMonth });
    return response.data;
  },
  validateAndSaveMapping: async (sessionId: string, mapping: MappingConfiguration): Promise<ValidationResult> => {
    const response = await api.post<ValidationResult>(`/sessions/${sessionId}/mapping`, mapping);
    return response.data;
  },
  getJobNumbers: async (sessionId: string): Promise<import('../types').JobNumberSummary> => {
    const response = await api.get<import('../types').JobNumberSummary>(`/sessions/${sessionId}/job-numbers`);
    return response.data;
  },
  matchJobNumbers: async (sessionId: string, jobNumbers: string[]): Promise<import('../types').MatchResult> => {
    const response = await api.post<import('../types').MatchResult>(`/sessions/${sessionId}/job-numbers/match`, { job_numbers: jobNumbers });
    return response.data;
  },
  calculateExcel1: async (sessionId: string, jobNumbers: string[], evaluationMonth: string): Promise<import('../types').JobCalculationResult[]> => {
    const response = await api.post<import('../types').JobCalculationResult[]>(`/sessions/${sessionId}/calculations/excel1`, { job_numbers: jobNumbers, evaluation_month: evaluationMonth });
    return response.data;
  },
  calculateInspection: async (sessionId: string, jobNumbers: string[], evaluationMonth: string): Promise<import('../types').InspectionJobResult[]> => {
    const response = await api.post<import('../types').InspectionJobResult[]>(`/sessions/${sessionId}/calculations/inspection`, { job_numbers: jobNumbers, evaluation_month: evaluationMonth });
    return response.data;
  },
  calculateCombined: async (sessionId: string, request: import('../types').CombinedCalculationRequest): Promise<import('../types').CombinedJobSummary[]> => {
    const response = await api.post<import('../types').CombinedJobSummary[]>(`/sessions/${sessionId}/calculations/combined`, request);
    return response.data;
  },
  getReviewJobs: async (sessionId: string, request: { job_numbers: string[], evaluation_month?: string }): Promise<import('../types').JobReviewResult[]> => {
    const response = await api.post<import('../types').JobReviewResult[]>(`/sessions/${sessionId}/review`, request);
    return response.data;
  },
  overrideJob: async (sessionId: string, jobNumber: string, request: import('../types').OverrideRequest): Promise<import('../types').JobReviewResult> => {
    const response = await api.post<import('../types').JobReviewResult>(`/sessions/${sessionId}/jobs/${jobNumber}/overrides`, request);
    return response.data;
  },
  resetJobOverrides: async (sessionId: string, jobNumber: string): Promise<import('../types').JobReviewResult> => {
    const response = await api.post<import('../types').JobReviewResult>(`/sessions/${sessionId}/jobs/${jobNumber}/reset-overrides`);
    return response.data;
  },
  approveAll: async (sessionId: string, request: { job_numbers: string[], evaluation_month?: string }): Promise<{ approved: number, failed: number }> => {
    const response = await api.post<{ approved: number, failed: number }>(`/sessions/${sessionId}/review/approve-all`, request);
    return response.data;
  },
  approveJob: async (sessionId: string, jobNumber: string, request: import('../types').ApprovalRequest): Promise<import('../types').JobReviewResult> => {
    const response = await api.post<import('../types').JobReviewResult>(`/sessions/${sessionId}/jobs/${jobNumber}/approve`, request);
    return response.data;
  },
  unapproveJob: async (sessionId: string, jobNumber: string): Promise<import('../types').JobReviewResult> => {
    const response = await api.post<import('../types').JobReviewResult>(`/sessions/${sessionId}/jobs/${jobNumber}/unapprove`);
    return response.data;
  },
  deleteJob: async (sessionId: string, jobNumber: string): Promise<import('../types').JobReviewResult> => {
    const response = await api.delete<import('../types').JobReviewResult>(`/sessions/${sessionId}/jobs/${jobNumber}`);
    return response.data;
  },
  undeleteJob: async (sessionId: string, jobNumber: string): Promise<import('../types').JobReviewResult> => {
    const response = await api.post<import('../types').JobReviewResult>(`/sessions/${sessionId}/jobs/${jobNumber}/undelete`);
    return response.data;
  },
  deleteAll: async (sessionId: string, request: { job_numbers: string[], evaluation_month?: string }): Promise<{ deleted: number, failed: number }> => {
    const response = await api.post<{ deleted: number, failed: number }>(`/sessions/${sessionId}/review/delete-all`, request);
    return response.data;
  }
};

export const excelService = {
  uploadWorkbook: async (sessionId: string, type: string, file: File): Promise<WorkbookMetadata> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<WorkbookMetadata>(
      `/sessions/${sessionId}/files/${type}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },
  getWorkbook: async (sessionId: string, type: string): Promise<WorkbookMetadata> => {
    const response = await api.get<WorkbookMetadata>(`/sessions/${sessionId}/workbooks/${type}`);
    return response.data;
  },
  getSheet: async (sessionId: string, type: string, sheetName: string): Promise<SheetMetadata> => {
    const response = await api.get<SheetMetadata>(
      `/sessions/${sessionId}/workbooks/${type}/sheets/${encodeURIComponent(sheetName)}`
    );
    return response.data;
  },
  removeWorkbook: async (sessionId: string, type: string): Promise<{ status: string, message: string }> => {
    const response = await api.delete<{ status: string, message: string }>(`/sessions/${sessionId}/files/${type}`);
    return response.data;
  },
  removeAllWorkbooks: async (sessionId: string): Promise<{ status: string, message: string }> => {
    const response = await api.delete<{ status: string, message: string }>(`/sessions/${sessionId}/files`);
    return response.data;
  }
};

export const outputService = {
  getChangePlan: async (sessionId: string, request: { job_numbers: string[], evaluation_month?: string }): Promise<import('../types').ChangePlan> => {
    const response = await api.post<import('../types').ChangePlan>(`/sessions/${sessionId}/output/plan`, request);
    return response.data;
  },
  generateOutput: async (sessionId: string, request: OutputGenerateRequest & { evaluation_month?: string }): Promise<import('../types').OutputMetadata> => {
    const response = await api.post<import('../types').OutputMetadata>(`/sessions/${sessionId}/output/generate`, request);
    return response.data;
  },
  downloadOutput: (sessionId: string) => {
    window.open(`${API_URL}/sessions/${sessionId}/output/download`, '_blank');
  }
};
