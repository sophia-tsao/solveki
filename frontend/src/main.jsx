import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.jsx'

// One shared client for the whole app. Defaults chosen for this SPA:
// - retry: transient network blips ("failed to fetch") get a couple of retries
//   with backoff before surfacing to the user.
// - refetchOnWindowFocus off: refocusing the tab must not silently refetch —
//   several screens (e.g. the practice deck) hold local interaction state that a
//   background refetch would discard; day-rollover reloads are handled explicitly.
// React Query also de-duplicates in-flight requests, so StrictMode's double
// mount in dev collapses to a single network call per query.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
);
