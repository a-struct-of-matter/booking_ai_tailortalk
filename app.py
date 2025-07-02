import streamlit as st
from agent import run_agent

# setting up streamlit functionalities

# You can re-enable this later once the core functionality works,
# and ensure the path to your image is absolutely correct or relative to the app.py file.
# st.set_page_config(page_title="Event Booking Bot", page_icon='/utilities/chat-bot.jpg')

st.title("TailorTalk Event Booking AI")
st.subheader("AI Bot to assists event Bookings in your Calendar!")

# setting up session states

# checking previous chat context
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("Ask me to check schedule or book an event in your calendar...")

# User messages validation
if user_input:
    st.chat_message("user").markdown(user_input)

    # --- CRITICAL CHANGE HERE ---
    # The agent_executor.invoke() returns a dictionary.
    # You need to extract the 'output' key for the actual response.
    raw_agent_response = run_agent(user_input)

    # This print helps confirm what `run_agent` is returning.
    print(f"DEBUG: Type of raw_agent_response: {type(raw_agent_response)}")
    print(f"DEBUG: Content of raw_agent_response: {raw_agent_response}")

    # Extract the actual output string
    if isinstance(raw_agent_response, dict) and "output" in raw_agent_response:
        display_response = raw_agent_response["output"]
    else:
        # Fallback if the structure is unexpected (e.g., if run_agent directly returns a string)
        display_response = str(raw_agent_response)

    # save context in session
    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("response", display_response))  # Store the extracted string

    st.chat_message("assistant").markdown(display_response)  # Display the extracted string

# previous chat
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)