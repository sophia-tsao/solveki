import { describe, expect, it } from 'vitest';
import { answerMatches } from './answerMatch';
import { cases } from './answerCases.json';

describe('answerMatches', () => {
  it.each(cases)('%j vs %j -> %s', (answer, solution, expected) => {
    expect(answerMatches(answer, solution)).toBe(expected);
  });
});
