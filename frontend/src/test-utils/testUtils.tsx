// import React, { ReactElement } from 'react';
// import { render, RenderOptions } from '@testing-library/react';
// import { MemoryRouter, MemoryRouterProps } from 'react-router-dom';

// interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
//   routerProps?: MemoryRouterProps;
// }

// /**
//  * Custom render that wraps components in MemoryRouter.
//  */
// export function renderWithRouter(
//   ui: ReactElement,
//   { routerProps, ...renderOptions }: CustomRenderOptions = {},
// ) {
//   function Wrapper({ children }: { children: React.ReactNode }) {
//     return <MemoryRouter {...routerProps}>{children}</MemoryRouter>;
//   }
//   return render(ui, { wrapper: Wrapper, ...renderOptions });
// }

// export { render };
// export { default as userEvent } from '@testing-library/user-event';
// export * from '@testing-library/react';

// test-utils/testUtils.tsx
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create a wrapper with all necessary providers
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false, // Disable retries for testing
    },
  },
});

interface WrapperProps {
  children: React.ReactNode;
}

const AllTheProviders = ({ children }: WrapperProps) => {
  const queryClient = createTestQueryClient();
  
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';
export { customRender as renderWithRouter };
