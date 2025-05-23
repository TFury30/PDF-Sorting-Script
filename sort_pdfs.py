import os
import shutil
import logging
import hashlib
import json
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
HASH_CACHE_FILE = os.path.join(LOG_FOLDER, "hashes.json")
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

duplicate_logger = logging.getLogger("duplicates")
duplicate_logger.addHandler(logging.FileHandler(os.path.join(LOG_FOLDER, "duplicates.log"), mode='w', encoding='utf-8'))

unreadable_logger = logging.getLogger("unreadable")
unreadable_logger.addHandler(logging.FileHandler(os.path.join(LOG_FOLDER, "unreadable.log"), mode='w', encoding='utf-8'))

error_logger = logging.getLogger("errors")
error_logger.addHandler(logging.FileHandler(os.path.join(LOG_FOLDER, "errors.log"), mode='w', encoding='utf-8'))
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
    except Exception as e:
        error_logger.warning(f"Language detection failed: {e}")
        return "unknown"

def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_unique_path(dest_folder, file_name, used):
    base, ext = os.path.splitext(file_name)
    candidate = os.path.join(dest_folder, file_name)
    counter = 1
    while candidate in used:
        candidate = os.path.join(dest_folder, f"{base}_{counter}{ext}")
        counter += 1
    used.add(candidate)
    return candidate

def process_pdf(path):
    text = extract_text(path)
    if not text.strip():
        unreadable_logger.warning(f"Unreadable or empty: {path}")
        return (path, "", "unknown", None)
    lang = detect_language(text)
    text_hash = hash_text(text)
    return (path, text, lang, text_hash)

def move_pdf(path, language, topic, used_paths):
    file_name = os.path.basename(path)
    safe_topic = topic.replace(" ", "_").replace("/", "_")[:50]
    dest_folder = os.path.join(OUTPUT_FOLDER, language, safe_topic)
    os.makedirs(dest_folder, exist_ok=True)
    final_path = get_unique_path(dest_folder, file_name, used_paths)
    shutil.copy(path, final_path)
    return final_path

def write_index(entries):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write("\U0001F4DA SORTED PDF INDEX\n")
        f.write("\u2500" * 46 + "\n\n")
        for entry in entries:
            f.write(f"File: {entry['file']}\n")
            f.write(f"Language: {entry['language']}\n")
            f.write(f"Topic: {entry['topic']}\n")
            f.write(f"Path: {entry['path']}\n\n")

def load_hash_cache():
    if os.path.exists(HASH_CACHE_FILE):
        with open(HASH_CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_hash_cache(hashes):
    with open(HASH_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(hashes), f)

# ---------- Main Script ----------
def main():
    logging.info("Starting PDF sorting pipeline...")
    pdf_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith('.pdf')]
    pdf_paths = [os.path.join(SOURCE_FOLDER, f) for f in pdf_files]
    logging.info(f"Found {len(pdf_paths)} PDFs to process.")

    seen_hashes = load_hash_cache()
    index_entries = []
    used_paths = set()

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(tqdm(executor.map(process_pdf, pdf_paths), total=len(pdf_paths)))

    paths, texts, languages, hashes = zip(*results)

    logging.info("Running topic modeling with BERTopic...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    topic_model = BERTopic(embedding_model=embedding_model, language="multilingual")
    topics, _ = topic_model.fit_transform(texts)

    topic_info = topic_model.get_topic_info().set_index("Topic")
    topic_names = [topic_info.loc[t]["Name"] if t in topic_info.index else "Unknown" for t in topics]

    logging.info("Sorting and moving PDFs into topic/language folders...")
    for i, path in enumerate(paths):
        if not texts[i] or hashes[i] is None:
            continue

        if hashes[i] in seen_hashes:
            duplicate_logger.warning(f"Duplicate: {path}")
            continue
        seen_hashes.add(hashes[i])

        try:
            final_path = move_pdf(path, languages[i], topic_names[i], used_paths)
            index_entries.append({
                "file": os.path.basename(path),
                "language": languages[i],
                "topic": topic_names[i],
                "path": final_path
            })
        except Exception as e:
            error_logger.error(f"Failed to move {path}: {e}")

    write_index(index_entries)
    save_hash_cache(seen_hashes)
    logging.info(f"Finished. Index written to: {INDEX_FILE}")
    logging.info(f"Logs saved in: {LOG_FOLDER}")

if __name__ == "__main__":
    main()
