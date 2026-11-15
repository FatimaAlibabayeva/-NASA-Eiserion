from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, Field, ConfigDict

Number = Annotated[float, Field(ge=0, le=100000, allow_inf_nan=False)]
class Model(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Profile(Model):
    name: str = Field(default='Alex Vega', min_length=1, max_length=80)
    age: int = Field(default=34, ge=18, le=100)
    height: float = Field(default=175, ge=100, le=250)
    weight: float = Field(default=75, ge=30, le=250)
    activity: Literal['low','moderate','high'] = 'moderate'
    condition: Literal['good','fatigued','limited'] = 'good'
    experience: Literal['beginner','intermediate','experienced'] = 'intermediate'
    mission_day: int = Field(default=42, ge=1, le=10000)
    recovery: int = Field(default=8, ge=1, le=10)

class Nutrition(Model):
    calories: Number | None = None
    protein: Number | None = None
    carbs: Number | None = None
    fat: Number | None = None
    calcium: Number | None = None
    vitamin_d: Number | None = None
    vitamin_c: Number | None = None
    magnesium: Number | None = None
    vitamin_k: Number | None = None

class Targets(Model):
    calories: float = Field(default=2200, ge=500, le=10000)
    protein_per_kg: float = Field(default=1.4, ge=0.8, le=2)
    carbs: float = Field(default=300, ge=1, le=2000)
    fat: float = Field(default=75, ge=1, le=1000)
    calcium: float = Field(default=1000, ge=1, le=5000)
    vitamin_d: float = Field(default=600, ge=1, le=10000)
    vitamin_c: float = Field(default=90, ge=1, le=5000)
    magnesium: float = Field(default=400, ge=1, le=2000)
    vitamin_k: float = Field(default=120, ge=1, le=2000)

class Exercise(Model):
    type: Literal['resistance','cycling','running','mobility'] = 'resistance'
    duration: float = Field(default=40, ge=0, le=300)
    intensity: int = Field(default=5, ge=1, le=10)
    sets: int = Field(default=3, ge=0, le=100)
    reps: int = Field(default=10, ge=0, le=1000)
    resistance: float = Field(default=20, ge=0, le=1000)
    status: Literal['completed','partial','not completed'] = 'completed'

class QUS(Model):
    id: str = Field(min_length=1, max_length=80)
    date: date
    sos: float = Field(ge=500, le=3000)
    bua: float = Field(ge=0, le=300)
    location: str = Field(default='Left heel', min_length=1, max_length=80)
    quality: Literal['good','questionable','poor'] = 'good'

class Day(Model):
    nutrition: Nutrition = Field(default_factory=Nutrition)
    exercise: Exercise | None = None

class Scenario(Model):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    profile: Profile = Field(default_factory=Profile)
    targets: Targets = Field(default_factory=Targets)
    days: dict[date, Day] = Field(default_factory=dict)
    qus: list[QUS] = Field(default_factory=list)
    overrides: dict[date, Exercise] = Field(default_factory=dict)

class Workspace(Model):
    scenarios: list[Scenario] = Field(min_length=1, max_length=30)

class Calculation(Model):
    scenario: Scenario
    date: date
