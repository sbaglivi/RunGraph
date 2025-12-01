import models
import nodes
from langchain_core.messages import HumanMessage, AIMessage

def umsg(content: str) -> HumanMessage:
    return HumanMessage(content=content)

def amsg(content: str) -> AIMessage:
    return AIMessage(content=content)

def test_interviewer_node():
    print("Running test_interviewer_node...")
    state = models.State(
        user_level="advanced",
        messages=[
            umsg("I usually run about 30 miles a week, and I want to train for a half marathon in 3 months."),
        ]
    )
    response = nodes.interviewer(state)
    assert isinstance(response["messages"], AIMessage), "Interviewer should return an AIMessage"
    print("PASS")

def test_extractor_node():
    print("Running test_extractor_node...")
    state = models.State(
        user_level="advanced",
        messages=[
            umsg("I usually run about 30 miles a week, and I want to train for a half marathon in 3 months."),
            amsg("Got it, 30 miles a week is a solid base! Since you’re aiming for a half marathon, let’s discuss your training frequency. How many days per week do you plan to run?"),
            umsg("I can run about 4 days a week."),
        ]
    )
    response = nodes.extractor(state)
    # Check if days_per_week was extracted
    assert response.get("days_per_week") == 4, f"Expected 4 days per week, got {response.get('days_per_week')}"
    print("PASS")

def test_extractor_node_incomplete_data():
    print("Running test_extractor_node_incomplete_data...")
    state = models.State(
        user_level="advanced",
        messages=[
            umsg("I usually run about 30 miles a week, and I want to train for a half marathon in 3 months."),
            amsg("Got it, 30 miles a week is a solid base! Have you ran any recent race? This will help me understand your current fitness level"),
            umsg("I've ran my first marathon, around a month ago"),
        ]
    )
    response = nodes.extractor(state)
    recent_race = response.get("recent_race")
    assert recent_race, f"model should have created data for a recent race: {recent_race}"
    # The user didn't specify a time, so finish_time should be None
    assert recent_race.get("finish_time") is None, f"recent race finish time should be None, got: {recent_race.get('finish_time')}"
    print("PASS")

def test_verifier_node_coherent():
    print("Running test_verifier_node_coherent...")
    # A coherent beginner profile
    state = models.State.beginner(
        msgs=[], 
        activity_level="active", 
        age=25, 
        injury_history=[], 
        days_per_week=3, 
        goal=models.Goal(type="5k", target_date=models.RaceDate(relative="in 3 months"))
    )
    response = nodes.verifier(state)
    check = response.get("coherence_check")
    assert check.ok, f"Expected coherent check to be True, got {check}"
    print("PASS")

def test_incoherent_plan():
    print("Running test_incoherent_plan...")
    msgs=[
        umsg("Hi, I've basically never ran since I was a teenager, so I'm a beginner"),
        amsg("Got it, good job on choosing to start running! What's your current activity level? Do you practice any other sport?"),
        umsg("Up to last year I went to the gym once or twice a week, this year I've been busy so I haven't done much"),
        amsg("Understood, sometimes it's hard to find time for exercise. What's your age?"),
        umsg("I'm 40"),
        amsg("Nice, you have plenty of time to get fit! Are you currently dealing with any injury or pain?"),
        umsg("My right knee often hurts, right under the rotula. Also sometimes I get back pain, probably from sitting too much."),
        amsg("Sorry to hear that, many people health improves after they start being more active. Do you have a specific goal in mind - like a race that you'd like to participate in - or are you just looking to improve your fitness?"),
        umsg("I'd like to run a marathon, a month from now"),
    ]
    state = models.State.beginner(
        msgs, "sedentary", 40, ["pain under the right knee", "low back pain sometimes"], 
        3, models.Goal(type="marathon", target_date=models.RaceDate(relative="in a month"))
    )
    response = nodes.verifier(state)
    check = response.get("coherence_check")
    assert not check.ok, f"Expected coherence check to be False for marathon in 1 month for sedentary beginner, got {check}"
    print("PASS")

def test_workout_planner():
    print("Running test_workout_planner...")
    # Setup a complete state for a beginner
    plan = models.Plan(
        explanation="We will start slow with run/walk intervals.",
        content="Week 1: 3 days of run/walk. Day 1: 20 mins. Day 2: Rest. Day 3: 25 mins."
    )
    state = models.State.beginner(
        msgs=[],
        activity_level="sedentary",
        age=30,
        injury_history=[],
        days_per_week=3,
        goal=models.Goal(type="5k", target_date=models.RaceDate(relative="in 2 months"))
    )
    state.plan = plan
    state.plan_accepted = True
    
    response = nodes.workout_planner(state)
    schedule = response.get("schedule")
    
    assert schedule is not None, "Workout planner should return a schedule"
    # Check if it's a BeginnerSchedule (has workouts list)
    assert hasattr(schedule, "workouts"), "Schedule should have workouts"
    assert len(schedule.workouts) > 0, "Schedule should have at least one workout"
    print("PASS")

def main():
    print("Starting tests...")
    try:
        test_interviewer_node()
        test_extractor_node()
        test_extractor_node_incomplete_data()
        test_verifier_node_coherent()
        test_incoherent_plan()
        test_workout_planner()
        print("\nAll tests passed successfully!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()