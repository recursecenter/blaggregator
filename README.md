##Blog post aggregator for the Hacker School community.

Live site [here](http://blaggregator.us). Hacker School login required.

###Contribute

Want to practice working on web apps? Check out [CONTRIBUTE.md](CONTRIBUTE.md) for some feature ideas.

###Installation:

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

###Encountered errors on Ubuntu 12.10:

- If you get either of these errors: 

```
- Error: pg_config executable not found.

- ./psycopg/psycopg.h:30:20: fatal error: Python.h: No such file or directory
```

Do the following:

`sudo apt-get install libpq-dev`

- If you run into trouble with the Django installation within requirements.txt, install Django via:

`pip install django`

- If you recieve:

`No module named psycopg2.extensions:`

Do:

`sudo apt-get build-dep python-psycopg2`

Then:

`pip install psycopg2`

Note: running `pip install -r requirements.txt` might be neccesarry after running any of the above commands.

- For postgres installation:

`sudo apt-get install postgresql`

- The following creates a super user:

```
- sudo -u postgres psql postgres 
- \password postgres
```

- The following creates new database called blaggregator_dev

`sudo -u postgres createdb blaggregator_dev`

- To set up other postgres user accounts do:

```
- create user user_name 
- \password user_name
```

- Then open settings.py and under `USER`: put the newly created user name, under `PASSWORD`: put the password of the user

- Then run your local server

 `python manage.py dbshell`
