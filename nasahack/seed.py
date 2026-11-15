from datetime import date, timedelta
from models import Workspace, Scenario, Day, Nutrition, Exercise, QUS, Profile

def examples():
    today = date.today()
    scenarios = []
    for i, name in enumerate(['Balanced mission day', 'Low intake / demanding exercise', 'Increased workload']):
        s = Scenario(id=f'example-{i}', name=name, profile=Profile(name=['Alex Vega','Sam Orion','Jules Nova'][i]))
        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            low = i == 1 and offset == 0
            duration = (90 if i else 40) if offset == 0 else 30 + offset * 3
            s.days[day] = Day(nutrition=Nutrition(calories=1200 if low else 2500, protein=45 if low else 115, carbs=140 if low else 320, fat=40 if low else 80, calcium=600 if low else 1000, vitamin_d=300 if low else 600, vitamin_c=90, magnesium=400, vitamin_k=120), exercise=Exercise(duration=duration, intensity=8 if i and offset == 0 else 5, type='cycling' if i == 2 else 'resistance'))
        s.qus = [QUS(id=f'q{n}', date=today-timedelta(days=14-n*7), sos=1550-n*3, bua=85-n, location='Left heel', quality='good') for n in range(3)]
        scenarios.append(s)
    return Workspace(scenarios=scenarios)
