# classifier.py
import os
from litellm import completion

def classify_complexity(user_prompt: str) -> str:
    """Uses a tiny model to tag the incoming prompt."""
    system_instruction = (
        "Classify the complexity of the following prompt as 'simple', 'medium', or 'hard'. "
        "'simple' = basic facts/greeting. 'medium' = logic/summarization. 'hard' = complex coding/math."
        "Respond with ONLY the word."
    )
    
    # We use a cheap/fast model like Phi-3 via Ollama or a small cloud model
    response = completion(
        model="ollama/phi3", 
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content.lower().strip()