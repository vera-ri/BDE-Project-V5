from django.db.models import Q

from fame.models import Fame, FameLevels
from socialnetwork.models import Posts, SocialNetworkUsers


# general methods independent of html and REST views
# should be used by REST and html views


def _get_social_network_user(user) -> SocialNetworkUsers:
    """Given a FameUser, gets the social network user from the request. Assumes that the user is authenticated."""
    try:
        user = SocialNetworkUsers.objects.get(id=user.id)
    except SocialNetworkUsers.DoesNotExist:
        raise PermissionError("User does not exist")
    return user


def timeline(user: SocialNetworkUsers, start: int = 0, end: int = None, published=True):
    """Get the timeline of the user. Assumes that the user is authenticated."""
    _follows = user.follows.all()
    posts = Posts.objects.filter(
        (Q(author__in=_follows) & Q(published=published)) | Q(author=user)
    ).order_by("-submitted")
    if end is None:
        return posts[start:]
    else:
        return posts[start: end + 1]


def search(keyword: str, start: int = 0, end: int = None, published=True):
    """Search for all posts in the system containing the keyword. Assumes that all posts are public"""
    posts = Posts.objects.filter(
        Q(content__icontains=keyword)
        | Q(author__email__icontains=keyword)
        | Q(author__first_name__icontains=keyword)
        | Q(author__last_name__icontains=keyword),
        published=published,
    ).order_by("-submitted")
    if end is None:
        return posts[start:]
    else:
        return posts[start: end + 1]


def follows(user: SocialNetworkUsers, start: int = 0, end: int = None):
    """Get the users followed by this user. Assumes that the user is authenticated."""
    _follows = user.follows.all()
    if end is None:
        return _follows[start:]
    else:
        return _follows[start: end + 1]


def followers(user: SocialNetworkUsers, start: int = 0, end: int = None):
    """Get the followers of this user. Assumes that the user is authenticated."""
    _followers = user.followed_by.all()
    if end is None:
        return _followers[start:]
    else:
        return _followers[start: end + 1]


def follow(user: SocialNetworkUsers, user_to_follow: SocialNetworkUsers):
    """Follow a user. Assumes that the user is authenticated. If user already follows the user, signal that."""
    if user_to_follow in user.follows.all():
        return {"followed": False}
    user.follows.add(user_to_follow)
    user.save()
    return {"followed": True}


def unfollow(user: SocialNetworkUsers, user_to_unfollow: SocialNetworkUsers):
    """Unfollow a user. Assumes that the user is authenticated. If user does not follow the user anyway, signal that."""
    if user_to_unfollow not in user.follows.all():
        return {"unfollowed": False}
    user.follows.remove(user_to_unfollow)
    user.save()
    return {"unfollowed": True}


def submit_post(
        user: SocialNetworkUsers,
        content: str,
        cites: Posts = None,
        replies_to: Posts = None,
):
    """Submit a post for publication. Assumes that the user is authenticated.
    returns a tuple of three elements:
    1. a dictionary with the keys "published" and "id" (the id of the post)
    2. a list of dictionaries containing the expertise areas and their truth ratings
    3. a boolean indicating whether the user was banned and logged out and should be redirected to the login page
    """

    # create post  instance:
    post = Posts.objects.create(
        content=content,
        author=user,
        cites=cites,
        replies_to=replies_to,
    )

    # classify the content into expertise areas:
    # only publish the post if none of the expertise areas contains bullshit:
    _at_least_one_expertise_area_contains_bullshit, _expertise_areas = (
        post.determine_expertise_areas_and_truth_ratings()
    )
    post.published = not _at_least_one_expertise_area_contains_bullshit

    redirect_to_logout = False

    #########################
    # add your code here
    # T1: not publish posts that have an expertise area which is contained in the user's fame profile
    # and marked negative there

    # find the negative expertise areas for the given user
    neg_expertise_areas = Fame.objects.filter(
        user=user,
        fame_level__numeric_value__lt=0
    )
    # check if content in the post overlaps with negative expertise areas of the user
    for e in _expertise_areas:
        if neg_expertise_areas.filter(expertise_area=e["expertise_area"]).exists():
            post.published = False

    # T2: adjust the fame profile for the expertise area pf the user if they submit a post with
    # a negative truth rating

    # collect expertise areas with negative truth ratings
    areas_with_neg_truth_ratings = set()
    for e in _expertise_areas:
        if e["truth_rating"]:  # TruthRating can also be None
            if e["truth_rating"].numeric_value < 0:
                areas_with_neg_truth_ratings.add(e["expertise_area"])

    # update fame profiles based on negative truth ratings
    for n in areas_with_neg_truth_ratings:
        if Fame.objects.filter(user=user, expertise_area=n).exists():
            # T2a: if the expertise area is already contained in the user's fame profile
            # lower the fame to the next possible level
            current_area = Fame.objects.get(user=user, expertise_area=n)
            try:
                next_lower_fame_level = current_area.fame_level.get_next_lower_fame_level()
                current_area.fame_level = next_lower_fame_level
                current_area.save()
            except ValueError:
                # T2c: if the fame level cannot be lowered further ban the user
                user.is_active = False
                user.save()
                # logging out the user if they are logged in
                redirect_to_logout = True
                # unpublish all their posts
                Posts.objects.filter(author=user).update(published=False)
        else:
            # T2b: if expertise area is not contained, add an entry in the user's fame profile
            # with the fame level "Confuser"
            new_area = Fame.objects.create(
                user=user,
                expertise_area=n,
                fame_level=FameLevels.objects.get(name="Confuser")
            )
            new_area.save()

    #########################
    post.save()

    return (
        {"published": post.published, "id": post.id},
        _expertise_areas,
        redirect_to_logout,
    )


def rate_post(
        user: SocialNetworkUsers, post: Posts, rating_type: str, rating_score: int
):
    """Rate a post. Assumes that the user is authenticated. If user already rated the post with the given rating_type,
    update that rating score."""
    user_rating = None
    try:
        user_rating = user.userratings_set.get(post=post, rating_type=rating_type)
    except user.userratings_set.model.DoesNotExist:
        pass

    if user == post.author:
        raise PermissionError(
            "User is the author of the post. You cannot rate your own post."
        )

    if user_rating is not None:
        # update the existing rating:
        user_rating.rating_score = rating_score
        user_rating.save()
        return {"rated": True, "type": "update"}
    else:
        # create a new rating:
        user.userratings_set.add(
            post,
            through_defaults={"rating_type": rating_type, "rating_score": rating_score},
        )
        user.save()
        return {"rated": True, "type": "new"}


def fame(user: SocialNetworkUsers):
    """Get the fame of a user. Assumes that the user is authenticated."""
    try:
        user = SocialNetworkUsers.objects.get(id=user.id)
    except SocialNetworkUsers.DoesNotExist:
        raise ValueError("User does not exist")

    return user, Fame.objects.filter(user=user)


def experts():
    """Return for each existing expertise area in the fame profiles a list of the users having positive fame for that
    expertise area. The list should be a Python dictionary with keys ``user'' (for the user) and ``fame_level_numeric''
    (for the corresponding fame value), and should be ranked, i.e. users with the highest fame are shown first, in case
    there is a tie, within that tie sort by date_joined (most recent first). Note that expertise areas with no expert
    may be omitted.
    """
    # existing expertise area in the fame profiles with positive fame --> filter Fame objects
    # users with the highest fame are shown first (desc), within a tie sort by date_joined (most recent first)
    # expertise areas with no expert are omitted because then the fame profile does not exist
    positive_fame_profiles = (Fame.objects
                              .filter(fame_level__numeric_value__gt=0)
                              .order_by("-fame_level__numeric_value", "-user__date_joined"))

    # Returned value should be a dictionary with expertise areas as keys and a list of users as values.
    result = {}
    for profile in positive_fame_profiles:
        expertise_area = profile.expertise_area
        # list should be a Python dictionary with keys "user" and "fame_level_numeric"
        user_dict = {
            "user": profile.user,
            "fame_level_numeric": profile.fame_level.numeric_value
        }
        if expertise_area not in result:
            result[expertise_area] = []  # initialize new key entry with empty value list
        result[expertise_area].append(user_dict)  # add new user data to expertise area entry
    return result


def bullshitters():
    """Return for each existing expertise area in the fame profiles a list of the users having negative fame for that
    expertise area. The list should be a Python dictionary with keys ``user'' (for the user) and ``fame_level_numeric''
    (for the corresponding fame value), and should be ranked, i.e. users with the lowest fame are shown first, in case
    there is a tie, within that tie sort by date_joined (most recent first). Note that expertise areas with no expert
    may be omitted.
    """
    # existing expertise area in the fame profiles with negative fame --> filter Fame objects
    # users with the lowest fame are shown first (asc), within a tie sort by date_joined (most recent first)
    # expertise areas with no expert are omitted because then the fame profile does not exist
    negative_fame_profiles = (Fame.objects
                              .filter(fame_level__numeric_value__lt=0)
                              .order_by("fame_level__numeric_value", "-user__date_joined"))

    # Returned value should be a dictionary with expertise areas as keys and a list of users as values.
    result = {}
    for profile in negative_fame_profiles:
        expertise_area = profile.expertise_area
        # list should be a Python dictionary with keys "user" and "fame_level_numeric"
        user_dict = {
            "user": profile.user,
            "fame_level_numeric": profile.fame_level.numeric_value
        }
        if expertise_area not in result:
            result[expertise_area] = []  # initialize new key entry with empty value list
        result[expertise_area].append(user_dict)
    return result
