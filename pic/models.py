from django.db import models
from PIL import Image
import os
from django.core.exceptions import ValidationError
from ms_brd.settings import MEDIA_ROOT
from django.core.files.storage import default_storage
import io
from django.core.files.base import ContentFile

new_height = 300


# def validate_image_size(image):
#     # 验证图像大小是否超过10MB
#     if image.size > 10 * 1024 * 1024:  # 10MB的字节数
#         raise ValidationError("图像大小不能超过10MB。")

def remove_query_params(url):
    clean_url = url.split('?')[0]
    return clean_url


# Create your models here.
class Img(models.Model):
    id = models.AutoField(primary_key=True)
    ori_img = models.ImageField(upload_to='img/ori')
    sml_img = models.ImageField(upload_to='img/small')
    # img = models.ImageField(upload_to='img')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    link = models.TextField(blank=True, null=True, auto_created=True)

    @property
    def sml_img_clean_url(self):
        return remove_query_params(self.sml_img.url)

    @property
    def ori_img_clean_url(self):
        return remove_query_params(self.ori_img.url)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # 调用父类的 save 方法保存原始图像
        img = Image.open(self.ori_img)
        original_width, original_height = img.size

        # 计算正方形的边长
        side_length = min(original_width, original_height)

        # 计算截取图像的左上角坐标
        left = (original_width - side_length) // 2
        top = (original_height - side_length) // 2

        # 计算截取图像的右下角坐标
        right = left + side_length
        bottom = top + side_length

        # 截取正中央的正方形图像
        cropped_img = img.crop((left, top, right, bottom))

        # 调整图像大小为目标尺寸
        target_size = (new_height, new_height)  # 给定的目标尺寸
        sml_img = cropped_img.resize(target_size)
        self.sml_img.name = self.ori_img.name.replace('ori', 'small')  # 设置sml_img的文件名
        # print(self.sml_img.name)
        sml_img = sml_img.convert('RGB')
        sml_img_file = io.BytesIO()
        # 将剪裁过的图片保存到内存文件对象中
        sml_img.save(sml_img_file, format='JPEG')  # 保存为 JPEG 格式，可以根据需要进行调整
        # 设置内存文件对象的指针位置为起始位置
        sml_img_file.seek(0)
        # 使用 default_storage.save() 函数上传内存文件对象
        self.sml_img = default_storage.save(self.sml_img.name, ContentFile(sml_img_file.read()))
        # file_name = default_storage.save(self.sml_img.name, sml_img)
        # sml_img.save(self.sml_img.url)
        # print('saved', self.sml_img.name)
        #     # self.link = sml_img_path.split('\\')[-1]
        # self.sml_img.url = remove_query_params(self.sml_img.url)
        # self.ori_img.url = remove_query_params(self.ori_img.url)
        self.link = self.sml_img_clean_url
        super().save(*args, **kwargs)
