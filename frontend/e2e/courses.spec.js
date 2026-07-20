import { test, expect } from '@playwright/test';
import { resetUser } from './fixtures.js';

test.describe('courses page', () => {
  test.beforeEach(async ({ page }) => {
    await resetUser(page);
    await page.goto('/#/courses');
  });

  test('lists seeded courses', async ({ page }) => {
    // seed_courses loads a fixed curriculum; check a couple of known names.
    // Course names live in .course-bar-name (some, like "Grade 1", also appear
    // as a grade label, so scope to the name span to stay unambiguous).
    await expect(page.locator('.course-bar').first()).toBeVisible();
    await expect(page.locator('.course-bar-name', { hasText: /^Grade 1$/ })).toBeVisible();
    await expect(page.locator('.course-bar-name', { hasText: /^Algebra I$/ })).toBeVisible();
  });

  test('expanding a course reveals its topics', async ({ page }) => {
    const firstCourse = page.locator('.course-bar').first();
    await firstCourse.locator('.course-bar-name').click();
    // Topic rows become visible once the course is open.
    await expect(firstCourse.locator('.topic-name').first()).toBeVisible();
  });

  test('toggling a topic persists across reload', async ({ page }) => {
    const firstCourse = page.locator('.course-bar').first();
    await firstCourse.locator('.course-bar-name').click();

    // The checkbox is controlled and only flips once the API round-trip
    // resolves, so click and assert with a retrying expectation rather than
    // .check() (which expects the state to change synchronously).
    const firstTopic = firstCourse.locator('.topic-checkbox').first();
    await expect(firstTopic).not.toBeChecked();
    await firstTopic.click();
    await expect(firstTopic).toBeChecked();

    // Reload and re-open: the selection came from the server, so it sticks.
    await page.reload();
    await page.locator('.course-bar').first().locator('.course-bar-name').click();
    await expect(
      page.locator('.course-bar').first().locator('.topic-checkbox').first(),
    ).toBeChecked();
  });

  test('shows every topic of a course with many topics (no clipping)', async ({ page }) => {
    // Grade 7 has the longest topic list in the seed curriculum, enough to
    // overflow a fixed-height panel. Every topic must stay visible, including
    // the last one — a clipped panel would hide the tail.
    const grade7 = page
      .locator('.course-bar')
      .filter({ has: page.locator('.course-bar-name', { hasText: /^Grade 7$/ }) });
    await grade7.locator('.course-bar-name').click();

    const topics = grade7.locator('.topic-name');
    await expect(topics.first()).toBeVisible();
    const count = await topics.count();
    expect(count).toBeGreaterThan(0);

    // The panel uses overflow:hidden, so a topic scrolled past a fixed height
    // is clipped from view yet still reports as "visible" to Playwright. The
    // real signal is that the container isn't clipping any content: its full
    // content height (scrollHeight) must fit within its rendered height
    // (clientHeight). Wait for the expand transition to settle first.
    const panel = grade7.locator('.course-bar-topics');
    await expect
      .poll(async () =>
        panel.evaluate((el) => el.scrollHeight <= el.clientHeight),
      )
      .toBe(true);
  });

  test('selecting a course selects all its topics', async ({ page }) => {
    const firstCourse = page.locator('.course-bar').first();
    await firstCourse.locator('.course-bar-checkbox').click();
    await expect(firstCourse.locator('.course-bar-checkbox')).toBeChecked();
    await firstCourse.locator('.course-bar-name').click();

    // Wait for the topic rows to load before counting them.
    const topicBoxes = firstCourse.locator('.topic-checkbox');
    await expect(topicBoxes.first()).toBeVisible();
    const count = await topicBoxes.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      await expect(topicBoxes.nth(i)).toBeChecked();
    }
  });
});
