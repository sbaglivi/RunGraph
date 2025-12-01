import models
import utils

def planner(state: models.State):
    prompt = utils.prompt(f"""
        You're an expert running coach. 
        Your job is to create a high level training plan (macrocycles) to help the user reach his goal.
        Do not get into the details of the individual workout session, describe mostly what the focus will be in a given cycle, and what kind of session (by intensity, duration, etc) the user can expect
        This is the user profile:
        {utils.format_user_info(state)}
    """)
    if state.user_level == "beginner":
        prompt += "\nThe user is a beginner, so try to keep language simple and explain the terms he might not be familiar with"
    
    plan_gpt = utils.gpt.with_structured_output(models.Plan)
    response = plan_gpt.invoke(utils.with_system_prompt(state.plan_messages, prompt))
    return {"plan": response}