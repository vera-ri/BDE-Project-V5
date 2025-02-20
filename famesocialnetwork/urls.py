"""
URL configuration for famesocialnetwork famesocialnetwork.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

from famesocialnetwork.views.html import home, MyLogoutView, MyLoginView
from socialnetwork.views.html import timeline, follow, unfollow

urlpatterns = [
    path(
        "",
        MyLoginView.as_view(
            template_name="login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path(
        "logout/",
        MyLogoutView.as_view(
            template_name="logged_out.html",
            next_page="/",
        ),
        name="logout",
    ),
    path("home/", home, name="home"),
    path("admin/", admin.site.urls),
    path("fame/", include("fame.urls", namespace="fame")),  # reroute to fame app
    path(
        "sn/", include("socialnetwork.urls", namespace="sn")
    ),  # reroute to social network app
    path("timeline/", timeline, name="timeline"),
    path("follow/", follow, name="follow"),
    path("unfollow/", unfollow, name="unfollow"),
]
