import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

# Environment variables loading
load_dotenv()

# Groq Client Initialize 
try:
    client = Groq(
        api_key=os.getenv("GROQ_API_KEY")
    )
except Exception:
    client = None

def parse_expense_with_ai(user_text):
    """
    Groq (Llama 3) use for text to structured JSON.
    """
    if not client:
        print("Groq Client not initialized. Check API Key.")
        return None

    try:
        #Prompt for better consistency
        prompt = f"""
        Extract expense details from this text: "{user_text}"
        
        Return ONLY a raw JSON object (no markdown, no backticks) with this exact format:
        {{
            "item": "capitalized name of item",
            "amount": numeric_value,
            "category": "Food/Transport/Shopping/Bills/Health/Entertainment/Education/Housing/Others"
        }}
        
        Rules:
        1. If currency symbol (Rs, $, etc) is present, strip it. Use only numbers.
        2. Categorize intelligently. If not clear, use "Others".
        3. Do NOT add any explanation, preambles, or markdown formatting. Just the JSON string.
        4. If multiple amounts are mentioned, sum them up if they belong to the same logical expense, or pick the main one.
        """

        # Groq API Call
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise JSON extractor. You output only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile", 
            temperature=0.1, 
        )

        # Response handling
        res_text = chat_completion.choices[0].message.content.strip()

        # Regex to extract JSON if there's extra text
        json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if json_match:
            res_text = json_match.group(0)

        # String ko JSON dictionary mein convert karna
        data = json.loads(res_text)
        
        # Validate data types
        if 'amount' in data:
            if isinstance(data['amount'], str):
                # cleanup string amount
                 data['amount'] = float(re.sub(r'[^\d.]', '', data['amount']))
        
        return data

    except json.JSONDecodeError:
        print(f"JSON Decode Error. Raw text: {res_text}")
        return None
    except Exception as e:
        print(f"Groq AI Error: {e}")
        return None

def get_ai_budget_advice(expenses_summary):
    """
    Generates a personalized budget advice tip based on spending summary.
    summary format: [{'category': 'Food', 'total': 5000}, ...]
    """
    if not client:
        return "AI client not initialized."
        
    try:
        # Construct a readable summary string
        summary_text = ", ".join([f"{item['category']}: {item['total']}" for item in expenses_summary])
        
        prompt = f"""
        Analyze this monthly spending breakdown: {summary_text}.
        
        Provide ONE short, specific, and actionable savings tip (max 2 sentences).
        Focus on the highest spending category.
        Example: "You spent 40% on Food. diverse cooking at home could save you Rs. 3000."
        Do NOT be generic. Be direct and helpful.
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "You are a financial advisor giving brief, actionable tips."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=100,
        )
        
        return chat_completion.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"AI Advice Error: {e}")
        return "Could not generate advice at this time."