// import { rest } from 'msw';
// import { mockHearing, mockHearingsList, mockCourtroom, mockCase } from './mockData';

// const API_BASE = 'http://localhost:8000/api/v1';

// export const handlers = [
//   // GET /hearings/ — list
//   rest.get(`${API_BASE}/hearings/`, (_req, res, ctx) => {
//     const hearings = mockHearingsList();
//     return res(
//       ctx.json({
//         count: hearings.length,
//         next: null,
//         previous: null,
//         results: hearings,
//       }),
//     );
//   }),

//   // GET /hearings/:id — detail
//   rest.get(`${API_BASE}/hearings/:id/`, (req, res, ctx) => {
//     const { id } = req.params;
//     return res(ctx.json(mockHearing({ id: id as string })));
//   }),

//   // POST /hearings/ — create
//   rest.post(`${API_BASE}/hearings/`, async (req, res, ctx) => {
//     const body = await req.json();
//     return res(ctx.status(201), ctx.json(mockHearing({ ...body, id: 'new-hearing-1' })));
//   }),

//   // PUT /hearings/:id/ — update
//   rest.put(`${API_BASE}/hearings/:id/`, async (req, res, ctx) => {
//     const body = await req.json();
//     const { id } = req.params;
//     return res(ctx.json(mockHearing({ ...body, id: id as string })));
//   }),

//   // DELETE /hearings/:id/
//   rest.delete(`${API_BASE}/hearings/:id/`, (_req, res, ctx) => {
//     return res(ctx.status(204));
//   }),

//   // POST /hearings/:id/add_participants/
//   rest.post(`${API_BASE}/hearings/:id/add_participants/`, (req, res, ctx) => {
//     const { id } = req.params;
//     return res(ctx.json(mockHearing({ id: id as string })));
//   }),

//   // POST /hearings/:id/cancel/
//   rest.post(`${API_BASE}/hearings/:id/cancel/`, (req, res, ctx) => {
//     const { id } = req.params;
//     return res(ctx.json(mockHearing({ id: id as string, status: 'cancelled' })));
//   }),

//   // POST /hearings/:id/reschedule/
//   rest.post(`${API_BASE}/hearings/:id/reschedule/`, (req, res, ctx) => {
//     const { id } = req.params;
//     return res(ctx.json(mockHearing({ id: id as string })));
//   }),

//   // GET /courts/courtrooms/
//   rest.get(`${API_BASE}/courts/courtrooms/`, (_req, res, ctx) => {
//     return res(
//       ctx.json({
//         count: 1,
//         results: [mockCourtroom()],
//       }),
//     );
//   }),

//   // GET /cases/
//   rest.get(`${API_BASE}/cases/`, (_req, res, ctx) => {
//     return res(
//       ctx.json({
//         count: 1,
//         results: [mockCase()],
//       }),
//     );
//   }),
// ];


import { rest } from 'msw';
import { mockHearing, mockHearingsList, mockCourtroom, mockCase } from './mockData';

const API_BASE = 'http://localhost:8000/api/v1';

export const handlers = [
  // GET /hearings/ — list
  rest.get(`${API_BASE}/hearings/`, (_req, res, ctx) => {
    const hearings = mockHearingsList();
    return res(
      ctx.delay(100), // Add small delay to simulate network
      ctx.status(200),
      ctx.json({
        count: hearings.length,
        next: null,
        previous: null,
        results: hearings,
      })
    );
  }),

  // GET /hearings/:id — detail
  rest.get(`${API_BASE}/hearings/:id/`, (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.delay(50),
      ctx.status(200),
      ctx.json(mockHearing({ id: id as string }))
    );
  }),

  // POST /hearings/ — create
  rest.post(`${API_BASE}/hearings/`, async (req, res, ctx) => {
    const body = await req.json();
    return res(
      ctx.delay(100),
      ctx.status(201),
      ctx.json(mockHearing({ ...body, id: 'new-hearing-1' }))
    );
  }),

  // PUT /hearings/:id/ — update
  rest.put(`${API_BASE}/hearings/:id/`, async (req, res, ctx) => {
    const body = await req.json();
    const { id } = req.params;
    return res(
      ctx.delay(50),
      ctx.status(200),
      ctx.json(mockHearing({ ...body, id: id as string }))
    );
  }),

  // DELETE /hearings/:id/
  rest.delete(`${API_BASE}/hearings/:id/`, (_req, res, ctx) => {
    return res(ctx.delay(50), ctx.status(204));
  }),

  // POST /hearings/:id/add_participants/
  rest.post(`${API_BASE}/hearings/:id/add_participants/`, async (req, res, ctx) => {
    const { id } = req.params;
    const body = await req.json();
    return res(
      ctx.delay(100),
      ctx.status(200),
      ctx.json(mockHearing({ id: id as string, participants: body.participants }))
    );
  }),

  // POST /hearings/:id/cancel/
  rest.post(`${API_BASE}/hearings/:id/cancel/`, (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.delay(50),
      ctx.status(200),
      ctx.json(mockHearing({ id: id as string, status: 'cancelled' }))
    );
  }),

  // POST /hearings/:id/reschedule/
  rest.post(`${API_BASE}/hearings/:id/reschedule/`, async (req, res, ctx) => {
    const { id } = req.params;
    const body = await req.json();
    return res(
      ctx.delay(50),
      ctx.status(200),
      ctx.json(mockHearing({ id: id as string, scheduled_at: body.scheduled_at }))
    );
  }),

  // GET /courts/courtrooms/
  rest.get(`${API_BASE}/courts/courtrooms/`, (_req, res, ctx) => {
    return res(
      ctx.delay(50),
      ctx.status(200),
      ctx.json({
        count: 2,
        results: [mockCourtroom(), mockCourtroom({ id: 'courtroom-2', name: 'Courtroom B' })],
      })
    );
  }),

  // GET /cases/
  rest.get(`${API_BASE}/cases/`, (_req, res, ctx) => {
    return res(
      ctx.delay(50),
      ctx.status(200),
      ctx.json({
        count: 2,
        results: [
          mockCase(),
          mockCase({ id: 'case-2', case_number: 'CASE-2025-002', title: 'State vs. Jones' }),
        ],
      })
    );
  }),
];