from .call_llm import call_llm_cached
from .models import CV
from .query import search_cvs


def summarise_cv(cv: CV):
    prompt = f"""
        Summarize the following CV data into a concise summary.
        Return the plain text summary only.
        
        CV Data:
        Skills: {cv.skills}
        Education: {cv.education}
        Years of commercial experience: {cv.years_of_experience}
        Past experience: {cv.past_experience}
    """

    res = call_llm_cached(prompt)
    return res

def format_cv_past_experience(cv: CV):
    output_format="""
    [
        {
            "company_name": "CompanyName",
            "job_role": "Job Role at this company",
            "responsibilities": "responsibilities at the company",
            "achievements": "achievements at the company",
            "challenges": "challenges faced at the company"
        },
        ...
    ]
    """
    prompt = f"""
        Reformat the following CV past experience data into a structured JSON array.            
        Desired output format example:
        
        {output_format}            

        Input CV data:
        {cv.past_experience}

        Do not include ```json at the beginning and ``` at the end!
    """

    res = call_llm_cached(prompt)
    return res

def find_similar_cvs(cv: CV, top_k: int = 4):
    output_format = """
        [
            {
                "id": "ID of the CV",
                "name": "Name of the CV owner",
                "job_title": {
                    "name": "Job title name of the CV owner"
                },
            },
            ...
        ]
    """

    similar_prompt = f"""
        Find {top_k} CVs that are most similar or somehow related to a provided CV details.
        Desired response format - a JSON array of following items:
        
        {output_format}        

        CV details:
            Skills: {cv.skills}
            Education: {cv.education}
            Job title: {cv.job_title.name}
            Past experience: {cv.past_experience}

        Do not include ```json at the beginning and ``` at the end!
        Do not include current CV in response!
    """

    related_cvs = search_cvs(similar_prompt, top_k=top_k)
    return related_cvs