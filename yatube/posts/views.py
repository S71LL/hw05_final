from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import page_maker


@cache_page(20, key_prefix='index_page')
def index(request):
    templates = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = page_maker(request, posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, templates, context)


def group_posts(request, slug):
    templates = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts_of_group.all()
    page_obj = page_maker(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, templates, context)


def profile(request, username):
    templates = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts_of_author.all()
    posts_quantity = author.posts_of_author.count()
    page_obj = page_maker(request, posts)
    user = request.user
    following = Follow.objects.filter(user_id=user.id,
                                      author_id=author.id).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'quantity': posts_quantity,
        'following': following,
    }
    return render(request, templates, context)


def post_detail(request, post_id):
    templates = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    posts_quantity = post.author.posts_of_author.count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'quantity': posts_quantity,
        'form': form,
        'comments': comments
    }
    return render(request, templates, context)


@login_required
def post_create(request):
    templates = 'posts/post_create.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
    return render(request, templates, {'form': form})


@login_required
def post_edit(request, post_id):
    templates = 'posts/post_create.html'
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    context = {
        'form': form,
        'post_id': post_id,
        'is_edit': True
    }
    if request.user == post.author:
        if form.is_valid() and request.method == 'POST':
            form.save()
            return redirect('posts:post_detail', post.pk)
        return render(request, templates, context)
    return render(request, 'posts:post_detail', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    templates = 'posts/follow.html'
    user = get_object_or_404(User, username=request.user.username)
    following = Follow.objects.filter(user_id=user.id)
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = page_maker(request, posts)
    if following:
        context = {
            'page_obj': page_obj,
        }
    else:
        context = {
            'page_obj': [],
        }
    return render(request, templates, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if request.user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:follow_index')
