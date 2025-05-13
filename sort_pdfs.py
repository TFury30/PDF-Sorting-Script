import os
import shutil
import json
import logging
import hashlib
import pdfplumber
from langdetect import detect
from concurrent.futures import ProcessPoolExecutor
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ---------- CONFIG ----------
SOURCE_FOLDER = "./pdfs"
OUTPUT_FOLDER = "./sorted_pdfs"
LOG_FOLDER = os.path.join(OUTPUT_FOLDER, "logs")
INDEX_FILE = os.path.join(OUTPUT_FOLDER, "index.txt")
SAMPLE_PAGES = 10
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MAX_WORKERS = os.cpu_count() or 4
# ----------------------------

# ---------- LOGGING SETUP ----------
os.makedirs(LOG_FOLDER, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_FOLDER, "process.log"), mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Set up separate loggers for duplicates and unreadable PDFs
duplicate_logger = logging.getLogger("duplicates")
duplicate_logger.addHandler(logging.FileHandler(os.path.join(LOG_FOLDER, "duplicates.log"), mode='w', encoding='utf-8'))

unreadable_logger = logging.getLogger("unreadable")
unreadable_logger.addHandler(logging.FileHandler(os.path.join(LOG_FOLDER, "unreadable.log"), mode='w', encoding='utf-8'))
# -----------------------------------

# ---------- Helper Functions ----------
def extract_text(pdf_path, max_pages=SAMPLE_PAGES):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            front = pdf.pages[:max_pages // 2]
            back = pdf.pages[-(max_pages // 2):] if total_pages > max_pages // 2 else []
            pages = front + back
            for page in pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
    except Exception as e:
        error_logger.error(f"Failed to extract {pdf_path}: {e}")
    return text.strip()

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def hash_text(text):
    """Generate a SHA256 hash of the text for duplicate detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def process_pdf(path):
    """Process a PDF, extract text and detect language, return tuple with hash for duplicate check."""
    text = extract_text(path)
    if not text.strip():
        unreadable_logger.warning(f"Unreadable or empty: {path}")
        return (path, "", "unknown", None)  # Return None for unreadable PDFs
    lang = detect_language(text)
    text_hash = hash_text(text)
    return (path, text, lang, text_hash)

def move_pdf(path, language, topic):
    """Move PDF to the appropriate folder based on language and topic."""
    file_name = os.path.basename(path)
    safe_topic = topic.replace(" ", "_").replace("/", "_")[:50]
    dest_folder = os.path.join(OUTPUT_FOLDER, language, safe_topic)
    os.makedirs(dest_folder, exist_ok=True)
    final_path = os.path.join(dest_folder, file_name)
    shutil.copy(path, final_path)
    return final_path

def write_index(entries):
    """Write a table of contents (index) of all sorted PDFs."""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write("📚 SORTED PDF INDEX\n")
        f.write("──────────────────────────────────────────────\n\n")
        for entry in entries:
            f.write(f"File: {entry['file']}\n")
            f.write(f"Language: {entry['language']}\n")
            f.write(f"Topic: {entry['topic']}\n")
            f.write(f"Path: {entry['path']}\n\n")

# ---------- Main Script ----------
def main():
    logging.info("Starting PDF sorting pipeline...")
    pdf_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith('.pdf')]
    pdf_paths = [os.path.join(SOURCE_FOLDER, f) for f in pdf_files]
    logging.info(f"Found {len(pdf_paths)} PDFs to process.")

    # Track already seen hashes for duplicate detection
    seen_hashes = set()
    index_entries = []

    # Start PDF processing using multiprocessing
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(tqdm(executor.map(process_pdf, pdf_paths), total=len(pdf_paths)))

    paths, texts, languages, hashes = zip(*results)

    logging.info("Running topic modeling with BERTopic...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    topic_model = BERTopic(embedding_model=embedding_model, language="multilingual")
    topics, _ = topic_model.fit_transform(texts)

    topic_names = [topic_model.get_topic(t)[0][0] if t != -1 else "Unknown" for t in topics]

    logging.info("Sorting and moving PDFs into topic/language folders...")
    for i, path in enumerate(paths):
        if not texts[i] or hashes[i] is None:
            continue  # Skip unreadable PDFs

        # Skip duplicates
        if hashes[i] in seen_hashes:
            duplicate_logger.warning(f"Duplicate: {path}")
            continue
        seen_hashes.add(hashes[i])

        try:
            final_path = move_pdf(path, languages[i], topic_names[i])
            index_entries.append({
                "file": os.path.basename(path),
                "language": languages[i],
                "topic": topic_names[i],
                "path": final_path
            })
        except Exception as e:
            error_logger.error(f"Failed to move {path}: {e}")

    # Write the final index
    write_index(index_entries)
    logging.info(f"Finished. Index written to: {INDEX_FILE}")
    logging.info(f"Logs saved in: {LOG_FOLDER}")

if __name__ == "__main__":
    main()
