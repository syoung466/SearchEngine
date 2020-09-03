from django.core.management.base import BaseCommand, CommandError
import main.models as models
try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup
import json
import os
import re
from collections import defaultdict

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('name', type=str, default="", nargs='?')
        parser.add_argument('stream', type=int, default=-1, nargs='?')

    def handle(self, *args, **kwargs):
        #  Load all english words from linux dictionary
        english_dictionary = set(open('/usr/share/dict/american-english', 'r').read().split('\n'))

        if kwargs["name"] == "":
            print "Please, specify the name of the folder"
            exit(0)

        if kwargs['stream'] == -1:
            print 'Loading all the stories'
        else:
            print 'Loading only stories with stream', kwargs['stream']

        #  Jump to the folder with all the data that is to be loaded into the database
        os.chdir(kwargs["name"])

        #  Open the JSON containing all the records and parse it
        with open('bookkeeping.json', 'r') as f:
            index = json.loads(f.read())


        total = len(index)
        current = 0
        for path in index:
            try:
                if current % 10 != kwargs['stream'] and kwargs['stream'] != -1:
                    print "Skipping"
                    current += 1
                    continue
                #  Read the page
                with open(path, 'r') as f:
                    html = f.read()
                url = index[path]

                #  Clear the html from all the rubbish symbols
                html = filter(lambda x: 0 < ord(x) < 128, html)

                #  Make the text proper html and turn it into the text
                tags = defaultdict(str)
                if '<body>' in html:
                    html = '<html> <head> <title>' + html.replace('<body>', '</title></head><body>') + '</html>'
                    try:
                        soup = BeautifulSoup(html, 'html.parser')
                    except AttributeError:
                        soup = BeautifulSoup(html)
                    try:
                        text = soup.get_text()
                    except TypeError:
                        text = soup.getText()
                    tags['title'] = soup.title.string.encode('ascii','ignore')
                    for x in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b']:
                        elems = soup.findAll(x)
                        elem_text = ""
                        for elem in elems:
                            elem_text += (elem.string + " ")
                        tags[x] = elem_text
                else:
                    text = html



                #  Set up dictionary where the number of occurances of each word is to be counted
                words = defaultdict(int)

                #  Parse the page word by word
                for word in re.findall('[0-9a-z]+', text.lower()):
                    words[word] += 1

                #  Create the database object to represent the webpage
                webpage = models.WebPage()
                webpage.url = url
                webpage.title = tags['title']
                webpage.content = text.replace(tags['title'], '')
                webpage.save()

                #  For each word, save it as a keyword and create the object that matches keywords to pages
                for word in words:
                    #  Get the keyword object from the database if the keyword exists or create otherwise
                    keywords_from_database = models.Keyword.objects.filter(text=word)
                    if len(keywords_from_database) == 0:
                        keyword = models.Keyword()
                        keyword.text = word
                    else:
                        keyword = keywords_from_database[0]
                    #  Update number of total times the keyword was seen
                    keyword.total_count += words[word]
                    keyword.save()
                    #  Record keyword_in_webpage
                    keyword_in_webpage = models.KeywordInWebpage()
                    keyword_in_webpage.webpage = webpage
                    keyword_in_webpage.keyword = keyword
                    keyword_in_webpage.count = words[word]
                    keyword_in_webpage.title = tags['title'].count(word)
                    keyword_in_webpage.h1 = tags['h1'].count(word)
                    keyword_in_webpage.h2 = tags['h2'].count(word)
                    keyword_in_webpage.h3 = tags['h3'].count(word)
                    keyword_in_webpage.h4 = tags['h4'].count(word)
                    keyword_in_webpage.h5 = tags['h5'].count(word)
                    keyword_in_webpage.h6 = tags['h6'].count(word)
                    keyword_in_webpage.b = tags['b'].count(word)
                    keyword_in_webpage.url = url.count(word)
                    keyword_in_webpage.save()

                # Once in a while, remove all the keywords that we only met once from the database
                if current != 0 and current % 20 == 0:
                    rare_keywords = models.Keyword.objects.filter(total_count=1)
                    for keyword in rare_keywords:
                        if keyword.text not in english_dictionary:
                            keyword.delete()
                    print "Removed weird keywords"


                print '{} out of {} is done'.format(current, total)
                current += 1
            except Exception as e:
                print e, 'Skipped'

