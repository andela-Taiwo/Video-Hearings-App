import { api } from './api.ts';
import { Case } from './types.ts';

interface CaseListResponse {
  results: Case[];
  count: number;
}

class CaseService {
  async getCases(): Promise<Case[]> {
    const response = await api.get<CaseListResponse>('/cases/');
    return response.results;
  }
}

export const caseService = new CaseService();
