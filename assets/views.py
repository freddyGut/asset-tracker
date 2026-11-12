from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import AssetFilterForm, AssetForm, AssetLimitedForm
from .models import Asset, AssetHistory
from .services import log_asset_changes


class AssetListView(PermissionRequiredMixin, ListView):
    permission_required = "assets.view_asset"
    
    model = Asset
    context_object_name = "assets"  # template variable name (default: object_list)
    paginate_by = 20

    def get_queryset(self):
        """Apply the search/filter form to the asset queryset."""
        # select_related fetches the foreign keys with a JOIN in the same query,
        # avoiding one extra query per row (the N+1 problem).
        queryset = super().get_queryset().select_related("category", "location", "assigned_to")

        self.filter_form = AssetFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data["q"]:
                queryset = queryset.filter(
                    Q(tag__icontains = data["q"])
                    | Q(name__icontains = data["q"])
                    | Q(serial_number__icontains = data["q"])
                )
            if data["category"]:
                queryset = queryset.filter(category=data["category"])
            if data["location"]:
                queryset = queryset.filter(location=data["location"])
            if data["status"]:
                queryset = queryset.filter(status=data["status"])

        return queryset


    def get_context_data(self, **kwargs):
        """Add the filter form and the current filters to the template context."""
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form

        # Pagination links must keep the active filters: the querystring is the
        # current GET parameters without "page" (e.g. "q=Laptop&location=3").
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()

        return context



class AssetDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "assets.view_asset"

    model = Asset
    queryset = Asset.objects.select_related("category", "location", "assigned_to")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Last 50 events only (SQL LIMIT); select_related avoids a query per event for the user.
        context["history"] = self.object.history.select_related("user")[:50]
        return context
        

class AssetCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "assets.add_asset"

    model = Asset
    form_class = AssetForm

    def form_valid(self, form):
        # atomic: the asset and its history are saved together or not at all
        with transaction.atomic():
            response = super().form_valid(form)
            # Asset.save() already created the CREATED event without an author;
            # here the user is known, so attach it.
            self.object.history.filter(event_type=AssetHistory.EventType.CREATED).update(user=self.request.user)
        messages.success(self.request, f"Asset {self.object.tag} created")
        return response

    
class AssetUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "assets.change_asset"

    model = Asset
    
    def get_form_class(self):
        if self.request.user.has_perm("assets.change_asset_details"):
            return AssetForm
        else:
            return AssetLimitedForm

    def form_valid(self, form):
        # Validation has already written the new values into self.object (in memory),
        # so the "before" snapshot must be re-read from the database.
        old = Asset.objects.select_related("location", "assigned_to").get(pk=self.object.pk)

        with transaction.atomic():
            response = super().form_valid(form)
            log_asset_changes(old, self.object, self.request.user, form.changed_data) 
        messages.success(self.request, f"Asset {self.object.tag} updated")
        return response

class AssetDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "assets.delete_asset"

    model = Asset
    success_url = reverse_lazy("assets:asset_list")

    def form_valid(self, form):
        label = str(self.object)  # captured before the row is deleted
        response = super().form_valid(form)
        messages.success(self.request, f"Asset {label} deleted")
        return response