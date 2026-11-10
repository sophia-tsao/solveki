// Whether a typed answer is the same as a problem's solution. A port of
// backend/myapp/answers.py (the deck grades on the server; the diagnostic
// grades here): whitespace and case don't matter, numbers compare by exact
// value ("1/2" is "0.5"), a fraction matches the rounded decimal it rounds to
// ("1/3" is "0.333"), a typed fraction must be in lowest terms ("6/8" is never
// "3/4"), and a unit after a lone number is optional ("216" is "216 m^2").
// Both are tested against the cases in answerCases.json.

// An integer or decimal, optionally over an integer denominator. Signs stay in
// the surrounding text. Global, for split/match; never used with .test/.exec.
const NUMBER_RE = /(?:\d+(?:\.\d*)?|\.\d+)(?:\/\d+)?/g;
// A solution that is one number followed by a unit ("216 m^2", "4.5 cm").
const WITH_UNIT_RE = /^(-?(?:\d+(?:\.\d*)?|\.\d+)(?:\/\d+)?)[a-z]+(?:\^\d)?$/;
// What Python's float() accepts that matters here (no hex, no empty string).
const FLOAT_RE = /^\s*[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?\s*$/i;

function normalize(text) {
  return String(text).replace(/\s+/g, '').replaceAll('$', '').replaceAll('−', '-').toLowerCase();
}

function gcd(a, b) {
  while (b) [a, b] = [b, a % b];
  return a;
}

// An unsigned decimal string as an exact fraction [numerator, denominator].
function decimalValue(text) {
  const [whole, fraction = ''] = text.split('.');
  return [BigInt((whole || '0') + fraction), 10n ** BigInt(fraction.length)];
}

// A number token's exact value as [numerator, denominator], or null for a zero
// denominator.
function value(token) {
  const [numerator, denominator] = token.split('/');
  const [p, q] = decimalValue(numerator);
  if (denominator === undefined) return [p, q];
  const d = BigInt(denominator);
  return d === 0n ? null : [p, q * d];
}

function isReduced(token) {
  const [numerator, denominator] = token.split('/');
  if (denominator === undefined) return true;
  if (numerator.includes('.')) return false;
  const p = BigInt(numerator);
  const q = BigInt(denominator);
  return q > 1n && gcd(p, q) === 1n;
}

// Mirrors generators._format.num for a non-negative fraction: round half up to
// three places, then drop trailing zeros.
function roundedText([p, q]) {
  const thousandths = (2n * p * 1000n + q) / (2n * q);
  const whole = thousandths / 1000n;
  const rest = String(thousandths % 1000n).padStart(3, '0').replace(/0+$/, '');
  return rest ? `${whole}.${rest}` : String(whole);
}

function numbersMatch(typed, expected) {
  if (!isReduced(typed)) return false;
  const a = value(typed);
  if (a === null) return false;
  const e = value(expected);
  if (e !== null && a[0] * e[1] === e[0] * a[1]) return true;
  // A fraction for an answer that was rounded: right if it rounds to it.
  return typed.includes('/') && !expected.includes('/') && roundedText(a) === expected;
}

export function answerMatches(answer, solution) {
  const withUnit = normalize(solution).match(WITH_UNIT_RE);
  if (withUnit && matches(answer, withUnit[1])) return true;
  return matches(answer, solution);
}

function matches(answer, solution) {
  if (answer === solution) return true;
  if (FLOAT_RE.test(answer) && FLOAT_RE.test(solution)) {
    const a = Number(answer);
    if (Number.isFinite(a) && a === Number(solution)) return true;
  }
  const typed = normalize(answer);
  const expected = normalize(solution);
  if (!typed) return false;
  const typedNumbers = typed.match(NUMBER_RE) ?? [];
  const expectedNumbers = expected.match(NUMBER_RE) ?? [];
  if (typedNumbers.length !== expectedNumbers.length) return false;
  const typedText = typed.split(NUMBER_RE);
  const expectedText = expected.split(NUMBER_RE);
  if (typedText.join('\u0000') !== expectedText.join('\u0000')) return false;
  return typedNumbers.every((t, i) => numbersMatch(t, expectedNumbers[i]));
}
