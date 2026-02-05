from django.db import transaction
from academics.models import AcademicTerm


class AcademicTermService:

    @staticmethod
    @transaction.atomic
    def set_current_term(term: AcademicTerm):
        AcademicTerm.objects.filter(
            institution=term.institution,
            is_current=True
        ).exclude(id=term.id).update(is_current=False)

        term.is_current = True
        term.save(update_fields=["is_current"])
