FOR VERSION 0.1: Handle user login and data

[x] add route for /profile/id
[x] build profile template
[x] build login page and get successful 200 response
[x] check the db for their hacker school username. display status page
[x] add Blog model
[x] if they're a new user, create a new account for them
[ ] fix login/login redirection bug

FOR VERSION 0.2: Full login flow with skeleton pages
[ ] if they have an account, forward them to the /new page on login
[ ] build an account edit page (that redirects to /new on save)
[ ] if they just had a new account created, redirect them to the account edit page
[ ] add 404 handling to views

FOR VERSION 0.3: Sessions
[ ] recognize logged in users with cookies https://docs.djangoproject.com/en/dev/topics/http/sessions/

FOR VERSION 0.4: Handle their blogs
[ ] expose blog field in the user profile & edit views
[ ] make /new template that lists links to everyone's blogs

FOR VERSION 0.5: Put all posts into /new
[ ] Pull Planet's spider and scraper to grab ALL new posts
[ ] Show them in the /new view - title, author, link

FOR VERSION 0.6: Auxiliary stuff
[ ] Add Twitter Bootstrap themes
[ ] Add GA

FOR FUTURE
[ ] make some fields optional http://www.djangobook.com/en/2.0/chapter06.html
[ ] only allow you to view your own profile
[ ] make a public profile view (aka what another user sees when they view your profile)