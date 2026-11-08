import { test, expect } from '@playwright/test';
import { resetUser, selectFirstCourse, setQuestionsPerDay, answerProblem } from './fixtures.js';

// The deck's progress bar; it shows no text, so tests read its accessible value
// ("Question 2 of 5").
const progress = (page) => page.getByRole('progressbar', { name: "Today's practice" });

test.describe('daily deck', () => {
  test('shows the no-topics prompt when nothing is selected', async ({ page }) => {
    await resetUser(page);
    await page.goto('/#/math');
    await expect(
      page.getByText('Select topics from the Courses page to get started.'),
    ).toBeVisible();
  });

  test('renders a problem once a topic is selected', async ({ page }) => {
    await resetUser(page);
    await selectFirstCourse(page);
    await page.goto('/#/math');
    await expect(progress(page)).toHaveAttribute('aria-valuetext', /^Question \d+ of \d+$/);
    await expect(page.locator('.math-problem-input')).toBeVisible();
    await expect(page.locator('.math-problem-attempt')).toContainText('Attempt 1 of 2');
  });

  test('a correct answer advances to the next problem', async ({ page }) => {
    await resetUser(page);
    await selectFirstCourse(page);

    await page.goto('/#/math');
    await expect(progress(page)).toHaveAttribute('aria-valuetext', /^Question 1 of /);

    await answerProblem(page, { correct: true });
    // A brief "Correct!" confirmation, then the next card.
    await expect(page.locator('.math-problem-correct-text')).toBeVisible();
    await expect(progress(page)).toHaveAttribute('aria-valuetext', /^Question 2 of /);
  });

  test('a wrong answer consumes an attempt; two wrongs advance', async ({ page }) => {
    await resetUser(page);
    await selectFirstCourse(page);

    await page.goto('/#/math');
    await expect(progress(page)).toHaveAttribute('aria-valuetext', /^Question 1 of /);

    // First wrong attempt: feedback shows, still on question 1, now attempt 2.
    await answerProblem(page, { correct: false });
    await expect(page.locator('.math-problem-submit')).toContainText('Incorrect!');
    await expect(page.locator('.math-problem-attempt')).toContainText('Attempt 2 of 2');
    await expect(progress(page)).toHaveAttribute('aria-valuetext', /^Question 1 of /);

    // Second wrong attempt: out of attempts, the card flips to reveal the
    // answer and its step-by-step solution, and waits. Clicking Continue
    // accepts the miss and advances.
    await answerProblem(page, { correct: false });
    await page.getByRole('button', { name: 'See step-by-step solution' }).click();
    await expect(page.locator('.solution-step').first()).toBeVisible();
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(progress(page)).toHaveAttribute('aria-valuetext', /^Question 2 of /);
  });

  test('reporting an issue on an incorrect answer advances to the next question', async ({ page }) => {
    await resetUser(page);
    await selectFirstCourse(page);

    await page.goto('/#/math');
    await expect(progress(page)).toHaveAttribute('aria-valuetext', /^Question 1 of /);

    // Burn both attempts, then report the miss via "Report issue".
    await answerProblem(page, { correct: false });
    await expect(page.locator('.math-problem-attempt')).toContainText('Attempt 2 of 2');
    await answerProblem(page, { correct: false });
    await page.getByRole('button', { name: 'Report issue' }).click();
    await page.getByRole('radio', { name: "Solveki's solution is incorrect" }).click();
    await page.getByRole('button', { name: 'Submit report' }).click();
    await expect(progress(page)).toHaveAttribute('aria-valuetext', /^Question 2 of /);
  });

  test('finishing the deck shows the completion screen', async ({ page }) => {
    await resetUser(page);
    await selectFirstCourse(page);
    await setQuestionsPerDay(page, 2); // keep it short

    await page.goto('/#/math');
    await expect(progress(page)).toHaveAttribute('aria-valuetext', 'Question 1 of 2');

    // Both cards are brand-new topics, and one right answer isn't enough
    // practice on a new topic: each comes back until 3 of its last 4 are right,
    // so the deck grows past the 2-card setting.
    await answerProblem(page, { correct: true });
    await expect(progress(page)).toHaveAttribute('aria-valuetext', 'Question 2 of 3');

    for (let card = 2; card <= 6; card++) {
      await expect(progress(page)).toHaveAttribute('aria-valuetext', new RegExp(`^Question ${card} of `));
      await answerProblem(page, { correct: true });
    }
    await expect(page.getByText(/You've finished all 6 questions for today/)).toBeVisible();
  });
});
