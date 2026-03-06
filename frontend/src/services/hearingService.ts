
import { api } from './api.ts';
import {
  Hearing,
  Participant,
  CreateHearingData,
  UpdateHearingData,
  AddParticipantData,
  HearingFilters,
  PaginatedResponse,
} from './types.ts';

class HearingService {
  private baseUrl = '/hearings';

  async getHearings(filters?: HearingFilters): Promise<PaginatedResponse<Hearing>> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
    }
    return api.get(`${this.baseUrl}/?${params.toString()}`);
  }

  async getUpcomingHearings(days: number = 7): Promise<Hearing[]> {
    return api.get(`${this.baseUrl}/upcoming/?days=${days}`);
  }

  async getHearingsByDateRange(start: string, end: string): Promise<Hearing[]> {
    return api.get(`${this.baseUrl}/by_date_range/?start=${start}&end=${end}`);
  }

  async getHearing(id: string): Promise<Hearing> {
    return api.get(`${this.baseUrl}/${id}/`);
  }

  async createHearing(data: CreateHearingData): Promise<Hearing> {
    return api.post(`${this.baseUrl}/`, data);
  }

  async updateHearing(id: string, data: UpdateHearingData): Promise<Hearing> {
    return api.put(`${this.baseUrl}/${id}/`, data);
  }

  async partialUpdateHearing(id: string, data: Partial<UpdateHearingData>): Promise<Hearing> {
    return api.patch(`${this.baseUrl}/${id}/`, data);
  }

  async deleteHearing(id: string): Promise<void> {
    return api.delete(`${this.baseUrl}/${id}/`);
  }

  async addParticipants(id: string, participants: AddParticipantData[]): Promise<Hearing> {
    return api.post(`${this.baseUrl}/${id}/add_participants/`, { participants });
  }

  async removeParticipants(
    id: string,
    participantIds?: string[],
    participantEmails?: string[],
    roles?: string[],
    userIds?: string[]
  ): Promise<void> {
    return api.delete(`${this.baseUrl}/${id}/participants/`, {
      data: { participant_ids: participantIds, participant_emails: participantEmails, roles, user_ids: userIds },
    });
  }

  async rescheduleHearing(id: string, scheduled_at: string, reason?: string): Promise<Hearing> {
    return api.post(`${this.baseUrl}/${id}/reschedule/`, { scheduled_at, reason });
  }

  async cancelHearing(id: string, reason?: string): Promise<Hearing> {
    return api.post(`${this.baseUrl}/${id}/cancel/`, { reason });
  }
}

export const hearingService = new HearingService();