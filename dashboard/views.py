from collections import defaultdict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count, Sum
from django.views.generic import TemplateView

from assets.models import Asset, AssetHistory, Category, Location


def percent(part, whole):
    return round(part * 100 / whole) if whole else 0


def build_location_rows(total_assets):
    """Flatten the location tree in pre-order with cumulative asset counts."""
    locations = Location.objects.annotate(direct_count=Count("assets")).order_by("name")
    children = defaultdict(list)
    for location in locations:
        children[location.parent_id].append(location)

    rows = []

    def visit(location, depth):
        row = {
            "name": location.name,
            "indent": depth * 20,
            "direct": location.direct_count,
        }
        total = location.direct_count
        rows.append(row)
        for child in children[location.pk]:
            total += visit(child, depth + 1)
        row["total"] = total
        row["percent"] = percent(total, total_assets)
        return total

    for root in children[None]:
        visit(root, 0)

    return rows


class DashboardView(PermissionRequiredMixin, TemplateView):
    permission_required = ["assets.view_asset", "assets.view_assethistory"]
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_assets = Asset.objects.count()
        status_counts = {
            row["status"]: row["n"]
            for row in Asset.objects.values("status").annotate(n=Count("id"))
        }

        context["total_assets"] = total_assets
        context["total_value"] = Asset.objects.aggregate(total=Sum("purchase_price"))["total"]
        context["in_use"] = status_counts.get(Asset.Status.IN_USE, 0)
        context["in_maintenance"] = status_counts.get(Asset.Status.MAINTENANCE, 0)

        # Iterate over Status.choices so statuses with zero assets still appear.
        context["by_status"] = [
            {
                "value": value,
                "label": label,
                "count": status_counts.get(value, 0),
                "percent": percent(status_counts.get(value, 0), total_assets),
            }
            for value, label in Asset.Status.choices
        ]

        context["by_category"] = [
            {
                "pk": category.pk,
                "name": category.name,
                "count": category.n,
                "percent": percent(category.n, total_assets),
            }
            for category in Category.objects.annotate(n=Count("assets")).order_by("-n", "name")
        ]

        context["by_location"] = build_location_rows(total_assets)
        context["recent_events"] = AssetHistory.objects.select_related("asset", "user")[:10]
        return context