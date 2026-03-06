import React from 'react';
import { render, screen, fireEvent } from '../../test-utils/testUtils';
import { HearingList } from '../../components/hearings/HearingList';
import { mockHearingsList } from '../../test-utils/mockData';

describe('HearingList', () => {
  it('shows loading state', () => {
    render(<HearingList hearings={[]} loading />);

    expect(screen.getByText(/loading hearings/i)).toBeInTheDocument();
  });

  it('shows empty state when there are no hearings', () => {
    render(<HearingList hearings={[]} />);

    expect(screen.getByText(/no hearings on the docket/i)).toBeInTheDocument();
  });

  it('renders a card for each hearing and handles click', () => {
    const hearings = mockHearingsList();
    const handleClick = jest.fn();

    render(<HearingList hearings={hearings} onHearingClick={handleClick} />);

    hearings.forEach((h) => {
      expect(screen.getByText(h.name)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(hearings[0].name));
    expect(handleClick).toHaveBeenCalledTimes(1);
    expect(handleClick).toHaveBeenCalledWith(hearings[0]);
  });
});

