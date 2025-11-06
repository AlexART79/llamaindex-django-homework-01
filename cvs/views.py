from django.http import HttpResponse, HttpResponseBadRequest, StreamingHttpResponse
from django.template import loader
import json

from django.views.decorators.csrf import csrf_exempt

from .models import CV
from .cv_tools import format_cv_past_experience, find_similar_cvs, summarise_cv
from .query import agent_runner


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

def ai_chat(request):
    template = loader.get_template("cvs/chat.html")
    context = {"cv_list": ""}

    return HttpResponse(template.render(context, request))

@csrf_exempt  # if you POST; SSE must use GET, so you can also read from querystring
def ai_chat_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            prompt = data.get("message", "").strip()
        except Exception:
            return HttpResponseBadRequest("Invalid JSON")
    else:
        prompt = (request.GET.get("message") or "").strip()

    if not prompt:
        return HttpResponseBadRequest("Empty prompt")

    async def event_stream():
        # Important: send initial headers and keepalive comments
        yield ":ok\n\n"  # SSE comment to open the stream early

        r = await agent_runner(prompt)

        # replace new line character with empty str
        data = r.response.content.replace("\n", "")
        yield f"data: {data}\n\n"

        # Signal end (optional)
        yield "event: done\ndata: [DONE]\n\n"

    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")

    # Prevent buffering by proxies/servers
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"  # for nginx
    return resp
