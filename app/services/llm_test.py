from app.services.llm import LLMService

llm = LLMService()
response = llm.generate_response(
    "explain pythoon in one sentence"
)

print("AI response : ")
print(response)