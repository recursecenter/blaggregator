{% load customtags %}
Hi {{blog.author}},

You added {{blog.feed_url}} as a Blaggregator feed. We are unable to parse it.
Could you please update/remove it from [here]({{base_url}}{% url 'profile' user.id %})?

{% stripnewlines %}
    If this appears to be a problem with Blaggregator, or you need help fixing
    this, please
    {% if admins %}
        get in touch with {{admins}}
    {% else %}
        {% spaceless  %}
            file an issue [here](https://github.com/recursecenter/blaggregator/issues)
        {% endspaceless %}
    {% endif %}
{% endstripnewlines %}
