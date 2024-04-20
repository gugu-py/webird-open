import matplotlib.pyplot as plt
import numpy as np
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum, Avg
import io
import os
from datetime import date


# Create your models here.
class BirdClasses(models.Model):
    id = models.AutoField(primary_key=True)
    eng_name = models.TextField(null=True)
    chi_name = models.TextField(null=True)
    chi_description = models.TextField(null=True, blank=True)
    eng_description = models.TextField(null=True, blank=True)
    wiki_url = models.TextField(null=True, blank=True)

    def whole_name(self):
        return self.chi_name + ' ' + self.eng_name

    def single_name(self):
        return self.eng_name if self.eng_name else self.chi_name


'''
Songbirds 鸣禽
Climbing birds 攀禽
Birds of prey 猛禽
Terrestrial birds 陆禽
Waders 涉禽
Water birds 游禽
'''


class BirdInfo(models.Model):
    id = models.AutoField(primary_key=True)
    eng_species = models.CharField(max_length=30, blank=True, null=True)
    chi_species = models.CharField(max_length=30, blank=True, null=True)
    chi_description = models.TextField(max_length=700, blank=True, null=True)
    eng_description = models.TextField(max_length=700, blank=True, null=True)
    wiki_url = models.TextField(max_length=100, blank=True, null=True)
    bird_class = models.ForeignKey(BirdClasses, on_delete=models.PROTECT, null=True)

    def whole_name(self):
        return (self.eng_species if self.eng_species else '') + (self.chi_species if self.chi_species else '')

    def single_name(self):
        return self.eng_species if self.eng_species else self.chi_species


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.TextField(max_length=700, blank=True, null=True, verbose_name='description')
    img_src = models.TextField(max_length=60, blank=True, null=True)
    name = models.TextField(max_length=30, blank=False, null=True, verbose_name='name')
    pos_x = models.PositiveSmallIntegerField(blank=False, null=True)
    pos_y = models.PositiveSmallIntegerField(blank=False, null=True)
    display = models.BooleanField(null=False, default=True, blank=True)

    def whole_name(self):
        return self.name


class Img(models.Model):
    id = models.AutoField(primary_key=True)
    src = models.TextField(blank=True, null=True)
    ori_src = models.TextField(blank=True, null=True)
    # bird_id = models.ForeignKey(BirdInfo, on_delete=models.PROTECT)
    date = models.DateField(blank=True, null=True)
    # loc_choices = LOC_CHOICES
    description = models.TextField(blank=True, null=True, verbose_name='description')
    author = models.TextField(blank=True, null=True, verbose_name='author')
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    species = models.ManyToManyField(BirdInfo)


class Records(models.Model):
    id = models.AutoField(primary_key=True)
    bird_id = models.ForeignKey(BirdInfo, on_delete=models.PROTECT)
    # loc_choices = LOC_CHOICES
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    date = models.DateField(blank=True, null=True, verbose_name='date(YYYY-MM-DD)')
    num = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='num')
    author = models.CharField(max_length=30, blank=True, null=True, verbose_name='author')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # bird_target = self.bird_id
        # bird_target.refresh_distribution_graph()
        super().save(*args, **kwargs)

    def get_row(self):
        return [self.bird_id.whole_name(), self.location.whole_name(), self.date, self.num, self.author]


class blogs(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, default='constructing')
    content = models.TextField(default='constructing')

    def __str__(self):
        return self.title


def get_sum_data(rule, *args, **kwargs):
    # day = date(day)
    # rule = {
    #     'date__day': tar_day,
    #     'date__month': tar_month,
    # }
    record_sum = (
        Records.objects
        .filter(**rule)
        .values('bird_id')
        .annotate(avg_value=Avg('num'))
        .aggregate(total=Sum('num'))['total']
    )
    if not record_sum:
        record_sum = 0
    return record_sum


def record_query(q_dic):
    bird_filter = None
    if 'species' in q_dic:
        species_ids = q_dic['species']
        for species_id in species_ids:
            if bird_filter:
                bird_filter = Q(bird_id=int(species_id)) | bird_filter
            else:
                bird_filter = Q(bird_id=int(species_id))
    elif 'bird_class_ids' in q_dic:
        classes_ids = q_dic['bird_class_ids']
        for classes_id in classes_ids:
            bird_class = BirdClasses.objects.get(id=classes_id)
            birds = bird_class.birdinfo_set.all()
            for bird in birds:
                species_id = bird.id
                if bird_filter:
                    bird_filter = Q(bird_id=int(species_id)) | bird_filter
                else:
                    bird_filter = Q(bird_id=int(species_id))

    location_filter = None
    if 'location_id' in q_dic:
        location_ids = q_dic['location_id']
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

    api_filter = Q(date__range=time_interval)
    if bird_filter:
        api_filter = bird_filter & api_filter
    if location_filter:
        api_filter = location_filter & api_filter
    # api_filter = bird_filter & location_filter & Q(date__range=time_interval)
    return Records.objects.all().filter(api_filter).distinct()
