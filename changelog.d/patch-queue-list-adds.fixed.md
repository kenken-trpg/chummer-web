- **Two quick adds to the same list no longer undo each other.** An edit made
  while the previous one was still being saved could be taken for "the same
  control, one step on" when both added a different item to a list, and
  saving it removed the first item. Such an edit is now dropped instead, as
  any other edit that would undo the one in front of it.
