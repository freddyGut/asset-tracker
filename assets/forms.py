from django import forms

from .models import Asset, Category, Location


# form used by CreateView and UpdateView to create and update an asset
# It is a ModelForm, so it collects data for a Model
class AssetForm(forms.ModelForm):

    class Meta:
        model = Asset
        # asset_tag is editable=False so it is excluded automatically
        # created_ad/updated_at are managed by Django
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
        # by default, all fields are text
        # we can modify it to enhance the 
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type":"date"}, format="%Y-%m-%d"),
            "description": forms.TextArea(attrs={"rows": 3}),
            "notes": forms.TextArea(attrs={"rows": 3}),
        }


# Search/filter bar of the asset list. Data is sent via GET method
class AssetFilterForm(forms.Form):

    q = forms.CharField(
        required = False,
        label = "Search",
        widget = forms.TextInput(attrs={"placeholder": "Tag, name or serial number"}),
    )
    category = forms.ModelChoiceField(
        # the menu options are not fixed. Go pick them from the database in real-time
        queryset = Category.objects.all(),
        required = False,
        # the first option of the menu, if user does not select anything
        empty_label = "All categories"
    )
    location = forms.ModelChoiceField(
        queryset = Location.objects.all(),
        required = False,
        empty_label = "All locations"
    )
    status = forms.ChoiceField(
        #choices do not change over time so they are fixed
        choices = [("", "All statuses"), *Asset.Status.choices],
        required = False
    )
