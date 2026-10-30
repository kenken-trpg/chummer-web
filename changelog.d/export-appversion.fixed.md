- **Chummer no longer treats an exported character as an old save.** The
  export wrote "Chummer Web" as the Chummer version, which Chummer reads as
  0.0.0, so it ran every fix-up meant for old saves on the file. It now writes
  the Chummer version the export is made for (5.226.0).
