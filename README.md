---

# PDF Sorting Script

This script automatically processes, sorts, and organizes PDF files based on their language and topic. It can:

* Detect the language of each PDF.
* Automatically categorize PDFs by topic using BERTopic and a pre-trained sentence transformer model.
* Handle **duplicate PDFs** by checking their content (using SHA256 hashes).
* Detect **unreadable PDFs** with no extractable text and log them separately.
* Generate a **Table of Contents (index)** of all sorted PDFs.

## Features:

* **Language Detection**: Automatically detects the language of a PDF using `langdetect`.
* **Topic Detection**: Classifies PDFs into topics using **BERTopic** (based on their extracted text).
* **Duplicate Detection**: Flags PDFs with identical content as duplicates.
* **Unreadable PDF Detection**: Flags PDFs that cannot be parsed or have no extractable text.
* **Automatic Sorting**: Organizes PDFs into folders based on **language** and **topic**.
* **Logging**: Logs all operations and errors, including duplicates and unreadable PDFs.
* **Table of Contents**: Generates an index file listing all sorted PDFs with their paths and languages.

##  Requirements:

* Python 3.7 or higher
* Required Python libraries:

  * `pdfplumber`
  * `langdetect`
  * `bert-topic`
  * `sentence-transformers`
  * `tqdm`
  * `concurrent.futures` (for parallel processing)
  * `shutil`
  * `logging`

You can install the required libraries by running:

```bash
pip install -r requirements.txt
```

Where `requirements.txt` includes the following dependencies:

```
pdfplumber
langdetect
bert-topic
sentence-transformers
tqdm
```

## Installation:

1. **Clone this repository**:

   ```bash
   git clone https://github.com/your-username/pdf-sorting-script.git
   cd pdf-sorting-script
   ```

2. **Install required Python packages**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your PDFs**:

   * Place all your PDFs into a folder called `pdfs/` inside the project directory.

##  How to Use:

### 1. **Run the Script**:

To start the sorting process, simply run the following command:

```bash
python sort_pdfs.py
```

### 2. **What Happens After Running the Script?**

* The script will:

  * **Scan** the `pdfs/` folder for PDF files.
  * **Extract** text from each PDF (using `pdfplumber`).
  * **Detect the language** of each PDF.
  * **Analyze topics** using **BERTopic**.
  * **Move** PDFs into new folders based on their detected **language** and **topic**.
  * **Log** any duplicate PDFs, unreadable PDFs, or errors that occur during the process.
  * **Generate** a **Table of Contents** (`index.txt`) listing all sorted PDFs with their language and topic.

### 3. **Check the Output:**

* **Sorted PDFs**: Located in the `sorted_pdfs/` directory, organized by `language/topic/`.

* **Index**: A `index.txt` file will be created in the `sorted_pdfs/` directory, which contains a table of contents for all sorted PDFs.

* **Log Files**:

  * `logs/process.log` – Normal operation log.
  * `logs/errors.log` – Errors encountered during the process.
  * `logs/duplicates.log` – Logs any duplicate PDFs based on content.
  * `logs/unreadable.log` – Logs PDFs that could not be parsed or have no extractable text.

## Cleaning Up:

If you need to delete the sorted PDFs and start fresh, simply remove the `sorted_pdfs/` folder:

```bash
rm -rf sorted_pdfs/
```

You can also clean up log files if desired by deleting the `logs/` folder.

## Example Output Structure:

```
sorted_pdfs/
├── English/
│   ├── Technology/
│   │   └── tech_book_1.pdf
│   │   └── tech_book_2.pdf
│   ├── Science/
│   │   └── science_book_1.pdf
├── Spanish/
│   └── Literature/
│       └── literatura_1.pdf
└── index.txt
logs/
├── process.log
├── errors.log
├── duplicates.log
└── unreadable.log
```

## Folder Structure:

1. **`pdfs/`**: Place all your PDFs here for processing.
2. **`sorted_pdfs/`**: This is where the script will move the sorted PDFs, categorized by **language** and **topic**.
3. **`logs/`**: This directory will store all the logs (process, duplicates, unreadables).
4. **`index.txt`**: The table of contents file listing all the PDFs sorted by language and topic.

## Troubleshooting:

* **If a PDF is unreadable**: Check the `logs/unreadable.log` to find which PDF couldn't be parsed. It might be corrupted or encrypted.
* **If there are duplicate PDFs**: Check the `logs/duplicates.log` to see the paths of PDFs with the same content.

## Contributing:

If you'd like to contribute to this project:

* Fork the repository.
* Create a new branch (`git checkout -b feature-name`).
* Make your changes and commit (`git commit -am 'Add new feature'`).
* Push to the branch (`git push origin feature-name`).
* Create a pull request.

---

### License:

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

