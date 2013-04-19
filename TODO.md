- add profile links to the hacker school site
- write script that crawls the posts once an hour
- handle the wrong URL more gracefully
- figure out how to handle USER, HOST, AWS_STORAGE_BUCKET_NAME in settings.py

ON DECK
- [ ] Fix "Welcome Firstname!" bug - template processors are probably the issues here
- [ ] check the submitted blog url to make sure it returns a 200 - use Ajax to display this?
- [ ] redirect /log_in if they're already logged in
- [ ] stop hotlinking to hacker school and save a copy of the file locally
- [ ] implement South http://south.readthedocs.org/en/latest/tutorial/index.html
- [ ] migrate form fields to proper data types (e.g. URLField)
- [ ] create profile views /profile/293
- [ ] create edit profile view /profile/edit
- [ ] have "edit" button only appear on your own profile
- [ ] expose blog field in the user profile & edit views
- [ ] make a public profile view (aka what another user sees when they view your profile)
- [ ] redirect /profile to the profile of the logged-in user

MAYBE
- [ ] add responsive layouts with bootstrap?
- [ ] Add GA
- [ ] Add flash messaging (this might still work in 1.5 https://groups.google.com/forum/?fromgroups=#!topic/django-users/1YtRSukvviE) Also useful https://docs.djangoproject.com/en/dev/ref/contrib/messages/
- [ ] graphs of blogging over time. github timestamp