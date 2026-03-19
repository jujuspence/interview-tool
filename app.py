from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Streamlit Chatbot", page_icon=":robot_face:")
st.title("AI Interviewer")   

#Initialize session state variables
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
#Store msg history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:

    st.subheader("Personal Information", divider='rainbow')

    #check if elements in sesh state are initialized
    if "name" not in st.session_state:
        st.session_state.name = ""
    if "experience" not in st.session_state:
        st.session_state.experience = ""
    if "skills" not in st.session_state:
        st.session_state.skills = ""

    st.session_state.name = st.text_input(label="Name", max_chars = 35, placeholder= "Enter your name")

    st.session_state.experience = st.text_area(label="Experience", value = "", height=None, max_chars=200, placeholder="Describe your experience")

    st.session_state.skills = st.text_area(label="Skills", value = "", height=None, max_chars=200, placeholder="List your skills")

    st.subheader("Company and Position", divider='rainbow')

    if "level" not in st.session_state:
        st.session_state.level = ""
    if "position" not in st.session_state:
        st.session_state.position = ""
    if "company" not in st.session_state:
        st.session_state.company = ""

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.level = st.radio(
            "Choose level",
            key="visibility",
            options=["Junior", "Mid Level", "Senior"],

        )

    with col2:
        st.session_state.position = st.selectbox(
            "Choose position",
            ("Data Scientist", "Data Analyst", "Machine Learning Engineer", "Financial Analyst", "Data Engineer", "Business Analyst", "AI Researcher"),
        )

    st.session_state.company = st.selectbox(
        "Choose company",
        ("Amazon", "Meta", "Udemy", "Google", "Microsoft", "Apple", "Netflix"),
    )

    st.write(f"**Your information**: {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}")

    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")


if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info("""
        Start by introducing yourself.
            """,
            icon = "👋")

    client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4"

    if not st.session_state.messages:
        st.session_state.messages = [{ "role": "system", "content": f"You are Rick, a strict HR executive working at {st.session_state['company']}. You are interviewing {st.session_state['name']} with experience {st.session_state['experience']} and skills {st.session_state['skills']}. You should interview them for the position {st.session_state['level']} {st.session_state['position']} at your company." }]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer", max_chars = 1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state.openai_model,
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True, 
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})    
            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True
        

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    st.info("""
        Interview complete! Click the button below to receive feedback on your performance.
            """,
            icon = "✅")
    if st.button("Show Feedback", on_click=show_feedback):
        st.write("Generating feedback...")

if st.session_state.feedback_shown:
    st.subheader("Feedback", divider='rainbow')

    conversation_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m["role"] != "system"])

    feedback_client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"""You are a helpful tool that provides feedback on an interviewee performance.
              Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overall Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questions"""},
            {"role": "user", "content": f"This is the interview you need to evaluate. You are only a tool and shouldn't engage in conversation:\n{conversation_history}"}
        ]

    )

    st.write(feedback_completion.choices[0].message.content)

    #Restart interview by refreshing the page
    if st.button("Restart Interview", type = "primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")