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
system_prompt = """You are an agent that can use a calculator tool.
You must ALWAYS use the calculator for any math, even simple math. Never compute math yourself.

Example:
User: What is 5 times 3?
You: ACTION: calculator INPUT: 5 * 3

If you already know the final answer with no math involved, respond:
FINAL ANSWER: <your answer>

Respond with ONLY one of these two formats, nothing else."""

question = "What is 8734 times 92, divided by 17?"

response = client.chat.completions.create(
model="openai/gpt-oss-120b",
messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": question}
],
temperature=0,
) 

print("Response:", response.choices[0].message.content)



output = response.choices[0].message.content

if output.startswith("ACTION:"):
    expression = output.split("INPUT:")[1].strip()
    result = calculator(expression)
    print("Tool used. Calculator result:", result)
else:
    print("Model answered directly:", output)