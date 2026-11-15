"""Transparent demonstration rules, not a physiological or clinical model."""
from datetime import timedelta
from models import Scenario, Day, Exercise

def workload(exercise):
    if exercise is None:
        return None
    factor = {'completed': 1, 'partial': .5, 'not completed': 0}[exercise.status]
    return round(exercise.duration * exercise.intensity * factor, 1)

def calculate(s: Scenario, day):
    record = s.days.get(day, Day())
    p, t, e = s.profile, s.targets, record.exercise
    intake = record.nutrition.model_dump()
    targets = t.model_dump(exclude={'protein_per_kg'})
    targets['protein'] = round(p.weight * t.protein_per_kg, 1)
    missing = [k for k,v in intake.items() if v is None]
    below = [k for k,v in intake.items() if v is not None and v < targets[k]]
    load = workload(e)
    reasons = []
    alerts = []
    base_duration = {'beginner':25, 'intermediate':40, 'experienced':50}[p.experience]
    multiplier = 1.0
    if missing:
        multiplier = min(multiplier, .7)
        alerts.append('Missing intake: ' + ', '.join(missing) + '. Nutritional adequacy cannot be confidently evaluated.')
        reasons.append('Missing nutrient information limits the proposed workout to 70% of the experience baseline.')
    if any(intake[k] is not None and intake[k] < targets[k] * .8 for k in ['calories','protein']):
        multiplier = min(multiplier, .6)
        reasons.append('Recorded energy or protein is below 80% of its configured target: workout duration limited to 60%.')
    if p.recovery <= 4 or p.condition != 'good':
        multiplier = min(multiplier, .5)
        reasons.append('Low recovery or a fatigued/limited condition: workout duration limited to 50%.')
    if load is not None and load > 400:
        multiplier = min(multiplier, .75)
        reasons.append('Previous workload exceeds 400 demonstration units: workout duration limited to 75%.')
    if load is None:
        alerts.append('Exercise information is missing; no exercise energy adjustment can be estimated.')
        multiplier = min(multiplier, .7)
        reasons.append('Missing exercise information limits the proposed workout to 70% of the experience baseline.')
    if not reasons:
        reasons.append('Recorded intake and recovery permit maintaining the experience-based workout baseline.')
    reasons.append(f'Experience baseline: {base_duration} minutes. Recorded workload: {load if load is not None else "unknown"} demonstration units; sets, reps and resistance are descriptive inputs, not additional energy estimates.')
    proposed = Exercise(type='mobility' if multiplier <= .5 else 'resistance', duration=round(base_duration*multiplier), intensity=3 if multiplier < 1 else 5, sets=2 if multiplier < 1 else 3, reps=10, resistance=0 if multiplier <= .5 else 10 if p.experience == 'beginner' else 20, status='not completed')
    type_factor = {'resistance':1, 'cycling':1.1, 'running':1.2, 'mobility':.4}
    energy = round((load or 0) * (type_factor[e.type] if e else 0) * .8)
    activity = {'low':-150, 'moderate':0, 'high':150}[p.activity]
    tomorrow_targets = dict(targets)
    tomorrow_targets['calories'] = max(500, targets['calories'] + energy + activity)
    tomorrow_targets['carbs'] = round(targets['carbs'] + energy / 4, 1)
    reasons.append(f'Next-day energy = base {targets["calories"]:g} + activity {activity:+g} + exercise {energy:g} kcal. Exercise adjustment = duration × intensity × completion factor × type factor × 0.8; this is a demonstration heuristic, not measured expenditure.')
    reasons.append('Exercise energy is assigned to carbohydrate at 4 kcal/g; protein stays at the configured g/kg target. Micronutrient targets stay unchanged.')
    if e and e.status == 'partial':
        reasons.append('Partial completion counts as 50% of entered workload; use actual completed duration when possible.')
    if below:
        alerts.append('Below configured targets: ' + ', '.join(below) + '. This is an intake comparison, not a diagnosis.')
    history = sorted([q for q in s.qus if q.date <= day], key=lambda q:q.date)
    qus = {'latest': history[-1].model_dump(mode='json') if history else None, 'delta': None, 'note':'No QUS measurement on or before the selected date.'}
    if history:
        latest = history[-1]
        previous = [q for q in history[:-1] if q.location.casefold() == latest.location.casefold() and q.date < latest.date and q.quality == 'good']
        qus['note'] = 'QUS values are simulated. Device/protocol differences are unknown; changes cannot establish bone loss or BMD.'
        if previous and latest.quality == 'good':
            qus['delta'] = {'sos':round(latest.sos-previous[-1].sos,2), 'bua':round(latest.bua-previous[-1].bua,2)}
            qus['note'] += ' Difference shown against the previous good-quality entry at the same location.'
            qus['note'] += f' Recorded difference: SOS {qus["delta"]["sos"]:+g} m/s; BUA {qus["delta"]["bua"]:+g} dB/MHz.'
        else:
            qus['note'] += ' No comparable pair of good-quality measurements is available.'
        if latest.quality != 'good':
            alerts.append('Latest QUS quality is questionable or poor; trend interpretation is withheld.')
    macro = None if any(intake[k] is None for k in ['protein','carbs','fat']) else round(intake['protein']*4+intake['carbs']*4+intake['fat']*9)
    tomorrow = day + timedelta(days=1)
    override = s.overrides.get(tomorrow)
    return {'date':str(day), 'tomorrow':str(tomorrow), 'intake':intake, 'targets':targets, 'missing':missing, 'below':below, 'macro_calories':macro, 'workload':load, 'nutrition_plan':tomorrow_targets, 'proposed_workout':proposed.model_dump(), 'workout':(override or proposed).model_dump(), 'overridden':override is not None, 'reasons':reasons, 'alerts':alerts, 'qus':qus, 'summary':f'{len(below)} recorded nutrients below target; {len(missing)} missing. Tomorrow: {tomorrow_targets["calories"]:g} simulated kcal and {(override or proposed).duration:g} minutes of {(override or proposed).type}.', 'workload_history':[{'date':str(d), 'value':workload(r.exercise)} for d,r in sorted(s.days.items()) if d <= day][-14:]}
