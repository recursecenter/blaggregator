Blaggregator is a Django app with a Bootstrap frontend, that is deployed on
Heroku and uses their Postgres and Scheduler add-ons.

This document aims to help you setup a development environment and to help you
get started with the code.

## Quick start (Docker)

You need [Docker](https://docs.docker.com/get-docker/) with the `docker compose`
plugin.  You don't need any Recurse Center credentials.

```bash
git clone https://github.com/recursecenter/blaggregator
cd blaggregator
docker compose up
```

This starts Postgres, runs the migrations and starts the app at
http://localhost:8000.  The code is mounted into the container, so your edits
show up right away.

In another terminal, add some fake users, blogs and posts:

```bash
docker compose exec web python manage.py seed_dev_data
```

Now open http://localhost:8000 and click "Log in as the dev user".  This logs
you in as a superuser, so the [admin](http://localhost:8000/admin) works too.
(The button only shows up when `DJANGO_DEBUG` and `DEV_LOGIN` are set, as they
are in `docker-compose.yml`.  It is never enabled on a deployed server.)

Other useful commands:

```bash
docker compose run --rm web python manage.py test home   # run the tests
docker compose exec web python manage.py shell            # Django shell
docker compose logs db                                    # database logs
```

If a port is already in use, pick other ones:

```bash
WEB_PORT=8001 DB_PORT=5433 docker compose up
```

If `docker compose up` fails with a database connection error, check the logs of
the `db` container first.

## Without Docker

You need [uv](https://docs.astral.sh/uv/) and a Postgres server.  uv installs
the Python version in `.python-version` for you.

```bash
uv sync
```

For Postgres, either use the one from `docker-compose.yml`:

```bash
docker compose up db
```

or create a database called `blaggregator_dev` in your own Postgres, owned by
a user `sasha` with password `sasha` (the defaults in
`blaggregator/settings/base.py`) that is allowed to create databases (the tests
create their own).

```bash
export DJANGO_DEBUG=1 DEV_LOGIN=1
uv run manage.py migrate
uv run manage.py seed_dev_data
uv run manage.py runserver
uv run manage.py test home
```

## Logging in with Recurse Center OAuth (optional)

You only need this to work on the login flow, or on things that use the
Recurse Center API (like fetching user details).  You need to be a Recurser.

Go to [your settings on recurse.com](https://www.recurse.com/settings/apps),
and make a new app.  Name it something like "blaggregator-local", and set the
redirect URL to http://localhost:8000/complete/hackerschool/ (WITH trailing
slash).  Then, set these environment variables:

| Variable                | Where to find it                       |
|-------------------------|----------------------------------------|
| `SOCIAL_AUTH_HS_KEY`    | the app's "ID"                         |
| `SOCIAL_AUTH_HS_SECRET` | the app's "Secret"                     |
| `HS_PERSONAL_TOKEN`     | a personal access token, created in the same settings page (give it a name) |

With Docker, copy `web-variables.env.template` to `web-variables.env`, fill it
in, and restart `docker compose up`.  Without Docker, export them.

When you log in through OAuth, don't use an email address for your local admin
account that is the same as your Recurse Center account, or you won't be able
to create a user account for yourself.  Using the dev login avoids this problem.

## Making yourself an admin

The dev user is already a superuser.  If you logged in with OAuth, open a Django
shell (`manage.py shell`) and run:

```python
from django.contrib.auth.models import User
u = User.objects.get(first_name="Sasha")  # your first name
u.is_superuser = u.is_staff = True
u.save()
```

## Code overview

Key files:

- `home/views.py`: the heart of the app. all of the views ("controllers" if
  you're coming from Ruby)
- `blaggregator/settings/`: app settings (`base.py`, plus one file per environment)
- `home/management/commands/crawlposts.py`: background crawler script
- `home/feedergrabber27.py`: feed parser
- `home/templates/home`: all templates live here
- `home/dev.py`, `home/management/commands/seed_dev_data.py`: the dev login and
  fake data, for working without Recurse Center credentials
