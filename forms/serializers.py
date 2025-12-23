from rest_framework import serializers
from forms.models import (
    MosqueCourseRegistration,
    QuranAndDeenCourse,
    ProgramRegistration,
    AlItisamRegistration,
    KhutbaRegistration
)


class MosqueCourseRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MosqueCourseRegistration
        fields = [
            "id",
            "mosque_name",
            "full_name_bangla",
            "full_name_english",
            "email",
            "mobile_number",
            "mosque_address",
            "upazila",
            "district",
            "profession",
            "interested_person",
            "course_source",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class QuranAndDeenCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuranAndDeenCourse
        fields = [
            "id",
            "full_name_bangla",
            "full_name_english",
            "email",
            "mobile_number",
            "village_locality",
            "post_office",
            "upazila",
            "district",
            "date_of_birth",
            "current_age",
            "course_source",
            "photo_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProgramRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramRegistration
        fields = [
            "id",
            "responsible_person_name",
            "field_name",
            "village",
            "post_office",
            "postal_code",
            "upazila",
            "division",
            "reference_person_name",
            "responsible_person_number",
            "program_type",
            "district",
            "program_probable_date",
            "venue_google_location_url",
            "program_fund_collection",
            "speakers",
            "program_time",
            "participated_quran_deen_course",
            "mosque_has_maktab",
            "attend_salafi_conferences",
            "subscriber_al_itisam",
            "affiliated_jamiah_salafiyyah",
            "participated_3day_madrasa",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AlItisamRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlItisamRegistration
        fields = [
            "id",
            "your_name",
            "email",
            "mobile_number",
            "village_locality_institution",
            "post",
            "upazila",
            "district",
            "how_many_copies",
            "delivery_medium",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class KhutbaRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = KhutbaRegistration
        fields = [
            "id",
            "mosque_name",
            "village_locality_street",
            "post_office",
            "upazila",
            "district",
            "mosque_responsible_person_name",
            "responsible_person_number",
            "whatsapp_number",
            "email",
            "mosque_google_location_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

