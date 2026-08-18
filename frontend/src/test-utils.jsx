import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Render a component under a fresh QueryClient so components using useQuery /
// useMutation have the required provider. Each call gets its own client so tests
// stay isolated (no cache bleed between tests). Retries are disabled so a
// scripted error surfaces immediately instead of after backoff, and window-focus
// refetching is off to match the app's configuration.
export function renderWithClient(ui, options) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false, gcTime: Infinity },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
    options,
  );
}
