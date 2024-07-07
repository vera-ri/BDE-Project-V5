from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from fame.serializers import FameSerializer
from socialnetwork import api
from socialnetwork.api import _get_social_network_user
from socialnetwork.models import SocialNetworkUsers


@require_http_methods(["GET"])
@login_required
def fame_list(request):
    # try to get the user from the request parameters:
    userid = request.GET.get("userid", None)
    user = None
    if userid is None:
        user = _get_social_network_user(request.user)
    else:
        try:
            user = SocialNetworkUsers.objects.get(id=userid)
        except ValueError:
            pass

    user, fame = api.fame(user)
    context = {
        "fame": FameSerializer(fame, many=True).data,
        "user": user if user else "",
    }
    return render(request, "fame.html", context=context)


# things required:
@require_http_methods(["GET"])  # require GET methode to show us the data
@login_required  # need to be logged in
#  compute what I want to use in view of experts
def experts(request):
    expertsdictionary = api.experts()  # get the dictionary of experts by calling function experts()
    context = {
        "expertsdictionary": expertsdictionary  # give it as context to the template
    }
    return render(request, "experts.html", context=context)  # render experts.html file considering
    # the initial request and context


# same for the bullshitters
@require_http_methods(["GET"])
@login_required
def bullshitters(request):
    bullshittersdictionary = api.bullshitters()
    context = {
        "bullshittersdictionary": bullshittersdictionary
    }
    return render(request, "bullshitters.html", context=context)
