from django import template
from webird import models
from django.db.models import Sum
import markdown

# from models import LOC_CHOICES_MAP
register = template.Library()


@register.filter
def id_get_location(loc_id):
    try:
        return loc_id.name
    except:
        return models.Location.objects.filter(id=loc_id).first().name


@register.filter
def id_get_bird_whole_name(bird_id):
    try:
        return bird_id.whole_name()
    except:
        return models.BirdInfo.objects.filter(id=bird_id).first().whole_name()


@register.filter
def id_get_bird_single_name(bird_id):
    try:
        return bird_id.single_name()
    except:
        return models.BirdInfo.objects.filter(id=bird_id).first().single_name()


@register.filter
def location_get_total_record_num(loc):
    return models.Location.objects.get(id=loc.id).records_set.aggregate(total=Sum('num'))['total']


@register.filter
def img_get_species(img):
    img = models.Img.objects.get(id=img.id)
    species_queryset = img.species.all()
    name_list = [bird_info.whole_name() for bird_info in species_queryset]
    return name_list


@register.filter
def md2view(txt):
    md = markdown.Markdown(extensions=["fenced_code"])
    txt = md.convert(txt)
    return txt


@register.filter
def bird_class_get_class_name(bird_class):
    return bird_class.whole_name()

# @register.filter
# def get_all_name(bird):  # need modification
#     out = ""
#     if bird['eng_species']:
#         out += bird['eng_species']
#     if bird['chi_species']:
#         out += " " + bird['chi_species']
#     return out
#
#
# @register.filter
# def get_single_name(bird):  # need modification
#     if bird['eng_species']:
#         return bird['eng_species']
#     return bird['chi_species']


# @register.filter
# def get_single_name_sub(bird):  # need modification
#     if bird.eng_species:
#         return bird.eng_species
#     return bird.chi_species
