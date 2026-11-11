from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import AssetFilterForm, AssetForm
from .models import Asset, AssetHistory
from .services import log_asset_changes


class AssetListView(LoginRequiredMixin, ListView):
    # tells Django which db table to query
    model = Asset 
    # by default, the list fetched is named "object_list" by Django, 
    # here, I'm personalizing the name
    context_object_name = "assets"
    paginated_by = 20

    def get_queryset(self):
        """
        Overrides the default query to add SQL optimization (select_related) 
        and dynamic search filtering based on user input.
        """
        # technical note: a queryset is actually a SQL query. This function builds the query for the db

        # optimization: translates in a JOIN query. All foreign keys are replaced with their verbose name
        # with one single query, the db returns all the data the user expects
        # this is the so-called "N+1 problem"
        # SELECT * FROM assets JOIN categories JOIN locations ...
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

        # the query is created in a optimized manner. now it goes to the dbms!
        return queryset 


    def get_context_data(self, **kwargs):
        """
        Overrides the context dictionary to inject extra variables (like the form 
        and the pagination string) before sending data to the HTML template.
        """
        context = super().get_context_data(**kwargs)
        # if the page is refreshed, the filters are saved in this variable and the user sees the same result
        context["filter_form"] = self.filter_form

        # Problem: If the user searches for "Laptop" and clicks "Page 2", the default 
        # link would be "?page=2", causing the server to forget the "Laptop" filter.
        # Solution: Create a copy of the current URL parameters (e.g., {"q": "Laptop", "page": "2"})
        params = self.request.GET.copy()
        # Remove the 'page' parameter from our copy, leaving only the active filters {"q": "Laptop"}
        params.pop("page", None)
        # Encode the dictionary back into a clean URL string (e.g., "q=Laptop") 
        # and pass it to the template as 'querystring'.
        # The template will use it to build dynamic pagination links: href="?{{ querystring }}&page=2"
        context["querystring"] = params.urlencode()
        # querystring = q=Laptop&location=Milano
        context["querystring"] = params.urlencode()

        return context



class AssetDetailView(LoginRequiredMixin, DetailView):
    model = Asset
    queryset = Asset.objects.select_related("category", "location", "assigned_to")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # go to the AssetHistory table and fetch all records related to this specific asset
        # also here, we have the N+1 problem for the user field in the history record
        # [:50] corresponds to the SQL LIMIT 50. The user will see only the last 50 history records
        context["history"] = self.object.history.select_related("user")[:50]
        return context
        

class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm

    # automatically called by Django if the data inserted in the form is valid
    # we can decide what happens before and after the data is saved in the database 
    def form_valid(self, form):
        # atomic: the asset and its history are saved together or not at all
        with transaction.atomic():
            # self.object created (contains the data of the newly created asset)
            # an INSERT is sent to the dbms, but the operation is on hold, still not executed
            response = super().form_valid(form)
            # INSERT for the history table
            self.object.history.filter(event_type=AssetHistory.EventType.CREATED).update(user=self.request.user)
        # if the operation is successful, we confirm that to the user, enhancing their experience
        messages.success(self.request, f"Asset {self.object.tag} created")
        # response is a HttpResponseRedirect (HTTP 302) that redirects to the URL specified in the 
        # get_absolute_url() of the Asset model
        return response

    
class AssetUpdateView(LoginRequiredMixin, UpdateView):
    model = Asset
    form_class = AssetForm

    def form_valid(self, form):
        # validation already wrote the new data in self.object (in memory only)
        # the "before" snapshot has to be read from the database
        old = Asset.objects.select_related("location", "assigned_to").get(pk=self.object.pk)

        with transaction.atomic():
            response = super().form_valid(form)
            log_asset_changes(old, self.object, self.request.user, form.changed_data) 
        messages.success(self.request, f"Asset {self.object.tag} updated")
        return response

class AssetDeleteView(LoginRequiredMixin, DeleteView):
    model = Asset
    success_url = reverse_lazy("assets:asset_list")

    def form_valid(self, form):
        label = str(self.object) # capture before the row disappears
        response = super().form_valid(form)
        messages.success("Asset {label} deleted")
        return response
                
    











