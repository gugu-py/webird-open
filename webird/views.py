import codecs
import requests
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Sum
from rest_framework.response import Response
from webird import models
# from ms_brd.settings import MEDIA_URL, MEDIA_SMALL_URL, MEDIA_ORI_URL, MEDIA_DISTRIBUTION_URL
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as dj_login, logout as dj_logout
from django.contrib.auth.decorators import login_required
from webird.forms import *
import csv
import io
from rest_framework import serializers
from django.http import QueryDict
import json
from urllib.parse import urlencode
from rest_framework import generics
# from django_filters.rest_framework import DjangoFilterBackend
# from django_filters import rest_framework
from rest_framework.views import APIView

if not models.Location.objects.filter(name='unknown'):  # create the place "unknown" after launched immediately
    unknown = models.Location()
    unknown.name = 'unknown'
    unknown.display = False
    unknown.description = "records imported from external tools, like ebird, end up have this place tag."
    unknown.save()

if not models.BirdClasses.objects.filter(eng_name='not classified'):
    unknown = models.BirdClasses()
    unknown.eng_name = 'not classified'
    unknown.chi_name = '未分类'
    unknown.eng_description = 'The administrators forgot to classify these birds.'
    unknown.save()


def convert_querydict2dict(querydict):
    return dict(querydict)


class RecordsSerializer(serializers.ModelSerializer):
    bird = serializers.CharField(source='bird_id.whole_name')
    location = serializers.CharField(source='location.name')

    class Meta:
        model = models.Records
        # fields = ['date', 'num']
        fields = ['bird', 'location', 'date', 'num']
        # fields = '__all__'
        strict = True


def tmp(request):
    return render(request, 'tmp.html')


# Create your views here.
# @ratelimit(key='ip', rate='1/s')
# @throttle_classes([UserRateThrottle])
def index(request):  # the map is here首页
    # population = {}
    locations = models.Location.objects.all()
    population = models.Records.objects.values('location').annotate(total_num=Sum('num'))
    # for place in locations:
    #     place_instance = models.Location.objects.get(id=place.id)
    #     population[place] = place_instance.records_set.aggregate(Sum('num'))['num__sum']
    # blogs = models.blogs.objects.all()
    context = {
        'locations': locations,
        'population': population,
        'user': request.user,
        # 'blogs': blogs,
    }
    return render(request, 'index.html', context)
    # return HttpResponse("this is the map!")


def records(request):
    form = record_search_form(data=request.GET, num_fields=9999)
    result = models.Records.objects.all().order_by('-date')

    # if form.is_valid():
    #     result = form.search()
    # else:
    #     form = record_search_form(num_fields=9999)
    if request.GET:
        # q_dic = dict(request.GET.iterlists())
        q_dic = convert_querydict2dict(request.GET)
        del_lst = []
        for key, val in q_dic.items():
            if val == ['']:
                del_lst.append(key)
        for item in del_lst:
            q_dic.pop(item)
            # del q_dic[item]
        bird_ids = []
        if q_bird_ids := request.GET.getlist('species'):
            bird_ids = q_bird_ids
        if len(bird_ids) > 0:
            q_dic['species'] = bird_ids
        result = models.record_query(q_dic)

    paginator = Paginator(result, 10)  # Set 10 records per page
    page_number = request.GET.get('page')  # Get the current page number
    page_obj = paginator.get_page(page_number)  # Get the page object

    query_params = request.GET.copy()  # Get a mutable copy of the query parameters
    if 'page' in query_params:
        del query_params['page']  # Remove the 'page' parameter from the query parameters

    context = {
        'result': page_obj,
        'form': form,
        'query_params': query_params.urlencode(),  # Encode the query parameters as a URL-encoded string
    }
    return render(request, 'records_search_result2.html', context)


@login_required
def records_edit(request, record_id):
    record = models.Records.objects.get(id=record_id)
    if request.method == 'POST':
        record.bird_id_id = request.POST.get('species')
        record.location_id = request.POST.get('location')
        record.date = request.POST.get('date')
        record.num = request.POST.get('num')
        # record.author = request.POST.get('author')
        record.save()
        return redirect('/records/')
    form = record_edit_form(
        initial={
            'location': record.location_id,
            'species': record.bird_id_id,
            'date': record.date,
            'num': record.num,
        },
        num_fields=9999,
    )
    return render(request, 'records_edit.html', {'form': form})


# bird_class_id=6&location_id=1&location_id=2&start_date=2020-1-1&end_date=2025-1-1
# bird_id=1&bird_id=2&location_id=1&location_id=2&start_date=2020-1-1&end_date=2025-1-1
def record_api(request):
    q_dic = convert_querydict2dict(request.GET)
    record_result = models.record_query(q_dic)
    json_data = RecordsSerializer(record_result, many=True).data
    return JsonResponse(json_data, safe=False)


def record_get_csv(request, arg):
    # api_url = "http://127.0.0.1:8000/api/species-distribution/?" + arg
    # response = requests.get(api_url)
    data = models.record_query(dict(QueryDict(arg)))
    # data = json.dumps(list(records.values()))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'
    # # 创建 CSV 写入器
    response.write(codecs.BOM_UTF8)
    writer = csv.writer(response)

    # print(data[0])
    if data:
        fields = [field.name for field in models.Records._meta.fields]  # 写入 CSV 标题行
        writer.writerow(fields)
        # writer.writerow(data[0].keys())
        # 写入 CSV 数据行

        # 写入数据行
        for item in data:
            writer.writerow(item.get_row())
        return response
    else:
        return 'data is null'


def visualized_record(request):
    form = record_visualized_form(data=request.GET, num_fields=9999)
    if form.is_valid():
        query_dict = QueryDict(mutable=True)
        if bird_ids := form.cleaned_data['species']:
            for bird_id in bird_ids:
                query_dict.update({'bird_id': bird_id})
        elif bird_classes := form.cleaned_data['bird_class_ids']:
            for class_id in bird_classes:
                query_dict.update({'bird_class_ids': class_id})
        location_ids = form.cleaned_data['locations']
        for location_id in location_ids:
            query_dict.update({'location_id': location_id})
        if start_date := form.cleaned_data['start_date']:
            query_dict.update({'start_date': start_date})
        if end_date := form.cleaned_data['end_date']:
            query_dict.update({'end_date': end_date})
        query_string = query_dict.urlencode()
        context = {
            'query_string': query_string,
            'form': form,
        }
        return render(request, 'visualized_record.html', context)
    form = record_visualized_form(num_fields=99999)
    context = {
        'form': form,
    }
    return render(request, 'visualized_record_initial.html', context)


def bird_species(request):
    form = species_search_form(data=request.GET)
    result = models.BirdInfo.objects.all()
    if form.is_valid():
        result = form.search()
    else:
        form = species_search_form()
    # print(result)
    paginator = Paginator(result, 5)  # Set 10 records per page
    page_number = request.GET.get('page')  # Get the current page number
    page_obj = paginator.get_page(page_number)  # Get the page object

    query_params = request.GET.copy()  # Get a mutable copy of the query parameters
    if 'page' in query_params:
        del query_params['page']  # Remove the 'page' parameter from the query parameters
    context = {
        'form': form,
        'result': page_obj,
        'query_params': query_params.urlencode(),  # Encode the query parameters as a URL-encoded string
    }
    return render(request, 'species_search.html', context)
    # return HttpResponse("Feel free to explore the bird species here!")


def classes_view(request, bird_class_name):
    qst = Q(eng_name=bird_class_name) | Q(chi_name=bird_class_name)
    data = models.BirdClasses.objects.filter(qst)
    if data is None:
        return redirect('/404/')
    bird_class = models.BirdClasses.objects.get(qst)
    if request.method == 'POST' and request.user.is_authenticated:
        bird_class.eng_name = request.POST.get('eng_name')
        bird_class.chi_name = request.POST.get('chi_name')
        bird_class.eng_description = request.POST.get('eng_description')
        bird_class.chi_description = request.POST.get('chi_description')
        bird_class.wiki_url = request.POST.get('wiki_url')
        bird_class.save()
        # form = bird_class_add(request.POST)
        # if form.is_valid():
        #     form.save()
    related_birds = bird_class.birdinfo_set.all()
    related_birds_num = related_birds.count()
    image = models.BirdInfo.objects.get(id=related_birds.first().id).img_set.first()

    month_data = []
    for month in range(1, 13):
        month_data.append(0)
        for bird in related_birds:
            month_data[-1] += models.get_sum_data({
                'bird_id': bird.id,
                'date__month': month,
            })
    places = models.Location.objects.all()
    location = []
    location_data = []
    for place in places:
        location.append(place.whole_name())
        location_data.append(0)
        for bird in related_birds:
            location_data[-1] += models.get_sum_data({
                'bird_id': bird.id,
                'location': place,
            })

    context = {
        'bird_class': bird_class,
        'related_birds': related_birds,
        'related_birds_num': related_birds_num,
        'month_data': month_data,
        'location': location,
        'location_data': location_data,
    }
    if image:
        context['image'] = image
    if request.user.is_authenticated:
        form = bird_class_add(instance=bird_class)
        context['form'] = form
    return render(request, 'bird_class_page.html', context)


def species_view(request, species_name):
    qst = Q(eng_species=species_name) | Q(chi_species=species_name)
    data = models.BirdInfo.objects.filter(qst)
    if data is None:
        return redirect('/404/')
    bird = models.BirdInfo.objects.get(qst)
    if request.method == 'POST' and request.user.is_authenticated:
        bird.eng_species = request.POST.get('eng_species')
        bird.chi_species = request.POST.get('chi_species')
        bird.eng_description = request.POST.get('eng_description')
        bird.chi_description = request.POST.get('chi_description')
        bird.wiki_url = request.POST.get('wiki_url')
        bird.bird_class_id = request.POST.get('bird_class')
        bird.save()
        # return redirect('')
    image = bird.img_set.first()
    record_num = bird.records_set.count()
    # image = models.Img.objects.filter(qst).first()
    # record_num = models.Records.objects.filter(qst).count()
    month_data = []
    for month in range(1, 13):
        month_data.append(models.get_sum_data({
            'bird_id': bird.id,
            'date__month': month
        }))
    places = models.Location.objects.all()
    location = []
    location_data = []
    for place in places:
        location.append(place.whole_name())
        location_data.append(models.get_sum_data({
            'bird_id': bird.id,
            'location': place,
        }))
    context = {
        # 'image': image,
        'bird': bird,
        'record_num': record_num,
        'month_data': month_data,
        'location': location,
        'location_data': location_data,
        # 'MEDIA_SMALL_URL': MEDIA_SMALL_URL,
        # 'MEDIA_ORI_URL': MEDIA_ORI_URL,
        # 'MEDIA_DISTRIBUTION_URL': MEDIA_DISTRIBUTION_URL,
    }
    if image:
        context['image'] = image
    if request.user.is_authenticated:
        form = birdinfo_edit_form(
            initial={
                'eng_species': bird.eng_species,
                'chi_species': bird.chi_species,
                'chi_description': bird.chi_description,
                'eng_description': bird.eng_description,
                'wiki_url': bird.wiki_url,
                'bird_class': bird.bird_class_id,
            },
            num_fields=9999,
        )
        context['form'] = form
    return render(request, 'species_page.html', context)


def location_view(request, page_name):  # 渲染/location/地点/的函数
    data = models.Location.objects.get(name=page_name)
    if data is None:
        return redirect('/404')
    species_data = data.records_set.values('bird_id').annotate(total=Sum('num'))
    record_data = data.records_set.all()[:5]
    imgs_data = data.img_set.all()[:3]
    month_data = []
    qrule = {
        'location': data.id,
    }
    for month in range(1, 13):
        qrule['date__month'] = month
        month_data.append(models.get_sum_data(qrule))
    context = {
        'location': data,
        'species': species_data,
        'records': record_data,
        # 'Places_MAP': Places_MAP,
        'images': imgs_data,
        # 'MEDIA_SMALL_URL': MEDIA_SMALL_URL,
        'month_data': month_data,
    }
    return render(request, 'location_page.html', context)


def gallery(request):
    form = img_search_form(data=request.GET, num_fields=9999)
    result = models.Img.objects.all()
    if request.GET:
        # result = form.search()
        q_dic = convert_querydict2dict(request.GET)
        del_lst = []
        for key, val in q_dic.items():
            if val == ['']:
                del_lst.append(key)
        for item in del_lst:
            q_dic.pop(item)
        bird_filter = None
        if 'bird_id' in q_dic:
            species_ids = q_dic['bird_id']
            for species_id in species_ids:
                if bird_filter:
                    bird_filter = Q(species__id=int(species_id)) | bird_filter
                else:
                    bird_filter = Q(species__id=int(species_id))
        location_filter = None
        if 'location' in q_dic:
            location_ids = q_dic['location']
            for location_id in location_ids:
                if location_filter:
                    location_filter = Q(location=int(location_id)) | location_filter
                else:
                    location_filter = Q(location=int(location_id))
        time_interval = ['2020-1-1', '2030-1-1']
        if 'start_date' in q_dic:
            time_interval[0] = q_dic['start_date'][0]
        if 'end_date' in q_dic:
            time_interval[1] = q_dic['end_date'][0]
        # description_filter = None
        # if 'description' in q_dic and len(q_dic['description']):
        #     description_filter = Q(description__icontains=q_dic['description'])

        api_filter = Q(date__range=time_interval)
        if bird_filter:
            api_filter = bird_filter & api_filter
        if location_filter:
            api_filter = location_filter & api_filter
        # if description_filter:
        #     api_filter = description_filter & api_filter
        result = models.Img.objects.filter(api_filter).all().distinct()
    else:
        form = img_search_form(num_fields=9999)
    # print(result)
    paginator = Paginator(result, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'form': form, 'result': page_obj}
    return render(request, "gallery2.html", context)


def blogs_view(request):
    # blogs = models.blogs.objects.all()
    # context = {
    #     'blogs': blogs,
    # }
    # return render(request, 'blogs_view.html', context)
    return redirect('https://padlet.com/zxgu23/about-webird-qo0l10irz9dyiuq9')


def error_404(request):
    return render(request, "404.html")


def management(request):
    return render(request, "management.html")


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # email = request.POST['email']
        user = User.objects.create_user(username=username, password=password)
        # 其他逻辑
        return redirect('/')
    return render(request, 'register.html')


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 登录成功
            dj_login(request, user)
            return redirect('/')
        else:
            # 登录失败
            return redirect('/admin/login')
    return render(request, 'login.html')


def logout(request):
    dj_logout(request)
    return redirect("/")


@login_required
def add_birdinfo(request):
    if request.method == 'POST':
        # form = birdinfo_add_form(request.POST)
        new_bird = models.BirdInfo()
        new_bird.eng_species = request.POST.get('eng_species')
        new_bird.chi_species = request.POST.get('chi_species')
        new_bird.eng_description = request.POST.get('eng_description')
        new_bird.chi_description = request.POST.get('chi_description')
        new_bird.wiki_url = request.POST.get('wiki_url')
        # new_bird.bird_class = request.POST.get('bird_class')
        new_bird.bird_class_id = request.POST.get('bird_class')
        new_bird.save()
        # if form.is_valid():
        #     form.save()
        return redirect('/management/')
    form = birdinfo_add_form(num_fields=99999)
    return render(request, 'add_birdinfo.html', {'form': form})


def bird_exist(eng_species, chi_species):
    result = False
    if eng_species and models.BirdInfo.objects.filter(eng_species__icontains=eng_species):
        result = True
    if chi_species and models.BirdInfo.objects.filter(chi_species__icontains=chi_species):
        result = True
    return result


@login_required
def add_birdinfo_csv_verify(request):
    if request.method == 'POST':
        if request.FILES['file']:
            new_file = request.FILES['file']
            record_file_wrapper = io.TextIOWrapper(new_file, encoding='utf-8', errors='replace')
            reader = csv.reader(record_file_wrapper)
            next(reader)  # 跳过标题行
            names = []
            for row in reader:
                if bird_exist(row[0], row[1]):
                    continue
                new_row = []
                for item in row:
                    if item:
                        new_row.append(item)
                    else:
                        new_row.append('___')
                if len(new_row) != 5:
                    return HttpResponse("wrong input file format!")
                names.append(new_row)
            context = {
                'names': names,
            }
            return render(request, 'add_birdinfo_csv_verify.html', context)
    form = birdinfo_add_csv_form()
    context = {
        'form': form,
        'link': '/add_birdinfo_csv_verify/',
    }
    return render(request, 'upload_csv_birdinfo.html', context)


@login_required
def add_birdinfo_csv_upload(request):
    if request.method == 'POST':
        new_file = request.FILES['file']
        record_file_wrapper = io.TextIOWrapper(new_file, encoding='utf-8', errors='replace')
        reader = csv.reader(record_file_wrapper)
        next(reader)  # 跳过标题行
        for row in reader:
            if bird_exist(row[0], row[1]):
                continue
            new_bird = models.BirdInfo()
            new_bird.eng_species = row[0]
            new_bird.chi_species = row[1]
            new_bird.chi_description = row[2]
            new_bird.eng_description = row[3]
            new_bird.wiki_url = row[4]
            new_bird.save()
        return HttpResponse('Success! Thank u!')
    form = birdinfo_add_csv_form(request)
    context = {
        'form': form,
        'link': ''
    }
    return render(request, 'upload_csv.html', context)


@login_required
def refresh_distribution_graph_button(request, bird_id):
    bird = models.BirdInfo.objects.get(id=bird_id)
    if bird is None:
        return redirect('/404/')
    # bird.refresh_distribution_graph()
    # return HttpResponse('Success.')
    return HttpResponse('function not available.')


@login_required
def add_location(request):
    if request.method == 'POST':
        form = location_add_form(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/management/')
    form = location_add_form()
    return render(request, 'add_location.html', {'form': form})


@login_required
def add_record(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        location_id = request.POST.get('location')
        location = models.Location.objects.get(id=location_id)
        all_birds = models.BirdInfo.objects.all()
        for bird in all_birds:
            if request.POST.get(f'bird_{bird.id}'):
                record = models.Records()
                record.date = date
                record.location = location
                # record.bird_id = bird.id
                record.bird_id = models.BirdInfo.objects.get(id=bird.id)
                record.num = request.POST.get(f'bird_{bird.id}')
                record.save()
        return redirect('/management/')  # 重定向到成功页面
    # form = record_add_form()
    form = record_add_form(num_fields=9999)
    return render(request, 'add_record.html', {'form': form})


@login_required
def add_img(request):
    if request.method == 'POST':
        img_record = models.Img()
        img_record.date = request.POST.get('date')
        location_id = request.POST.get('location')
        img_record.location = models.Location.objects.get(id=location_id)
        # bird_id = request.POST.get('bird')
        # img_record.bird_id = models.BirdInfo.objects.get(id=bird_id)
        img_record.ori_src = request.POST.get('ori_src')
        img_record.src = request.POST.get('src')
        img_record.author = request.POST.get('author')
        img_record.description = request.POST.get('description')
        img_record.save()
        img_record = models.Img.objects.get(id=img_record.id)
        all_birds = models.BirdInfo.objects.all()
        for bird in all_birds:
            if request.POST.get(f'bird_{bird.id}'):
                bird_info = models.BirdInfo.objects.get(id=bird.id)
                img_record.species.add(bird_info)
        img_record.save()
        return HttpResponse("nice!")
    form = img_submit_form(num_fields=9999)
    return render(request, 'img_submit.html', {'form': form})


@login_required
def add_record_ebird_verify(request):
    if request.method == 'POST':
        if request.FILES['records']:
            record_file = request.FILES['records']
            record_file_wrapper = io.TextIOWrapper(record_file, encoding='utf-8', errors='replace')
            reader = csv.reader(record_file_wrapper)
            next(reader)  # 跳过标题行
            names = set()
            for row in reader:
                # print(row)
                names.add(row[0])
            name_list = []
            for name in names:
                bird = models.BirdInfo.objects.filter(chi_species__icontains=name).first()
                if bird:
                    name_list.append([name, bird.whole_name()])
                else:
                    name_list.append([name, 'species not found'])
            context = {
                'name_list': name_list,
            }
            return render(request, 'add_record_ebird_verify.html', context)
    form = record_add_ebird_csv_form()
    return render(request, "upload_csv.html", {'form': form, 'link': '/ebird_add_verify/'})


@login_required
def add_record_ebird_upload(request):
    if request.method == 'POST':
        record_file = request.FILES['records']
        record_file_wrapper = io.TextIOWrapper(record_file, encoding='utf-8', errors='replace')
        reader = csv.reader(record_file_wrapper)
        next(reader)  # 跳过标题行
        location = models.Location.objects.get(name='unknown')
        for row in reader:
            name = row[0]
            date = row[4]
            num = row[1]
            bird = models.BirdInfo.objects.filter(chi_species__icontains=name).first()
            bird = models.BirdInfo.objects.get(id=bird.id)

            record = models.Records()
            record.date = date
            record.location = location
            record.bird_id = bird
            record.num = num
            record.save()
        return HttpResponse('Success! Thank you!')
    form = record_add_ebird_csv_form()
    return render(request, "upload_csv.html", {'form': form, 'link': '/ebird_add_verify/upload/'})
