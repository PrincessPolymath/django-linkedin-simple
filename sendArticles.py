import psycopg2
from twilio.rest import TwilioRestClient

import oauth2 as oauth
import time
import simplejson
import datetime
import httplib2

account = "TWILIO_ACCT_NUMBER"
token = "TWILIO_TOKEN"
twilioclient = TwilioRestClient(account, token)

consumer = oauth.Consumer(
        key="LINKEDIN_CONSUMER_KEY",
        secret="LINKEDIN_CONSUMER_SECRET")

url = "http://api.linkedin.com/v1/people/~/topics:(description,id,topic-stories:(topic-articles:(relevance-data,article-content:(id,title,resolved-url))))"


try:
	conn = psycopg2.connect("dbname='YOUR_DBNAME' user='postgres' password='YOUR_POSTGRES_PASSWD'")
except:
	print "I am unable to connect to the database"

cur = conn.cursor()

cur.execute("""SELECT * from linkedin_userprofile""")
rows = cur.fetchall()

for row in rows:
	token = oauth.Token(
        	key=row[2],
        	secret=row[3])

	phone = row[4]
	userid = row[1]
	# Now make the LinkedIn today call and get the articles in question
	client = oauth.Client(consumer, token)

	resp, content = client.request(url, headers={"x-li-format":'json'})
	results = simplejson.loads(content)

	for topic in results['values']:
           for story in topic['topicStories']['values']:
                for article in story['topicArticles']['values']:
                        score = article['relevanceData']['score']
                        if score > 6:
                                print article['articleContent']['title']
                                print article['articleContent']['id']
                                print article['articleContent']['resolvedUrl']
				cur.execute("SELECT id from linkedin_sentarticle where user_id='%s' and article_number='%s'" % (str(userid),str(article['articleContent']['id'])))
				sentarticles = cur.fetchall()
				if not sentarticles:
					# This is where we get the shortened URL from google because LinkedIn doesn't provide one
					http = httplib2.Http()
					body = {"longUrl": article['articleContent']['resolvedUrl']}
					print simplejson.dumps(body)
					resp,content = http.request("https://www.googleapis.com/urlshortener/v1/url?key=GOOGLE_API_KEY","POST",body=simplejson.dumps(body),headers={"Content-Type":"application/json"})
					googleresponse = simplejson.loads(content)
					
					cur.execute("INSERT into linkedin_sentarticle(user_id,article_number,timestamp) values ('%s','%s','%s')" % (str(userid),str(article['articleContent']['id']),datetime.datetime.today()))
					cur.execute("SELECT id from linkedin_sentarticle where user_id='%s' and article_number='%s'" % (str(userid),str(article['articleContent']['id'])))
					sentarticles = cur.fetchall()
					bodytext = article['articleContent']['title'] + " " + googleresponse['id']
					bodytext += " ('save %s')" % sentarticles[0]
					print bodytext
					message = twilioclient.sms.messages.create(to="+1" + phone, from_="+YOUR_TWILIO_PHONE", body=bodytext)
				
	conn.commit()
