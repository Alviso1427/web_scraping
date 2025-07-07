import streamlit as st
import os
import importlib.util
import shutil

CLIENTS_DIR = "clients"

def list_clients():
    return [d for d in os.listdir(CLIENTS_DIR) if os.path.isdir(os.path.join(CLIENTS_DIR, d))]

def load_client_script(client_name):
    script_path = os.path.join(CLIENTS_DIR, client_name, "run.py")
    spec = importlib.util.spec_from_file_location("run_module", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

st.title("Client Script Runner")

clients = list_clients()
selected_client = st.selectbox("Select a client", clients)

if selected_client:
    input_dir = os.path.join(CLIENTS_DIR, selected_client, "input")
    output_dir = os.path.join(CLIENTS_DIR, selected_client, "output")

    st.subheader("Upload Input Files")
    uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True)

    if uploaded_files:
        os.makedirs(input_dir, exist_ok=True)
        for uploaded_file in uploaded_files:
            with open(os.path.join(input_dir, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success("Files uploaded!")

    if st.button("Run Script"):
        with st.spinner("Running..."):
            module = load_client_script(selected_client)
            module.run()
        st.success("Script executed!")

    st.subheader("Download Output Files")
    if os.path.exists(output_dir):
        output_files = os.listdir(output_dir)
        for fname in output_files:
            with open(os.path.join(output_dir, fname), "rb") as f:
                st.download_button(label=f"Download {fname}", data=f, file_name=fname)
