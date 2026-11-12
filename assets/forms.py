from django import forms

from .models import Asset, Category, Location


class AssetForm(forms.ModelForm):
    """Form used by both CreateView and UpdateView."""

    class Meta:
        model = Asset
        # "tag" is editable=False and created_at/updated_at are automatic,
        # so they are not part of the form.
        fields = [
            "name",
            "description",
            "category",
            "location",
            "status",
            "serial_number",
            "purchase_date",
            "purchase_price",
            "assigned_to",
            "notes",
        ]
        widgets = {
            # type="date" gives a native date picker; the format pre-fills it when editing.
            "purchase_date": forms.DateInput(attrs={"type":"date"}, format="%Y-%m-%d"),
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class AssetFilterForm(forms.Form):
    """Search/filter bar of the asset list, submitted via GET."""

    q = forms.CharField(
        required = False,
        label = "Search",
        widget = forms.TextInput(attrs={"placeholder": "Tag, name or serial number"}),
    )
    category = forms.ModelChoiceField(
        queryset = Category.objects.all(),  # options are read from the database at render time
        required = False,
        empty_label = "All categories"
    )
    location = forms.ModelChoiceField(
        queryset = Location.objects.all(),
        required = False,
        empty_label = "All locations"
    )
    status = forms.ChoiceField(
        choices = [("", "All statuses"), *Asset.Status.choices],
        required = False
    )