import asyncio

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from decouple import config
import tiktoken

from app.schemas import First, Second, Third, FirstObjectiveWorkExperience


def get_number_of_tokens(documents, job_description):
    encoding = tiktoken.encoding_for_model("gpt-4o")
    # pages, job = encoding.encode(documents), encoding.encode(job_description)
    number_tokens_pages = len(encoding.encode(str(documents)))
    number_tokens_job_description = len(encoding.encode(job_description))
    return number_tokens_pages + number_tokens_job_description


async def extract_resume(pages, job_description):
   
    first_output_parser = PydanticOutputParser(pydantic_object=First)
    second_output_parser = PydanticOutputParser(pydantic_object=Second)
    third_output_parser = PydanticOutputParser(pydantic_object=Third)

    first_format_instructions = first_output_parser.get_format_instructions()
    second_format_instructions = second_output_parser.get_format_instructions()
    third_format_instructions = third_output_parser.get_format_instructions()

    first_template = """
        Extract the personal_information and education in this resume. Education is different from certificate
        
        Extract the job_title in this job_description. Extract the key_skills and qualifications in this job_description. 
        Generate a concise and compelling career objective that
        targets the extracted 'job_title', highlights the relevant skills from the 'key_skills' that Conveys the candidate's career 
        goals and how they align with the target position. 
      
        Step by step Extract the work_experience comprehensively in this resume.  

        The resume is: {first_documents}
        The job_description is: {job_description}   

        Format instructions: {format_instructions}

        """
    first_prompt = PromptTemplate(
        template=first_template,
        input_variables=["first_documents", "job_description"],
        partial_variables={"format_instructions": first_format_instructions})

   
    second_template = """
    Extract the work_experience in this resume. 
    
       
    The resume is: {second_documents}. 

    Format instructions: {format_instructions}

            """
    second_prompt = PromptTemplate(
        template=second_template,
        input_variables=["second_documents",],
        partial_variables={"format_instructions": second_format_instructions})


    third_template = """Extract the certifications in this resume. Extract the skills and tools in this resume. A tool is a skill.
    Extract the job_description_skills in this job_description. 
    When there are more than one skill on a statement, separate a single skill by the comma. 
    The response for the skills, should be one skill per line, proficiency_level, and years_of_experience. 

    For examples:
        statement: AWS, Microsoft Azure
        Response: 
            skill: AWS
            proficiency_level: Advanced
            years_of_experience: 5

            skill: Microsoft Azure
            proficiency_level: Advanced
            years_of_experience: 5

        statement: Ansible, saltstack
        Response:
            skill: Ansible
            proficiency_level: Advanced
            years_of_experience: 4

            skill: Saltstack
            proficiency_level: Advanced
            years_of_experience: 5


    The resume is: {third_documents}  
    The job_description is: {job_description} 

    Format instructions: {format_instructions}

    """
    third_prompt = PromptTemplate(
        template=third_template,
        input_variables=["third_documents", "job_description"],
        partial_variables={"format_instructions": third_format_instructions})
    
    llm = ChatOpenAI(openai_api_key=config("OPENAI_API_KEY"), temperature=0.0, model_name='gpt-4-0125-preview', max_tokens=4096)
    llm_second_prompt = ChatOpenAI(openai_api_key=config("OPENAI_API_KEY"), temperature=0.1, model_name='gpt-4-0125-preview', max_tokens=4096)

    first = first_prompt | llm | first_output_parser
    second = second_prompt | llm | second_output_parser
    third = third_prompt | llm | third_output_parser

    tasks = [first.ainvoke({"first_documents": pages, "job_description": job_description}),
             second.ainvoke({"second_documents": pages, }),
             third.ainvoke({"third_documents": pages, "job_description": job_description})
             ]

    list_of_tasks = await asyncio.gather(*tasks)

    # db.delete_collection()
    return list_of_tasks


async def rewrite_resume(pages, job_description, number_of_responsibilities):
    first_objective_output_parser = PydanticOutputParser(pydantic_object=FirstObjectiveWorkExperience)
    
    first_objective_format_instructions = first_objective_output_parser.get_format_instructions()
   
    first_objective_template = """
     
    
    Write {number_of_responsibilities} sentences and paragraphs for new_responsibility based on the job_title in this job_description, the key_skills in this job_description, 
    and the the qualifications in this job_description. The company name in the job_description should not be mentioned Don't mention the company name in the job_description. The new_responsibility should explain how their work_experience will make them valuable in this job_title
    and help them grow into this key_skills and the qualifications. 
    Focus on quantifiable achievements, technical proficiencies, and relevant industry experience (if applicable). 
    
    For example: 
        company: Thanos Consulting LLC
        position: Security Engineer
        start_date: November 2015
        end_date: September 2017
        responsibility:
            Managed 10+ AWS & GCP account with multiple VPCs in different environments (prod & non-prod) and
            700+ servers. Worked as IAM admin, creating new IAM users & groups, defining roles and policies, 
            Identity providers and KMS. Produced comprehensive architecture strategy for environment mapping in AWS that 
            involved Active Directory, LDAP, AWS Identity and Access Management (IAM) Role for AWS API Gateway platform. 
            Utilized tools like EvidentIO, CloudCustodian, Dome9 and Cloudhealth to manage, analyze health and keep track 
            on security of AWS.    
        
        new_responsibility:
            Leveraged deep understanding of networking protocols (TCP/IP, DNS, DHCP) and firewall configurations to enhance
            security posture across the AWS & GCP environments, implementing and managing ACLs and VPNs for secure access 
            control within and between cloud resources. Implemented robust backup and recovery procedures for critical 
            network devices and cloud infrastructure, ensuring business continuity and minimizing downtime in case of 
            system failures or security incidents.
        

    The resume is: {second_documents}. The job description is: {job_description}

    Format instructions: {format_instructions}

            """
    first_objective_prompt = PromptTemplate(
        template=first_objective_template,
        input_variables=["second_documents", "job_description", "number_of_responsibilities"],
        partial_variables={"format_instructions": first_objective_format_instructions})


    llm = ChatOpenAI(openai_api_key=config("OPENAI_API_KEY"), temperature=0.0, model_name='gpt-4-0125-preview', max_tokens=4096)
    llm_second_prompt = ChatOpenAI(openai_api_key=config("OPENAI_API_KEY"), temperature=0.1, model_name='gpt-4o', max_tokens=4096)

    first_objective = first_objective_prompt | llm_second_prompt | first_objective_output_parser
    
    tasks = [
             first_objective.ainvoke({"second_documents": pages, "job_description": job_description, "number_of_responsibilities": number_of_responsibilities}),
             
             ]

    list_of_tasks = await asyncio.gather(*tasks)
    
    return list_of_tasks





