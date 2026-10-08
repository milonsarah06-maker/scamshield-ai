import json
import time
import streamlit as st
from google import genai
from google.genai import types

# Put your Gemini model ID here
MODEL = "gemini-3.1-flash-lite"


SYSTEM = """You are a cyber-fraud analyst helping Indian users.

The user will paste ONE SMS, WhatsApp message or email.

Analyze the message and reply ONLY with ONE valid JSON object.

Use exactly this format:

{
  "verdict": "SCAM",
  "confidence": 95,
  "red_flags": ["Urgency", "Threat", "Unknown phone number"],
  "what_to_do": ["Do not call the number", "Do not share personal information"]
}

The verdict MUST be exactly one of:
SCAM
SUSPICIOUS
SAFE

Confidence must be a number from 0 to 100.

red_flags must be a list of short strings.

what_to_do must be a list of short action steps.

If you are unsure, use SUSPICIOUS.

Never ask the user for personal data.
"""


# Connect to Gemini
client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


def analyse(message, retries=3):

    for attempt in range(retries):

        try:

            reply = client.models.generate_content(
                model=MODEL,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            result = json.loads(reply.text)

            # Make sure Gemini returned an object
            if isinstance(result, list):

                if len(result) > 0:
                    result = result[0]
                else:
                    return {"error": "Gemini returned an empty result."}

            return result

        except Exception as error:

            if attempt < retries - 1:
                time.sleep(2 ** attempt)

            else:
                return {"error": str(error)}


# Page settings
st.set_page_config(
    page_title="ScamShield AI",
    page_icon="🛡️"
)


st.title("🛡️ ScamShield AI")

st.caption(
    "Paste a suspicious message. Do not paste real personal data."
)


# History
if "history" not in st.session_state:
    st.session_state.history = []


# Message input
text = st.text_area(
    "Message to check",
    height=150
)


# Check button
if st.button("Check message") and text.strip():

    with st.spinner("Checking..."):

        result = analyse(text)


    if "error" in result:

        st.error(
            "Could not check right now: "
            + result["error"]
        )

    else:

        st.session_state.history.append(
            (
                text[:60],
                result["verdict"]
            )
        )

        st.subheader(
            f"Verdict: {result['verdict']} "
            f"({result['confidence']}%)"
        )


        st.write("### 🚩 Red flags")

        for flag in result["red_flags"]:
            st.write(f"- {flag}")


        st.write("### 🛡️ What to do")

        for step in result["what_to_do"]:
            st.write(f"- {step}")


        st.info(
            "In India, report cyber fraud at "
            "cybercrime.gov.in or call 1930."
        )


# History section
if st.session_state.history:

    st.divider()

    st.write("### Checked in this session")

    for preview, verdict in st.session_state.history:

        st.write(
            f"- {verdict}: {preview}..."
        )