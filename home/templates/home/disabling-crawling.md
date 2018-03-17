{% load customtags %}
Hi {{user.get_full_name}},

Blaggregator bot is unable to parse the following blogs that you own:

{% for blog in blogs %}
- {{blog.feed_url}}
{% endfor %}

{% stripnewlines %}
Crawling has been **disabled** for these blogs. You could re-enable crawling by changing
the feed url in your [profile]({{base_url}}{% url 'profile' user.id %}).
{% endstripnewlines %}

{% stripnewlines %}
    If this appears to be a problem with Blaggregator, or you need help fixing
    this, please
    {% if admins %}
        get in touch with {{admins}}.
    {% else %}
        {% spaceless  %}
            file an [issue](https://github.com/recursecenter/blaggregator/issues).
        {% endspaceless %}
    {% endif %}
{% endstripnewlines %}

Happy Blogging!
