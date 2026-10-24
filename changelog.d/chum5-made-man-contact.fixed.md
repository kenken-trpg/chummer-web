- **A Made Man from a Chummer save keeps its own contact.** The import looked
  for the quality's data id in `<sourceid>` and `<guid>`, but Chummer saves it
  in `<id>`, so the contact Made Man added came back as a paid contact and
  the quality added a made-up second one (Ushi Resub). The export now also
  writes what Made Man's bonus makes for Chummer: the contact's forced
  loyalty, free and group flags, and the Made Man improvement.
