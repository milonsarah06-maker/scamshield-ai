import json
import time
import pandas as pd
import tomllib
from google import genai
from google.genai import types

MODEL = "gemini-3.1-flash-lite"

# Read Gemini API key
with open(".streamlit/secrets.toml", "rb") as f:
    key = tomllib.load(f)["GEMINI_API_KEY"]

client = genai.Client(api_key=key)

# Read system prompt
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM = f.read()

# Read test messages
data = pd.read_csv("tests.csv")

predictions = []

print(f"Testing {len(data)} messages...\n")

for i, message in enumerate(data["message"], start=1):

    print(f"Testing message {i}/{len(data)}...")

    success = False

    for attempt in range(3):

        try:
            reply = client.models.generate_content(
                model=MODEL,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    response_mime_type="application/json",
                ),
            )

            result = json.loads(reply.text)
            prediction = result["verdict"]

            predictions.append(prediction)

            print(f"Prediction: {prediction}\n")

            success = True
            break

        except Exception as e:

            error_text = str(e)

            if "429" in error_text:
                print("Quota exceeded. Stopping evaluation.")
                raise

            if "503" in error_text:
                print(f"Temporary 503 error. Retry {attempt + 1}/3...")
                time.sleep(20)
            else:
                print(f"Error: {e}")
                break

    if not success:
        print("Could not classify this message.")
        predictions.append("ERROR")

    time.sleep(7)


# Add predictions
data["predicted"] = predictions

# Calculate accuracy only for successful predictions
valid = data["predicted"] != "ERROR"

if valid.any():
    accuracy = (
        data.loc[valid, "predicted"] == data.loc[valid, "expected"]
    ).mean() * 100

    print("\n==============================")
    print(f"Accuracy: {accuracy:.1f}%")
    print("==============================")

print("\nConfusion Matrix:")
print(pd.crosstab(data["expected"], data["predicted"]))

# Save results
data.to_csv("results.csv", index=False)

print("\nResults saved to results.csv")