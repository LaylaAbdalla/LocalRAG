import streamlit as st
import requests
import time

# Configuration
API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="Know Your University", layout="wide")

st.title("Know Your University")
st.markdown("Upload university program guidelines and query them to understand requirements and policies.")

# Sidebar for Project and Data Processing
with st.sidebar:
    st.header("Project Setup")
    project_id = st.text_input("University Identifier (Project ID)", value="demo_university")
    
    st.subheader("1. Upload Document")
    uploaded_file = st.file_uploader("Upload University Syllabus (PDF, TXT, DOCX, HTML)", type=["pdf", "txt", "docx", "html"])
    
    if st.button("Upload File"):
        if uploaded_file and project_id:
            with st.spinner("Uploading..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_BASE_URL}/data/upload/{project_id}", files=files, timeout=30)
                    if response.status_code == 200:
                        st.success("File uploaded successfully.")
                    else:
                        st.error(f"Upload failed (HTTP {response.status_code}): {response.text}")
                except Exception as e:
                    st.error(f"Upload error: {e}")
        else:
            st.warning("Please provide a Project ID and select a file.")

    st.subheader("2. Process Document")
    chunk_size = st.number_input("Chunk Size", value=500, step=100)
    overlap = st.number_input("Chunk Overlap", value=50, step=10)
    
    if st.button("Process Data"):
        if uploaded_file and project_id:
            with st.spinner("Chunking document..."):
                payload = {
                    "file_name": uploaded_file.name,
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                    "do_reset": 0
                }
                response = requests.post(f"{API_BASE_URL}/data/process/{project_id}", json=payload)
                if response.status_code == 200:
                    st.success("Document processed and chunked successfully.")
                else:
                    st.error(f"Processing failed: {response.text}")
        else:
            st.warning("Please upload a file first.")

    st.subheader("3. Build Index")
    if st.button("Push to Vector Index"):
        if project_id:
            with st.spinner("Embedding and building index..."):
                payload = {"do_reset": 0}
                response = requests.post(f"{API_BASE_URL}/nlp/index/push/{project_id}", json=payload)
                if response.status_code == 200:
                    st.success("Index built successfully.")
                else:
                    st.error(f"Indexing failed: {response.text}")

# Main Chat Interface
st.header("Query University Data")

query = st.text_input("Ask a question about the university requirements:")
col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    top_k = st.number_input("Context Chunks", value=5, min_value=1, max_value=20)
with col2:
    lang = st.selectbox("Language", options=["en", "ar"])
with col3:
    model = st.selectbox("LLM Model", options=["gemma2:2b", "qwen2.5:1.5b", "phi3:mini"])

if st.button("Generate Answer"):
    if query and project_id:
        with st.spinner("Searching and generating answer..."):
            payload = {
                "text": query,
                "top_k": top_k,
                "lang": lang,
                "model": model
            }
            start_time = time.time()
            try:
                response = requests.post(f"{API_BASE_URL}/nlp/index/answer/{project_id}", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "No answer generated.")
                    duration = time.time() - start_time
                    
                    st.markdown("### Answer")
                    st.info(answer)
                    st.caption(f"Generated in {duration:.2f} seconds")
                    
                    with st.expander("View Context Prompt"):
                        st.text(data.get("full_prompt", ""))
                else:
                    st.error(f"Query failed: {response.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")
    else:
        st.warning("Please enter a question and ensure Project ID is set.")
