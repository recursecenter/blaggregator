##Contributions Welcome!

This project is for the whole Hacker School community. Right now, we don't have a great place to chat across the batches: email is too high-pressure, Zulip is too noisy. But here, alums from every batch can come to talk about interesting articles about programming. 

Please feel free to contribute features if you'd like practice working on web applications. Here are some ideas for potential projects. Reach out to Sasha if you have any other project ideas or questions. 

### High priority:
- Celery backend so everything works more better
- a "submit" function so people can add outside articles for discussion, like on Hacker News. Then, the new blog posts by Hacker Schoolers will be considered "auto-submitted"
- Email subscription: allow people to sign up to get emailed when there are new posts (dependency: celery backend)

### Second priority: 
- tracking link clicks
- voting on posts (this might be used someday to determine which articles should publicly represent Hacker School)
- allow users to edit their profiles (avatar, displayed name, social media links, and most importantly, edit the blogs they've added)

### Would also be awesome:
- a natural language parser that autotags posts by content ('python', 'bash', etc)
- a bookmarklet so people can submit articles right from their browser (dependency: 'submit' feature above)
- a security audit of the app
- a profile for each user within Blaggregator (right now we just link to their HS page) that collates their posts and comments
- host avatars in the app instead of hotlinking them 
- [there are some nice bugs to tackle](https://github.com/sursh/blaggregator/issues?page=1&state=open), mostly around encoding

### Done by past contributors: 
- a bot to post new blog posts to Humbug (thanks, @einashaddad and @kenyavs)
- comments on posts (@sursh)
- scraper script to check blogs for updates (thanks, @brannerchinese)
- an atom feed (thanks, @santialbo)
- pagination of the main page (so users can look back through the archives) (thanks, @santialbo)
- dropdown navigation menu so you can add your blog and log out (thanks, @porterjamesj)