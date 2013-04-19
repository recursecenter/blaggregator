FOR VERSION 0.1: Handle user login and data

- [x] add route for /profile/id
- [x] build profile template
- [x] build login page and get successful 200 response
- [x] check the db for their hacker school username. display status page
- [x] add Blog model
- [x] if they're a new user, create a new account for them
- [M] fix login/login redirection bug

FOR VERSION 0.2: Full login flow with skeleton pages
- [M] if they have an account, forward them to the /new page on login
- [M] add 404 handling to views

FOR VERSION 0.3: Sessions
- [M] implement django's built in user model
- [M] auth users with django left off [here](https://docs.djangoproject.com/en/dev/topics/auth/default/#topic-authorization) on `user = authenticate(username='john', password='secret')`
- [M] make /new require a logged in user
- [M] refactor login view to have a separate login and create_account views

FOR VERSION 0.4: Profiles++: Handle their blogs
- [T/W] forward successfully created accounts to a page that asks for their blog feed url
- [W] fix the models so the blog connects to a user
- [W] expose blog url in the admin interface
- [W] make some profile fields optional http://www.djangobook.com/en/2.0/chapter06.html
- [W] make /new template that lists links to everyone's blogs
- [R] add 'url' to the Blog model
- [R] display First Last rather than FirstLast (need to pull first_name and last_name from the user database that corresponds to the blog instance)
- [R] make sure links start with http://
- [R] fix the link so that it goes to the blog, not to the feed
- [R] add 'or create account' link to the login page

FOR VERSION 0.5: Bootstrap
- [R] Add Twitter Bootstrap themes
- [F] Add navbar fixed to the top with title and logged in user firstname
- [F] Style the login/account forms
- [F] Style /new
- [M] Style all forms
- [M] Implement avatars from the Hacker School API

DEPLOY 
- [T] Set Heroku remote to have S3 creds as env vars 
- [T] finish reading the django page
- [T] get the app to stop 500'ing locally (make sure to comment out S3 stuff, may need to fix the templates too)
- [T] Rejigger django app be CDN-agnostic
- [W] Clarify the login flow with copy
- [R] Get master to a point where I can deploy it - with rebase or cherry-pick
- [W] set DJANGO_DEBUG permanently locally
- [W] set s3 vars locally
- [-] Outline a post about what I found confusing
- [R] change AWS credentials, and update env vars remotely & locally
- [ ] Make separate dev and prod envs
- [ ] Update contribute.md
 
FOR VERSION 0.6: Put all posts into /new
- [W] Plan out a Post model
- [W] Build the model and add some data from dpb
- [R] Build the new /new view that looks more like hacker news. 
- [W] Read to see if Heroku can handle two different versions of Python in the same app. If not, whether the add-on can have two apps talk to the same db.
- [R] plan out one-time parsing vs. ongoing. How to check for unique posts?