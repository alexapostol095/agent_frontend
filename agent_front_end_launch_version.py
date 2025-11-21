import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole

# ============================================================
# 1️⃣ Load config from Streamlit Secrets
# ============================================================

PROJECT_ENDPOINT = st.secrets["PROJECT_ENDPOINT"]
PROJECT_API_KEY = st.secrets["PROJECT_API_KEY"]

PRICE_MONITORING_AGENT_ID = st.secrets["AGENT_PRICE_MONITORING"]
COMP_GAP_AGENT_ID = st.secrets["AGENT_COMP_GAP"]

# ============================================================
# 2️⃣ Create Azure Agents client using ONLY API Key
# ============================================================

@st.cache_resource
def get_client():
    return AgentsClient(
        endpoint=PROJECT_ENDPOINT,
        credential=AzureKeyCredential(PROJECT_API_KEY)
    )

# ============================================================
# 3️⃣ Initialize agent + create thread (cached)
# ============================================================

@st.cache_resource
def init_agent(agent_id: str):
    client = get_client()
    agent = client.get_agent(agent_id)
    thread = client.create_thread()
    return client, agent, thread.id

# ============================================================
# 4️⃣ Function to send message & read reply
# ============================================================

def ask_agent(client, agent, thread_id, prompt):
    # Send user message
    client.create_message(
        thread_id=thread_id,
        role=MessageRole.USER,
        content=prompt,
    )

    # Process run
    run = client.create_and_process_run(
        thread_id=thread_id,
        agent_id=agent.id,
    )

    # Retrieve response
    msg = client.get_last_message_by_role(
        thread_id=thread_id,
        role=MessageRole.AGENT,
    )

    if not msg or not msg.text_messages:
        return "⚠ No response received."

    return msg.text_messages[0].text.value


# ============================================================
# 5️⃣ Streamlit UI Layout
# ============================================================

st.set_page_config(page_title="Azure Agents Chat", layout="wide")
st.title("🤖 Azure Multi-Agent Chat (API Key Based)")
st.caption("Runs using a simple Azure API Key — no login required.")

tab1, tab2 = st.tabs(["📊 Price Monitoring Agent", "⚔️ Competitor Gap Agent"])


# ============================================================
# TAB 1 — Price Monitoring
# ============================================================

with tab1:
    st.header("📊 In-Season Price Monitoring Agent")

    client1, agent1, thread1 = init_agent(PRICE_MONITORING_AGENT_ID)

    if "pm_history" not in st.session_state:
        st.session_state.pm_history = []

    # Display chat history
    for role, content in st.session_state.pm_history:
        if role == "user":
            st.markdown(f"**🧑 You:** {content}")
        else:
            st.markdown(f"**🤖 Agent:** {content}")

    user_input_pm = st.text_input("Ask a question:", key="pm_input")
    if st.button("Send", key="pm_send") and user_input_pm.strip():

        # Add to chat history
        st.session_state.pm_history.append(("user", user_input_pm))

        with st.spinner("Thinking..."):
            reply = ask_agent(client1, agent1, thread1, user_input_pm)

        st.session_state.pm_history.append(("agent", reply))
        st.rerun()


# ============================================================
# TAB 2 — Competitor Gap Agent
# ============================================================

with tab2:
    st.header("⚔️ Competitor Price Gap Agent")

    client2, agent2, thread2 = init_agent(COMP_GAP_AGENT_ID)

    if "cg_history" not in st.session_state:
        st.session_state.cg_history = []

    for role, content in st.session_state.cg_history:
        if role == "user":
            st.markdown(f"**🧑 You:** {content}")
        else:
            st.markdown(f"**🤖 Agent:** {content}")

    user_input_cg = st.text_input("Ask a question:", key="cg_input")
    if st.button("Send", key="cg_send") and user_input_cg.strip():

        st.session_state.cg_history.append(("user", user_input_cg))

        with st.spinner("Thinking..."):
            reply2 = ask_agent(client2, agent2, thread2, user_input_cg)

        st.session_state.cg_history.append(("agent", reply2))
        st.rerun()
