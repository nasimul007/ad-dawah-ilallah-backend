from django.urls import path, include
from rest_framework.routers import DefaultRouter
from forms.views import (
    MosqueCourseRegistrationViewSet,
    QuranAndDeenCourseViewSet,
    ProgramRegistrationViewSet,
    AlItisamRegistrationViewSet,
    KhutbaRegistrationViewSet,
)

router = DefaultRouter()
router.register(
    "mosque-course-registrations",
    MosqueCourseRegistrationViewSet,
    basename="mosque-course-registrations"
)
router.register(
    "quran-deen-course-registrations",
    QuranAndDeenCourseViewSet,
    basename="quran-deen-course-registrations"
)
router.register(
    "program-registrations",
    ProgramRegistrationViewSet,
    basename="program-registrations"
)
router.register(
    "al-itisam-registrations",
    AlItisamRegistrationViewSet,
    basename="al-itisam-registrations"
)
router.register(
    "khutba-registrations",
    KhutbaRegistrationViewSet,
    basename="khutba-registrations"
)

urlpatterns = [
    path("", include(router.urls)),
]

