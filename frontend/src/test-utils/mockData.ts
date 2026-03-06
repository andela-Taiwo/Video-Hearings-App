import { Hearing, Participant, Courtroom, Case, CreateHearingData } from '../services/types';

export const mockParticipant = (overrides?: Partial<Participant>): Participant => ({
  id: 'participant-1',
  user_id: 'user-1',
  user_email: 'john@example.com',
  user_name: 'John Doe',
  first_name: 'John',
  last_name: 'Doe',
  role: 'judge',
  join_token: 'token-123',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  ...overrides,
});

export const mockHearing = (overrides?: Partial<Hearing>): Hearing => ({
  id: 'hearing-1',
  case_id: 'case-1',
  courtroom_id: 'courtroom-1',
  courtroom: 'courtroom-1',
  courtroom_name: 'Courtroom A',
  scheduled_at: '2025-06-15T10:00:00Z',
  status: 'scheduled',
  name: 'State vs. Smith - Arraignment',
  description: 'Initial arraignment hearing',
  hearing_type: 'arraignment',
  participants: [mockParticipant()],
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  ...overrides,
});

export const mockCourtroom = (overrides?: Partial<Courtroom>): Courtroom => ({
  id: 'courtroom-1',
  court: 'court-1',
  name: 'Courtroom A',
  court_name: 'District Court',
  capacity: 50,
  ...overrides,
});

export const mockCase = (overrides?: Partial<Case>): Case => ({
  id: 'case-1',
  case_number: 'CASE-2025-001',
  title: 'State vs. Smith',
  case_type: 'criminal',
  status: 'active',
  ...overrides,
});

export const mockCreateHearingData = (overrides?: Partial<CreateHearingData>): CreateHearingData => ({
  case_id: 'case-1',
  courtroom_id: 'courtroom-1',
  scheduled_at: '2025-06-15T10:00:00Z',
  name: 'New Hearing',
  description: 'Test hearing',
  hearing_type: 'trial',
  participants: [
    {
      email: 'judge@example.com',
      role: 'judge',
      first_name: 'Jane',
      last_name: 'Judge',
    },
  ],
  ...overrides,
});

/**
 * Create a list of mock hearings with different statuses.
 */
export const mockHearingsList = (): Hearing[] => [
  mockHearing({ id: 'h-1', name: 'Hearing Alpha', status: 'scheduled' }),
  mockHearing({ id: 'h-2', name: 'Hearing Beta', status: 'in_progress' }),
  mockHearing({ id: 'h-3', name: 'Hearing Gamma', status: 'completed' }),
  mockHearing({ id: 'h-4', name: 'Hearing Delta', status: 'cancelled' }),
  mockHearing({ id: 'h-5', name: 'Hearing Epsilon', status: 'postponed' }),
];

