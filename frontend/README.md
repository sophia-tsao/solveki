# Solveki frontend

React + Vite single-page app for Solveki. See the [root README](../README.md)
for a project overview and full setup.

## Development

```bash
npm install
npm run dev       # dev server on http://localhost:5173
npm run build     # production build to dist/
npm run lint      # oxlint
npm run preview   # preview the production build
```

## Configuration

Set the backend URL in `frontend/.env`:

```
VITE_API_URL=http://localhost:8000
```

Requests are sent with credentials so the Django session cookie flows from the
Vite dev server (`:5173`) to the backend (`:8000`).
