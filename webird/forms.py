from webird import models
from django import forms


def get_bird_id(eng_species, chi_species):  # make sure the bird exists
    bird_id = -1
    if eng_species:
        bird_id = models.BirdInfo.objects.filter(eng_species__icontains=eng_species).first().id
    if chi_species:
        bird_id = models.BirdInfo.objects.filter(chi_species__icontains=chi_species).first().id
    return bird_id


class record_visualized_form(forms.Form):
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    locations = forms.MultipleChoiceField(choices=[])
    species = forms.MultipleChoiceField(choices=[], required=False)
    num_fields = len(models.BirdInfo.objects.all()) + len(models.Location.objects.all())
    bird_class_ids = forms.MultipleChoiceField(choices=[], required=False)

    def __init__(self, num_fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['locations'].choices = [(place.id, place.whole_name()) for place in
                                            models.Location.objects.all()]
        self.fields['species'].choices = [(bird.id, bird.whole_name()) for bird in
                                          models.BirdInfo.objects.all()]
        self.fields['bird_class_ids'].choices = [(bc.id, bc.whole_name()) for bc in
                                                 models.BirdClasses.objects.all()]


class bird_class_add(forms.ModelForm):
    class Meta:
        model = models.BirdClasses
        fields = '__all__'


class record_add_ebird_csv_form(forms.Form):
    records = forms.FileField(label='your ebird .csv file')


class birdinfo_add_csv_form(forms.Form):
    file = forms.FileField(label='your ebird .csv file')


class record_add_form(forms.Form):
    location = forms.ChoiceField(choices=[], required=True)
    date = forms.DateField(label='date')
    num_fields = len(models.BirdInfo.objects.all())

    def __init__(self, num_fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].choices = [(place.id, place.whole_name()) for place in
                                           models.Location.objects.all()]
        # print(self.fields['location'].choices)
        all_birds = models.BirdInfo.objects.all()
        # print(all_birds)
        for bird in all_birds:
            self.fields[f'bird_{bird.id}'] = forms.IntegerField(label=bird.whole_name(), required=False)


class record_edit_form(forms.Form):
    location = forms.ChoiceField(choices=[], required=True)
    date = forms.DateField(label='date')
    num = forms.IntegerField()
    species = forms.ChoiceField(choices=[])
    num_fields = len(models.BirdInfo.objects.all())

    def __init__(self, num_fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].choices = [(place.id, place.whole_name()) for place in
                                           models.Location.objects.all()]
        # print(self.fields['location'].choices)
        all_birds = models.BirdInfo.objects.all()
        self.fields['species'].choices = [(bird.id, bird.whole_name()) for bird in all_birds]


class record_search_form(forms.Form):  # 用来搜索记录的表单
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    # eng_species = forms.CharField(label='English name', max_length=50, required=False)
    # chi_species = forms.CharField(label='Chinese name', max_length=50, required=False)
    species = forms.MultipleChoiceField(choices=[], label='bird name', required=False)
    # location = forms.ModelChoiceField(label='location', queryset=models.Location.objects.all(), empty_label='',
    #                                   to_field_name='name', required=False)
    location_id = forms.ChoiceField(label='location', choices=[], required=False)
    num_fields = len(models.Location.objects.all())

    def __init__(self, num_fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location_id'].choices = [(place.id, place.whole_name()) for place in
                                              models.Location.objects.all()]
        self.fields['location_id'].choices.append((None, ''))
        self.fields['species'].choices = [(bird.id, bird.whole_name()) for bird in models.BirdInfo.objects.all()]

    def search(self, q_dic):
        bird_ids = [-1]
        if q_bird_ids := self.cleaned_data['bird_ids']:
            bird_ids = q_bird_ids
        else:
            bird_ids = [get_bird_id(self.cleaned_data['eng_species'], self.cleaned_data['chi_species'])]

        results = models.record_query(q_dic)
        return results


class img_search_form(forms.Form):  # 用来搜索图片的表单
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    # description = forms.CharField(label='description', max_length=50, required=False)
    location = forms.ChoiceField(choices=[], required=False)
    # bird_id = forms.IntegerField(label='species id', required=False)
    bird_id = forms.MultipleChoiceField(choices=[], label='species', required=False)
    num_fields = len(models.Location.objects.all())

    def __init__(self, num_fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].choices = [(place.id, place.whole_name()) for place in
                                           models.Location.objects.all()]
        self.fields['location'].choices.append((None, ''))
        self.fields['bird_id'].choices = [(bird.id, bird.whole_name()) for bird in models.BirdInfo.objects.all()]

    def search(self):
        query_dic = {}
        bird_id = self.cleaned_data['bird_id']
        if bird_id:
            query_dic['species'] = bird_id
        location_id = self.cleaned_data['location']
        if location_id:
            query_dic['location'] = models.Location.objects.get(id=location_id)
        # 一个一个判断是否为空，date_range特判，然后把不为空的字段进行查询
        # date_range默认为2000~2077，读入valid的日期就更新
        date_range = ['2000-01-01', '2077-01-01']
        if self.cleaned_data['start_date']:
            date_range[0] = self.cleaned_data['start_date']
        if self.cleaned_data['end_date']:
            date_range[1] = self.cleaned_data['end_date']
        if self.cleaned_data['species']:
            query_dic['description__icontains'] = self.cleaned_data['species']
        query_dic['date__range'] = (date_range[0], date_range[1])
        query_dic = {key: value for key, value in query_dic.items() if value is not None}
        # print(query_dic)
        # **query_dic把query_dic解包成参数
        results = models.Img.objects.filter(**query_dic)
        return results


class img_submit_form(forms.Form):  # 用来提交图片的表单
    location = forms.ChoiceField(choices=[], required=True, label='location')
    # bird = forms.ChoiceField(choices=[], required=True, label='bird')
    date = forms.DateField(label='date', required=True)
    src = forms.CharField(label='small img source', required=True)
    ori_src = forms.CharField(label='original img source', required=True)
    num_fields = len(models.BirdInfo.objects.all())
    author = forms.CharField(required=False, label='author')
    description = forms.CharField(required=False, label='description')

    def __init__(self, num_fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].choices = [(place.id, place.whole_name()) for place in
                                           models.Location.objects.all()]
        # self.fields['bird'].choices = [(bird.id, bird.whole_name()) for bird in
        #                                models.BirdInfo.objects.all()]

        all_birds = models.BirdInfo.objects.all()
        # print(all_birds)
        for bird in all_birds:
            self.fields[f'bird_{bird.id}'] = forms.IntegerField(label=bird.whole_name(), required=False)


class species_search_form(forms.ModelForm):
    class Meta:
        model = models.BirdInfo
        fields = ['chi_species', 'eng_species']

    def search(self):
        query_dic = {
            'eng_species__icontains': self.cleaned_data.get('eng_species'),
            'chi_species__icontains': self.cleaned_data.get('chi_species'),
        }
        query_dic = {key: value for key, value in query_dic.items() if value is not None}
        # print(query_dic)
        # **query_dic把query_dic解包成参数
        results = models.BirdInfo.objects.filter(**query_dic)
        return results


class birdinfo_add_form(forms.ModelForm):
    num_fields = len(models.BirdClasses.objects.all())
    bird_class = forms.ChoiceField(choices=[], required=True)

    class Meta:
        model = models.BirdInfo
        fields = ['eng_species', 'chi_species', 'chi_description', 'eng_description', 'wiki_url']

    def __init__(self, num_fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bird_class'].choices = [(bc.id, bc.whole_name()) for bc in
                                             models.BirdClasses.objects.all()]


class birdinfo_edit_form(forms.Form):
    eng_species = forms.CharField()
    chi_species = forms.CharField()
    eng_description = forms.CharField(required=False)
    chi_description = forms.CharField(required=False)
    wiki_url = forms.CharField(required=False)
    bird_class = forms.ChoiceField(choices=[])

    def __init__(self, num_fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bird_class'].choices = [(bc.id, bc.whole_name()) for bc in
                                             models.BirdClasses.objects.all()]


class location_add_form(forms.ModelForm):
    class Meta:
        model = models.Location
        fields = ['name', 'description', 'img_src', 'pos_x', 'pos_y']


class blog_add_form(forms.ModelForm):
    class Meta:
        model = models.blogs
        fields = '__all__'
