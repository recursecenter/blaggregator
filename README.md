## Blog post aggregator for the Hacker School community. 

### Contribute

Want to practice working on web apps? Check out [Contribute.md](CONTRIBUTE.md) for some feature ideas. 

### Installation: 

- Set up your virtual environment

- Install dependencies:

`pip install -r requirements.txt`

- Set up your database. Install Postgres (it's easy on OSX with [postgres.app](http://postgresapp.com/)) and open a Postgres shell: 

`python manage.py dbshell`

Create your database: 

`CREATE DATABASE blaggregator_dev;`

The semicolon is critical. Then go back to bash and populate the database from the app's models. IMPORTANT: when you are creating your admin account, *don't* use the same email address as your Hacker School account or you won't be able to create a user account for yourself. Do username+root@example.com or something.

`python manage.py syncdb`

If you get this error: 

```
OperationalError: could not connect to server: No such file or directory
Is the server running locally and accepting
connections on Unix domain socket "/var/pgsql_socket/.s.PGSQL.5432"?
```

Then open `settings.py` and under `HOST:` add `/tmp`. 

- Turn on debugging in your environment:

`export DJANGO_DEBUG=True`

- Then run a local server:

`python manage.py runserver`

You can administer your app through the [handy-dandy admin interface](http://localhost:8000/admin). You can be logged in as the admin or as your user account, but not both at the same time.
