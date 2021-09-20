# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/).  Though
this project doesn't really have releases (or even versioning, until now), it
is a project that effects Recursers in "real ways".  It would be nice to have a
place to quickly see the latest changes that the project has undergone.


## 2021-09

### Added

- [#165] Mention post authors when announcing posts on Zulip -- @punchagan

### Changed

- [0095aef45af9e906259b48f1e6757ec9cef86870] Switch to using Poetry to manage
  dependencies. The requirements.txt file was quite unmanageable. Also, updated
  all the dependencies to the latest versions.

- [421af8fe46b74715a8d2f4020d6253607568821e] Upgrade to the latest version of
  Django -- @punchagan

## 2019-12

### Changed

- [cd957294e7f75f5b9ec2c9668325a3abc40ccca9] Upgrade from Python2 to Python3 -- @punchagan

## 2019-10

### Fixed

- [90d681383d840b913e8f53bbd4b0e5de70461391] Fixed problem with feed generation
  when a post title/content contains control characters

## 2018-03

### Added

- [#155,#156] Added command to update all user details -- @punchagan

- [#151] Added command to delete posts with duplicate titles -- @punchagan

- [#147] Added a skip_crawl flag on blogs to ignore them during crawls. Also,
  added a command to mark offending blogs and notify their owners. -- @punchagan

### Fixed

- [#143,#144] Don't add medium comments as posts -- @punchagan

### Changed

- [#107] - Use gevent to make crawls asynchronous -- @punchagan

- [2d6d3986f019b10f67616054c0a2fb8287c9f345] Remove the add_blog page, and move
  the form to the profile page -- @punchagan

- [#145] Change Django to 1.11.11 (LTS) -- @punchagan

- [#148] Don't add posts when a new blog is added. Also clean up how feed URL
  suggestions are done -- @punchagan

- [#154] Upgraded to the latest version of bootstrap 4.0.0 and switched to CDN.
  Also merged the edit_blog page into the profile page. -- @punchagan

- [#155] Use a personal token to update user details, and old hairy code that
  fetched backend and tried to get user's new details -- @punchagan

### Removed

- [#157] Removed URL attribute for blogs -- @punchagan

- [#156] Removed code for authenticating legacy users -- @punchagan

## 2017-02

### Added

- [#138] Added simple post title based search -- @stanzheng
- [#137] Added a Docker based development environment -- @stanzheng

## 2016-12

### Fixed

- [#132] OAuth account creation fails if user does not have 'twitter' or
  'github' details in their profile -- @punchagan

## 2016-11

### Changed

- [#106] Upgraded to Django 1.10 -- @punchagan

## 2016-10

### Added

- [#116] Added an AGPL license to the project -- @punchagan

- [#128] Added token based authentication for atom feed -- @punchagan

### Changed

- [#127] Use Django's feed generation mechanism instead of a custom template
  for Atom feeds -- @punchagan

- [#127] Also, set-up travis integration to start running Django tests -- @punchagan

- [#124] Post content is also saved to the DB for each crawled blog post -- @punchagan

- [#118] Switched over the live site to https://blaggregator.recurse.com -- @punchagan

### Removed

- [#121] The comments feature has been removed because it didn't see many
  people using it.  Instead, links to the Zulip thread have been added --
  @punchagan

### Fixed

- [#115] Fixed a bug introduced when allowing crawls of posts without a date --
  they always showed up at the top because the `date_updated` was being reset
  on every crawl -- @punchagan

## 2016-09

### Fixed

- [#113] Allow adding feeds that may not have published dates for posts --
  @punchagan

## 2016-08

### Changed

- [#112] Change the Zulip API endpoint to the new Zulip domain -- @punchagan

- [#112] Stop using runscope for making API calls to Zulip to post
  notifications -- @punchagan

## 2016-05

### Changed

- [#110] Improve user profiles to display all posts made by an author on a page
  -- @punchagan

- [#107] Add a header row to the most viewed posts table -- @sursh

### Fixed

- [#111] Ignore `CharacterEncodingOverride` exception is really a warning, but
  `feedparser` treats it as an error causing some blogs to not be parsed
  correctly. -- @punchagan

- [#100] Verify if a url is valid before adding it as a feed url to parse --
  @punchagan

## 2015-12

### Changed
- [#105] Allow specifying the number of days for which to generate the most
  viewed post stats

### Fixed
- [#105] most viewed posts stats generation failed when post titles had unicode
  -- @punchagan

## 2015-06

- [#83] Add a view to see most viewed posts during the last week -- @punchagan

## 2015-05

### Changed

- [#92] Blaggregator previously checked only for the URL of posts to see if a
  post is different from another. A bug in Medium's RSS generation caused Zulip
  to be spammed with tens or hundreds of notifications.  This change added a
  check to check for titles of posts, first, before checking URLs -- @punchagan

- [#81] Fix naive datetime warnings when new blogs are added. -- @punchagan

## 2015-03

### Changed

- [#88] Switch to using OAuth API from recurse.com instead of hackerschool.com
  -- @zachallaun

### Fixed

- [#85] First crawl of the blog of a user with (an)other blog(s) already added
  would fail silently -- @punchagan

## 2015-03

### Added

- [#69] Add a button to the header to allow users to add a blog, if they
  already didn't add one. -- @punchagan

- [#67] Log blog post link clicks/visits -- @punchagan

### Changed

- [#68] Instead of ignoring posts older than 2 days, and not announcing them on
  Zulip, limit the number of posts announced per crawl per blog to 2 -- @nnja

### Removed

- [#67] Get rid of html frames in the site -- @punchagan

### Fixed

- [#71] Return a 404 instead of a 500 for unknown slugs, and improve the 404
  page. -- @punchagan

## 2014-08

### Fixed

- [#65] Fix broken profile images because of stale user information obtained
  from Hacker School's OAuth end-point  -- @punchagan

### Changed

- [#64] Allow user to pick stream & edit their own blogs -- @sursh and @punchagan

## 2014-03

### Added

- [#55] Add authentication using Hacker School OAuth -- @davidbalbert

### Changed

- [#59] Use /people/me instead of /people/me.json -- @davidbalbert

## 2014-02

### Changed

- [#52] Simplify the topic names, since the notification stream on Zulip was
  changed to 'blogging' -- @graue

- Changed the notification stream to blogging -- @sursh

## 2014-02

### Fixed

- [#50] Get runscope bucket information from an environment variable -- @pnf

## 2013-07

### Added

- [#33] Add menu to navbar to let users add their blog, and logout functionality -- @porterjamesj

## 2013-10

### Fixed

- [#30] Changed CharFields to Textfields -- @PuercoPop

## 2013-07

### Added

- [#24] Added pagination in the home page "/new". -- @santialbo

### Fixed

- [#28] Secret key should be loaded from an environment variable -- @PuercoPop

## 2013-06

### Changed

- [#17] Made the layout for post discussion page clearer, trying to make the
  blog post info the focal point -- @alliejones

## 2013-04

### Added

- [#6] Added a bot to post new blog-posts to humbug -- @einashaddad and
  @kenyavs

- [#2] Added an (authenticated) atom feed for all the posts -- @santialbo

## Changed

- [#4] Don't require S3 in local environment -- @thomasboyt
