# AutoStoryMap
Repository for Process to Publish Automated Story Map Journal Sections via Python with customizations to the Map Journal Application via ArcGIS JavaScript API.

# General Structure
Three python scripts handle the publishing of a JSON payload to a pre-existing Map Journal item on an administrator's AGOL or AGS content. The JSON payload is built from the contents of a 'Publishing MXD' map document. This map document is structure with group layers that will correspond to the sections, section narrative, and section extent in the resulting map journal. 

The index.html file contains a customized MapJournal application, with widgets from the ArcGIS JavaScript API 3.x. At present, a Layer List widget, a Basemap selection widget, and a Section searching custom Dojo widget have been implemented.
