import { api } from './api.ts';
import { Courtroom } from './types.ts';

interface CourtroomListResponse {
  results: Courtroom[];
  count: number;
}

class CourtService {
  async getCourtrooms(): Promise<Courtroom[]> {
    const response = await api.get<CourtroomListResponse>('/courts/courtrooms/');
    return response.results;
  }
}

export const courtService = new CourtService();
