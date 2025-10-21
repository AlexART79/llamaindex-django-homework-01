from .call_llm import call_llm_cached
from .models import CV

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
    # TODO: replace prompt to return JSON array and then format it to HTML in Python code
    prompt = f"""
            Reformat the following CV data into a well-structured HTML section.
            Each item of past experience should be a separate block of code.
            Desired format example:

            <div class="col">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title text-primary">Job Role at CompanyName</h5>
                        <p><strong>Responsibilities:</strong> responsibilities at the company</p>
                        <p><strong>Achievements:</strong> achievements at the company</p>
                        <p><strong>Challenges:</strong> challenges faced at the company</p>
                    </div>
                </div>
            </div>

            Do not include ```html at the beginning and ``` at the end!

            Input CV data:
            {cv.past_experience}
            """

    res = call_llm_cached(prompt)
    return res