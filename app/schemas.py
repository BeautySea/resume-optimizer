from typing import List, Dict, Union

from langchain_core.pydantic_v1 import BaseModel, Field


class First(BaseModel):
    personal_information: Union[Dict[str, str], None] = Field(
        description='Extract a Python dictionary of the personal information in the resume. The following keys are full_name, email, phone, address, linkedin, personal_website')
    education: Union[List[Dict[str, str]], None] = Field(
        description='Generate a List of dictionaries containing the education detail in the resume. The following keys in the dictionary are institution, degree, field_of_study, start_date, end_date.')
    objective: str



class Second(BaseModel):
    work_experience: Union[List[Dict[str, str]], None] = Field(
        description='Extract a List of dictionaries containing the work experience. The following keys in the dictionary are company, position, start_date, end_date, responsibility.')


class Third(BaseModel):
    skills: Union[List[Dict[str, str]], None] = Field(description='Generate a List of dictionaries containing the skills. The following keys in the dictionary are name, proficiency_level, years_of_experience')
    certifications: Union[List[Dict[str, str]], None] = Field(
        description='Generate a List of dictionaries containing the certifications. The following keys in the dictionary are name, issuing_organization, issue_date, expiry_date')
    job_description_skills: Union[List[Dict[str, str]], None] = Field(description='Generate a List of dictionaries containing the job_description_skills. The following keys in the dictionary are name, proficiency_level, years_of_experience')
    

class FirstObjectiveWorkExperience(BaseModel):
    work_experience: Union[List[Dict[str, str]], None] = Field(
        description='Extract a List of dictionaries containing the work experience. The following keys in the dictionary are company, position, start_date, end_date, and new_responsibility.')
