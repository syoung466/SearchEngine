from __future__ import unicode_literals

from django.db import models
from math import *

# Create your models here.

class Keyword(models.Model):
    text = models.CharField(max_length=1000)
    total_count = models.IntegerField(default=0)

    def __hash__(self):
        return hash(self.text)


class WebPage(models.Model):
    url = models.TextField()
    title = models.TextField(default="")
    content = models.TextField(default="")

    def __hash__(self):
        return hash(self.url)

    @property
    def show_content(self):
        return self.content[:300]

    @property
    def empty_title(self):
        return self.title.strip() == ""


class KeywordInWebpage(models.Model):
    keyword = models.ForeignKey(Keyword)
    webpage = models.ForeignKey(WebPage)
    count = models.IntegerField()
    h1 = models.IntegerField(default=0)
    h2 = models.IntegerField(default=0)
    h3 = models.IntegerField(default=0)
    h4 = models.IntegerField(default=0)
    h5 = models.IntegerField(default=0)
    h6 = models.IntegerField(default=0)
    b = models.IntegerField(default=0)
    url = models.IntegerField(default=0)
    title = models.IntegerField(default=0)
    tfidf = models.FloatField(default=0)
