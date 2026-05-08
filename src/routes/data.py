"""
routes/data.py File upload and processing endpoints

POST /api/data/upload Upload a file, create fetch project
POST /api/data/process Load file, chunk it, store in MongoDB
"""

import os
import aiofiles
from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import JSONResponse

from helpers.config import Settings, get_settings
from controllers.DataController import DataController
from controllers.FileController import FileController
from controllers.ProcessController import ProcessController
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.db_schemes.data_chunk import DataChunk
from routes.schema.data import RequestProcess


# Create router with /api/data prefix
data_router = APIRouter(prefix="/api/data", tags=["Data"])


# Endpoint 1 File Upload

@data_router.post("/upload/{dir_name}")
async def upload_file(
    request: Request,
    dir_name: str,
    file: UploadFile = File(...),
    app_settings: Settings = Depends(get_settings),
):
    """
    Upload a file and associate it with a project.

    Flow:
        1. Validate MIME type and file size   (DataController)
        2. Create project directory           (FileController)
        3. Stream-write file to disk          (aiofiles)
        4. Create/fetch project in MongoDB    (ProjectModel)
    """
    # Step 1 Validate the uploaded file
    data_controller = DataController()
    is_valid, error_msg = data_controller.validate_file(file)

    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={"error_msg": error_msg},
        )

    # Step 2 Resolve project directory
    file_controller = FileController()
    project_dir = file_controller.get_file_path(dir_name)

    # Step 3 Stream write file to disk chunk by chunk
    file_path = os.path.join(project_dir, file.filename)

    async with aiofiles.open(file_path, "wb") as out_file:
        while chunk := await file.read(app_settings.FILE_CHUNK_SIZE):
            await out_file.write(chunk)

    # Step 4 Create or fetch the project in MongoDB
    project_model = ProjectModel(db_client=request.app.mongodb)
    project = await project_model.get_project_or_create_one(project_id=dir_name)

    return JSONResponse(
        status_code=200,
        content={
            "message": f"File '{file.filename}' uploaded successfully to project '{dir_name}'.",
            "project_id": str(project.id),
            "file_name": file.filename,
        },
    )


# Endpoint 2 File Processing Chunking

@data_router.post("/process/{project_id}")
async def process_data(
    request: Request,
    project_id: str,
    process_request: RequestProcess,
):
    """
    Load a previously uploaded file, split it into chunks,
    and store the chunks in MongoDB.

    Flow:
        1. (Optional) Delete existing chunks if do_reset=1
        2. Load file content via ProcessController
        3. Split into overlapping chunks
        4. Batch-insert chunks into MongoDB
    """
    # Get MongoDB models
    project_model = ProjectModel(db_client=request.app.mongodb)
    chunk_model = ChunkModel(db_client=request.app.mongodb)

    # Fetch the project
    project = await project_model.get_project_or_create_one(project_id=project_id)

    # Step 1 Optionally reset existing chunks
    if process_request.do_reset == 1:
        deleted = await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )

    # Step 2 Load file content
    process_controller = ProcessController(project_id=project_id)
    file_content = process_controller.get_file_content(
        file_name=process_request.file_name
    )

    if file_content is None:
        return JSONResponse(
            status_code=400,
            content={
                "error_msg": (
                    f"Unsupported or missing file: '{process_request.file_name}'. "
                    f"Supported formats: .txt, .pdf, .docx, .html"
                )
            },
        )

    if not file_content:
        return JSONResponse(
            status_code=400,
            content={"error_msg": "File is empty or could not be read."},
        )

    # Step 3 Chunk the content
    chunks = process_controller.process_files(
        file_content=file_content,
        file_name=process_request.file_name,
        chunk_size=process_request.chunk_size,
        overlap=process_request.overlap,
    )

    if not chunks:
        return JSONResponse(
            status_code=400,
            content={"error_msg": "No chunks were generated from the file."},
        )

    # Step 4 Convert to DataChunk objects and batch insert
    data_chunks = [
        DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=idx,
            chunk_project_id=project.id,
        )
        for idx, chunk in enumerate(chunks)
    ]

    inserted_count = await chunk_model.insert_many_chunks(data_chunks)

    return JSONResponse(
        status_code=200,
        content={
            "message": f"File processed successfully. {inserted_count} chunks created.",
            "chunks_count": inserted_count,
            "project_id": str(project.id),
            "file_name": process_request.file_name,
            "chunk_size": process_request.chunk_size,
            "overlap": process_request.overlap,
        },
    )
