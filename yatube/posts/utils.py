from django.core.paginator import Paginator


QUANTTIY_OF_POSTS = 10


def page_maker(request, posts):
    paginator = Paginator(posts, QUANTTIY_OF_POSTS)
    page_nuber = request.GET.get('page')
    page_obj = paginator.get_page(page_nuber)
    return page_obj
