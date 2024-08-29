import os
import asyncio
from typing import Annotated, Union

import requests
from fastapi import FastAPI, UploadFile, File, status, Form, Response, Header
from fastapi.middleware.cors import CORSMiddleware

from docx import Document as Doc
from pypdf import PdfReader
from langchain_core.documents.base import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .prompts import rewrite_resume, extract_resume

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

URL = "https://quick-apply-b4e936c5c50c.herokuapp.com/api/v1/users/verifications"


def check_doc_type(document: Annotated[UploadFile, File()]):
    if document.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        docs = Doc(document.file)
        paragraphs = [paragraph.text for paragraph in docs.paragraphs]
        texts = " ".join(paragraphs)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False
        )
        pages = text_splitter.create_documents([texts])
        return pages
    elif document.content_type == "application/pdf":
        reader = PdfReader(document.file)
        pages = [Document(page_content=page.extract_text()) for page_number, page in enumerate(reader.pages)]
        return pages


@app.post("/rewrite/", status_code=status.HTTP_201_CREATED)
async def rewrite(resume: Annotated[UploadFile, File()], job_description: Annotated[str, Form()], 
                  authorization: Annotated[Union[str, None], Header(name="Authorization")], response: Response):
    
    verification_response = requests.get(url=URL, headers={"Authorization": authorization})
    if verification_response.text == "OK":
        
        pages = check_doc_type(resume)
        result = await extract_resume(pages=pages, job_description=job_description)
        
        extracted_work_experiences = result[1].work_experience
        
        tasks = []
        for experience in extracted_work_experiences[:1]:
            responsibility = experience["responsibility"]
            updated_responsibilities = responsibility.split(". ")
            number_of_responsibilities = len(updated_responsibilities)
            tasks.append(rewrite_resume(pages=experience, job_description=job_description, number_of_responsibilities=number_of_responsibilities))
            number_of_responsibilities = 0
            
        
        
        list_of_tasks = await asyncio.gather(*tasks)
        list_of_tasks = list_of_tasks[0][0].work_experience + extracted_work_experiences[1:]
        
        processed_work_experiences = []
        for index, experience in enumerate(list_of_tasks):
            if index < 1:  
                rewritten_responsibility = experience["new_responsibility"]
                updated_rewritten_responsibilities = rewritten_responsibility.split(". ")
                experience["new_responsibility"] = [{"new_responsibility": responsibility} for responsibility in updated_rewritten_responsibilities]
            else:
                rewritten_responsibility = experience["responsibility"]
                updated_rewritten_responsibilities = rewritten_responsibility.split(". ")
                experience["responsibility"] = [{"responsibility": responsibility} for responsibility in updated_rewritten_responsibilities]
            
            processed_work_experiences.append(experience)
            
        job_description_skills = result[2].job_description_skills
        result[2].skills = result[2].skills + job_description_skills

        processed_skills = []
        unique_skills = set()
        for skill in result[2].skills:
            value = skill.get("name")
            if value in unique_skills:
                pass
            elif value not in unique_skills:
                unique_skills.add(value)
                processed_skills.append(skill)


        response = {
            "personal_information": result[0].personal_information,
            "education": result[0].education,
            "objective": result[0].objective,
            "processed_work_experience": processed_work_experiences,
            "skills": processed_skills,
            "certifications": result[2].certifications,
            "work_experience": extracted_work_experiences
        }
        return {"data": response, "status": status.HTTP_201_CREATED}
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return {"data": "Error", "status": status.HTTP_401_UNAUTHORIZED, "message": "Not Authorized"}

