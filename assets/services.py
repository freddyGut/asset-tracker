from .models import AssetHistory

# set of field names that represent major changes and deserve their own
# dedicated history event type, rather than being grouped together
TRACKED_FIELDS = {"location", "status", "assigned_to"}

# if a computer is not assigned to a person anymore, it is going to write a "-" in the db record
# it is a helper function
def _display(value):
    """
    Helper function to provide readable text for a possibly-empty value.
    If the value is None (e.g., an unassigned asset), it returns a clean "—"
    instead of displaying "None" in the UI.
    """
    return str(value) if value else "-"



def log_asset_changes (old, new, user, changed_fields):
    """
    Compares two snapshots of an asset and stores history entries for any changes.
    
    Arguments:
    - old:            The asset object as it was in the database BEFORE saving.
    - new:            The asset object AFTER saving (with user modifications).
    - user:           The user instance who performed the action.
    - changed_fields: A list of field names that were actually modified by the user.
    """

    events = AssetHistory.EventType
    # list to temporarily hold the history entries before saving them to the DB
    entries = []

    # compares the raw foreign key IDs (like location_id) instead of the 
    # full objects (location) to prevent Django from executing extra SQL queries (computationally faster)
    if old.location_id != new.location_id:
        # es: (MOVED, "Milan warehouse", "Rome office")
        entries.append((events.MOVED, str(old.location), str(new.location)))

    if old.status != new.status:
        # es: (STATUS_CHANGED, "In use", "In maintainance")
        entries.append((events.STATUS_CHANGED, old.get_status_display(), new.get_status_display()))

    if old.assigned_to_id != new.assigned_to_id:
        # this field might be empty. Daniel (id=45) changes job and brings back the iPad (now... assigned_to=None)
        # (ASSIGNED, "Daniel", "-") ==> _display() saves the None value as "-" so the result is clean
        entries.append((events.ASSIGNED, _display(old.assigned_to), _display(new.assigned_to)))



    # tracking minor events (grouped history log)
    other_fields = []
    for f in changed_fields:
        if f not in TRACKED_FIELDS:
            other_fields.append(f)

    if other_fields:
        verbose_name_fields = []
        for f in other_fields:
            verbose_name_fields.append(str(new._meta.get_field(f).verbose_name))

        labels = ", ".join(verbose_name_fields)
        entries.append((events.UPDATED, "", labels))


    # DATABASE OPTIMIZATION (bulk save) 
    # bulk_create() writes all logs simultaneously in a SINGLE SQL query
    # this is way faster than calling .save() in a loop
    AssetHistory.objects.bulk_create(
    [
        AssetHistory(
            asset=new,
            user=user,
            event_type=event_type,
            old_value=old_value[:255],  # columns are max_length=255
            new_value=new_value[:255],
        )
        for event_type, old_value, new_value in entries
    ]
    )
        