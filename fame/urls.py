from django.urls import path

from fame.views.html import fame_list, experts, bullshitters
from fame.views.rest import ExpertiseAreasApiView, FameUsersApiView, FameListApiView

app_name = "fame"

urlpatterns = [
    path(
        "api/expertise_areas", ExpertiseAreasApiView.as_view(), name="expertise_areas"
    ),
    path("api/users", FameUsersApiView.as_view(), name="fame_users"),
    path("api/fame", FameListApiView.as_view(), name="fame_fulllist"),
    path("html/fame", fame_list, name="fame_list"),
    path("html/experts", experts, name="experts"),  # add a path to experts /fame/html/experts so mapping urls to views
    # see lecture 07 p.27 mapping urls to views
    path("html/bullshitters", bullshitters, name="bullshitters")  # add a path to bullshitters /fame/html/bullshitters
]
