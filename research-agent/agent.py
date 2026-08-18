system_prompt = """You are an agent with access to 3 tools:
- calculator: for math expressions
- unit_converter: for converting between km and miles
- web_search: for factual lookup questions

Always use a tool if the question needs one. Respond in ONE of these formats:
ACTION: calculator INPUT: <math expression>
ACTION: unit_converter INPUT: <value and units, e.g. "10 km to miles">
ACTION: web_search INPUT: <search query>
FINAL ANSWER: <answer, only if no tool is needed>

Examples:
User: What is 12 times 4?
You: ACTION: calculator INPUT: 12 * 4

User: Convert 5 miles to km
You: ACTION: unit_converter INPUT: 5 miles to km

User: What is the capital of France?
You: ACTION: web_search INPUT: capital of france

Respond with ONLY one line in one of these formats, nothing else."""


def unit_converter(query):
    # Simple version: km to miles, or miles to km
    try:
        parts = query.lower().split()
        value = float(parts[0])
        if "km" in query and "mile" in query:
            return f"{value * 0.621371} miles"
        elif "mile" in query and "km" in query:
            return f"{value * 1.60934} km"
        else:
            return "Unsupported conversion"
    except Exception as e:
        return f"Error: {e}"

print(unit_converter("10 km to miles"))


def web_search(query):
    query_lower = query.lower().strip()
    if "japan" in query_lower and "population" in query_lower:
        return "Japan's population is approximately 123 million."
    if "france" in query_lower and "capital" in query_lower:
        return "The capital of France is Paris."
    return "No results found for that search."

print(web_search("capital of france"))


def calculator(expression):
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

print(calculator("47 * 89 + 12"))


from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

question = "What is the population of Japan divided by 1000, then multiplied by 7?"

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": question}
]

max_steps = 5

for step in range(max_steps):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0
    )

    output = response.choices[0].message.content
    print(f"\n--- Step {step + 1} ---")
    print("Model said:", output)

    messages.append({"role": "assistant", "content": output})

    if output.startswith("FINAL ANSWER:"):
        print("\nDone:", output)
        break

    elif output.startswith("ACTION:"):
        tool_name = output.split("ACTION:")[1].split("INPUT:")[0].strip()
        tool_input = output.split("INPUT:")[1].strip()

        if tool_name == "calculator":
            result = calculator(tool_input)
        elif tool_name == "unit_converter":
            result = unit_converter(tool_input)
        elif tool_name == "web_search":
            result = web_search(tool_input)
        else:
            result = f"Unknown tool: {tool_name}"

        print("Tool used:", tool_name, "-> Result:", result)

        messages.append({"role": "user", "content": f"OBSERVATION: {result}"})



# question = "Convert 1 mile to km?"

# response = client.chat.completions.create(
# model="openai/gpt-oss-120b",
# messages=[
#     {"role": "system", "content": system_prompt},
#     {"role": "user", "content": question}
# ],
# temperature=0,
# ) 

# print("Response:", response.choices[0].message.content)



# output = response.choices[0].message.content

# if output.startswith("ACTION:"):
#     tool_name = output.split("ACTION:")[1].split("INPUT:")[0].strip()
#     tool_input = output.split("INPUT:")[1].strip()

#     if tool_name == "calculator":
#         result = calculator(tool_input)
#     elif tool_name == "unit_converter":
#         result = unit_converter(tool_input)
#     elif tool_name == "web_search":
#         result = web_search(tool_input)
#     else:
#         result = f"Unknown tool: {tool_name}"

#     print("Tool used:", tool_name)
#     print("Result:", result)
# else:
#     print("Model answered directly:", output)