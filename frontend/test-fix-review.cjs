const { readFileSync } = require('node:fs');
const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');

// Exercise the actual frontend request and review handlers without CDN assets
// or a live AI provider. This is handler coverage, not browser rendering QA.
const html = readFileSync(`${__dirname}/index.html`, 'utf8');
test('the inline application reaches its mount before the HTML script boundary', () => {
  const script = html.match(/<script type="text\/babel">([\s\S]*?)<\/script\s*>/i)?.[1];
  assert.ok(script?.includes('ReactDOM.createRoot'), 'A literal closing script tag must not truncate the app');
});
test('escaping the HTML boundary preserves the displayed hint text', () => {
  const hints = html.match(/const DEMO_HINTS = (\{[\s\S]*?\n\});/)?.[1];
  assert.ok(hints);
  const text = vm.runInNewContext(`(${hints})["xss-01"][1]`);
  assert.ok(text.startsWith('Try: <script>'));
  assert.ok(text.endsWith('</script>'));
  assert.ok(!text.includes('\\'), 'The escape belongs to source, not displayed text');
});
function between(start, end) {
  const from = html.indexOf(start);
  const to = html.indexOf(end, from);
  assert.ok(from >= 0 && to > from, `Missing frontend handler: ${start}`);
  return html.slice(from, to);
}
const handlers = between('  async function callAPI(', '  async function explain(')
  + between('  async function reviewFix(', '  async function sendChat(');
const demo = html.match(/function getDemoFixReview\(challenge\) \{[\s\S]*?\n\}/)?.[0] || '';

function harness(fetch) {
  const state = { review: '', error: '', loading: false };
  const context = vm.createContext({
    API_BASE: 'http://backend.invalid',
    AbortSignal: { timeout: () => 'fixture-timeout-signal' },
    fetch,
    challenge: { id: 'fixture-challenge', language: 'python' },
    userFix: 'print("synthetic fixture")',
    loadingFix: false,
    setLoadingFix(value) { state.loading = value; context.loadingFix = value; },
    setFixReview(value) { state.review = value; },
    setFixError(value) { state.error = value; },
  });
  vm.runInContext(`${demo}\n${handlers}`, context);
  return { state, context, review: () => context.reviewFix() };
}
const response = (body) => ({ ok: true, json: async () => body });

test('valid AI feedback is displayed and the original submission is sent', async () => {
  const requests = [];
  const { state, context, review } = harness(async (url, options) => {
    requests.push({ url, options });
    return response({ review: 'Fixture feedback: revise this implementation.' });
  });
  await review();
  assert.equal(state.review, 'Fixture feedback: revise this implementation.');
  assert.equal(state.error, '');
  assert.equal(state.loading, false);
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, 'http://backend.invalid/api/mentor/review-fix');
  assert.equal(requests[0].options.method, 'POST');
  assert.deepEqual(JSON.parse(requests[0].options.body), {
    challenge_id: 'fixture-challenge', user_fix: context.userFix, language: 'python',
  });
});

const failures = [
  ['network failure', async () => { throw new TypeError('Network unavailable'); }],
  ['timeout', async () => { throw new DOMException('Timed out', 'TimeoutError'); }],
  ['HTTP 401', async () => ({ ok: false, status: 401 })],
  ['HTTP 429', async () => ({ ok: false, status: 429 })],
  ['HTTP 500', async () => ({ ok: false, status: 500 })],
  ['invalid JSON', async () => ({ ok: true, json: async () => { throw new SyntaxError('Invalid JSON'); } })],
  ...[null, {}, { review: '' }, { review: '   ' }, { review: 42 }, { review: {} }, { review: [] }]
    .map((body) => [`malformed review ${JSON.stringify(body)}`, async () => response(body)]),
];

for (const [name, fetch] of failures) {
  test(`${name} reports unavailable feedback rather than approving the code`, async () => {
    const { state, context, review } = harness(fetch);
    const originalFix = context.userFix;
    await review();
    assert.equal(state.review, '');
    assert.match(state.error, /no valid feedback was received/i);
    assert.doesNotMatch(state.error, /looks good/i);
    assert.equal(state.loading, false);
    assert.equal(context.userFix, originalFix, 'Keep the editor intact for retry');
  });
}

test('a successful retry clears the unavailable state', async () => {
  let attempts = 0;
  const { state, review } = harness(async () => {
    if (++attempts === 1) throw new TypeError('Offline');
    return response({ review: 'Actual fixture review' });
  });
  await review();
  assert.match(state.error, /no valid feedback was received/i);
  await review();
  assert.equal(state.error, '');
  assert.equal(state.review, 'Actual fixture review');
  assert.equal(state.loading, false);
});

test('a later failed review never reuses an earlier successful verdict', async () => {
  let attempts = 0;
  const { state, review } = harness(async () => {
    if (++attempts === 1) return response({ review: 'Earlier feedback' });
    throw new TypeError('Offline');
  });
  await review();
  assert.equal(state.review, 'Earlier feedback');
  await review();
  assert.equal(state.review, '');
  assert.match(state.error, /no valid feedback was received/i);
});

test('loading clears after a delayed failure and the form remains retryable', async () => {
  let rejectRequest;
  const { state, review } = harness(() => new Promise((resolve, reject) => { rejectRequest = reject; }));
  const pending = review();
  assert.equal(state.loading, true);
  rejectRequest(new TypeError('Offline'));
  await pending;
  assert.equal(state.loading, false);
  assert.equal(state.review, '');
  assert.match(state.error, /no valid feedback was received/i);
});

test('blank submissions do not request or synthesize feedback', async () => {
  let requests = 0;
  const { state, context, review } = harness(async () => { requests++; return response({}); });
  context.userFix = '  \n ';
  await review();
  assert.equal(requests, 0);
  assert.deepEqual(state, { review: '', error: '', loading: false });
});

test('the review failure is wired to an accessible error, not the AI response', () => {
  assert.match(html, /const \[fixError, setFixError\] = useState\(''\)/);
  assert.match(html, /fixError && \([\s\S]*?role="alert"[\s\S]*?\{fixError\}/);
  assert.doesNotMatch(html, /Your fix looks good!/);
});
