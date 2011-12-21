from django.core.management import setup_environ
import settings
setup_environ(settings)

from todaynag.linkedin.models import UserProfile,SentArticle
from django.contrib.auth.models import User 
from twilio.rest import TwilioRestClient

import oauth2 as oauth
import time
import simplejson
import datetime
import httplib2
import psycopg2

account = "AC80f1b83ec7f84c4fbf7977330b503745"
token = "ac026657401b239fdce4d14c182820fe"
twilioclient = TwilioRestClient(account, token)

url = "http://api.linkedin.com/v1/people/~/topics:(description,id,topic-stories:(topic-articles:(relevance-data,article-content:(id,title,resolved-url))))"

consumer = oauth.Consumer(
        key="1iK9RUZ1FLJaLUpp90xztjhJXLkdTooiNqXMAORUrpoWJaR0cozd863qyIwvb0ZJ",
        secret="fbW_tq9SrAQ_8KM9dlcbSW5oGjmd3aJWVDvs1mcTbFzmkBRQSRO4DeddfWlEN0b9")

users = User.objects.all()

for djangouser in users:
	if djangouser.username == "admin":
		continue
	profile = UserProfile.objects.get(user=djangouser)
	token = oauth.Token(
        	key=profile.oauth_token,
        	secret=profile.oauth_secret)
	phone = profile.phone_number
	userid = profile.user_id
	user_articles = SentArticle.objects.filter(user=djangouser)

	# Now make the LinkedIn today call and get the articles in question
	client = oauth.Client(consumer, token)

	resp, content = client.request(url, headers={"x-li-format":'json'})
	results = simplejson.loads(content)

	for topic in results['values']:
           for story in topic['topicStories']['values']:
                for article in story['topicArticles']['values']:
                        score = article['relevanceData']['score']
                        if score > 4:
				checkarticle = 	user_articles.filter(article_number__exact=article['articleContent']['id'])
				if len(checkarticle) == 0:
					# This is where we get the shortened URL from google because LinkedIn doesn't provide one
					http = httplib2.Http()
					body = {"longUrl": article['articleContent']['resolvedUrl']}
					resp,content = http.request("https://www.googleapis.com/urlshortener/v1/url?key=AIzaSyCEPv85KrJIKGX5sYWEy267lQCYcOrUg1s","POST",body=simplejson.dumps(body),headers={"Content-Type":"application/json"})
					googleresponse = simplejson.loads(content)
					sentarticle = SentArticle(article_number=article['articleContent']['id'],user=djangouser,timestamp=datetime.datetime.today())	
					sentarticle.save()
					bodytext = article['articleContent']['title'] + " " + googleresponse['id']
					bodytext += " ('save %s')" % sentarticle.id
					message = twilioclient.sms.messages.create(to="+1" + phone, from_="+18312161666", body=bodytext)
				
