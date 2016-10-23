Blaggregator is a Django app with a Bootstrap frontend, that is deployed on
Heroku and uses their Postgres and Scheduler add-ons.

This document aims to help you setup a development environment and to help you
get started with the code.

## Installation:

- Set up your virtual environment

- Install dependencies:

```bash
$ pip install -r requirements.txt
```

- Install Postgres (it's easy on OSX
  with [postgres.app](http://postgresapp.com/)) and `pip install
  psycopg2`. Open the app to start your database server running locally.

    - Open a Postgres shell:

      ```bash
      $ psql
      ```

    - Create your database:

      ```sql
      CREATE DATABASE blaggregator_dev;
      ```
    The semicolon is critical. IMPORTANT: when you are creating your admin
    account on the db, *don't* use the same email address as your Recurse
    Center account or you won't be able to create a user account for
    yourself. Do username+root@example.com or something.

- Alternatively, you could use Sqlite instead of Postgres to get off the
  blocks, quickly.  Change the value of `'ENGINE'` in the
  `DATABASES['default']` dictionary to `'django.db.backends.sqlite3'`.

- Set up initial tables:

```bash
$ python manage.py syncdb
```

- Bring the tables up to date with the latest South migrations:

```bash
$ python manage.py migrate
```

If you get this error:

```
OperationalError: could not connect to server: No such file or directory
Is the server running locally and accepting
connections on Unix domain socket "/var/pgsql_socket/.s.PGSQL.5432"?
```
then your server isn't running. Go fiddle with Postgres.app.

- Turn on debugging in your environment so you can get useful error messages:

```bash
$ export DJANGO_DEBUG=True
```

- Blaggregator uses oauth2 to log in users against recurse.com. Go
  to [your settings on recurse.com](https://www.recurse.com/settings), make a
  new app. Name it something like "blaggregator-local" and the url should be
  http://localhost:8000/complete/hackerschool/ (WITH trailing slash). Grab the
  keys and store them in your environment as SOCIAL_AUTH_HS_KEY and
  SOCIAL_AUTH_HS_SECRET.

- Then run a local server:

```bash
$ python manage.py runserver
```

You can administer your app through
the [handy-dandy admin interface](http://localhost:8000/admin). To see this
page, you'll need to give your user account superuser privileges:

1. go to http://localhost:8000/ and auth in through HS's oauth
2. `$ python manage.py shell` to open Django's shell and use its ORM
3. `>>> from django.contrib.auth.models import User` import the User model
   (should you need the other models defined in `models.py`, import from
   `home.models`. User uses Django's built-in User model)
4. 	`>>> u = User.objects.get(first_name="Sasha")` or whatever your first name
       is. Grab your user object from the db.
5. 	`>>> u.is_superuser = True` make your account a superuser so you can access
       the admin
6. 	`>>> u.save()` Save these changes to the db.
7. 	You should now be able to access localhost:8000/admin while logged in!

## Code overview

Key files:

- `home/views.py`: the heart of the app. all of the views ("controllers" if
  you're coming from Ruby)
- `blaggregator/settings.py`: app settings
- `home/management/commands/crawlposts.py`: background crawler script
- `home/feedergrabber27.py`: feed parser
- `home/templates/home`: all templates live here
