from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
class SimpleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)
        path = str(request.path)
        if not request.user.is_authenticated and not path.startswith('/login/') and not path.startswith('/recuperar_senha/'):
            return HttpResponseRedirect('/login/')
        if request.user.is_authenticated and path == '/':
            return HttpResponseRedirect('/index/')
            
        # Code to be executed for each request/response after
        # the view is called.

        return response