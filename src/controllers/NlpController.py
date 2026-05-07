import math
from controllers.BaseController import BaseController
from models.db_schemes.project import Project
from stores.llm.LLMInterface import LLMInterface
from stores.vectordb.VectorDBInterface import VectorDBInterface
from stores.llm.tempelate.template_parser import TemplateParser
from models.ChunkModel import ChunkModel

class NlpController(BaseController):
    def __init__(
        self,
        vectordb_client: VectorDBInterface,
        generation_client: LLMInterface,
        embedding_client: LLMInterface,
        template_parser: TemplateParser,
    ):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    async def push_data_to_index(self, project: Project, chunk_model: ChunkModel, do_reset: bool = False):
        collection_name = f"collection_{project.project_id}"
        
        if do_reset and self.vectordb_client.has_collection(collection_name):
            self.vectordb_client.delete_collection(collection_name)
            
        if not self.vectordb_client.has_collection(collection_name):
            self.vectordb_client.create_collection(
                collection_name=collection_name,
                embedding_size=int(self.app_settings.EMBEDDING_DIMENSION),
                distance_metric=self.app_settings.VECTOR_DB_DISTANCE_METRIC
            )

        total_chunks = await chunk_model.get_total_chunks_count(project.id)
        if total_chunks == 0:
            return False, "No chunks found for this project."

        page_size = 50
        pages = math.ceil(total_chunks / page_size)
        total_pushed = 0

        for page in range(1, pages + 1):
            chunks = await chunk_model.get_chunks_by_project_id(project.id, page, page_size)
            if not chunks:
                continue
                
            vectors = []
            for chunk in chunks:
                vector = await self.embedding_client.embed_text(chunk.chunk_text, document_type="document")
                if vector:
                    vectors.append(vector)
                else:
                    vectors.append([0.0]*int(self.app_settings.EMBEDDING_DIMENSION))
            
            success = self.vectordb_client.add_documents(collection_name, chunks, vectors)
            if success:
                total_pushed += len(chunks)

        return True, f"Successfully pushed {total_pushed} chunks to index."

    async def search_by_vector(self, project: Project, text: str, top_k: int = 5):
        collection_name = f"collection_{project.project_id}"
        if not self.vectordb_client.has_collection(collection_name):
            return []
            
        vector = await self.embedding_client.embed_text(text, document_type="query")
        if not vector:
            return []
            
        results = self.vectordb_client.search_by_vector(collection_name, vector, top_k)
        return results

    async def answer_rag_question(self, project: Project, text: str, top_k: int = 5, lang: str = "en", model: str = None):
        if model:
            self.generation_client.set_generation_model(model)
            
        self.template_parser.set_language(lang)
        retrieved_docs = await self.search_by_vector(project, text, top_k)
        
        if not retrieved_docs:
            return None, "", []
            
        docs_text = ""
        for i, doc in enumerate(retrieved_docs):
            docs_text += self.template_parser.get("document_prompt", doc_id=i+1, text=doc.text)
            
        system_prompt = self.template_parser.get("system_prompt", documents=docs_text)
        user_prompt = self.template_parser.get("footer_prompt", question=text)
        
        chat_history = [self.generation_client.construct_prompt(system_prompt, "system")]
        
        answer = await self.generation_client.generate_response(
            prompt=user_prompt,
            chat_history=chat_history,
            max_tokens=self.app_settings.MAX_RESPONSE_TOKENS,
            temperature=self.app_settings.TEMPERATURE
        )
        
        full_prompt = system_prompt + "\n" + user_prompt
        return answer, full_prompt, chat_history
