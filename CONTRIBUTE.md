##Contributions Welcome!

This project is for the whole Hacker School community. Right now, we don't have a great place to chat across the batches: email is too high-pressure, Zulip is too noisy. But here, alums from every batch can come to talk about interesting articles about programming. They can also be an engaged, friendly, technical audience for each other. 

If you enjoy the tool or are interested in practice web programming on a real app that's heavily used every day, this is a great way to get some experience. Please feel free to contribute features and fixes. Here are some upcoming plans. Please feel free to reach out to Sasha (@sursh) if you have any other project ideas or questions. 

### High priority:
- Fix broken avatars: query the HS API to grab the updated URLs, and store the images in our db 
- Celery backend so everything works more faster
- Email subscription: allow people to sign up to get emailed when there are new posts (dependency: celery backend)
- Set up testing infrastructure so future PRs can be reviewed more quickly

### Second priority: 
- tracking link clicks
- voting on posts (this might be used someday to determine which articles should publicly represent Hacker School)
- Improve the header so that it shows other articles on the same topic or by the same author

### Would also be awesome:
- a natural language parser that autotags posts by content ('python', 'bash', etc)
- a security audit of the app
- allow users to edit their profiles (avatar, displayed name, social media links, and most importantly, edit the blogs they've added)
- enhancing the profile page for each user within Blaggregator (right now we just list their blogs) that collates their posts and comments
- [there are some nice bugs to tackle](https://github.com/sursh/blaggregator/issues?page=1&state=open)
- Rewrite the app in Flask so it is easier to maintain

### Done by past contributors: 
- allow users to edit their blog registrations and allow posting to different streams on Zulip (thanks, @punchagan)
- a bot to post new blog posts to Humbug (thanks, @einashaddad and @kenyavs)
- comments on posts (@sursh)
- scraper script to check blogs for updates (thanks, @brannerchinese)
- an atom feed (thanks, @santialbo)
- pagination of the main page (so users can look back through the archives) (thanks, @santialbo)
- dropdown navigation menu so you can add your blog and log out (thanks, @porterjamesj)