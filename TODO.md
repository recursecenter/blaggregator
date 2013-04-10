FOR VERSION 0.1: Handle user login and data

[x] add route for /profile/id
[x] build profile template
[x] build login page and get successful 200 response
[x] check the db for their hacker school username. display status page
[x] add Blog model
[x] if they're a new user, create a new account for them
[M] fix login/login redirection bug

FOR VERSION 0.2: Full login flow with skeleton pages
[M] if they have an account, forward them to the /new page on login
[M] add 404 handling to views

FOR VERSION 0.3: Sessions
[M] implement django's built in user model
[M] auth users with django left off [here](https://docs.djangoproject.com/en/dev/topics/auth/default/#topic-authorization) on `user = authenticate(username='john', password='secret')`
[M] make /new require a logged in user
[M] refactor login view to have a separate login and create_account views

FOR VERSION 0.4: Profiles++: Handle their blogs
[T/W] forward successfully created accounts to a page that asks for their blog feed url
[W] fix the models so the blog connects to a user
[W] expose blog url in the admin interface
[W] make some profile fields optional http://www.djangobook.com/en/2.0/chapter06.html
[ ] make /new template that lists links to everyone's blogs
[ ] create profile views /profile/293
[ ] create edit profile view /profile/edit
[ ] have "edit" button only appear on your own profile
[ ] expose blog field in the user profile & edit views

FOR VERSION 0.5: Vanity
[ ] Add Twitter Bootstrap themes
[ ] Add GA
[ ] Add flash messaging (this might still work in 1.5 https://groups.google.com/forum/?fromgroups=#!topic/django-users/1YtRSukvviE)
[ ] Also useful https://docs.djangoproject.com/en/dev/ref/contrib/messages/

FOR VERSION 0.6: Put all posts into /new
[ ] Pull Planet's spider and scraper to grab ALL new posts
[ ] Show them in the /new view - title, author, link

FOR FUTURE

[ ] make a public profile view (aka what another user sees when they view your profile)
[ ] redirect /profile to the profile of the logged-in user
[ ] Maybe add more content to the external view to the outside world