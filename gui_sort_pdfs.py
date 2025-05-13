import streamlit as st
import os
import subprocess

st.set_page_config(page_title="PDF Sorter GUI", layout="centered")
st.title("📚 PDF Sorter with BERTopic")

st.markdown("This tool uses language detection and topic modeling to organize your PDFs by folder.")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("Settings")
    source = st.text_input("Source Folder", value="./pdfs")
    output = st.text_input("Output Folder", value="./sorted_pdfs")
    sample_pages = st.slider("Sample Pages for Text Extraction", min_value=1, max_value=20, value=10)
    force_rerun = st.checkbox("Force reprocess all PDFs", value=False)

# --- Launch Script ---
if st.button("🚀 Start Sorting PDFs"):
    cmd = ["python", "sort_pdfs.py"]
    env = os.environ.copy()
    env["SOURCE_FOLDER"] = source
    env["OUTPUT_FOLDER"] = output
    env["SAMPLE_PAGES"] = str(sample_pages)
    if force_rerun:
        env["FORCE_REPROCESS"] = "1"

    with st.spinner("Running the PDF sorter..."):
        try:
            subprocess.run(cmd, check=True, env=env)
            st.success("PDF sorting complete!")
        except subprocess.CalledProcessError as e:
            st.error(f"Error running script: {e}")

# --- Display index if exists ---
index_file = os.path.join(output, "index.csv")
if os.path.exists(index_file):
    st.subheader("📄 Sorted PDF Index")
    import pandas as pd
    df = pd.read_csv(index_file)
    st.dataframe(df)
    st.download_button("Download CSV Index", df.to_csv(index=False), "index.csv")
