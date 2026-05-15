<div align="center">
  <img src="./map.jpeg" alt="LocalRAG Architecture" width="600"/>
  <h1>LocalRAG</h1>
  <p>A robust, privacy-first Retrieval-Augmented Generation (RAG) system with extensive native Arabic support.</p>

  <!-- Badges -->
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI"></a>
  <a href="https://streamlit.io/"><img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"></a>
  <a href="https://ollama.com/"><img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=Ollama&logoColor=white" alt="Ollama"></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
</div>

## Executive Summary
**LocalRAG** is designed to process, index, and query uploaded documents locally. The system allows users to upload various document formats (`TXT`, `PDF`, `DOCX`, `HTML`), securely processes them using overlapping chunks, and stores them in both a **MongoDB** instance (for document metadata) and a **ChromaDB Vector Store** for semantic search. 

A Factory Pattern architecture enables seamless switching between LLM providers (e.g., local Ollama, remote APIs) and embedding models. The system incorporates extensive **Arabic language support** (via NFKC normalization, ligature fixing, and HTML whitelisting) to ensure high-quality, localized question-answering capabilities.

---

## Interface Showcases

<div align="center">
  <table>
    <tr>
      <td align="center"><b>English Query & Response</b></td>
      <td align="center"><b>Arabic Query & Response</b></td>
    </tr>
    <tr>
      <td><img src="./assets/English%20Prompt.jfif" alt="English Query & Response" width="400"/></td>
      <td><img src="./assets/Arabic%20Prompt.jfif" alt="Arabic Query & Response" width="400"/></td>
    </tr>
  </table>
  <p><i>The intuitive Streamlit frontend enables seamless document processing and real-time parameter tuning.</i></p>
</div>

---

## Embedding Model & Chunking Strategy

### Embedding Model
The application utilizes `BAAI/bge-small-en` (configurable via `.env`) and supports localized models via the `LLMFactory` pattern. 
- **Performance:** Balances processing speed, low memory footprint, and high accuracy for semantic representation on consumer-grade hardware.
- **Multilingual Support:** Works natively for English and Arabic. For optimal Arabic and multilingual results, it integrates seamlessly with a multilingual variant via the `local_bge` provider.

### Chunking Strategy
The system supports two chunking approaches, dynamically selectable via the User Interface and the API:

1. **Semantic Chunking (Default):** 
   - Utilizes LangChain's `SemanticChunker` paired with `paraphrase-multilingual-MiniLM-L12-v2`.
   - Splits text at semantic breakpoints to prevent cutting thoughts in half, vastly improving context quality for complex Arabic literature.
2. **Standard Chunking (Fallback):** 
   - Utilizes `RecursiveCharacterTextSplitter`.
   - Default: `chunk_size` of `500` characters with an `overlap` of `50` characters. Optimal for academic policies, ensuring a complete semantic focus without severing contextual links.

> **Pro Tip:** The chunking method, chunk size, chunk overlap, and Top-K retrieved context chunks are fully customizable in real-time to dynamically accommodate varying document types and LLM context limits.

---

## Arabic Language Processing

The pipeline implements robust native preprocessing mechanisms for Arabic text:
- **Text Normalization:** Uses NFKC (Normalization Form Compatibility Composition) to handle 'لا' variations without breaking them into separate characters. Removes diacritics (Harakat/Tashkeel), visual stretching (Tatweel), and unifies Alef shapes (أ, إ, آ -> ا).
- **HTML Whitelist Parsing:** Eliminates layout noise and RTL formatting issues in HTML, preserving logical Arabic sentence order.
- **Language-Aware Templating:** Automatically switches the generation template (`lang="ar"`), priming the LLM with an Arabic persona and context headers.

### Arabic Test Case Evaluation
- **Query:** `ما هي اهداف الكلية` (What are the college's goals?)
- **Configuration:** 10 Context Chunks, Language `ar`.
- **Generated Answer:**
  ```text
  وفقًا للمستندات المقدمة، تركز أهداف الكلية على:
  - تطوير مهارات تنافسية: لإعداد الطلاب للعمل في عالم متطور.
  - التطبيق العلمي: بناءً على النظرية، تهدف إلى تطبيق المعرفة في مجالات مختلفة.
  - تحسين التنمية: لتحقيق التنمية في مختلف المجالات.
  - تطوير البحث العلمي: لإعداد الطلاب للبحث العلمي والعمل في مجال البحث.
  ```
- **Result:** Accurate response generated in **6.28 seconds**, demonstrating successful extraction, normalization, retrieval, and coherent text generation.

---

## API Documentation

<details>
<summary><b>Click to expand Data Endpoints</b></summary>

- **Upload File** `POST /api/data/upload/{dir_name}`
  - **Payload:** `multipart/form-data` with a `file` field.
  - **Response:** `200 OK` with `project_id` and `file_name`.

- **Process File** `POST /api/data/process/{project_id}`
  - **Payload (JSON):**
    ```json
    {
      "file_name": "example.pdf",
      "chunk_size": 500,
      "overlap": 50,
      "do_reset": 0,
      "use_semantic_chunking": true
    }
    ```
  - **Response:** `200 OK` with `chunks_count`.
</details>

<details>
<summary><b>Click to expand NLP Endpoints</b></summary>

- **Push Data to Index** `POST /api/nlp/index/push/{project_id}`
  - **Payload (JSON):** `{"do_reset": 1}`
- **Check Index Info** `GET /api/nlp/index/info/{project_id}`
  - **Response:** `200 OK` with `{"results": true/false}`
- **Search Vector Index** `POST /api/nlp/index/search/{project_id}`
  - **Payload (JSON):** `{"text": "Query string", "top_k": 5}`
- **Generate Answer (RAG)** `POST /api/nlp/index/answer/{project_id}`
  - **Payload (JSON):**
    ```json
    {
      "text": "ما هي اهداف الكلية",
      "top_k": 5,
      "lang": "ar",
      "model": "llama3"
    }
    ```
</details>

---

## Getting Started

### Docker Deployment (Recommended)

The project is fully containerized using Docker Compose, orchestrating two services: the **FastAPI application** and a **MongoDB** instance.

1. **Prerequisites:** Docker, Docker Compose, and [Ollama](https://ollama.com/) running on the **host machine** (not inside Docker).
2. **Pull Model:** `ollama pull gemma`
3. **Build & Start:**
   ```bash
   docker build -t localrag .
   docker-compose up -d
   ```
4. **Access:**
   - FastAPI Interactive Docs: [http://localhost:5000/docs](http://localhost:5000/docs)
   - MongoDB: `localhost:27017` (Credentials: `admin` / `admin`)

> **Note:** The application container reaches Ollama via `host.docker.internal`.
> *To stop and remove all volumes (deletes MongoDB data and ChromaDB index): `docker-compose down -v`*

### Local Execution

1. Ensure **MongoDB** (`mongodb://localhost:27017`) and **Ollama** are running.
2. Install dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   cd src
   uvicorn main:app --port 8000 --reload
   ```
4. Start the Streamlit UI:
   ```bash
   cd src
   streamlit run interface.py
   ```


