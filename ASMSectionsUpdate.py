"""
This module builds/sends an update JSON payload to the M3 MapJournal appItem
Author: Alberto Nieto
Created: 07/24/2016
Copyright: (c) Alberto Nieto 2016
"""

import arcpy
import argparse
import sys
import json
import time
import getpass
import urllib
import urllib2
# import httplib
import contextlib
import socket
import requests

#TODO Refactor all requests sections to leverage ArcREST
#TODO Determine if the real URL should be passed initially or if it should be used when building the Series tabs

from arcrest import security, manageorg

print "Process started - Modules imported."

# Define needed functions
def get_oauth_token(portal):
    """
    Function leveraging requests module
    used to authenticate with a Portal

    :param portal: Portal URL
    :return: Token used for authentication
    """
    # Establish a parameters dictionary corresponding to an app configured
    # with credentials on the ESRI dev site
    params = {
        'client_id': "",
        'client_secret': "",
        'grant_type': "client_credentials"
    }
    # Use requests' get method to send a GET request to the token rest endpoint
    # using the params dictionary
    request = requests.get(url="{0}/sharing/rest/oauth2/token".format(portal),
                           params=params,
                           verify=False)
    # Parse the response into a json and set the response variable to the 
    # JSON value
    response = request.json()
    # Query the response json for the token value
    token = response["access_token"]
    # Return the token value
    return token


def submit_request(request):
    """
    Returns the response from an HTTP request in json format.

    :param request: request to be sent via HTTP
    :return: json-format response from the parameter request
    """
    with contextlib.closing(urllib2.urlopen(request)) as response:
        job_info = json.load(response)
        return job_info


def get_PortalToken(username, password):
    """
    Returns an authentication token for use in ArcGIS Online.

    :param username: username to be used for the Portal token
    :param password: password for the username to be used for the Portal token
    :return: Token if successful; exception if unsuccessful
    """

    # Set the username and password parameters before
    # getting the token.
    params = {"username": username,
              "password": password,
              "referer": "https://my.ags.server.url.com/arcgis",
              "ip": socket.gethostbyname(socket.gethostname()),
              "f": "json"}
    # Establish the token url and point it at a designated portal
    token_url = "{}/generateToken".format(
        "https://my.portal.url.com/arcgis/sharing/rest")
    # Send the request using urllib2
    request = urllib2.Request(token_url, urllib.urlencode(params))
    print("Getting Portal token...")
    # Use the submit_request function to receive a json response
    tokenResponse = submit_request(request)
    # If a token is present in tokenResponse's JSON...
    if "token" in tokenResponse:
        # Retrieve the token
        token = tokenResponse.get("token")
        print("Success")
        # Return the token
        return token
    # If a token is NOT present in tokenResponse's JSON...
    else:
        # If an error is present in tokenResponse...
        if "error" in tokenResponse:
            # Retrieve the error
            error_mess = tokenResponse.get("error", {}).get("message")
            # Raise an exception
            raise Exception("Portal error: {} ".format(error_mess))


def get_AGSToken(username, password):
    """
    Returns an authentication token for use in ArcGIS Server (AGS).

    :param username: username to be used for the AGS token
    :param password: password for the username to be used for the AGS token
    :return: Token if successful; exception if unsuccessful
    """

    # Set the username and password parameters before
    # getting the token.
    params = {"username": username,
              "password": password,
              "client": "ip",
              "ip": socket.gethostbyname(socket.gethostname()),
              "f": "json"}

    token_url = "{}/generateToken".format(
        "https://my.ags.server.com:6443/arcgis/admin")
    request = urllib2.Request(token_url, urllib.urlencode(params))
    print("Getting Server token...")
    tokenResponse = submit_request(request)
    if "token" in tokenResponse:
        token = tokenResponse.get("token")
        print("Success")
        return token
    else:
        if "error" in tokenResponse:
            error_mess = tokenResponse.get("error", {}).get("message")
            raise Exception("Server error: {} ".format(error_mess))


def PortalToken_to_ServerToken(PortalToken):
    """
    Exchanges a Portal Token for a Server Token to provide access to
    restricted resources hosted on a Server federated with Portal
    """
    params = {"token": PortalToken,
              "serverURL": "https://my.ags.server.com:6443/arcgis",
              "f": "json"}
    tokenURL = "{}/generateToken".format(
        "https://my.portal.url.com/arcgis/sharing/rest")
    request = urllib2.Request(tokenURL, urllib.urlencode(params))
    print("Exchanging Portal token for Server token...")
    tokenResponse = submit_request(request)
    if "token" in tokenResponse:
        token = tokenResponse.get("token")
        print("Success")
        return token
    else:
        if "error" in tokenResponse:
            error_mess = tokenResponse.get("error", {}).get("message")
            raise Exception("Token Exchange error: {} ".format(error_mess))


def _raw_input(prompt=None, stream=None, input=None):
    """
    A raw_input() replacement that doesn't save the string in the
    GNU readline history.
    """
    if not stream:
        stream = sys.stderr
    if not input:
        input = sys.stdin
    prompt = str(prompt)
    if prompt:
        stream.write(prompt)
        stream.flush()
    # NOTE: The Python C API calls flockfile() (and unlock) during readline.
    line = input.readline()
    if not line:
        raise EOFError
    if line[-1] == '\n':
        line = line[:-1]
    return line


def decode_list(lst):
    newList = []
    for i in lst:
        i = safeValue(i)
        newList.append(i)
    return newList


def safeValue(inVal):
    outVal = inVal
    if isinstance(inVal, unicode):
        outVal = inVal.encode('utf-8')
    elif isinstance(inVal, list):
        outVal = decode_list(inVal)
    return outVal


def decode_dict(dct):
    newdict = {}
    for k, v in dct.iteritems():
        k = safeValue(k)
        v = safeValue(v)
        newdict[k] = v
    return newdict


def copy_item(item_id,
              folder,
              title):
    """
    Copies a portal item

    :param item_id: Item ID of the item to be copied
    :param folder: Folder to contain the copy output
    :param title: Title of the copy output
    """
    # Retrieve the item object using a portal object (previously retrieved)
    item = portal_content.getItem(item_id)
    print(item)
    itemParams = manageorg.ItemParameter()
    itemParams.title = title
    # ArcREST was failing if item.thumbnail was null
    if item.thumbnail:
        # If the item to be copied has a thumbnail,
        # set the new item's thumbnail
        itemParams.thumbnail = item.thumbnail
    # Set all aspects of the output item to be the same as the input item
    itemParams.type = item.type
    itemParams.typeKeywords = ', '.join(item.typeKeywords)
    itemParams.description = item.description
    itemParams.tags = ', '.join(item.tags)
    itemParams.snippet = item.snippet
    itemParams.extent = item.extent
    itemParams.spatialReference = item.spatialReference
    itemParams.accessInformation = item.accessInformation
    itemParams.licenseInfo = item.licenseInfo
    itemParams.culture = item.culture
    itemParams.url = item.url
    # Switch to the designated folder where the output will be saved
    portal_user.currentFolder = folder
    # Use the portal_user object's addItem method to write the output item
    # using the itemParams that have been set by the previous logic
    new_item = portal_user.addItem(
                itemParameters=itemParams,
                # url=item.url,
                # text=None,
                # metadata=item.metadata
                overwrite=True)
    # Print and return the output item
    print(new_item)
    return new_item


def delete_folder(folder_name):
    for folder in portal_user.folders:
        if folder_name == folder['title']:
            portal_user.currentFolder = folder_name
            portal_user.deleteFolder()


def add_folder(folder_name):
    id = -1
    response = portal_user.createFolder(folder_name)
    if response['success']:
        id = response['folder']['id']
    return id


def recreate_folder(folder_name):
    delete_folder(folder_name)
    return add_folder(folder_name)


def update_item_url(item):
    url = '{0}?appid={1}'.format(item.url.split('?')[0], item.id)
    itemParams = manageorg.ItemParameter()

    itemParams.url = url
    res = item.updateItem(itemParameters=itemParams,
                          clearEmptyFields=True,
                          data=None,
                          serviceUrl=None,
                          text=None
                          )

#parameters
##########
# parser = argparse.ArgumentParser()
# parser.add_argument('-u', '--user')
# parser.add_argument('-p', '--password')
# parser.add_argument('-portal', '--portal')
# parser.add_argument('-itemid', '--itemid')
# parser.add_argument('-webmap', '--webmap')
# parser.add_argument('-mxd', '--mxd')
# parser.add_argument('-groupLayer', '--groupLayer')
# parser.add_argument('-poiLayerName', '--poiLayerName')
# parser.add_argument('-aoiLayerName', '--aoiLayerName')
# parser.add_argument('-descriptionField', '--descriptionField')
#
# args = parser.parse_args()
#
# if args.user == None:
#     args.user = _raw_input("Username:")
#
# if args.portal == None:
#     args.portal = _raw_input("Portal: ")
#
# if args.password == None:
#     args.password = getpass.getpass()
# else:
#     args.password = args.password
#
# args.portal = str(args.portal).replace("http://", "https://")
#
# # agoAdmin = Admin(args.user, args.portal, args.password)
#
# if args.itemid == None:
#     args.itemid = _raw_input("Application Item Id: ")
#
# if args.webmap == None:
#     args.webmap = _raw_input("webMap Id: ")
#
# if args.mxd == None:
#     args.mxd = _raw_input("Map Document Path: ")
#
# if args.groupLayer == None:
#     args.groupLayer = _raw_input("Group Layer Name: ")
#
# if args.poiLayerName == None:
#     args.poiLayerName = _raw_input("POI Layer Name: ")
#
# if args.aoiLayerName == None:
#     args.aoiLayerName = _raw_input("AOI Layer Name: ")
#
# if args.descriptionField == None:
#     args.descriptionField = _raw_input("Description Field Name: ")
#
# webmapid = args.webmap  #'2105a270e16548eabff5f94e07110034'
# mxd = args.mxd  # r"D:\data\RevolutionaryWar\WarMapsV4.mxd"
#
# groupLayerName = args.groupLayer  # 'Battles'
# poiLayerName = args.poiLayerName  # "Battlesite"
# aoiLayerName = args.aoiLayerName  #"Troop Movements"
# descriptionField = args.descriptionField  #"DESCRIPTION"
# appItemId = args.itemid
##########

#prototyping parameters
##########

# Start run_mode parameter loop to accept valid run_mode from user
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
                portal = 'https://my/portal.url.com/arcgis'
                webmapid = ''
                appItemId = ''
                break

            elif run_mode == "AGOL":
                # AGOL Config
                user = ''
                password = getpass.getpass()
                portal = 'https://my.organization.arcgis.com'
                webmapid = ''
                appItemId = ''
                break

    except ValueError as e:
        print e
        print e.message
        print "Run_mode value could not be parsed!"

# Establish a Portal securityHandler object using arcREST
securityHandler = security.PortalTokenSecurityHandler(username=user,
                                                      password=password,
                                                      org_url=portal)
# Establish a portal admin object using the securityHandler
portal_admin = manageorg.Administration(securityHandler=securityHandler)
# Get the portal content
portal_content = portal_admin.content
# Set up a user object
portal_user = portal_content.users.user()
# Designate the folder where the work content will reside
folder = '_MapJournal'
# Create the folder in portal user's content
# folder_id = recreate_folder(folder)


# Legacy authentication section - now obsolete
# """ TOKEN DEV SECTION """
# # Get token using requests
# if run_mode == "AGOL":
#     print "Acquiring ArcGIS Online token..."
#     token_url = '{0}/sharing/rest/generateToken?'.format(portal)
#     token_params = {'username': user,
#                     'password': password,
#                     'client': 'referer',
#                     'referer': portal,
#                     'expiration': 60,
#                     'f': 'json'}
#     token_request = requests.post(token_url, params=token_params, verify=False)
#     token = token_request.json()['token']
#     print "Token acquired: {0}".format(token)

# elif run_mode == "ATLAS":
#     # token = get_PortalToken(user, password)
#     # token = PortalToken_to_ServerToken(pToken)

#     # token = get_oauth_token(portal)

#     print "Acquiring ATLAS token..."
#     token_url = '{0}/sharing/rest/generateToken?'.format(portal)
#     token_params = {'username': user,
#                     'password': password,
#                     'client': 'referer',
#                     'referer': portal,
#                     'expiration': 1440,
#                     'f': 'json'}
#     token_request = requests.post(token_url, params=token_params, verify=False)
#     token = token_request.json()['token']
#     print "Token acquired: {0}".format(token)
# """ END TOKEN DEV SECTION """


# [SP] Gather data and folderID in the current appItem on Portal

# Establish a parameteres payload containing the token and format requested
parameters_dict = {'token': securityHandler.token, 'f': 'json'}

# Send a request to the appItem's REST endpoint to get the current data
request_url = '{0}/sharing/rest/content/items/{1}/data?'.format(
    portal, appItemId)
request = requests.post(request_url, params=parameters_dict, verify=False)
my_data = request.json()

# Send another request to the appItem's REST endpoint, this time to
# get folder info
requestForInfo = "{0}/sharing/rest/content/items/{1}".format(portal, appItemId)
responseInfo = requests.post(requestForInfo, parameters_dict, verify=False)
jResponse = responseInfo.json()
folderID = str(jResponse['ownerFolder'])


# [SP] Iteration to build the update JSON payload using the DataPublisher.mxd

# Variable for the datapublisher map document
mxd = r"C:\Users\gmh148\Documents\Development\AutoStoryMaps\Work\DataPublisher.mxd"
# Set up references to each of the TOI element names
# needed to build the update JSON
groupLayerName = "GroupLayer"
poiLayerName = "POI"
aoiLayerName = "AOI"
descriptionField = "publish_narrative"
# Establish variables that denote the parent group
# folder's delineator for group/subgroup
GROUP = 'GROUP-'
SUBGROUP = 'SUBGROUP-'

# Set up references to the data publisher mxd and its active dataframe
print "Building update JSON from DataPublisher.mxd..."
mxd_object = arcpy.mapping.MapDocument(mxd)
layers = arcpy.mapping.ListLayers(mxd_object)
df = arcpy.mapping.ListDataFrames(mxd_object)[0]

title_section_name = "Section Title Name"  # The section in the publishing MXD must be named as such
title_narrative = "Sample Title Narrative."

sJSON = '['

# For each layer in the map's TOC:
for layer in layers:

    # find our target group layer of sections:
    if layer.isGroupLayer and layer.name == groupLayerName:
        print "Found Section Group Layer: {0}".format(groupLayerName)

        # This iteration is at the GROUP level
        for groupLayer in layer:

            # If this sub layer is a group layer it is a GROUP:
            if groupLayer.isGroupLayer and GROUP in groupLayer.name:
                # Split the layer name to find the GROUP name
                group = groupLayer.name.split(GROUP)[1]
                # # Create a new item on Portal for this MapJournal
                # new_item = copy_item(appItemId, folder, GROUP)
                # # Update the new item's URL using its new ID
                # update_item_url(new_item)
                # # Assign the new app ID to a variable
                # # (Since we can't query it before updating its URL)
                # newAppId = new_item.id

                # Start building the section's JSON element
                # sJSON = '"sections": ['

                print "\nReading group '{0}'...".format(group)

                # Iterate on the sections (subgroups) within
                # the groupLayer group
                for sectionLayer in groupLayer:
                    # Determine if the SUBGROUP string is in the name
                    # (since not all layers will be section group layers)
                    if sectionLayer.isGroupLayer and SUBGROUP in sectionLayer.name:
                        # Assign the section name string to a variable
                        # (split it up using the SUBGROUP variable string)
                        section = sectionLayer.name.split(SUBGROUP)[1]
                        print "\tAdding subgroup '{0}' to sections JSON...".format(section)

                        # Iterate on AOI and POI layers
                        for subLayer2 in sectionLayer:

                            # If the sublayer is a poi layer
                            if subLayer2.name == poiLayerName:
                                # Assign it to a variable
                                poiLayer = subLayer2
                                # open first record
                                with arcpy.da.SearchCursor(poiLayer.dataSource,
                                                           descriptionField,
                                                           poiLayer.definitionQuery) as cursor:
                                    for row in cursor:
                                        if section == title_section_name:
                                            sectionDescription = title_narrative
                                        else:
                                            sectionDescription = row[0]
                                            # Determine if section description is not empty
                                            if sectionDescription is not None:
                                                sectionDescription = sectionDescription.replace(r'"', r'\"')
                                            # If section description is empty,
                                            # insert empty section string
                                            else:
                                                sectionDescription = ''

                            # If the subLayer is an aoi layer
                            if subLayer2.name == aoiLayerName:
                                # Assign it to a variable
                                aoiLayer = subLayer2
                                # Set the dataframe extent to equal the
                                # aoilayer's extent for the current
                                # def-queried section
                                df.extent = aoiLayer.getExtent(True)
                                # Alter the scale of the dataframe
                                df.scale = df.scale * 1.25
                                # Transfer the extent to a variable for the
                                # JSON payload
                                # sectionExtent = aoiLayer.getExtent(True)
                                sectionExtent = df.extent

                        # Attempt to update make a variable from
                        # the section extent in JSON format
                        try:
                            sExtentJSON = sectionExtent.JSON
                        # ... otherwise insert an empty JSON
                        except:
                            sExtentJSON = "{}"

                        # [SP] Start assembling the section JSON using
                        # the gathered narrative and extent

                        # Start the JSON leading bracket
                        sJSON += '{'

                        # Add a JSON component containing
                        # the "group" and "section" strings
                        sJSON += r'"title":' + r'"<strong><span class=\"sectionTitle ' + group + r'\" style=\"font-size: 36px\">' + str(section) + r'</span></strong>"'
                        # TODO Strip bad characters out of 'section' variable
                        sJSON += ','

                        # Add the section narrative in the "content" key
                        sJSON += r'"content":"'
                        sJSON += sectionDescription
                        sJSON += r'"'

                        # Add an empty value to the contentActions key
                        sJSON += ','
                        sJSON += '"contentActions": [],'

                        # Add a time-stamp to the pubDate key in the
                        # section JSON
                        nDate = int(time.mktime(time.localtime()))
                        sJSON += '"pubDate": ' + str(nDate) + '000,'

                        # Change the status key to "PUBLISHED"
                        sJSON += r'"status": "PUBLISHED",'

                        # Add references to the webmapid and extent to
                        # the "media" key in the section's JSON
                        sJSON += '"media": {"type": "webmap","webmap": {"id": "' + webmapid + '","extent": ' + sExtentJSON + ',"layers": null,"popup": null,"overview": {"enable": false,"openByDefault": false},"legend": {"enable": false,"openByDefault": false}}'
                        sJSON += '}},'

# Iteration though all sections has ended
# We need to trim the last "," and add a closing bracket
sJSON = sJSON.rstrip(',')
sJSON += ']'

# Encode the JSON using utf-8
sOut = sJSON.encode("utf-8", "replace")

print "\nGenerated sections JSON. Sending JSON payload to {0}...".format(run_mode)

# Use unicode() to encode the sJSON
sJSONIn = unicode(sOut, "cp866").encode("utf-8")

# load the final sections JSON into my_sections
# strict=False to prevent error during development
my_sections = json.loads(sJSONIn, strict=False)

# Write the sections JSON to the my_data variable
# (remember... this is what we requested at the very
# beginning from the current app!)
my_data['values']['story']['sections'] = my_sections

# Recreate final section JSON
sJSON = json.dumps(my_data)
sJSON = sJSON.encode("utf-8", "replace")

# If we need to write the sections json to a file...
# f.write(sJSON)

# Write the final sections JSON to the 'text' key
# to use for the JSON payload
out_sJSON_payload = {'text': sJSON}

# TODO - investigate: new_item.updateItem

securityHandler = security.PortalTokenSecurityHandler(username=user,
                                                      password=password,
                                                      org_url=portal)

# Establish a parameteres payload containing the token and format requested
parameters_dict = {'token': securityHandler.token, 'f': 'json'}

# If the user's app resides in a folder, the URL
# must pass it with a slash.
# Otherwise, the URL just includes the user
user_folder = "{0}/{1}".format(user, folderID) if folderID else user  # Comment this line if the mapjournal item is not in a user folder
# user_folder = user  # Uncomment this line if the mapjournal item is not in a user folder

# Build the request update URL
# requestUpdate = "{0}/sharing/rest/content/users/{1}/{2}/items/{3}/update".format(portal, user, folder_id, newAppId)
# requestUpdate = "{0}/sharing/rest/content/users/{1}/items/{2}/update".format(portal, user_folder, newAppId)
requestUpdate = "{0}/sharing/rest/content/users/{1}/items/{2}/update".format(portal, user_folder, appItemId)

# Post the request update using the JSON payload and parameters_dict 
# New method - works
requestResponse = requests.post(requestUpdate, data=out_sJSON_payload, params=parameters_dict, verify=False)

# Acquire the result of the post operation
sResult = requestResponse.json()

""" REFERENCE SECTION """
# parameters = urllib.urlencode({'token': securityHandler.token, 'f': 'json'})
# #requestToDelete = self.user.portalUrl + '/sharing/rest/content/users/' + v.owner + '/' + folderID + '/items/' + v.id + '/delete'
#
# #requestUpdate = agoAdmin.user.portalUrl + '/sharing/rest/content/users/' + user + '/items/' + appItemId +'/update?' + parameters
# requestUpdate = portal + '/sharing/rest/content/users/' + user + folderID + '/items/' + appItemId + '/update?' + parameters
#
# sResult = json.loads(urllib.urlopen(requestUpdate, urllib.urlencode(out_sJSON_payload)).read())
""" END REFERENCE SECTION """

print "Post operation complete. Success: " + str(sResult["success"])

print "\n\n\n\nGo Gators."
