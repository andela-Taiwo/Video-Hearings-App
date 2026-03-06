
import React from 'react';
import { renderWithRouter, screen, waitFor } from '../../test-utils/testUtils';
import userEvent from '@testing-library/user-event';
import { HearingsPage } from '../../pages/HearingsPage';
import { server } from '../../test-utils/server';
import { rest } from 'msw';

// Mock ResizeObserver which is needed for Headless UI Dialog
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe('HearingsPage (integration)', () => {
  it('loads and displays hearings from the API', async () => {
    renderWithRouter(<HearingsPage />);

    // Wait for the hearings to load
    expect(await screen.findByText(/Hearing Alpha/i)).toBeInTheDocument();
    expect(await screen.findByText(/Hearing Beta/i)).toBeInTheDocument();
  });

  it('allows scheduling modal to be opened', async () => {
    // Setup userEvent for realistic interactions
    const user = userEvent.setup();
    
    renderWithRouter(<HearingsPage />);

    // Wait for the page to load first
    expect(await screen.findByText(/Hearing Alpha/i)).toBeInTheDocument();
    
    // Find and click the schedule button
    const scheduleButton = screen.getByRole('button', { name: /schedule hearing/i });
    await user.click(scheduleButton);

    // Wait for modal to appear
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    
    // Check for modal title
    expect(screen.getByText(/schedule new hearing/i)).toBeInTheDocument();
  });

  it('allows closing the scheduling modal', async () => {
    const user = userEvent.setup();
    
    renderWithRouter(<HearingsPage />);

    // Wait for page to load
    expect(await screen.findByText(/Hearing Alpha/i)).toBeInTheDocument();
    
    // Open modal
    const scheduleButton = screen.getByRole('button', { name: /schedule hearing/i });
    await user.click(scheduleButton);

    // Verify modal is open
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Find and click cancel/close button
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    // Verify modal is closed
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

});