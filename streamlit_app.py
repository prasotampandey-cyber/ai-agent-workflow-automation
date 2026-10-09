import streamlit as st, json
from app.main import build_agent

st.set_page_config(page_title="AI Workflow Automation Agent",layout="wide")
st.title("AI Agent Workflow Automation")
st.caption("Excel-driven, reusable workflow architecture")

request=st.text_area("User request", "Which products need restocking?", height=100)
if st.button("Run Agent",type="primary"):
    with st.spinner("Selecting and executing workflow..."):
        result=build_agent().run(request)
    st.subheader("Selected Workflow")
    st.json(result["selected_workflow"])
    st.subheader("Steps Executed")
    for i,s in enumerate(result["steps_executed"],1):
        st.write(f"{i}. {s}")
    st.subheader("Final Output")
    st.json(result["final_output"])
