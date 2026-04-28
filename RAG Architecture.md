# 🧠 Mini-RAG — A Minimal Retrieval-Augmented Generation Application

> **A complete, educational implementation of the RAG pipeline** — from document upload to AI-powered answers — built with FastAPI, MongoDB, Qdrant, and OpenAI-compatible LLMs.

---

## 📖 Table of Contents

1. [What is RAG?](#-what-is-rag)
2. [How This Project Works (End-to-End)](#-how-this-project-works-end-to-end)
3. [Architecture Overview](#-architecture-overview)
4. [Project Directory Structure](#-project-directory-structure)
5. [File Dependency Map — How Files Call Each Other](#-file-dependency-map--how-files-call-each-other)
6. [Detailed Class Reference](#-detailed-class-reference)
   - [Configuration Layer](#1-configuration-layer)
   - [Controllers Layer](#2-controllers-layer)
   - [Models Layer](#3-models-layer)
   - [Routes Layer](#4-routes-layer)
   - [Stores Layer (LLM)](#5-stores-layer--llm)
   - [Stores Layer (VectorDB)](#6-stores-layer--vectordb)
   - [Template Layer](#7-template-layer)
   - [Streamlit Interface](#8-streamlit-interface)
7. [Design Patterns Used](#-design-patterns-used)
8. [API Endpoints Reference](#-api-endpoints-reference)
9. [Database Schemas](#-database-schemas)
10. [Environment Variables](#-environment-variables)
11. [Setup & Installation](#-setup--installation)
12. [How to Run](#-how-to-run)
13. [Requirements](#-requirements)

---

## 🤔 What is RAG?

**Retrieval-Augmented Generation (RAG)** is a technique that improves LLM answers by providing them with relevant documents from your own data before generating a response.

Instead of relying solely on the LLM's training data, RAG:
1. **Retrieves** the most relevant pieces of your documents.
2. **Augments** the LLM's prompt with those pieces.
3. **Generates** an answer grounded in your actual data.

```
Traditional LLM:
    User Question → LLM → Answer (from training data only)

RAG Pipeline:
    User Question → Embed Question → Search Vector DB → Retrieve Relevant Docs
                                                              ↓
                                        Build Prompt (Docs + Question) → LLM → Grounded Answer
```

---

## 🔄 How This Project Works (End-to-End)

The RAG pipeline has **5 sequential steps**. Here's what happens at each step, from the code perspective:

### Step 1: Upload a Document
```
Client sends file → POST /api/data/upload/{project_id}
                         │
                         ├── DataController.validate_file()     → Check MIME type & size
                         ├── FileController.get_file_path()     → Create project directory
                         ├── aiofiles.open()                     → Stream write to disk
                         └── ProjectModel.get_project_or_create_one() → Create MongoDB project
```

### Step 2: Process (Chunk) the Document
```
Client sends params → POST /api/data/process/{project_id}
                           │
                           ├── ProcessController.get_file_content()  → Load file (TextLoader / PyMuPDFLoader)
                           ├── ProcessController.process_files()     → Split into overlapping chunks
                           └── ChunkModel.insert_many_chunks()       → Batch-insert chunks into MongoDB
```

### Step 3: Push Chunks to Vector Database
```
Client sends request → POST /api/nlp/index/push/{project_id}
                            │
                            ├── ChunkModel.get_chunks_by_project_id()  → Fetch chunks from MongoDB (paginated)
                            ├── EmbeddingProvider.embed()               → Convert each chunk to a vector
                            ├── QDrantDB.create_collection()            → Create Qdrant collection
                            └── QDrantDB.add_documents()                → Upload vectors to Qdrant
```

### Step 4: Semantic Search
```
Client sends query → POST /api/nlp/index/search/{project_id}
                          │
                          ├── EmbeddingProvider.embed(query, "query")  → Embed the search query
                          └── QDrantDB.search_by_vector()              → Find top-K similar chunks
```

### Step 5: RAG Answer (Retrieve + Generate)
```
Client sends question → POST /api/nlp/index/answer/{project_id}
                             │
                             ├── NlpController.search_by_vector()      → Retrieve relevant chunks
                             ├── TemplateParser.get("rag", ...)         → Load prompt templates
                             ├── Build full prompt: [system] + [docs] + [question] + [footer]
                             └── OpenAIProvider.generate_response()     → Call LLM API → Get answer
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                │
│  ┌────────────────────────┐    ┌──────────────────────────────────┐    │
│  │  Streamlit UI           │    │  Any HTTP Client (curl, Postman) │    │
│  │  (interface.py)         │    │                                  │    │
│  └────────┬───────────────┘    └──────────┬───────────────────────┘    │
│           │         HTTP Requests          │                           │
└───────────┼────────────────────────────────┼───────────────────────────┘
            │                                │
┌───────────▼────────────────────────────────▼───────────────────────────┐
│                         API LAYER (FastAPI)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐     │
│  │ routes/base.py│  │routes/data.py│  │    routes/nlp.py         │     │
│  │ GET /api/     │  │ POST upload  │  │ POST push/search/answer  │     │
│  └──────────────┘  │ POST process │  └─────────┬────────────────┘     │
│                     └──────┬───────┘            │                      │
└────────────────────────────┼────────────────────┼──────────────────────┘
                             │                    │
┌────────────────────────────▼────────────────────▼──────────────────────┐
│                      CONTROLLER LAYER                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────────┐    │
│  │ DataController  │  │ProcessController│  │   NlpController       │    │
│  │ (validate file) │  │ (load & chunk)  │  │ (embed, search, RAG)  │    │
│  └────────────────┘  └────────────────┘  └───────────┬───────────┘    │
│                                                       │                │
│  ┌────────────────┐  ┌────────────────────────────────┘                │
│  │ FileController  │  │                                                │
│  │ (manage dirs)   │  │                                                │
│  └────────────────┘  │                                                │
│                       │                                                │
│  ┌────────────────────▼───────────────────────────────────────────┐    │
│  │                  BaseController (parent of all)                │    │
│  │         (app_settings, base_dir, file_dir, db_dir)            │    │
│  └───────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│                      DATA LAYER                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────────┐ │
│  │  ProjectModel   │  │  ChunkModel    │  │   DataBaseModel (base)  │ │
│  │  (projects CRUD)│  │  (chunks CRUD) │  │   (provides db_client)  │ │
│  └───────┬────────┘  └───────┬────────┘  └─────────────────────────┘ │
│          │                    │                                        │
│  ┌───────▼────────────────────▼────────┐                              │
│  │          MongoDB (Motor async)       │                              │
│  │  ┌──────────┐  ┌──────────────────┐ │                              │
│  │  │ projects │  │     chunks       │ │                              │
│  │  └──────────┘  └──────────────────┘ │                              │
│  └─────────────────────────────────────┘                              │
└───────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│                     STORES LAYER (External Services)                  │
│                                                                       │
│  ┌─── LLM Store ──────────────────────────────────────────────────┐  │
│  │  LLMFactory → creates:                                         │  │
│  │    ├── OpenAIProvider    (text generation via OpenAI API)      │  │
│  │    └── EmbeddingProvider (local embeddings via sentence-trans) │  │
│  │  LLMInterface (abstract contract)                              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─── VectorDB Store ────────────────────────────────────────────┐   │
│  │  VectorDBFactory → creates:                                    │   │
│  │    └── QDrantDB (Qdrant vector database operations)           │   │
│  │  VectorDBInterface (abstract contract)                         │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─── Template Store ────────────────────────────────────────────┐   │
│  │  TemplateParser → loads prompts from:                          │   │
│  │    ├── locales/en/rag.py  (English RAG prompts)               │   │
│  │    └── locales/ar/rag.py  (Arabic RAG prompts)                │   │
│  └────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Directory Structure

```
mini-rag-app/
├── README.md                          ← This file (project documentation)
│
├── docker/                            ← Docker configuration for external services
│   ├── .env                           ← Docker environment variables (Mongo credentials)
│   ├── .env.example                   ← Template for Docker env vars
│   ├── .gitignore                     ← Ignores .env in version control
│   ├── docker-compose.yaml            ← Docker Compose: MongoDB + Qdrant services
│   └── mongodb/                       ← MongoDB data persistence (auto-created)
│
└── src/                               ← Main application source code
    ├── main.py                        ★ APP ENTRY POINT — creates FastAPI, starts services
    ├── interface.py                   ★ STREAMLIT UI — interactive frontend for the RAG pipeline
    ├── requirements.txt               ← Python dependencies
    ├── .env                           ← Environment variables (API keys, DB URIs, model names)
    ├── .env.example                   ← Template for env vars
    ├── .gitignore                     ← Git ignore rules
    │
    ├── helpers/                       ← Utility modules shared across the app
    │   ├── __init__.py
    │   └── config.py                  ← Settings class — loads all config from .env
    │
    ├── controllers/                   ← Business logic layer
    │   ├── __init__.py                ← Package init — re-exports all controllers
    │   ├── BaseController.py          ← BASE CLASS — provides settings & file paths to all controllers
    │   ├── DataController.py          ← Validates uploaded files (MIME type, size)
    │   ├── FileController.py          ← Manages project directories under assets/files/
    │   ├── ProcessController.py       ← Loads files (TXT/PDF) and splits into overlapping chunks
    │   └── NlpController.py           ★ CORE RAG LOGIC — embed, push, search, answer
    │
    ├── models/                        ← Data access layer (MongoDB)
    │   ├── __init__.py
    │   ├── DataBaseModel.py           ← BASE CLASS — provides MongoDB client to all models
    │   ├── ProjectModel.py            ← CRUD operations for the "projects" collection
    │   ├── ChunkModel.py              ← CRUD operations for the "chunks" collection
    │   └── db_schemes/                ← Pydantic schemas for MongoDB documents
    │       ├── __init__.py            ← Re-exports: Project, DataChunk, RetrievalDocument
    │       ├── project.py             ← Project schema (project_id + MongoDB _id)
    │       └── data_chunk.py          ← DataChunk schema (text, metadata, order, project ref)
    │                                     + RetrievalDocument (search result: text + score)
    │
    ├── routes/                        ← API endpoint definitions (FastAPI routers)
    │   ├── __init__.py
    │   ├── base.py                    ← GET /api/ — welcome/health-check endpoint
    │   ├── data.py                    ← POST /api/data/upload & /api/data/process
    │   ├── nlp.py                     ← POST /api/nlp/index/push, search, answer + GET info
    │   └── schema/                    ← Pydantic request body schemas
    │       ├── __init__.py
    │       ├── data.py                ← RequestProcess (chunk_size, overlap, do_reset)
    │       └── nlp.py                 ← PushDataRequest (do_reset) + SearchRequest (text, top_k)
    │
    ├── stores/                        ← External service integrations
    │   ├── llm/                       ← LLM / Embedding providers
    │   │   ├── __init__.py
    │   │   ├── LLMInterface.py        ← ABSTRACT BASE — contract for all LLM providers
    │   │   ├── LLMFactory.py          ← FACTORY — creates OpenAIProvider or EmbeddingProvider
    │   │   ├── provider/              ← Concrete provider implementations
    │   │   │   ├── __init__.py
    │   │   │   ├── OpenAIProvider.py  ← OpenAI-compatible API (generation + embedding)
    │   │   │   └── EmbeddingProvider.py ← Local sentence-transformers (BGE embedding)
    │   │   └── tempelate/             ← Prompt template engine
    │   │       ├── __init__.py
    │   │       ├── template_parser.py ← TemplateParser — loads & renders locale prompts
    │   │       └── locales/           ← Language-specific prompt templates
    │   │           ├── __init__.py
    │   │           ├── en/            ← English prompts
    │   │           │   ├── __init__.py
    │   │           │   └── rag.py     ← system_prompt, document_prompt, footer_prompt
    │   │           └── ar/            ← Arabic prompts
    │   │               ├── __init__.py
    │   │               └── rag.py     ← Arabic versions of the same prompts
    │   │
    │   └── vectordb/                  ← Vector database providers
    │       ├── __init__.py
    │       ├── VectorDBInterface.py   ← ABSTRACT BASE — contract for all vector DB providers
    │       ├── VectorDBFactory.py     ← FACTORY — creates QDrantDB instances
    │       └── provider/              ← Concrete provider implementations
    │           ├── __init__.py
    │           └── QDrantDB.py        ← Qdrant operations (collections, upload, search)
    │
    └── assets/                        ← Runtime data (auto-created, gitignored)
        ├── files/                     ← Uploaded documents (one folder per project)
        │   └── <project_id>/          ← e.g. demoproject/lecture.pdf
        └── db/                        ← Local database storage
            └── qdrant_data/           ← Qdrant persistent storage
```

---

## 🔗 File Dependency Map — How Files Call Each Other

The arrows show **"calls / imports from"** relationships:

```
main.py
  ├──→ helpers/config.py              (get_settings)
  ├──→ routes/base.py                 (router)
  ├──→ routes/data.py                 (data_router)
  ├──→ routes/nlp.py                  (nlp_router)
  ├──→ stores/llm/LLMFactory.py       (create OpenAI + BGE providers)
  ├──→ stores/vectordb/VectorDBFactory.py (create Qdrant provider)
  └──→ stores/llm/tempelate/template_parser.py (create prompt parser)

routes/base.py
  └──→ helpers/config.py              (Settings, get_settings via Depends)

routes/data.py
  ├──→ helpers/config.py              (Settings, get_settings)
  ├──→ controllers/DataController.py  (validate_file)
  ├──→ controllers/FileController.py  (get_file_path)
  ├──→ controllers/ProcessController.py (get_file_content, process_files)
  ├──→ models/ProjectModel.py         (get_project_or_create_one)
  ├──→ models/ChunkModel.py           (insert_many_chunks, delete_chunks)
  ├──→ models/db_schemes/project.py   (Project)
  ├──→ models/db_schemes/data_chunk.py (DataChunk)
  └──→ routes/schema/data.py          (RequestProcess)

routes/nlp.py
  ├──→ controllers/NlpController.py   (push, search, answer, info)
  ├──→ models/ProjectModel.py         (get_project_or_create_one)
  ├──→ models/ChunkModel.py           (get_chunks_by_project_id)
  └──→ routes/schema/nlp.py           (PushDataRequest, SearchRequest)

controllers/BaseController.py
  └──→ helpers/config.py              (Settings, get_settings)

controllers/DataController.py
  └──→ controllers/BaseController.py  (inherits)

controllers/FileController.py
  └──→ controllers/BaseController.py  (inherits)

controllers/ProcessController.py
  ├──→ controllers/BaseController.py  (inherits)
  └──→ controllers/FileController.py  (get_file_path)

controllers/NlpController.py
  ├──→ controllers/BaseController.py  (inherits)
  └──→ models/db_schemes              (Project, DataChunk)

models/DataBaseModel.py
  └──→ helpers/config.py              (get_settings)

models/ProjectModel.py
  ├──→ models/DataBaseModel.py        (inherits)
  └──→ models/db_schemes/project.py   (Project)

models/ChunkModel.py
  ├──→ models/DataBaseModel.py        (inherits)
  └──→ models/db_schemes/data_chunk.py (DataChunk)

stores/llm/LLMFactory.py
  ├──→ stores/llm/provider/OpenAIProvider.py     (creates instances)
  └──→ stores/llm/provider/EmbeddingProvider.py  (creates instances)

stores/llm/provider/OpenAIProvider.py
  └──→ stores/llm/LLMInterface.py    (implements interface)

stores/vectordb/VectorDBFactory.py
  ├──→ controllers/BaseController.py  (get_db_path)
  └──→ stores/vectordb/provider/QDrantDB.py      (creates instances)

stores/vectordb/provider/QDrantDB.py
  ├──→ stores/vectordb/VectorDBInterface.py (implements interface)
  └──→ models/db_schemes/data_chunk.py      (RetrievalDocument)

stores/llm/tempelate/template_parser.py
  └──→ stores/llm/tempelate/locales/<lang>/rag.py (loads prompt templates)

interface.py (Streamlit)
  └──→ HTTP calls to FastAPI endpoints (no direct Python imports)
```

---

## 📚 Detailed Class Reference

### 1. Configuration Layer

#### `Settings` — (helpers/config.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | `pydantic_settings.BaseSettings` |
| **Purpose** | Loads ALL application configuration from `.env` file |
| **Key Fields** | `APP_NAME`, `MONGODB_URI`, `OPENAI_API_KEY`, `EMBEDDINGS_MODEL`, `VECTOR_DB_PATH`, etc. |
| **Used by** | Every layer — controllers, models, routes, stores |
| **How** | `get_settings()` creates a new `Settings()` instance which auto-reads `.env` |

---

### 2. Controllers Layer

#### `BaseController` — (controllers/BaseController.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | None (root class) |
| **Purpose** | Parent of ALL controllers — provides shared settings and filesystem paths |
| **Key Attributes** | `app_settings`, `base_dir` (src/), `file_dir` (assets/files/), `db_dir` (assets/db/) |
| **Key Methods** | `get_db_path(db_name)` → creates and returns a database subdirectory path |
| **Children** | `DataController`, `FileController`, `ProcessController`, `NlpController` |

#### `DataController` — (controllers/DataController.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | `BaseController` |
| **Purpose** | Validates uploaded files before saving |
| **Key Methods** | `validate_file(file)` → returns `(bool, message)` checking MIME type and file size |
| **Called by** | `routes/data.py → upload_file()` |

#### `FileController` — (controllers/FileController.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | `BaseController` |
| **Purpose** | Creates and resolves project-specific directories under `assets/files/` |
| **Key Methods** | `get_file_path(dir_name)` → returns full path to `assets/files/<dir_name>/` |
| **Called by** | `routes/data.py → upload_file()` and `ProcessController.__init__()` |

#### `ProcessController` — (controllers/ProcessController.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | `BaseController` |
| **Purpose** | Loads uploaded files and splits them into overlapping text chunks |
| **Key Methods** | `get_file_content(filename)` → load document, `process_files(content, ...)` → split into chunks |
| **Uses** | LangChain's `TextLoader`, `PyMuPDFLoader`, `RecursiveCharacterTextSplitter` |
| **Called by** | `routes/data.py → process_data()` |

#### `NlpController` — (controllers/NlpController.py) ⭐ Core
| Aspect | Detail |
|--------|--------|
| **Inherits** | `BaseController` |
| **Purpose** | The RAG brain — handles embedding, vector search, and LLM answer generation |
| **Constructor** | Receives `vectordb_client`, `generation_client`, `embedding_client`, `template_parser` as injected dependencies |
| **Key Methods** | `push_data_to_index()` → embed chunks & store in Qdrant |
| | `search_by_vector()` → embed query & retrieve similar chunks |
| | `answer_rag_question()` → retrieve + build prompt + generate LLM answer |
| **Called by** | `routes/nlp.py → push_data_to_index(), search_by_vector(), answer_rag(), get_project_data()` |

---

### 3. Models Layer

#### `DataBaseModel` — (models/DataBaseModel.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | None (root class for models) |
| **Purpose** | Base class for all MongoDB model classes — stores the database client |
| **Key Attributes** | `db_client` (Motor async database), `app_settings` |
| **Children** | `ProjectModel`, `ChunkModel` |

#### `ProjectModel` — (models/ProjectModel.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | `DataBaseModel` |
| **Purpose** | CRUD operations for the `projects` MongoDB collection |
| **Key Methods** | `create_project()`, `get_project_or_create_one()`, `get_project()`, `get_all_projects()` |
| **Collection** | `projects` |

#### `ChunkModel` — (models/ChunkModel.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | `DataBaseModel` |
| **Purpose** | CRUD operations for the `chunks` MongoDB collection |
| **Key Methods** | `insert_many_chunks()` (batch insert), `get_chunks_by_project_id()` (paginated fetch), `delete_chunks_by_project_id()` |
| **Collection** | `chunks` |

#### `Project` — (models/db_schemes/project.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | `pydantic.BaseModel` |
| **Purpose** | Pydantic schema for a MongoDB project document |
| **Fields** | `id` (ObjectId, alias "_id"), `project_id` (str, alphanumeric only) |
| **Validator** | `project_id` must be alphanumeric (used as directory name) |

#### `DataChunk` — (models/db_schemes/data_chunk.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | `pydantic.BaseModel` |
| **Purpose** | Pydantic schema for a MongoDB chunk document |
| **Fields** | `id`, `chunk_text`, `chunk_metadata`, `chunk_order`, `chunk_project_id` |

#### `RetrievalDocument` — (models/db_schemes/data_chunk.py)
| Aspect | Detail |
|--------|--------|
| **Inherits** | `pydantic.BaseModel` |
| **Purpose** | Lightweight search result — just text and similarity score |
| **Fields** | `text` (str), `score` (float) |

---

### 4. Routes Layer

#### `routes/base.py` — Health Check
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/` | GET | Returns welcome message with app name and version |

#### `routes/data.py` — Data Upload & Processing
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/data/upload/{dir_name}` | POST | Upload a file and create a project |
| `/api/data/process/{project_id}` | POST | Load file, split into chunks, store in MongoDB |

#### `routes/nlp.py` — RAG Pipeline
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/nlp/index/push/{project_id}` | POST | Embed chunks and push to Qdrant |
| `/api/nlp/index/info/{project_id}` | GET | Check if vector collection exists |
| `/api/nlp/index/search/{project_id}` | POST | Semantic similarity search |
| `/api/nlp/index/answer/{project_id}` | POST | Full RAG: retrieve + generate answer |

---

### 5. Stores Layer — LLM

#### `LLMInterface` — (stores/llm/LLMInterface.py)
| Aspect | Detail |
|--------|--------|
| **Type** | Abstract Base Class (ABC) |
| **Purpose** | Contract that all LLM providers must implement |
| **Methods** | `set_generation_model()`, `set_embedding_model()`, `generate_response()`, `embed_text()`, `construct_prompt()` |
| **Pattern** | Strategy Pattern — allows swapping providers without changing controller code |

#### `LLMFactory` — (stores/llm/LLMFactory.py)
| Aspect | Detail |
|--------|--------|
| **Purpose** | Creates LLM providers based on a string name |
| **Pattern** | Factory Method Pattern |
| **Supports** | `"openai"` → OpenAIProvider, `"local_bge"` → EmbeddingProvider |

#### `OpenAIProvider` — (stores/llm/provider/OpenAIProvider.py)
| Aspect | Detail |
|--------|--------|
| **Implements** | `LLMInterface` |
| **Purpose** | Text generation + embeddings via OpenAI-compatible API |
| **Key Methods** | `generate_response()` → Chat Completions API, `embed_text()` → Embeddings API |
| **Extras** | `construct_prompt()` → build chat messages, `process_input_text()` → truncate long input |

#### `EmbeddingProvider` — (stores/llm/provider/EmbeddingProvider.py)
| Aspect | Detail |
|--------|--------|
| **Purpose** | Local text embedding using sentence-transformers (e.g. BAAI/bge-small-en) |
| **Key Methods** | `embed(text, doc_type)` → returns a float vector |
| **Feature** | Asymmetric embedding — uses "query: " prefix for queries and "passage: " for documents |
| **Attribute** | `embedding_size` → auto-detected from the model (e.g. 384) |

---

### 6. Stores Layer — VectorDB

#### `VectorDBInterface` — (stores/vectordb/VectorDBInterface.py)
| Aspect | Detail |
|--------|--------|
| **Type** | Abstract Base Class (ABC) |
| **Purpose** | Contract for all vector database providers |
| **Methods** | `connect()`, `create_collection()`, `add_document()`, `search()`, `delete_collection()`, etc. |

#### `VectorDBFactory` — (stores/vectordb/VectorDBFactory.py)
| Aspect | Detail |
|--------|--------|
| **Purpose** | Creates vector DB providers based on a string name |
| **Supports** | `"qdrant"` → QDrantDB |
| **Uses** | `BaseController.get_db_path()` to resolve the storage directory |

#### `QDrantDB` — (stores/vectordb/provider/QDrantDB.py)
| Aspect | Detail |
|--------|--------|
| **Implements** | `VectorDBInterface` |
| **Purpose** | All Qdrant operations: collections, document upload, similarity search |
| **Key Methods** | `create_collection()`, `add_documents()` (batch), `search_by_vector()` → returns `RetrievalDocument` |
| **Distance** | Supports Cosine and Dot product similarity metrics |

---

### 7. Template Layer

#### `TemplateParser` — (stores/llm/tempelate/template_parser.py)
| Aspect | Detail |
|--------|--------|
| **Purpose** | Loads and renders language-specific prompt templates |
| **Key Methods** | `set_language(lang)`, `get(group, key, vars)` |
| **Supports** | English (`en`) and Arabic (`ar`) locales |
| **Mechanism** | Uses `importlib` to dynamically import locale Python files |
| **Templates** | `system_prompt` (LLM persona), `document_prompt` ($doc_id, $text), `footer_template_prompt` |

---

### 8. Streamlit Interface

#### `interface.py` — Interactive RAG UI
| Aspect | Detail |
|--------|--------|
| **Purpose** | Streamlit web UI for interacting with all 5 RAG pipeline steps |
| **Layout** | Two columns: Left = code & theory, Right = live execution |
| **Features** | File upload, chunking controls, push to index, semantic search, RAG Q&A |
| **Connection** | Communicates with FastAPI via HTTP (port 5000) |

---

## 🎨 Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Factory Method** | `LLMFactory`, `VectorDBFactory` | Decouple creation from usage — `main.py` doesn't need to know implementation details |
| **Strategy** | `LLMInterface`, `VectorDBInterface` | Allows swapping providers (e.g. OpenAI → HuggingFace) without changing controllers |
| **Template Method** | `BaseController` | Common setup (paths, settings) lives in the parent; children add specialised behaviour |
| **Data Access Object (DAO)** | `DataBaseModel`, `ProjectModel`, `ChunkModel` | Separates MongoDB operations from business logic |
| **Dependency Injection** | `NlpController` constructor, FastAPI `Depends()` | Controllers receive their dependencies instead of creating them — easier to test and swap |
| **Repository** | `ProjectModel`, `ChunkModel` | Encapsulates all database queries behind a clean API |

---

## 📡 API Endpoints Reference

### Health Check
```http
GET /api/
Response: {"message": "Welcome to the Mini-RAG App v0.1.0!"}
```

### Upload File
```http
POST /api/data/upload/{dir_name}
Content-Type: multipart/form-data
Body: file=@document.pdf

Response: {"message": "File uploaded successfully...", "project_id": "64a3f..."}
```

### Process File (Chunking)
```http
POST /api/data/process/{project_id}
Content-Type: application/json
Body: {
    "project_id": "document.pdf",  // filename to process
    "chunk_size": 500,
    "overlap": 50,
    "do_reset": 0
}

Response: 42  // number of chunks created
```

### Push to Vector Index
```http
POST /api/nlp/index/push/{project_id}
Body: {"do_reset": 0}

Response: {"message": "Successfully pushed 42 chunks to index."}
```

### Semantic Search
```http
POST /api/nlp/index/search/{project_id}
Body: {"text": "What is cache coherence?", "top_k": 5}

Response: {
    "results": [
        {"text": "Cache coherence is...", "score": 0.92},
        {"text": "The MESI protocol...", "score": 0.87}
    ]
}
```

### RAG Answer
```http
POST /api/nlp/index/answer/{project_id}
Body: {"text": "Explain the MESI protocol.", "top_k": 5}

Response: {
    "answer": "The MESI protocol is a cache coherence protocol...",
    "full_prompt": "## Document No: 1\n### Content: ...",
    "chat_history": [{"role": "system", "content": "..."}]
}
```

### Index Info
```http
GET /api/nlp/index/info/{project_id}

Response: {"results": true}  // or false if collection doesn't exist
```

---

## 🗄️ Database Schemas

### MongoDB: `projects` collection
```json
{
    "_id": "ObjectId('64a3f...')",
    "project_id": "demoproject"
}
```

### MongoDB: `chunks` collection
```json
{
    "_id": "ObjectId('64a3g...')",
    "chunk_text": "Cache coherence ensures that...",
    "chunk_metadata": {"source": "lecture.pdf", "page": 3},
    "chunk_order": 1,
    "chunk_project_id": "ObjectId('64a3f...')"
}
```

### Qdrant: `collection_<project_id>` 
```json
{
    "id": 0,
    "vector": [0.012, -0.034, 0.056, ...],  // 384 dimensions
    "payload": {
        "text": "Cache coherence ensures that...",
        "metadata": {"source": "lecture.pdf", "page": 3}
    }
}
```

---

## ⚙️ Environment Variables

Create a `.env` file in the `src/` directory (see `.env.example`):

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_NAME` | Application name | `Mini-RAG` |
| `APP_VERSION` | Version string | `0.1.0` |
| `FILE_ALLOWED_EXTENSIONS` | Allowed MIME types | `["plain/text", "application/pdf"]` |
| `FILE_MAX_SIZE_MB` | Max upload size (MB) | `10` |
| `FILE_CHUNK_SIZE` | Bytes per read chunk | `512000` |
| `MONGODB_URI` | MongoDB connection URI | `mongodb://admin:admin@localhost:27007` |
| `MONGODB_DB_NAME` | Database name | `mini_rag` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `OPENAI_API_BASE` | API base URL | `https://api.openai.com/v1` |
| `GENERATE_RESPONSE_MODEL` | LLM model name | `gemma2:9b-instruct-q5_0` |
| `EMBEDDINGS_MODEL` | Embedding model | `BAAI/bge-small-en` |
| `EMBEDDING_DIMENSION` | Vector dimensions | `384` |
| `MAX_INPUT_TOKENS` | Max input characters | `1000` |
| `MAX_RESPONSE_TOKENS` | Max output tokens | `500` |
| `TEMPERATURE` | LLM temperature | `0.1` |
| `VECTOR_DB_PATH` | Qdrant storage path | `qdrant_data` |
| `VECTOR_DISTANCE_METRIC` | Distance metric | `Cosine` |

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.8+**
- **Docker & Docker Compose** (for MongoDB and Qdrant)

### Step 1: Start Infrastructure Services
```bash
cd docker
docker-compose up -d
```
This starts:
- **MongoDB** on port `27007`
- **Qdrant** on port `6333`

### Step 2: Install Python Dependencies
```bash
cd src
pip install -r requirements.txt
```

### Step 3: Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

---

## ▶️ How to Run

### Start the FastAPI Backend
```bash
cd src
uvicorn main:app --reload --port 5000
```
- API docs available at: `http://localhost:5000/docs`

### Start the Streamlit Interface (Optional)
```bash
cd src
streamlit run interface.py
```
- Opens in browser at: `http://localhost:8501`

---

## 📦 Requirements

```
fastapi[standard]==0.110.2
uvicorn[standard]==0.29.0
python-multipart==0.0.9
pydantic-settings==2.2.1
aiofiles==23.2.1
langchain==0.1.20
Pymupdf==1.24.3
motor==3.4.0
openai==1.35.15
qdrant-client==1.10.1
sentence-transformers (for EmbeddingProvider)
streamlit (for the interface)
```

---

## 📄 License

This project is for educational purposes.

---

> **Built with ❤️ for learning** — Every file in this project is fully commented to help students understand the complete RAG pipeline from source code to AI-powered answers.