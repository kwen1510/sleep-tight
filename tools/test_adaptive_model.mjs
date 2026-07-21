import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
const model = require('../computer/adaptive_sleep_model.js');
const dataset = model.buildDataset();
assert.equal(dataset.nights.length, 30);
assert.equal(dataset.no_future_data, true);
assert.equal(dataset.nights[10].decision.history_count, 10);
assert.equal(dataset.nights[10].decision.history_used_through_day, 10);

for (const night of dataset.nights) {
  assert.equal(night.decision.history_count, night.day - 1, `Night ${night.day} history count`);
  assert.equal(night.decision.history_used_through_day, Math.max(0, night.day - 1), `Night ${night.day} boundary`);
  for (const estimate of night.decision.candidate_estimates) {
    assert.ok(estimate.prior_nights <= night.day - 1, `Night ${night.day} candidate count`);
    assert.ok(estimate.closest_nights.every(match => match.day < night.day), `Night ${night.day} future match`);
  }
  assert.ok(night.decision.closest_contexts.every(match => match.day < night.day), `Night ${night.day} closest context`);
  assert.equal(night.response.minutes.length, 10);
  assert.equal(night.response.heart_rate_bpm.length, 10);
  assert.equal(night.response.movement_events_per_minute.length, 10);
  assert.equal(night.response.steps_18_to_22.length, 5);
}

const counts = Object.fromEntries(dataset.intervention_summary.map(item => [item.id, item.n]));
assert.ok(Object.values(counts).every(count => count >= 4), 'Every routine needs four observations');
assert.equal(Object.values(counts).reduce((a,b)=>a+b,0), 30);
assert.ok(dataset.matched_pairs.length >= 6);
assert.ok(dataset.matched_pairs.every(pair => pair.similarity >= 78));
assert.equal(dataset.next_ten_plan.length, 10);
assert.deepEqual(dataset.next_ten_plan.map(item => item.day), [31,32,33,34,35,36,37,38,39,40]);

// Rebuilding prefixes must reproduce the stored decision and outcome exactly.
const rebuilt = [];
for (let day=1; day<=30; day++) {
  const night = model.simulateNight(day, rebuilt);
  assert.equal(night.intervention_id, dataset.nights[day-1].intervention_id, `Night ${day} recommendation reproducibility`);
  assert.equal(night.outcome_score, dataset.nights[day-1].outcome_score, `Night ${day} outcome reproducibility`);
  rebuilt.push(night);
}
console.log('Adaptive model passed 30-night prefix-only, balanced evidence, response-series, matched-pair, and forward-plan checks.');
