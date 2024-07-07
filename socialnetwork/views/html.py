from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from socialnetwork import api
from socialnetwork.api import _get_social_network_user
from socialnetwork.serializers import PostsSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

@require_http_methods(["GET"])
@login_required
def timeline(request):
    # using the serializer to get the data, then use JSON in the template!
    # avoids having to do the same thing twice

    # get extra URL parameters:
    keyword = request.GET.get("search", "")
    published = request.GET.get("published", True)
    error = request.GET.get("error", None)

    # if keyword is not empty, use search method of API:
    current_user = _get_social_network_user(request.user)
    if keyword and keyword != "":
        posts = api.search(keyword, published=published)
    else:
        posts = api.timeline(current_user, published=published)

    # Get the list of users the current user is following
    following_users = api.follows(current_user)

    # Create a set of user IDs that the current user is following
    following_user_ids = {user.id for user in following_users}

    context = {
        "posts": PostsSerializer(posts, many=True).data,
        "searchkeyword": keyword,
        "error": error,
        "following_user_ids": following_user_ids,
    }

    return render(request, "timeline.html", context=context)


@require_http_methods(["POST"])
@login_required
def follow(request):
    user_to_follow_id = request.POST.get('user_id')
    if user_to_follow_id:
        current_user = _get_social_network_user(request.user)
        try:
            user_to_follow = User.objects.get(id=user_to_follow_id)
            user_to_follow = _get_social_network_user(user_to_follow)
            if user_to_follow:
                api.follow(current_user, user_to_follow)
        except User.DoesNotExist:
            pass  # Handle the case where the user doesn't exist
    return redirect('timeline')

@require_http_methods(["POST"])
@login_required
def unfollow(request):
    user_to_unfollow_id = request.POST.get('user_id')
    if user_to_unfollow_id:
        current_user = _get_social_network_user(request.user)
        try:
            user_to_unfollow = User.objects.get(id=user_to_unfollow_id)
            user_to_unfollow = _get_social_network_user(user_to_unfollow)
            if user_to_unfollow:
                api.unfollow(current_user, user_to_unfollow)
        except User.DoesNotExist:
            pass  # Handle the case where the user doesn't exist
    return redirect('timeline')

