const API_URL = process.env.E2E_API_URL || 'http://localhost:8000';

// All helpers issue requests through `page.request`, which shares the browser
// context's cookie jar. This matters because Django rotates the session key on
// every login: a request made through a separate context would strand the
// browser on the old cookie. Going through page.request keeps the browser's
// session in sync (and lets these calls reuse the page's existing session).

// Reset the shared E2E user to a clean slate (no selections, no deck, default
// settings) and refresh the session. Call in beforeEach so each test starts
// from a known state regardless of ordering — the whole suite shares one
// backend user, so the database can't isolate tests on its own.
export async function resetUser(page) {
  const res = await page.request.post(`${API_URL}/auth/test-login/`);
  if (!res.ok()) {
    throw new Error(`resetUser failed (${res.status()})`);
  }
}

// Select every topic in the first course via the API, so deck tests don't
// depend on the courses UI. Returns the number of topics selected.
export async function selectFirstCourse(page) {
  const coursesRes = await page.request.get(`${API_URL}/courses/`);
  const { courses } = await coursesRes.json();
  const courseId = courses[0].id;
  await page.request.patch(`${API_URL}/courses/${courseId}/select`, {
    data: { is_selected: true },
  });
  const topicsRes = await page.request.get(`${API_URL}/courses/${courseId}/topics`);
  const { topics } = await topicsRes.json();
  return topics.length;
}

// Set the user's questions-per-day via the API. Handy for making the deck
// short enough to complete within a test.
export async function setQuestionsPerDay(page, count) {
  await page.request.patch(`${API_URL}/settings/`, {
    data: { questions_per_day: count },
  });
}

// Answer the currently-shown problem. Reads the expected solution from the
// deck response captured by the caller and types it, or types a deliberately
// wrong answer when `correct` is false.
export async function answerProblem(page, solution, { correct = true } = {}) {
  const input = page.locator('.math-problem-input');
  // A non-numeric token so it's never string- or numeric-equal to the solution
  // (parseFloat -> NaN), which is how MathProblemResponse checks correctness.
  const value = correct ? solution : 'definitely-wrong';
  await input.fill(value);
  await page.locator('.math-problem-submit').click();
}
