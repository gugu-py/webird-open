from django.shortcuts import render, redirect, HttpResponse
from django import forms
from .models import Img
from django.views.decorators.csrf import csrf_exempt


class ImageForm(forms.ModelForm):
    class Meta:
        model = Img
        fields = ('ori_img',)


class DistributionForm(forms.Form):
    img = forms.ImageField()


def upload_image(request):
    return render(request, 'upload_image.html')


@csrf_exempt
def receive_img(request):
    form = ImageForm(request.POST, request.FILES)
    if form.is_valid():
        result = form.save()
        return render(request, 'copy_redirect.html', {'link': result.link})
    print("not valid image")
    return redirect('/img/add/')


# @csrf_exempt
# def receive_distribution(request):
#     form = DistributionForm(request.POST, request.FILES)
#     if form.is_valid():
#         img = form.cleaned_data['img']
#         img_name = img.name
#         try:
#             target = Distribution.objects.get(img=img_name)
#             target.img.save(img_name, img, save=True)
#         except Distribution.DoesNotExist:
#             Distribution.objects.create(img=img)
#         return HttpResponse("NICE!")
#     print("not valid image")
#     return redirect('/img/add/')


def image_list(request):
    images = Img.objects.all()
    # distrs = Distribution.objects.all()
    # aa = Img.objects.get(id=11)
    # print(aa.sml_img.url)
    return render(request, 'image_list.html', {'images': images, })
