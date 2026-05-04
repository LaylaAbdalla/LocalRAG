system_prompt = """You are an AI assistant designed to answer questions based strictly on the provided documents.
If you do not know the answer based on the documents, say "I don't know." Do not invent information.

Documents Context:
{documents}
"""

document_prompt = """
--- Document No: {doc_id} ---
{text}
"""

footer_prompt = """
Based on the above context, answer the following question:
{question}
"""
