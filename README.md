# Blaggregator

Blog post aggregator for the Recurse Center community.  Live version runs at
<https://blaggregator.recurse.com> (RC login required).

<div class="well">

<h2>What is this?</h2>

<p>During her batch, Sasha (W '13) noticed that her peers were all blogging about
their work at the Recurse Center on their individual blogs. It was really cool
to see what they were working on and thinking about.</p>

<p>Some folks would post about their new posts in Zulip, some on Twitter, and some
wouldn't spread the word at all. There was all this great work going on, but it
was scattered across the internet.</p>

<p>Blaggregator puts all this awesome content in one place, and provides a place
for the members of the community to read and discuss it.  This has the nice
side effect of providing a friendly audience for those who may have just
launched their blog.</p>

</div>

## License

Copyright © 2013-2016 Sasha Laundy and others.

This software is licensed under the terms of the AGPL, Version 3. The complete
license can be found at https://www.gnu.org/licenses/agpl-3.0.html.

## FAQ

### How does it work?

Once an hour, the crawler checks all registered blogs for new posts. New posts
are displayed on the main page and a message is sent to Zulip.

"New" is defined as a post having a new URL and a new title.  So you can tweak
the title, change the content or the timestamp to your heart's content.

### Why do I have to log in?

The Recurse Center staff wishes to keep the list of people attending the
Recurse Center private. So you are required to authenticate with your Recurse
Center credentials

If that ever changes (for instance, to surface the best posts that are coming
out of the Recurse Center to show off what we're working on) you will be given
lots and lots of warning to decide how you want to participate.

### Who's behind it?

[Sasha](https://github.com/sursh) is the main author, with a bunch of
other
[recursers](https://github.com/recursecenter/blaggregator/graphs/contributors)
contributing.  You are welcome to contribute as well!

[Puneeth](https://github.com/punchagan) is the primary maintainer, currently.

### Can I contribute fixes and features?

Yes, that would be great! This is a project by and for the Recurse Center
community. Help make it more awesome!

There's a very generic and high level list
of
[areas that could use some help](https://github.com/recursecenter/blaggregator/blob/master/.github/CONTRIBUTING.md) and
a bunch of specific
[open issues](https://github.com/recursecenter/blaggregator/issues).

Look at
the
[developer documentation](https://github.com/recursecenter/blaggregator/blob/master/docs/development.md) for
help with setting up your development environment.

Before implementing a major contribution, it's wise to get in touch with the
maintainers by creating an issue (or using an existing issue) to discuss it.

### What's the stack?

It's a Django (Python) app, with some Bootstrap on the frontend.  It's deployed
on Heroku using their Postgres and Scheduler add-ons. Check out the
code [here](https://github.com/recursecenter/blaggregator).

### I don't see my blog post.

If you published it less than an hour ago, hang tight: it'll show up when the
crawler next checks the registered blogs. If Blaggregator finds many new posts
on your blog, it will only post the two most recent posts to Zulip. All of your
posts will still be available on the [site](https://blaggregator.recurse.com)

### My blog post appears on blaggregator but no Zulip notification sent.

- When a blog is added to Blaggregator, all the posts currently in the feed are
  added to the DB (and therefore marked as seen).  No notifications are sent
  for these posts.

- From the next crawl onwards, for every crawl a maximum of 2 notifications are
  sent for posts that haven't already been seen by blaggregator.

### My blog is multi-purpose and not wholly code/Recurse Center specific

No problem! Tag or categorize your relevant posts and make a separate RSS/Atom
feed for them.  Most blogging software has separate feeds for different
categories/tags.

If you use Wordpress, for instance, categorize all your code-related posts
"code", say. Then your code-specific RSS feed that you should publish to
Blaggregator is: http://yoururl.com/blog/category/code/feed/.

### Can I lurk?

Sure, just make an account and don't add your blog. But you shouldn't lurk. You
should blog.

### Why should I blog?

- It provides a record of your thinking and work for your future self.
- It gives prospective employers insight into the way you think.
- If you do a project that doesn't go as planned, you can still 'finish' the
  project and explain what you learned, even if you don't want to put the code
  on Github.
- It helps more people hear about and respect the Recurse Center, which in turn
  means more people will want to work with you.
- Writing helps you practice communicating, which is critical if you plan on
  working on a team of more than one person.
- It helps the developer community at large.

### But blogging takes too long!

Don't let the perfect be the enemy of the good. Your posts don't have to be
long, groundbreaking, perfect, or full of citations. Short, imperfect, and
*published* always beats unpublished.

### But I haven't found the perfect blogging tool

Don't let the perfect be the enemy of the good. Just get something up and
resist the urge to fiddle with it. Use Tumblr if you have to. Just start
writing.

### I need some more inspiration.

-   [You Should Write
    Blogs](https://sites.google.com/site/steveyegge2/you-should-write-blogs)
    (Steve Yegge)
-   [How to blog about code and give zero
    fucks](http://www.garann.com/dev/2013/how-to-blog-about-code-and-give-zero-fucks/).
    (Garann Means)
-   Please add your fave inspiration with a [pull
    request](https://github.com/recursecenter/blaggregator/pulls).

### I need some accountability!

Consider starting your own Iron Blogger challenge. Participants commit to
writing one blog post a week, and are on the hook for $5 if they don't
post. The pot can be used for a party, donated to charity, or donated to a
charity the group hates (added incentive to hit the publish button!).

The Fall 2013 batch ran a very successful Iron Blogger program. Mike
Walker
[wrote a very nice article on how it worked](http://blog.lazerwalker.com/blog/2013/12/24/one-post-a-week-running-an-iron-blogger-challenge/).
