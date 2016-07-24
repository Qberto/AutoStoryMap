"""
This module performs an update of a MapSeries app
with the relevant URLs for each region's MapJournal slice

Author: Alberto Nieto
Created: 07/24/2016
Copyright: (c) Alberto Nieto 2016
"""

from arcrest import security, manageorg
import getpass
import time
import json

# Determine run_mode - AGOL or AGS
# This section will start a run_mode parameter loop to
# accept a valid run_mode from user, then it will return
# the authentication and MapSeries appItemId value
while True:
    try:
        valid_options = ['AGS', 'AGOL']
        run_mode = raw_input("Which run method? (Options: AGS / AGOL)")

        if run_mode not in valid_options:
            print "Designated run mode '{0}' is not established. Try again.".format(run_mode)
            continue
        else:
            if run_mode == "AGS":
                # AGS Config
                user = ''
                password = getpass.getpass()
                portal = 'https://my.portal.com/arcgis'
                mapJournalId = ''
                appItemId = ''
                break

            elif run_mode == "AGOL":
                # AGOL Config
                user = ''
                password = getpass.getpass()
                portal = 'https://my.organization.arcgis.com'
                mapJournalId = ''
                appItemId = ''
                break

    except ValueError as e:
        print e
        print e.message
        print "Run_mode value could not be parsed!"

# Establish variables for the mapjournal app
mapjournal_url = "https://path.to.web.server.com/index.html?appid={0}&tab_group=".format(mapJournalId)

# Define a dictionary of Region values that will be used for each "Entry" tab in the series
tab_groups = ['Tab-Group-1', 'Tab-Group-2', 'Tab-Group-3']

# Set up arcrest items
securityHandler = security.PortalTokenSecurityHandler(username=user,
                                                      password=password,
                                                      org_url=portal)
portal_admin = manageorg.Administration(securityHandler=securityHandler)
portal_content = portal_admin.content
portal_user = portal_content.users.user()

# Get our template story map series
series_item = portal_content.getItem(appItemId)

# [SP] Build the Map Series JSON payload to update the sections
# (named "entries in Map Series")

# Create an empty bucket of entries
entries = []
# Iterate on each item found on the MapJournals folder
for tab_group in tab_groups:
    # Build the json for the entry
    builder_json = {
          "title": tab_group,
          "creaDate": int(time.mktime(time.localtime())),
          "status": "PUBLISHED",
          "description": 'Tab Group Placeholder',
          "media": {"type": "webpage",
                            "webpage": {"url": mapjournal_url + tab_group,
                                        "type": "webpage",
                                        "display": "fit",
                                        "unload": "false"}}
    }

    entries.append(builder_json)

# Retrieve the current MapSeries data JSON
# using the magic of ArcREST
itemData = series_item.itemData(f="json")

# Set the data JSON to be the entries payload
itemData['values']['story']['entries'] = entries

# Write the payload to a variable 'out_json'
out_json = json.dumps(itemData)

# In order to use updateItem in ArcREST
# we must query the manageorg class'
# itemParameter method and pass it to 
# updateItem's "itemParameter" parameter
itemParameter = manageorg.ItemParameter()

# Send post to update with the new payload
result = series_item.userItem.updateItem(itemParameters=itemParameter,
                                         clearEmptyFields=True,
                                         data=None,
                                         serviceUrl=None,
                                         text=out_json
                                         )

print "Post operation complete. Success: " + str(result["success"])

print "\n\n\n\nGo Gators."
