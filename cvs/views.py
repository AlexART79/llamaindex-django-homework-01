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
    from .cv_tools import format_cv_past_experience, find_similar_cvs

    cv = CV.objects.get(pk=cv_id)
    res = format_cv_past_experience(cv)

    import json
    formatted = json.loads(res.text)

    cv = CV.objects.get(pk=cv_id)

    import json
    related_cvs = json.loads(find_similar_cvs(cv)["answer"])

    template = loader.get_template("cvs/details.html")
    context = {"cv": cv, "past_exp": formatted, "related": related_cvs}

    return HttpResponse(template.render(context, request))

def summary(request, cv_id):
    # use LLM to summarise CV data
    from .cv_tools import summarise_cv, find_similar_cvs

    cv = CV.objects.get(pk=cv_id)
    res = summarise_cv(cv)

    summary_text = res.text

    import json
    related_cvs = json.loads(find_similar_cvs(cv)["answer"])

    template = loader.get_template("cvs/summary.html")
    context = {"cv": cv, "summary": summary_text, "related": related_cvs}

    return HttpResponse(template.render(context, request))
