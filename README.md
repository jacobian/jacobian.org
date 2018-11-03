# simonwillisonblog

The code that runs my weblog, http://simonwillison.net/

---

### heroku setup notes

```
heroku create
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
heroku addons:create sentry:f1

heroku buildpacks:add heroku/python
heroku buidpacks:add https://github.com/heroku/heroku-buildpack-nginx

heroku config:set DJANGO_SECRET=`openssl rand -hex 64
heroku config:set PINBOARD_API_KEY=...

git push heroku jacobian:master

heroku run bash
    python manage.py createsuperuser
    python manage.py import_blog_json {blog json url}
    python manage.py import_blog_json {pinboard json url}

```
