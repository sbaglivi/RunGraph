import utils
import models
from langchain.messages import HumanMessage, AIMessage

def is_beginner(state: models.State):
    prompt = utils.prompt("""
        Welcome, and pleasure to meet you. I'm placeholder, your new running coach!
        Are you new to running? Please answer with a yes or no
    """)
    print(prompt)
    update = {"messages": [AIMessage(prompt)]}
    if utils.yes_or_no():
        update["messages"] += [HumanMessage(content="yes")]
        update["user_level"] = "beginner"
    else:
        update["messages"] += [HumanMessage(content="no")]
        update["user_level"] = "advanced"
    return update

def get_user_info(state: models.State):
    print("Running coach: ", end="")
    print(state.messages[-1].content)
    user_input = input("Your response: ")
    return {
        "messages": [HumanMessage(content=user_input)]
    }

def get_plan_feedback(state: models.State):
    print("Here's the plan that I propose to reach your goal:")
    print(state.plan.content)
    print(state.plan.explanation)
    print("does this look okay to you?")
    if utils.yes_or_no():
        return {"plan_accepted": True}
    
    response = input("what does not satisfy you?")
    return {"plan_messsages": HumanMessage(content=response)}
    
