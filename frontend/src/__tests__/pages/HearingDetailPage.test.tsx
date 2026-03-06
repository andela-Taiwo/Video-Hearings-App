
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HearingDetailPage } from '../../pages/HearingDetailPage';
import { server } from '../../test-utils/server';
import { rest } from 'msw';
import { mockHearing } from '../../test-utils/mockData';

// Create a wrapper with all providers
const createTestQueryClient = () => new QueryClient({
  defaultOptions: { 
    queries: { 
      retry: false,
      staleTime: 0,
    } 
  },
});

const renderWithRoute = (initialEntry = '/hearings/h-1') => {
  const queryClient = createTestQueryClient();
  
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/hearings/:id" element={<HearingDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('HearingDetailPage (integration)', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it('shows loading state then hearing details', async () => {
    // Mock successful API response
    server.use(
      rest.get('http://localhost:8000/api/v1/hearings/h-1/', (_req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json(mockHearing({ 
            id: 'h-1', 
            name: 'State vs. Smith - Arraignment',
            status: 'scheduled'
          }))
        );
      }),
      // Mock stats endpoints
      rest.get('http://localhost:8000/api/v1/hearings/', (_req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({ count: 0, results: [] })
        );
      })
    );

    renderWithRoute();

    // Initially should show loading spinner
    expect(screen.getByRole('status')).toBeInTheDocument();
    
    // Wait for data to load - look for the main title specifically
    await waitFor(() => {
      expect(screen.getByRole('heading', { 
        name: /State vs\. Smith - Arraignment/i,
        level: 1  // Specifically the h1 element
      })).toBeInTheDocument();
    });
    
    // Check for the hearing ID
    expect(screen.getByText(/#h-1/i)).toBeInTheDocument();
    
    // Check for status badge
    expect(screen.getByText(/Scheduled/i)).toBeInTheDocument();
    
    // Verify the "not found" message never appears
    expect(screen.queryByText(/Hearing not found/i)).not.toBeInTheDocument();
  });

  it('renders not found message for unknown id', async () => {
    server.use(
      rest.get('http://localhost:8000/api/v1/hearings/unknown-id/', (_req, res, ctx) => {
        return res(ctx.status(404));
      }),
      rest.get('http://localhost:8000/api/v1/hearings/', (_req, res, ctx) => {
        return res(ctx.status(200), ctx.json({ count: 0, results: [] }));
      })
    );

    renderWithRoute('/hearings/unknown-id');

    // Wait for the not found message
    expect(await screen.findByRole('heading', { 
      name: /Hearing not found/i 
    })).toBeInTheDocument();
    
    expect(screen.getByRole('button', { name: /back to hearings/i })).toBeInTheDocument();
  });
});