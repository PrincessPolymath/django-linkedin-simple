django-linkedin-simple
=======================================
This is a basic example of a Django project set up with LinkedIn authentication.
A Procfile is included to make deployment to Heroku easy.  
For more detailed instructions on getting this code to work and deploy to Heroku see my blog post at http://www.princesspolymath.com/princess_polymath/?p=511

Requirements:
* simplejson
* oauth2

Install both with:
pip install simplejson oauth2

This library uses the REST authentication (1.0a) and stores the user's token and secret in the UserProfile. This is the "simplest thing that could possibly work" and is designed as a springboard for you to add the functionality you need.
