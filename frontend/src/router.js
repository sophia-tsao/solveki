// Parse "#/page", "#/page/42" or "#/page/42?class=3&tab=progress" into
// { page, id, params }. The optional id backs the detail pages
// (class/assignment/student) and the params carry page context such as the
// class a student was opened from, without pulling in a router library.
export function parseHash(hash = window.location.hash) {
  const raw = hash.replace(/^#\/?/, "");
  const [path, query = ""] = raw.split("?");
  const [page, idStr] = path.split("/");
  const id = idStr && /^\d+$/.test(idStr) ? Number(idStr) : null;
  const params = Object.fromEntries(new URLSearchParams(query));
  return { page, id, params };
}

// The hash for a route; the inverse of parseHash.
export function hashFor({ page, id = null, params = {} }) {
  const query = new URLSearchParams(
    Object.entries(params || {}).filter(([, v]) => v != null && v !== ""),
  ).toString();
  return `#/${page}${id != null ? `/${id}` : ""}${query ? `?${query}` : ""}`;
}
