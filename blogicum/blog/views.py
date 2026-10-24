from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import Post, Category, User, Comment
from .forms import PostForm, UserForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

def published_posts():
    return Post.objects.select_related(
        "author", "location", "category"
    ).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    )


def index(request):
    post_list = published_posts()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj}
    return render(request, 'blog/index.html', context)


def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug, is_published=True)

    post_list = published_posts().filter(category=category)

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {"category": category, "page_obj": page_obj}
    return render(request, 'blog/category.html', context)


def post_detail(request, pk):
    conditions = Q(
    is_published=True,
    pub_date__lte=timezone.now(),
    category__is_published=True,
    )
   
    if request.user.is_authenticated:
        conditions |= Q(author=request.user)

    post = get_object_or_404(
        Post.objects.select_related("author", "location", "category")
        .filter(conditions),
        pk=pk,
    )
       
    form = CommentForm()
    comments = Comment.objects.select_related('author').filter(post=post)

    context = {"form": form, "post": post, 'comments': comments}
    return render(request, 'blog/detail.html', context)


@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)

    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', pk=post_id)

    form = PostForm(request.POST or None, request.FILES or None,
                            instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', pk=post_id)
    
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comm = form.save(commit=False)
        comm.post = post
        comm.author = request.user
        comm.save()
        return redirect('blog:post_detail', pk=post_id)

    context = {'form': form}
    return render(request, 'includes/comments.html', context)


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)

    form = CommentForm(request.POST or None, instance=comment)

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', pk=post_id)

    context = {'form': form, 'post': post, 'comment': comment}
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', pk=post_id)
    
    context = {'comment': comment, 'post': post}
    return render(request, 'blog/comment.html', context)


def user_profile(request, username):
    user = get_object_or_404(User, username=username)

    if user == request.user:
        posts = Post.objects.select_related(
            'author', 'location', 'category').filter(author=user)
    else:
        posts = published_posts().filter(author=user)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'profile': user, 'page_obj': page_obj}
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    form = UserForm(request.POST or None, request.FILES or None,
                    instance=request.user)

    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)

    context = {'form': form}
    return render(request, 'blog/user.html', context)