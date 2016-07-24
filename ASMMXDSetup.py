"""
This module builds the DataPublisher map document (MXD)
for the AutoStoryMaps section update routine
Author: Alberto Nieto
Created: 07/24/2016
Copyright: (c) Alberto Nieto 2016
"""

import arcpy
import shutil
import os


##### Establish needed functions #####

# Define a function that allows creation of a group layer
def create_group_layer(lyr_template_file, new_lyr_name, df, mxd, position="TOP"):
    # Make a layer object pointing to the lyr file on disk
    group_layer = arcpy.mapping.Layer(lyr_template_file)
    # Change the name property of the lyr object to the designated new_lyr_name
    group_layer.name = new_lyr_name
    # Add the lyr object to the map document
    arcpy.mapping.AddLayer(df, group_layer, position)
    # Reestablish the group_layer variable to the loaded layer on the map document
    group_layer = arcpy.mapping.ListLayers(mxd, new_lyr_name, df)[0]
    # Return the layer object
    return group_layer


# Define a function that allows addition of a layer to a group layer
def add_layer_to_grp_layer(lyr_template_file, target_group_layer, new_lyr_name, df, mxd, position="BOTTOM"):
    # Make a layer object pointing to the lyr file on disk
    lyr_to_add = arcpy.mapping.Layer(lyr_template_file)
    # Change the name property of the lyr object to the designated new_lyr_name
    lyr_to_add.name = new_lyr_name
    # Add the lyr object to the map document
    arcpy.mapping.AddLayerToGroup(df, target_group_layer, lyr_to_add, position)
    # Reestablish the group_layer variable to the loaded layer on the map document
    subgroup_layer = arcpy.mapping.ListLayers(mxd, new_lyr_name, df)[0]
    # Return the layer object
    return subgroup_layer


# Define a function that allows addition of a layer to a group layer
def add_layer_to_grp_layer_w_def_query(lyr_template_file, target_group_layer, new_lyr_name, df, mxd, def_query, position="BOTTOM"):
    # Make a layer object pointing to the lyr file on disk
    lyr_to_add = arcpy.mapping.Layer(lyr_template_file)
    # Change the name property of the lyr object to the designated new_lyr_name
    lyr_to_add.name = new_lyr_name
    # Add def query to layer
    lyr_to_add.definitionQuery = def_query
    # Add the lyr object to the map document
    arcpy.mapping.AddLayerToGroup(df, target_group_layer, lyr_to_add, position)
    # Reestablish the group_layer variable to the loaded layer on the map document
    subgroup_layer = arcpy.mapping.ListLayers(mxd, new_lyr_name, df)[0]
    # Return the layer object
    return subgroup_layer


def build_group_to_subgroup_dict(table, groups_field, subgroups_field):
    """
    Function to extract regions and subgroups to a dictionary, where the group is the key, and the set of subgroups in the
    group is the value
    :param table:
    :param groups_field:
    :param subgroups_field:
    :return:
    """

    # Create empty dict
    dict = {}
    # Iterate on the subgroups (sections)
    with arcpy.da.SearchCursor(table, [groups_field, subgroups_field], sql_clause=(None, "ORDER BY {0}, {1}".format(groups_field, subgroups_field))) as cursor:
        for row in cursor:
            # Check if the key for the group exists in the dict
            if not row[0] in dict:
                dict[row[0]] = []
            dict[row[0]].append(row[1])
    return dict

##### Establish variables #####

print "Establishing variables..."

# project path variable
project_path = r"C:\my\path\to\project\AutoStoryMaps"
mxd_path = r"{0}\Work\MXDSource\Template.mxd".format(project_path)
new_mxd_path = r"{0}\Work\DataPublisher.mxd".format(project_path)
if os.path.isfile(new_mxd_path):
    os.remove(new_mxd_path)

# Establish subgroups EGDB table source as subgroups_table
subgroups_table = r'{0}\Inputs\path\to\table\with\subgroups\and\narrative\for\sections'.format(project_path)

# Establish parent group layer name as parent_group_lyr
parent_group_lyr_name = 'Parent Group Layer Name'
# Establish variable for subgroups_table field as subgroups_field
subgrouptable_field_name = 'subgroup_name'
# Establish variable for group field
group_field_name = 'group_name'
# Establish variable for story_map text as story_map_text_field
story_map_text_field = 'published_narrative'
# Establish layer template directory path
lyr_template_dir_path = "{0}\\Inputs\\TemplateLayers".format(project_path)
grp_template_lyr_path = "{0}\\group.lyr".format(lyr_template_dir_path)
# poiaoi_template_lyr_path = "{0}\\POI.lyr".format(lyr_template_dir_path)
poiaoi_template_lyr_path = "{0}\\POI_EGDB.lyr".format(lyr_template_dir_path)

print "Variables established..."


##### Procedural Logic ######

print "Establishing map document and dataframe..."
shutil.copyfile(mxd_path, new_mxd_path)
# Create mapdocument object from mxd path
mxd = arcpy.mapping.MapDocument(new_mxd_path)
# Create dataframe object using mxd object
df = arcpy.mapping.ListDataFrames(mxd)[0]


# Create a parent group layer
parent_group_layer = create_group_layer(grp_template_lyr_path, "SubGroups", df, mxd)

# Create list of subgroup name values from subgroups_table

groups_dict = build_group_to_subgroup_dict(subgroups_table, group_field_name, subgrouptable_field_name)

groups = sorted(groups_dict.keys())

for group in groups:
    print "\nCreating parent group layer '{0}'...".format(str(group))
    group_layer = add_layer_to_grp_layer(grp_template_lyr_path, parent_group_layer, str('GROUP-'+group), df, mxd)

    for subgroup in groups_dict[group]:

        print "\n\tCreating structure for subgroup '{0}'...".format(subgroup)

        print "\tAdding subgroup layer..."
        # Add the subgroup template layer to the parent group, changing the lyr name to the current subgroup value
        subgroup_lyr = add_layer_to_grp_layer(grp_template_lyr_path, group_layer, str('SUBGROUP-'+subgroup), df, mxd)
        print "\tAdding POI/AOI layers..."
        # Establish definition query for the poi and aoi layers corresponding to the current subgroup
        definition_query = "{0} = '{1}'".format(subgrouptable_field_name, str(subgroup))
        # Add poi and aoi lyrs for the micromarket
        poi_lyr = add_layer_to_grp_layer_w_def_query(poiaoi_template_lyr_path, subgroup_lyr, "POI", df, mxd, definition_query)
        aoi_lyr = add_layer_to_grp_layer_w_def_query(poiaoi_template_lyr_path, subgroup_lyr, "AOI", df, mxd, definition_query)

        print "\Subgroup '{0}' completed.".format(subgroup)




subgroups = set(row[0] for row in arcpy.da.SearchCursor(subgroups_table, [subgrouptable_field_name, group_field_name]))

##### Subgroup Iteration #####
print "\nStarting subgroup layer iteration..."
# For each subgroup
# subgroups = sorted(subgroups)
# print subgroups


# for subgroup in subgroups:
#     print "\n\tCreating structure for subgroup '{0}'...".format(subgroup)
#
#     print "\tAdding subgroup layer..."
#     # Add the subgroup template layer to the parent group, changing the lyr name to the current subgroup value
#     subgroup_lyr = add_layer_to_grp_layer(grp_template_lyr_path, group_layer, str(subgroup), df, mxd)
#     print "\tAdding POI/AOI layers..."
#     # Establish definition query for the poi and aoi layers corresponding to the current subgroup
#     definition_query = "{0} = '{1}'".format(subgrouptable_field_name, str(subgroup))
#     # Add poi and aoi lyrs for the subgroup
#     # poi_lyr = add_layer_to_grp_layer(poiaoi_template_lyr_path, subgroup_lyr, "POI", df, mxd)
#     poi_lyr = add_layer_to_grp_layer_w_def_query(poiaoi_template_lyr_path, subgroup_lyr, "POI", df, mxd, definition_query)
#     # aoi_lyr = add_layer_to_grp_layer(poiaoi_template_lyr_path, subgroup_lyr, "AOI", df, mxd)
#     aoi_lyr = add_layer_to_grp_layer_w_def_query(poiaoi_template_lyr_path, subgroup_lyr, "AOI", df, mxd, definition_query)
#
#     print "\tSubgroup '{0}' completed.".format(subgroup)

print "\nRefreshing views and saving map document."
# Refresh map document
arcpy.RefreshActiveView()
arcpy.RefreshTOC()

# Save the mxd
mxd.save()

print "\nOperation complete."

print "\nGo Gators."

