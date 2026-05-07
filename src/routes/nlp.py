from fastapi import APIRouter, Request, HTTPException
from routes.schema.nlp import PushDataRequest, SearchRequest, AnswerRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers.NlpController import NlpController
from stores.vectordb.VectorDBFactory import VectorDBFactory
from stores.llm.LLMFactory import LLMFactory
from stores.llm.tempelate.template_parser import TemplateParser
from helpers.config import get_settings

nlp_router = APIRouter(
    prefix="/api/nlp/index",
    tags=["NLP Pipeline"]
)

# Initialize dependencies. In a real app this might use FastAPI Depends.
settings = get_settings()
vectordb_client = VectorDBFactory.create(provider_type=settings.VECTOR_DB_PROVIDER)
generation_client = LLMFactory.create(provider_type=settings.LLM_PROVIDER)
embedding_client = LLMFactory.create(provider_type=settings.EMBEDDING_PROVIDER)
template_parser = TemplateParser()

nlp_controller = NlpController(
    vectordb_client=vectordb_client,
    generation_client=generation_client,
    embedding_client=embedding_client,
    template_parser=template_parser
)

@nlp_router.post("/push/{project_id}")
async def push_data_to_index(request: Request, project_id: str, payload: PushDataRequest):
    project_model = ProjectModel(request.app.mongodb)
    project = await project_model.get_project_or_create_one(project_id)
    if not project:
        raise HTTPException(status_code=400, detail="Could not create or get project")
        
    chunk_model = ChunkModel(request.app.mongodb)
    
    success, message = await nlp_controller.push_data_to_index(
        project=project,
        chunk_model=chunk_model,
        do_reset=bool(payload.do_reset)
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return {"message": message}

@nlp_router.get("/info/{project_id}")
async def get_index_info(request: Request, project_id: str):
    project_model = ProjectModel(request.app.mongodb)
    project = await project_model.get_project_or_create_one(project_id)
    collection_name = f"collection_{project.project_id}"
    
    exists = nlp_controller.vectordb_client.has_collection(collection_name)
    return {"results": exists}

@nlp_router.post("/search/{project_id}")
async def search_by_vector(request: Request, project_id: str, payload: SearchRequest):
    project_model = ProjectModel(request.app.mongodb)
    project = await project_model.get_project_or_create_one(project_id)
    
    results = await nlp_controller.search_by_vector(
        project=project,
        text=payload.text,
        top_k=payload.top_k
    )
    
    return {"results": [{"text": doc.text, "score": doc.score} for doc in results]}

@nlp_router.post("/answer/{project_id}")
async def answer_rag(request: Request, project_id: str, payload: AnswerRequest):
    project_model = ProjectModel(request.app.mongodb)
    project = await project_model.get_project_or_create_one(project_id)
    
    answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
        project=project,
        text=payload.text,
        top_k=payload.top_k,
        lang=payload.lang,
        model=payload.model
    )
    
    if not answer:
        raise HTTPException(status_code=400, detail="Failed to generate answer. Check if index is built.")
        
    return {
        "answer": answer,
        "full_prompt": full_prompt,
        "chat_history": chat_history
    }
