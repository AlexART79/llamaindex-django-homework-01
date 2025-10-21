from django.http import HttpResponse
from django.template import loader

from .models import CV
from .query import search_cvs

def index(request):
    cvs_list = CV.objects.order_by("name")
    template = loader.get_template("cvs/index.html")
    context = {"cv_list": cvs_list}
    return HttpResponse(template.render(context, request))

def details(request, cv_id):
    # use LLM to reformat past experience into HTML format
    from .cv_tools import format_cv_past_experience

    cv = CV.objects.get(pk=cv_id)
    res = format_cv_past_experience(cv)

    from django.utils.safestring import mark_safe
    formatted = mark_safe(res.text)

    template = loader.get_template("cvs/details.html")
    context = {"cv": cv, "formatted_experience": formatted}

    return HttpResponse(template.render(context, request))

def summary(request, cv_id):
    # use LLM to summarise CV data
    from .cv_tools import summarise_cv

    cv = CV.objects.get(pk=cv_id)
    res = summarise_cv(cv)

    summary = res.text

    similar_prompt = f"""
        Find the CVs most similar to a following summary.
        Desired response format - a list of following items:
        
        <div class="col">
        <a href="/cvs/[cv_id]/summary/" class="text-decoration-none text-dark fw-semibold d-block p-3 bg-white rounded shadow-sm hover-shadow">
        [cv_name] <span class="text-muted d-block small">[cv_job_title_name]</span>
        </a>
        </div>
        <div class="col">
            ...
        </div>
        ...
        
        Summary:
        {summary}
    """
    # related = search_cvs(similar_prompt, top_k=4)["answer"]

    template = loader.get_template("cvs/summary.html")
    context = {"cv": cv, "summary": summary, }

    return HttpResponse(template.render(context, request))
