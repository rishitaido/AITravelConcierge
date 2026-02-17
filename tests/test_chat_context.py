import requests
import json
import sys

BASE_URL = "http://localhost:8080/api/ask"

def test_chat_context():
    print("Testing chat context...")
    
    # 1. First message: "I want to go to Paris."
    history = []
    prompt1 = "I want to go to Paris."
    print(f"User: {prompt1}")
    
    try:
        resp1 = requests.post(BASE_URL, json={"prompt": prompt1, "history": history})
        resp1.raise_for_status()
        reply1 = resp1.json()["reply"]
        print(f"AI: {reply1[:100]}...")
        
        history.append({"role": "user", "content": prompt1})
        history.append({"role": "assistant", "content": reply1})
        
    except Exception as e:
        print(f"Failed step 1: {e}")
        return False

    # 2. Second message: "What is good to eat there?" (Context dependent)
    prompt2 = "What is good to eat there?"
    print(f"User: {prompt2}")
    
    try:
        resp2 = requests.post(BASE_URL, json={"prompt": prompt2, "history": history})
        resp2.raise_for_status()
        reply2 = resp2.json()["reply"]
        print(f"AI: {reply2[:100]}...")
        
        # Check if response mentions French food or Paris
        keywords = ["Paris", "French", "croissant", "baguette", "escargot", "macaron", "bistro", "cheese", "wine"]
        if any(k.lower() in reply2.lower() for k in keywords):
            print("SUCCESS: AI maintained context!")
            return True
        else:
            print("FAILURE: AI did not seem to understand context.")
            print(f"Full reply: {reply2}")
            return False
            
    except Exception as e:
        print(f"Failed step 2: {e}")
        return False

if __name__ == "__main__":
    if test_chat_context():
        sys.exit(0)
    else:
        sys.exit(1)
