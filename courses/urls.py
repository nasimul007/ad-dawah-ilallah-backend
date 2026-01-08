from django.urls import path, include
from rest_framework.routers import DefaultRouter
from courses.views import CourseViewSet, ModuleViewSet, CourseContentViewSet

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("modules", ModuleViewSet, basename="modules")
router.register("contents", CourseContentViewSet, basename="contents")

urlpatterns = [
    path("", include(router.urls)),
]

