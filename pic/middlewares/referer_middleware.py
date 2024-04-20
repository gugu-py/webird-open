from django.shortcuts import render, redirect, HttpResponse


class RefererMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        referer = request.META.get('HTTP_REFERER')
        allowed_referer = 'localhost'  # 允许访问的域名

        if referer and not referer.startswith(allowed_referer):
            return HttpResponse('你干嘛哎哟')  # 如果Referer不匹配，返回403禁止访问

        return self.get_response(request)