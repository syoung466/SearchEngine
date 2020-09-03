import logging
from datamodel.search.datamodel import ProducedLink, OneUnProcessedGroup, robot_manager, Link
from spacetime.client.IApplication import IApplication
from spacetime.client.declarations import Producer, GetterSetter, Getter
from lxml import html,etree
import re, os
from time import time

from requests.exceptions import ConnectionError #ADDED IN BY ME
from collections import defaultdict #ADDED IN BY ME

try:
    # For python 2
    from urlparse import urlparse, parse_qs, urljoin
except ImportError:
    # For python 3
    from urllib.parse import urlparse, parse_qs, urljoin


#-------------------------------------GLOBAL VARIABLES GLOBAL VARIABLES GLOBAL VARIABLES----------------------------------
invalid_links = 0;
subdomains_dict = defaultdict(int)
most_outlinks = defaultdict(int)




logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"
url_count = (set() 
    if not os.path.exists("successful_urls.txt") else 
    set([line.strip() for line in open("successful_urls.txt").readlines() if line.strip() != ""]))
MAX_LINKS_TO_DOWNLOAD = 3000

@Producer(ProducedLink, Link)
@GetterSetter(OneUnProcessedGroup)
class CrawlerFrame(IApplication):

    def __init__(self, frame):
        self.starttime = time()
        # Set app_id <student_id1>_<student_id2>...
        self.app_id = "92078021_59566370_16788298"
        # Set user agent string to IR W17 UnderGrad <student_id1>, <student_id2> ...
        # If Graduate studetn, change the UnderGrad part to Grad.
        self.UserAgentString = "IR S17 UnderGrad 92078021, 59566370, 16788298"
		
        self.frame = frame
        assert(self.UserAgentString != None)
        assert(self.app_id != "")
        if len(url_count) >= MAX_LINKS_TO_DOWNLOAD:
            self.done = True

    def initialize(self):
        self.count = 0
        l = ProducedLink("http://www.ics.uci.edu", self.UserAgentString)
        print l.full_url
        self.frame.add(l)

    def update(self):
        for g in self.frame.get_new(OneUnProcessedGroup):
            print "Got a Group"
            outputLinks, urlResps = process_url_group(g, self.UserAgentString)
            for urlResp in urlResps:
                if urlResp.bad_url and self.UserAgentString not in set(urlResp.dataframe_obj.bad_url):
                    urlResp.dataframe_obj.bad_url += [self.UserAgentString]
            for l in outputLinks:
                if is_valid(l) and robot_manager.Allowed(l, self.UserAgentString):
                    lObj = ProducedLink(l, self.UserAgentString)
                    self.frame.add(lObj)
        if len(url_count) >= MAX_LINKS_TO_DOWNLOAD:
            self.done = True

    def shutdown(self):
        print "downloaded ", len(url_count), " in ", time() - self.starttime, " seconds."
        write_to_file()
	pass

def save_count(urls):
    global url_count

    urls = set(urls).difference(url_count)
    url_count.update(urls)
    if len(urls):
        with open("successful_urls.txt", "a") as surls:
            surls.write(("\n".join(urls) + "\n").encode("utf-8"))
	
    
def process_url_group(group, useragentstr):
    rawDatas, successfull_urls = group.download(useragentstr, is_valid)
    save_count(successfull_urls)
    return extract_next_links(rawDatas), rawDatas
    
#######################################################################################
'''
STUB FUNCTIONS TO BE FILLED OUT BY THE STUDENT.
'''

#invalid_links_count = 0

def extract_next_links(rawDatas):
    outputLinks = list()
    '''
    rawDatas is a list of objs -> [raw_content_obj1, raw_content_obj2, ....]
    Each obj is of type UrlResponse  declared at L28-42 datamodel/search/datamodel.py
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded. 
    The frontier takes care of that.

    Suggested library: lxml
    '''
 
    for i in rawDatas:
	final_url = ""    #TO FIND THE TRUE URL
	if i.is_redirected:
		final_url = i.final_url

	else:
		final_url = i.url

	try:
		parse = urlparse(final_url) #parsing parts or original URL

		parsed_html = html.document_fromstring(i.content) #parsing html from i

		for element, attribute, link, pos in parsed_html.iterlinks(): #getting elements from html
			base = parse.scheme + "://" + parse.netloc
			absolute = urljoin(base,link)	 #creating new urls (scraped)
			print "=======THIS IS ABSOLUTE=============== ",  absolute
		
			total_count = (absolute).count("/",0,len(absolute))
			if total_count < 6 and ".." not in absolute:
				global most_outlinks
				global subdomains_dict
				most_outlinks[final_url]+= 1  #counts the most outlinks here if they are legit
				

				parsed_absolute = urlparse(absolute)
				parsed_absolute = parsed_absolute.netloc
				
				print "Parsed Absolute: ", parsed_absolute, "\n"
				if parsed_absolute.find(".ics.uci.edu") != -1:
					subdomains_dict[parsed_absolute[0:(parsed_absolute.find(".ics.uci.edu"))]]+=1
					outputLinks.append(absolute)


		total_count = (final_url).count("/",0,len(final_url))
		if total_count >= 6 or ".." in final_url:
			i.bad_url = True
		else:
			outputLinks.append(final_url)

	
	except:
		continue


    return outputLinks


def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be downloaded or not.
    Robot rules and duplication rules are checked separately.

    This is a great place to filter out crawler traps.
    '''


    try:
	    is_true_or_false = False	
	    parsed = urlparse(url)
	    

	    print url, "\n"

	    if "calender" in url or ".." in url:
		is_true_or_false = False

	    if parsed.scheme not in set(["http", "https"]):
		is_true_or_false = False
	    try:
		is_true_or_false =  ".ics.uci.edu" in parsed.hostname \
		    and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
		    + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
		    + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
		    + "|thmx|mso|arff|rtf|jar|csv"\
		    + "|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

	    except TypeError:
		print ("TypeError for ", parsed)

	    if(is_true_or_false == False or "~mlearn" in url):
		is_true_or_false = False 


	    total_count = (parsed.path).count("/",0,len(parsed.path))
	    if total_count >= 6:
		is_true_or_false = False
		

	    if is_true_or_false == False:
		global invalid_links
		invalid_links += 1

	    return is_true_or_false

     
    except:
	    print "SKIPPING"	

def write_to_file():

	new_object = open("analytics_info.txt","w");
	new_object.write("----------------ANALYTICS-------------------\n")   
	new_object.write("------SUBDOMAINS:------\n")
	for dic,value in subdomains_dict.items():
		new_object.write(str(dic) + ": " + str(value) +"\n")

	new_object.write("------INVALID LINKS-----\n")
	new_object.write("INVALID LINKS: " + str(invalid_links) + "\n")


	new_object.write("------PAGE WITH THE MOST OUTLINKS-----\n")

	new_object.write("Page with most outlinks: " + str(max(most_outlinks,key=most_outlinks.get)))  



