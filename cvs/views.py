from django.http import HttpResponse
from django.template import loader
import json

from .models import CV
from .cv_tools import format_cv_past_experience, find_similar_cvs, summarise_cv


def cv_index(request):
    cvs_list = CV.objects.order_by("name")

    template = loader.get_template("cvs/index.html")
    context = {"cv_list": cvs_list}

    return HttpResponse(template.render(context, request))

def cv_details(request, cv_id):
    # use LLM to reformat experience into HTML format
    cv = CV.objects.get(pk=cv_id)
    res = format_cv_past_experience(cv)

    formatted = json.loads(res.text)
    related_cvs = json.loads(find_similar_cvs(cv)["answer"])

    template = loader.get_template("cvs/details.html")
    context = {"cv": cv, "past_exp": formatted, "related": related_cvs}

    return HttpResponse(template.render(context, request))

def cv_summary(request, cv_id):
    # use LLM to summarise CV data
    cv = CV.objects.get(pk=cv_id)

    summary_text = summarise_cv(cv).text
    related_cvs = json.loads(find_similar_cvs(cv)["answer"])

    template = loader.get_template("cvs/summary.html")
    context = {"cv": cv, "summary": summary_text, "related": related_cvs}

    return HttpResponse(template.render(context, request))
