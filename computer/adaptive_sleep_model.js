(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SleepAdaptiveModel = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const interventions = [
    { id: 'control', label: 'Usual quiet routine', short: 'Control', colour: '#7b8581' },
    { id: 'amber', label: '45-minute amber fade', short: 'Amber', colour: '#c77a45' },
    { id: 'instrumental', label: 'Low-arousal instrumental', short: 'Music', colour: '#527e9d' },
    { id: 'pink', label: 'Pink masking noise', short: 'Pink', colour: '#a26d8f' },
    { id: 'amber_music', label: 'Amber fade + instrumental', short: 'Amber + music', colour: '#247664' },
  ];
  const byId = Object.fromEntries(interventions.map(item => [item.id, item]));
  const outcomeNoise = [0,2,-2,1,-1,3,-3,1,0,2,-1,2,-2,3,0,-1,1,-3,2,0,1,-2,3,-1,2,0,-2,1,3,-1];
  const exploration = ['control','amber','instrumental','pink','amber_music','control','amber','instrumental','pink','amber_music'];
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const mean = values => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;

  function contextFor(day, previousNight) {
    const caffeineDays = new Set([4,9,15,22,28]);
    const noisyDays = new Set([3,8,14,19,24,29]);
    const lateMealDays = new Set([6,17,25]);
    const steps = 5200 + ((day * 1847) % 6900);
    const activeMinutes = 18 + ((day * 13) % 47);
    const tension = 2 + ((day * 5 + Math.floor(day / 4)) % 7);
    return {
      steps,
      active_minutes: activeMinutes,
      tension,
      caffeine_after_15: caffeineDays.has(day),
      external_noise: noisyDays.has(day),
      late_meal: lateMealDays.has(day),
      previous_sleep_minutes: previousNight ? previousNight.sleep_minutes : 418,
      previous_morning_quality: previousNight ? previousNight.morning_quality : 6.4,
    };
  }

  function contextSimilarity(a, b) {
    const distance =
      Math.abs(a.steps - b.steps) / 7000 * .22 +
      Math.abs(a.active_minutes - b.active_minutes) / 50 * .14 +
      Math.abs(a.tension - b.tension) / 7 * .27 +
      (a.caffeine_after_15 === b.caffeine_after_15 ? 0 : .15) +
      (a.external_noise === b.external_noise ? 0 : .13) +
      (a.late_meal === b.late_meal ? 0 : .04) +
      Math.abs(a.previous_sleep_minutes - b.previous_sleep_minutes) / 150 * .05;
    return Math.round(clamp((1 - distance) * 100, 0, 100));
  }

  function estimateCandidates(history, context) {
    return interventions.map(intervention => {
      const rows = history.filter(row => row.intervention_id === intervention.id)
        .map(row => ({ row, similarity: contextSimilarity(context, row.context) }))
        .sort((a, b) => b.similarity - a.similarity);
      const weighted = rows.reduce((acc, item) => {
        const weight = Math.pow(item.similarity / 100, 2) + .08;
        acc.sum += item.row.outcome_score * weight;
        acc.weight += weight;
        return acc;
      }, { sum: 0, weight: 0 });
      return {
        intervention_id: intervention.id,
        prior_nights: rows.length,
        predicted_outcome: weighted.weight ? Math.round(weighted.sum / weighted.weight * 10) / 10 : null,
        closest_nights: rows.slice(0, 3).map(item => ({ day: item.row.day, similarity: item.similarity })),
      };
    });
  }

  function chooseIntervention(history, context) {
    const estimates = estimateCandidates(history, context);
    if (history.length < exploration.length) {
      const id = exploration[history.length];
      return {
        id,
        mode: history.length < 5 ? 'initial exploration' : 'repeat for reliability',
        estimates,
        reason: history.length === 0
          ? 'No personal history yet. Start with the usual routine to establish a baseline.'
          : `Only ${history.length} earlier night${history.length === 1 ? '' : 's'} existed. Repeat the balanced starter sequence before personalizing.`,
      };
    }
    const counts = Object.fromEntries(interventions.map(item => [item.id, history.filter(row => row.intervention_id === item.id).length]));
    const leastCount = Math.min(...Object.values(counts));
    if (leastCount < 4) {
      const eligible = estimates.filter(item => item.prior_nights === leastCount).map(item => {
        const contextFit = item.intervention_id === 'pink' && context.external_noise ? 3
          : item.intervention_id === 'instrumental' && context.tension >= 6 ? 2
          : item.intervention_id === 'amber_music' && context.tension >= 6 ? 1.5
          : item.intervention_id === 'control' && context.tension <= 3 ? 1 : 0;
        return { ...item, value: (item.predicted_outcome ?? 65) + contextFit };
      }).sort((a,b)=>b.value-a.value);
      const selected=eligible[0];
      return {
        id:selected.intervention_id,
        mode:'balanced confirmation',
        estimates,
        reason:`Only ${leastCount} earlier ${byId[selected.intervention_id].short.toLowerCase()} nights existed. Collect another comparable night before allowing the model to favour a winner.`,
      };
    }
    const scored = estimates.map(item => {
      const predicted = item.predicted_outcome ?? mean(history.map(row => row.outcome_score)) ?? 65;
      const explorationBonus = 3.2 / Math.sqrt(Math.max(1, item.prior_nights));
      const contextBonus = item.intervention_id === 'pink' && context.external_noise ? 2.5
        : item.intervention_id === 'instrumental' && context.tension >= 6 ? 2
        : item.intervention_id === 'amber_music' && context.tension >= 6 ? 1.5
        : item.intervention_id === 'control' && context.tension <= 3 && !context.external_noise ? 1 : 0;
      return { ...item, decision_score: predicted + explorationBonus + contextBonus };
    }).sort((a, b) => b.decision_score - a.decision_score);
    const selected = scored[0];
    const closest = selected.closest_nights[0];
    return {
      id: selected.intervention_id,
      mode: selected.prior_nights < 3 ? 'targeted exploration' : 'contextual personalization',
      estimates,
      reason: closest
        ? `${selected.prior_nights} earlier ${byId[selected.intervention_id].short.toLowerCase()} night${selected.prior_nights === 1 ? '' : 's'} were available; Night ${closest.day} was the closest context (${closest.similarity}% similar).`
        : 'No directly comparable night existed, so this remains an exploration choice.',
    };
  }

  function interventionEffect(id, context) {
    if (id === 'amber') return 4.5 + context.tension * .35;
    if (id === 'instrumental') return context.tension >= 6 ? 8 : context.tension <= 3 ? 1.5 : 4.5;
    if (id === 'pink') return context.external_noise ? 7.5 : -1.5;
    if (id === 'amber_music') return context.tension >= 5 ? 9 : 5;
    return 0;
  }

  function buildResponse(day, id, context, effect) {
    const startHr = Math.round(62 + context.tension * 1.7 + (context.caffeine_after_15 ? 4 : 0) + ((day * 3) % 3));
    const baseDrop = { control: 2, amber: 5, instrumental: 5.5, pink: context.external_noise ? 5 : 1.5, amber_music: 7 }[id];
    const startMovement = Math.round(8 + context.tension * .7 + (context.late_meal ? 2 : 0));
    const movementDrop = { control: 4, amber: 6, instrumental: 6.5, pink: context.external_noise ? 6 : 3.5, amber_music: 8 }[id];
    const preliminaryDropAt20 = baseDrop * Math.pow(20 / 45, .8);
    const preliminaryMovementAt20 = startMovement - movementDrop * Math.pow(20 / 45, .72);
    const nudge = preliminaryDropAt20 < 2.2 && preliminaryMovementAt20 > 6.5;
    const finalDrop = baseDrop + context.tension * .18 + (nudge ? 1.1 : 0);
    const finalMovement = Math.max(.5, startMovement - movementDrop - (nudge ? .8 : 0));
    const minutes = [0,5,10,15,20,25,30,35,40,45];
    const heartRate = minutes.map((minute, index) => Math.round((startHr - finalDrop * Math.pow(minute / 45, .82) + Math.sin(day + index) * .45) * 10) / 10);
    const movement = minutes.map((minute, index) => Math.round(Math.max(.3, startMovement - (startMovement - finalMovement) * Math.pow(minute / 45, .7) + Math.cos(day + index) * .25) * 10) / 10);
    const stepScale = .75 + context.steps / 14000;
    const stepSlowdown = [Math.round(620*stepScale),Math.round(410*stepScale),Math.round(220*stepScale),Math.round(75*stepScale),Math.round(12*stepScale)];
    const calmScore = Math.round(clamp(48 + finalDrop * 4 + (startMovement-finalMovement) * 2 + effect * .8, 45, 96));
    return {
      minutes,
      heart_rate_bpm: heartRate,
      movement_events_per_minute: movement,
      heart_rate_start: heartRate[0],
      heart_rate_end: heartRate.at(-1),
      heart_rate_change: Math.round((heartRate.at(-1)-heartRate[0])*10)/10,
      movement_start: movement[0],
      movement_end: movement.at(-1),
      movement_change_percent: Math.round((1-movement.at(-1)/movement[0])*100),
      steps_18_to_22: stepSlowdown,
      calm_score: calmScore,
      gentle_nudge_at_minute_20: nudge,
    };
  }

  function simulateNight(day, history) {
    const context = contextFor(day, history.at(-1));
    const decision = chooseIntervention(history, context);
    const effect = interventionEffect(decision.id, context);
    const response = buildResponse(day, decision.id, context, effect);
    const contextBase = 64 + Math.min(context.active_minutes, 45) * .09 - context.tension * .9
      - (context.caffeine_after_15 ? 6 : 0) - (context.late_meal ? 3 : 0) - (context.external_noise ? 2 : 0)
      + clamp((context.previous_sleep_minutes - 390) / 30, -2, 3);
    const outcome = Math.round(clamp(contextBase + effect + response.calm_score * .055 + outcomeNoise[day-1], 50, 94));
    const sleepMinutes = Math.round(clamp(392 + outcome * .43 + effect * 1.5 - (context.caffeine_after_15 ? 18 : 0) + outcomeNoise[(day+6)%30]*2, 370, 485));
    const morningQuality = Math.round(clamp(4.2 + (outcome-50)/10 + outcomeNoise[(day+11)%30]*.08, 4, 9.5)*10)/10;
    const allMatches = history.map(row => ({ day: row.day, similarity: contextSimilarity(context,row.context), intervention_id: row.intervention_id, outcome_score: row.outcome_score, calm_score: row.response.calm_score }))
      .sort((a,b)=>b.similarity-a.similarity);
    return {
      day,
      date: `2026-07-${String(day).padStart(2,'0')}`,
      context,
      decision: {
        history_count: history.length,
        history_used_through_day: history.length ? history.at(-1).day : 0,
        mode: decision.mode,
        reason: decision.reason,
        candidate_estimates: decision.estimates,
        closest_contexts: allMatches.slice(0,3),
      },
      intervention_id: decision.id,
      intervention_label: byId[decision.id].label,
      response,
      outcome_score: outcome,
      sleep_minutes: sleepMinutes,
      morning_quality: morningQuality,
    };
  }

  function generateThirtyNights() {
    const nights = [];
    for (let day=1;day<=30;day++) nights.push(simulateNight(day,nights));
    return nights;
  }

  function matchedPairs(nights) {
    const pairs=[];
    for(let i=0;i<nights.length;i++) for(let j=i+1;j<nights.length;j++) {
      if(nights[i].intervention_id===nights[j].intervention_id) continue;
      const similarity=contextSimilarity(nights[i].context,nights[j].context);
      if(similarity<78) continue;
      pairs.push({
        day_a:nights[i].day,day_b:nights[j].day,similarity,
        intervention_a:nights[i].intervention_id,intervention_b:nights[j].intervention_id,
        calm_a:nights[i].response.calm_score,calm_b:nights[j].response.calm_score,
        outcome_a:nights[i].outcome_score,outcome_b:nights[j].outcome_score,
        hr_change_a:nights[i].response.heart_rate_change,hr_change_b:nights[j].response.heart_rate_change,
      });
    }
    return pairs.sort((a,b)=>b.similarity-a.similarity || Math.abs(b.outcome_a-b.outcome_b)-Math.abs(a.outcome_a-a.outcome_b)).slice(0,12);
  }

  function interventionSummary(nights) {
    return interventions.map(intervention=>{
      const rows=nights.filter(row=>row.intervention_id===intervention.id);
      return {...intervention,n:rows.length,mean_outcome:Math.round(mean(rows.map(row=>row.outcome_score))*10)/10,mean_calm:Math.round(mean(rows.map(row=>row.response.calm_score))*10)/10,mean_hr_change:Math.round(mean(rows.map(row=>row.response.heart_rate_change))*10)/10};
    }).sort((a,b)=>b.mean_outcome-a.mean_outcome);
  }

  function nextTenPlan(nights) {
    const summary=interventionSummary(nights),best=summary[0],runner=summary[1];
    return Array.from({length:10},(_,index)=>{
      const day=31+index;
      let intervention=index%5===4?'control':index%3===2?runner.id:best.id;
      if(index===7) intervention='pink';
      return {day,intervention_id:intervention,intervention_label:byId[intervention].label,purpose:intervention==='control'?'Keep a comparison night':intervention==='pink'?'Use only if external noise is present':intervention===best.id?'Confirm the current leader in a new context':'Check whether the runner-up remains useful',collect:['pre-bed context','45-min heart-rate response','movement/stillness response','sleep duration','morning quality'],nudge_rule:'At most one opt-in breathing haptic at minute 20 if both heart rate and movement have not begun settling.'};
    });
  }

  function buildDataset() {
    const nights=generateThirtyNights();
    return {schema_version:2,data_status:'synthetic_demo',model:'prefix-only contextual experiment simulation',no_future_data:true,generated_at:'2026-07-18T22:00:08+08:00',interventions,nights,matched_pairs:matchedPairs(nights),intervention_summary:interventionSummary(nights),next_ten_plan:nextTenPlan(nights),capability_note:{currently_installed_watch:'Scheduled heart-rate window and summary',simulated_extension:'Intervention markers, movement/stillness series, step slowdown and opt-in haptic cue are demonstration fields, not current live watch data.'}};
  }

  return {interventions,contextSimilarity,estimateCandidates,chooseIntervention,simulateNight,generateThirtyNights,matchedPairs,interventionSummary,nextTenPlan,buildDataset};
});
