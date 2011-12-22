# Python
import oauth2 as oauth
import simplejson as json
import re
from xml.dom.minidom import getDOMImplementation,parse,parseString

# Django
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

# Project
from linkedin.models import UserProfile,SentArticle

# from settings.py
consumer = oauth.Consumer(settings.LINKEDIN_TOKEN, settings.LINKEDIN_SECRET)
client = oauth.Client(consumer)

def createSmsResponse(responsestring):
	impl = getDOMImplementation()
	responsedoc = impl.createDocument(None,"Response",None)
	top_element = responsedoc.documentElement
	sms_element = responsedoc.createElement("Sms")
	top_element.appendChild(sms_element)
	text_node = responsedoc.createTextNode(responsestring)
	sms_element.appendChild(text_node)
	html = responsedoc.toxml(encoding="utf-8")
	return html

@csrf_exempt
def sms_reply(request):
    if request.method == 'POST':
        params = request.POST
        phone = re.sub('\+1','',params['From'])
        smsuser = User.objects.get(userprofile__phone_number=phone)
        responsetext = "This is my reply text"
        token = oauth.Token(smsuser.get_profile().oauth_token, smsuser.get_profile().oauth_secret)
        client = oauth.Client(consumer,token)
        
        commandmatch = re.compile(r'(\w+)\b',re.I)
        matches = commandmatch.match(params['Body'])
        command = matches.group(0).lower()
        print command
        
        if command == "help":
        	helpstring = "Commands: 'cancel' to cancel Today SMS; 'level #number#' to change minimum score;"
        	helpstring += "'save #article#' to save; 'share #article# #comment#' to share"
        	return HttpResponse(createSmsResponse(helpstring))
        if command == 'cancel':
        	profile = smsuser.get_profile()
        	profile.min_score = 0
        	profile.save()
        	return HttpResponse(createSmsResponse("Today SMS Service Cancelled"))
        if command == 'level':
        	levelmatch = re.compile(r'level (\d+)(.*)',re.I)
        	matches = levelmatch.search(params['Body'])
        	level = matches.group(1)
        	profile = smsuser.get_profile()
        	profile.min_score = level
        	profile.save()
        	return HttpResponse(createSmsResponse("Today SMS minimum score changed to %d" % int(level)))
        if command == 'save':
        	savematch = re.compile(r'save (\d+)(.*)',re.I)
        	matches = savematch.search(params['Body'])
        	article = matches.group(1)
        	sentarticle = SentArticle.objects.get(user=smsuser, id=article)
        	
        	responsetext = "Saved article: %s" % (sentarticle.article_title)
        	saveurl = "http://api.linkedin.com/v1/people/~/articles"
        		
        	# Oddly JSON doesn't seem to work with the article save API
        	# Using XML instead
        	impl = getDOMImplementation()
        	xmlsavedoc = impl.createDocument(None,"article",None)
        	top_element = xmlsavedoc.documentElement
        	article_content_element = xmlsavedoc.createElement("article-content")
        	top_element.appendChild(article_content_element)
        	id_element = xmlsavedoc.createElement("id")
        	article_content_element.appendChild(id_element)
        	text_node = xmlsavedoc.createTextNode(sentarticle.article_number)
        	id_element.appendChild(text_node)
        	body = xmlsavedoc.toxml(encoding="utf-8")
        	print body
        	resp, content = client.request(saveurl, "POST",body=body,headers={"Content-Type":"text/xml"})
        	if (resp.status == 200):
        		return HttpResponse(createSmsResponse(responsetext))
        if command == 'share':
        	sharematch = re.compile(r'Share (\d+) (.*)')
        	matches = sharematch.search(params['Body'])
        	article = matches.group(1)
        	comment = matches.group(2)
        	sentarticle = SentArticle.objects.get(user=smsuser, id=article)
        	
        	responsetext = "Shared article: %s" % (sentarticle.article_title)
        	shareurl = "http://api.linkedin.com/v1/people/~/shares"
        	body = {"comment":comment,
        		"content":{
        			"article-id":sentarticle.article_number
       	 		},
        	"visibility":{"code":"anyone"}
        	}
	  
        	resp, content = client.request(shareurl, "POST",body=json.dumps(body),headers={"Content-Type":"application/json"})
        	if (resp.status == 201):
        		return HttpResponse(createSmsResponse(responsetext))
