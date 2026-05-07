"""
ProcessController Loads uploaded files and splits them into
overlapping text chunks for downstream embedding and indexing

Supports
    txt files LangChain TextLoader
    pdf files LangChain PyMuPDFLoader
    docx files python docx based loader
"""

import os
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from controllers.BaseController import BaseController
from controllers.FileController import FileController


class ProcessController(BaseController):
    """
    Handles the second stage of the ingestion pipeline:
    1. Loading raw file content into LangChain Document objects.
    2. Splitting those documents into overlapping chunks using
       RecursiveCharacterTextSplitter.
    """

    def __init__(self, project_id: str):
        """
        Args:
            project_id: the project folder name under assets/files/.
        """
        super().__init__()

        # Resolve the project's file directory
        file_controller = FileController()
        self.project_path = file_controller.get_file_path(project_id)

    # File extension detection

    @staticmethod
    def get_file_extension(file_name: str) -> str:
        """Return the lowercase file extension (e.g. '.pdf')."""
        return os.path.splitext(file_name)[-1].lower()

    # Loader factory picks the right LangChain loader by extension

    def get_file_loader(self, file_name: str):
        """
        Return the appropriate LangChain document loader for a file.

        Args:
            file_name: name of the file (within the project directory).

        Returns:
            A loader instance, or None if the extension is unsupported.
        """
        file_path = os.path.join(self.project_path, file_name)
        ext = self.get_file_extension(file_name)

        if ext == ".txt":
            return TextLoader(file_path, encoding="utf-8")

        if ext == ".pdf":
            return PyMuPDFLoader(file_path)

        if ext == ".docx":
            return self._load_docx(file_path)

        return None

    # Content loading

    def get_file_content(self, file_name: str) -> list[Document] | None:
        """
        Load a file and return its content as LangChain Documents.

        Args:
            file_name: name of the file in the project directory.

        Returns:
            List of Document objects, or None if loader unavailable.
        """
        loader = self.get_file_loader(file_name)

        if loader is None:
            return None

        # .docx returns documents directly (no .load())
        if isinstance(loader, list):
            return loader

        try:
            return loader.load()
        except FileNotFoundError:
            return None

    # Chunking

    def process_files(
        self,
        file_content: list[Document],
        file_name: str,
        chunk_size: int = 100,
        overlap: int = 20,
    ) -> list[Document]:
        """
        Split loaded documents into overlapping text chunks.

        Uses RecursiveCharacterTextSplitter which tries to split on
        paragraph breaks sentence endings word boundaries characters
        preserving semantic coherence as much as possible

        Args:
            file_content : list of LangChain Document objects from a loader.
            file_name    : original filename (added to chunk metadata).
            chunk_size   : maximum number of characters per chunk.
            overlap      : number of characters shared between consecutive chunks.

        Returns:
            List of chunked Document objects with metadata.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
        )

        # Inject source filename into each document's metadata
        for doc in file_content:
            doc.metadata = doc.metadata or {}
            doc.metadata["source_file"] = file_name

        chunks = text_splitter.create_documents(
            texts=[doc.page_content for doc in file_content],
            metadatas=[doc.metadata for doc in file_content],
        )

        return chunks

    # Private helpers

    @staticmethod
    def _load_docx(file_path: str) -> list[Document]:
        """
        Load a .docx file using python-docx and return as Documents.

        Each paragraph becomes part of the document text.
        """
        from docx import Document as DocxDocument

        docx_doc = DocxDocument(file_path)
        full_text = "\n".join(
            para.text for para in docx_doc.paragraphs if para.text.strip()
        )

        return [
            Document(
                page_content=full_text,
                metadata={"source": file_path},
            )
        ]
