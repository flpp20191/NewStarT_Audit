from django.db import models
from .models import OWL_Upload, OWL_Upload_Configs
from django.utils.deprecation import MiddlewareMixin

class AuditMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to execute before the view is called
        response = self.get_response(request)
        # Code to execute after the view is called
        return response
