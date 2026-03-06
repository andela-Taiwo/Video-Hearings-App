import React from 'react';
import { render, screen, fireEvent } from '../../test-utils/testUtils';
import { HearingCard } from '../../components/hearings/HearingCard';
import { mockHearing } from '../../test-utils/mockData';

describe('HearingCard', () => {
  it('renders hearing information correctly', () => {
    const hearing = mockHearing({
      name: 'State vs. Smith',
      hearing_type: 'arraignment',
      courtroom_name: 'Courtroom A',
      scheduled_at: '2025-06-15T10:00:00Z',
    });

    render(<HearingCard hearing={hearing} />);

    expect(screen.getByText('State vs. Smith')).toBeInTheDocument();
    expect(screen.getByText('Arraignment')).toBeInTheDocument();
    expect(screen.getByText(/Courtroom A/)).toBeInTheDocument();
  });

  it('calls callbacks when actions are clicked', () => {
    const hearing = mockHearing();
    const onClick = jest.fn();
    const onEdit = jest.fn();
    const onAddParticipants = jest.fn();

    render(
      <HearingCard
        hearing={hearing}
        onClick={onClick}
        onEdit={onEdit}
        onAddParticipants={onAddParticipants}
      />,
    );

    fireEvent.click(screen.getByText(hearing.name));
    expect(onClick).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: /add/i }));
    expect(onAddParticipants).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    expect(onEdit).toHaveBeenCalledTimes(1);
  });
});

