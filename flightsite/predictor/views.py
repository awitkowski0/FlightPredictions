from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.http import HttpResponse


def index(request):
    template = loader.get_template('predictor/index.html')

    return HttpResponse(template.render(request))
