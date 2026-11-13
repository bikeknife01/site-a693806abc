import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync(new URL('../src/map-selector.html', import.meta.url), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

function open(search = '') {
  const events = {};
  const elements = Object.fromEntries(['season', 'map', 'sourceNote'].map(id => [id, {
    addEventListener(type, callback) { events[`${id}:${type}`] = callback; },
  }]));
  const window = {
    location: new URL(`https://example.test/map/${search}`),
    history: { pushState(state, title, url) { window.location = new URL(url); } },
    addEventListener(type, callback) { events[type] = callback; },
  };
  vm.runInNewContext(script, {
    URL, URLSearchParams, window, document: { getElementById: id => elements[id] },
  });
  return { elements, events, window };
}

test('plain visits open Charlie and disclose partial terrain', () => {
  const { elements } = open();
  assert.equal(elements.season.value, 'season3');
  assert.equal(new URL(elements.map.src).pathname, '/map/season3.html');
  assert.match(elements.sourceNote.textContent, /Partial terrain/);
});

test('existing encyclopedia node links retain Bravo placement identity', () => {
  const { elements } = open('?node=map-node%3A000042');
  const target = new URL(elements.map.src);
  assert.equal(target.pathname, '/map/season2.html');
  assert.equal(target.searchParams.get('node'), 'map-node:000042');
});

test('explicit season links select the requested placement namespace', () => {
  for (const season of ['season1', 'season2', 'season3']) {
    const { elements } = open(`?season=${season}&node=map-node%3A000042`);
    const target = new URL(elements.map.src);
    assert.equal(target.pathname, `/map/${season}.html`);
    assert.equal(target.searchParams.get('node'), 'map-node:000042');
    assert.match(elements.sourceNote.textContent, /server- and season-specific/);
  }
});

test('switching seasons clears incompatible selected-node IDs; back restores them', () => {
  const { elements, events, window } = open('?season=season3&node=map-node%3A000042');
  elements.season.value = 'season1';
  events['season:change']();
  assert.equal(window.location.searchParams.get('season'), 'season1');
  assert.equal(window.location.searchParams.has('node'), false);
  assert.equal(new URL(elements.map.src).search, '');
  window.location = new URL('https://example.test/map/?season=season3&node=map-node%3A000042');
  events.popstate();
  assert.equal(elements.season.value, 'season3');
  assert.equal(new URL(elements.map.src).searchParams.get('node'), 'map-node:000042');
});

test('unknown or inherited object keys cannot select an arbitrary page', () => {
  for (const value of ['season99', '__proto__', 'constructor']) {
    assert.equal(open(`?season=${value}`).elements.season.value, 'season3');
    assert.equal(open(`?season=${value}&node=map-node%3A000042`).elements.season.value, 'season2');
  }
});
