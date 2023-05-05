
from django.core.paginator import Paginator

NUMB_POSTS = 10
# Кол-во постов на странице


def paginator(request, post_list):
    """Добавляет paginator"""
    paginator = Paginator(post_list, NUMB_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return (page_obj)
