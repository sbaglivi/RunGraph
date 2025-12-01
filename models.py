from pydantic import BaseModel, Field, create_model
from typing import Literal, Annotated
from datetime import datetime
from langgraph.graph.message import add_messages, AnyMessage

def iter_populated_fields(model: BaseModel):
    for name, value in model.model_dump(exclude_none=True).items():
        yield name, value

type Weekday = Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

class RaceDate(BaseModel):
    absolute: datetime | None = Field(
        default=None,
        description="Absolute date in ISO 8601 format, only if the user provided an explicit date (e.g. '2023-10-12', 'October 2023', 'on May 5th')."
    )
    relative: str | None = Field(
        default=None,
        description="The raw relative expression from the user (e.g. 'about a month ago', 'last summer'). Do NOT convert it; copy it as given, with minimal normalization."
    )

    def __repr__(self):
        if self.absolute:
            return f"on or before {self.absolute}"
        
        return self.relative

class Goal(BaseModel):
    type: Literal["5k", "10k", "half_marathon", "marathon", "fitness", "lose weight"]
    target_date: RaceDate | None = Field(
        default=None,
        description="Date by which user would like to accomplish the goal. If the user gave an absolute date, fill 'absolute'. If they gave a relative date, fill 'relative'."
    )
    target_time: float | None = None # minutes


    def __repr__(self):
        curr = f"has a goal of {self.type}"
        if self.target_date:
            curr += str(self.target_date)
        if self.target_time:
            curr += f"with a time of {self.target_time}"
            
        return curr

class RunTime(BaseModel):
    day: Weekday
    time_of_day: Literal["morning", "afternoon", "evening"]

class BaseUserProfile(BaseModel):
    preferred_distance_unit: Literal["miles", "kilometers"] | None
    goal: Goal | None
    age: int | None
    injury_history: list[str] | None
    days_per_week: int | None
    preferred_run_times: list[RunTime] | None

class BeginnerUserProfile(BaseUserProfile):
    starting_intensity_level: Literal["run", "run/walk", "walk"] | None = None
    activity_level: str | None

class Race(BaseModel):
    distance: Literal["5k", "10k", "half_marathon", "marathon"]
    finish_time: float | None = Field(None, description="time in minutes that it took to complete the race")
    date: RaceDate | None = Field(
        default=None,
        description="Date of the race. If the user gave an absolute date, fill 'absolute'. If they gave a relative date, fill 'relative'."
    )

class AdvancedUserProfile(BaseUserProfile):
    distance_per_week: float | None
    recent_race: Race | None

class State(BaseModel):
    preferred_distance_unit: Literal["miles", "kilometers"] | None = None
    goal: Goal | None = None
    age: int | None = None
    injury_history: list[str] | None = None
    days_per_week: int | None = None
    # timing_preferences: str | None = Field(None, description="specific days and rough times at which user is available to train e.g. All morning on weekdays, every other day, I have time for a long run only on sunday")

    # beginner
    activity_level: str | None = None
    starting_intensity_level: Literal["run", "run/walk", "walk"] = "run"
    # intermediate
    distance_per_week: float | None = None
    recent_race: Race | None = None

    # state
    messages: Annotated[list[AnyMessage], add_messages]
    plan_messages: Annotated[list[AnyMessage], add_messages] = []
    user_level: Literal["beginner", "advanced", "unknown"] = "unknown"
    coherence_check: "CoherenceCheck | None" = None
    awaiting_fields: list[str] = []
    failure_count: int = 0
    user_change_response: "UserChangeResponse | None" = None
    plan: "Plan | None" = None
    plan_accepted: bool = False
    weekly_schedule: "Schedule | None" = None

    @classmethod
    def beginner(cls, msgs, activity_level: str, age: int, injury_history: list[str], days_per_week: int, goal: Goal, preferred_unit: str = "kilometers"):
        return cls(user_level="beginner", messages=msgs, activity_level=activity_level, age=age, injury_history=injury_history, days_per_week=days_per_week, goal=goal, preferred_distance_unit=preferred_unit)

class ChangeableFields(BaseModel):
    goal: Goal | None = None
    days_per_week: int | None = None
    starting_intensity_level: Literal["run", "run/walk", "walk"] | None = None

    def to_lines(self) -> str:
        items = (
            f"- {k}: {v!s}"
            for k, v in self.model_dump().items()
            if v is not None
        )
        return "\n".join(items)

class UserChangeResponse(BaseModel):
    accept: bool
    new_proposal: ChangeableFields | None = None
    
class WeeklyPreferences(BaseModel):
    run_times: list[RunTime]

class TriageResult(BaseModel):
    reasoning: str = Field(..., description="Explain why you think the user is a beginner or advanced based on their message.")
    user_level: Literal["beginner", "advanced", "unknown"] = Field(..., description="The classification of the user.")

class CoherenceCheck(BaseModel):
    ok: bool
    reasoning: str
    suggested_changes: ChangeableFields | None = None

def build_info_request_model(allowed_fields: list[str]):
    # Literal must receive literals, not a list
    AwaitingLiteral = Literal[tuple(allowed_fields)]

    InfoRequest = create_model(
        "InfoRequest",
        question=(str, ...),
        awaiting_fields=(list[AwaitingLiteral], ...)
    )

    return InfoRequest

class Duration(BaseModel):
    type: Literal["time", "distance"]
    value: float
    measurement_unit: Literal["minutes", "km", "mile"]

    def __str__(self):
        return f"{self.value} {self.measurement_unit}"

class Pace(BaseModel):
    mins_per_unit: str = Field(pattern=r'^\d{1,2}:\d{2}$')
    measurement_unit: Literal["km", "mile"]
    range: float = Field(..., description="how narrow or large the band around the value should be in seconds. E.g. pace is 4:30 +- 10 seconds")

    def __str__(self):
        return f"{self.mins_per_unit} min/{self.measurement_unit} (+/- {self.range}s)"

class Segment(BaseModel):
    duration: Duration
    pace: Pace

    def __str__(self):
        return f"Run for {self.duration} at {self.pace}"

class Workout(BaseModel):
    day: Weekday
    notes: str | None = Field(None, description="details the user should pay attention to while performing the workout")

class AdvancedWorkout(Workout):
    segments: list[Segment]

    def __str__(self):
        segments_str = "\n".join([f"  - {s}" for s in self.segments])
        base = f"**{self.day}**:\n{segments_str}"
        if self.notes:
            base += f"\n  *Note: {self.notes}*"
        return base

class BeginnerWorkout(Workout):
    description: str

    def __str__(self):
        base = f"**{self.day}**: {self.description}"
        if self.notes:
            base += f"\n  *Note: {self.notes}*"
        return base

class BeginnerSchedule(BaseModel):
    workouts: list[BeginnerWorkout]

    def __str__(self):
        return "\n\n".join([str(w) for w in self.workouts])

class AdvancedSchedule(BaseModel):
    workouts: list[AdvancedWorkout]

    def __str__(self):
        return "\n\n".join([str(w) for w in self.workouts])

Schedule = BeginnerSchedule | AdvancedSchedule

class Plan(BaseModel):
    explanation: str = Field(..., description="what the plan aims to do and how, if the user is a beginner, this is also where you should explain unfamiliar terms")
    content: str = Field(..., description="the actual content of the plan")
