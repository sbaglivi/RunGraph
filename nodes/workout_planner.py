import models
import utils

def workout_planner(state: models.State):
    prompt = utils.prompt(f"""
        You're an expert running coach. 
        Your job is to create a workout plan for the first week of the user training.
        This is an high level view of the plan it should respect: {state.plan.content}
        This is the user profile:
        {utils.format_user_info(state)}
    """)

    output = models.AdvancedSchedule
    if state.user_level == "beginner":
        output = models.BeginnerSchedule
        prompt += "\nThe user is a beginner, so try to keep language simple and explain the terms he might not be familiar with"
    
    workout_gpt = utils.gpt.with_structured_output(output)
    response = workout_gpt.invoke(utils.with_system_prompt([], prompt))
    print("Here's your schedule for the first week:")
    print(str(response))
    return {"schedule": response}