from home.models import Blog


def primary_blog(request):
    count = Blog.objects.filter(user=request.user.id).count()
    return {"primary_blog_set": True if count > 0 else False}
