
// export interface Hearing {
//   id: string;
//   case_id: string;
//   courtroom_id: string;
//   scheduled_at: string;
//   status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled' | 'postponed';
//   name: string;
//   description?: string;
//   hearing_type: string;
//   participants?: Participant[];
//   created_at?: string;
//   updated_at?: string;
// }

// export interface Participant {
//   id: string;
//   user_id: string;
//   email: string;
//   full_name: string;
//   role: string;
//   join_token?: string;
//   created_at?: string;
// }

export interface Participant {
  id: string;
  user_id: string;
  user_email: string;
  user_name?: string;
  first_name?: string;
  last_name?: string;
  role: string;
  join_token?: string;
  created_at?: string;
  updated_at?: string;
  // Add any other fields your API returns
}

export interface Courtroom {
  id: string;
  court: string;   // parent Court UUID — used as court_id for participants
  name: string;
  court_name?: string;
  capacity?: number;
}

export interface Case {
  id: string;
  case_number: string;
  title: string;
  case_type: string;
  status: string;
}

export interface Hearing {
  id: string;
  case_id: string;
  courtroom_id: string;
  courtroom?: string;       // UUID returned by the API
  courtroom_name?: string;  // human-readable name returned by the API
  scheduled_at: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled' | 'postponed';
  name: string;
  description?: string;
  hearing_type: string;
  participants?: Participant[];
  created_at?: string;
  updated_at?: string;
}

export interface AddParticipantData {
  email: string;
  role: string;
  first_name?: string;
  last_name?: string;
  bar_number?: string;
  court_id?: string;
  phone_number?: string;
  send_invite?: boolean;
}

export interface CreateHearingData {
  case_id: string;
  courtroom_id: string;
  scheduled_at: string;
  name: string;
  description?: string;
  hearing_type: string;
  participants: AddParticipantData[];
}

export interface UpdateHearingData {
  case_id?: string;
  courtroom_id?: string;
  scheduled_at?: string;
  name?: string;
  description?: string;
  hearing_type?: string;
  status?: Hearing['status'];
}

export interface HearingFilters {
  status?: Hearing['status'];
  date_from?: string;
  date_to?: string;
  case_id?: string;
  courtroom_id?: string;
  search?: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}