##Blog post aggregator for the Hacker School community.

Hacker Schoolers are writing awesome blog posts all over the internet. This brings them together and provides a place where alums from every batch can discuss technical news.

The live site is [here](http://blaggregator.us). Hacker School login required.

###Add your blog
You will be prompted to add your blog when you create an account. You can also [add it later](http://blaggregator.us/add_blog).

Once your blog is added, Blaggregator will crawl it periodically for new posts.

###Contribute

Want to contribute a feature or bugfix? Blaggregator is a straightforward Django app with a Twitter Bootstrap frontend. It's deployed on Heroku and uses their Postgres and Scheduler add-ons. 

Key files: 
- blaggregator/settings.py: app settings
- home/management/commands/crawlposts.py: background crawler script
- home/feedergrabber27.py: feed parser contributed by dpb
- home/templates/home: all templates
- home/views.py: all of the views ("controllers" if you're coming from Ruby)

Check out [CONTRIBUTE.md](CONTRIBUTE.md) for ideas for what to build.

###Installation:

- Set up your virtual environment

- Install dependencies:

`pip install -r requirements.txt`

- Install Postgres (it's easy on OSX with [postgres.app](http://postgresapp.com/)) and `pip install psycopg2`. Open the app to start your database server running locally. Open a Postgres shell:

`psql`

Create your database: 

`CREATE DATABASE blaggregator_dev;`

The semicolon is critical. IMPORTANT: when you are creating your admin account on the db, *don't* use the same email address as your Hacker School account or you won't be able to create a user account for yourself. Do username+root@example.com or something.

Set up initial tables: 

`$ python manage.py syncdb`

and then bring them up to date with the latest South migrations:

`$ python manage.py migrate`

If you get this error:

```
OperationalError: could not connect to server: No such file or directory
Is the server running locally and accepting
connections on Unix domain socket "/var/pgsql_socket/.s.PGSQL.5432"?
```
then your server isn't running. Go fiddle with Postgres.app. 

- Turn on debugging in your environment so you can get useful error messages:

`export DJANGO_DEBUG=True`

- Then run a local server:

`python manage.py runserver`

You can administer your app through the [handy-dandy admin interface](http://localhost:8000/admin). You can be logged in as the admin or as your user account, but not both at the same time.

This installation can be a bit fiddly but once it's set up, it's smooth sailing. 
