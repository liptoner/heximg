from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from core.models import Plan, UserPlan


class Command(BaseCommand):
    help = "Switch user's plan"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--username", type=str, required=True)
        parser.add_argument("--plan", type=str, required=True)

    def handle(self, *args, **options):
        user = User.objects.get(username=options["username"])

        try:
            plan = Plan.objects.get(title=options["plan"])
        except Plan.DoesNotExist:
            raise CommandError(
                'Plan with "{plan}" title does not exist\nAvailable plans: {plan_titles}'.format(
                    plan=options["plan"],
                    plan_titles=",".join(Plan.objects.all().order_by("title").values_list("title", flat=True)),
                )
            )

        n = UserPlan.objects.update(user=user, plan=plan)
        if n == 0:
            UserPlan.objects.create(user=user, plan=plan)

        self.stdout.write(self.style.SUCCESS("Successfully changed plan"))
