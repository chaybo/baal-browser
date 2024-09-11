import maya.cmds as mc
import maya.mel as mm
import fnmatch
import os
import json
import re
import sys
import time
import glob
import importlib
import subprocess
import shutil
from datetime import datetime
import smtplib
import ssl
import pymel.core as pm
import getpass

"""
shotsculpt_tool.py

This is a publish shotsculpt tool, intended to be used on imported alembics that have been sculpted and need 
to be baked down again, to remove deformers and anything unwanted from the scene, and versioned up, 
it also re applies the grooms for any assets that need it post sculpt

By Chay

#create_gui()

"""

def delete_Namespaces():
    namespaces = mc.namespaceInfo(listOnlyNamespaces=True)
    if not namespaces:
        print("No namespaces to delete.")
        return
    
    for namespace in namespaces:
        if namespace != "UI" and namespace != "shared":
            mc.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
    print("Namespaces deleted.")

def stone_importer(force_frame_rate):
    # Setting the frame rate
    if force_frame_rate:
        frame_rate_str = str(force_frame_rate) + "fps"
        valid_frame_rates = ["game", "film", "pal", "ntsc", "show", "palf", "ntscf", "23.976fps", "29.97fps", "59.94fps", "48fps", "30fps", "25fps", "24fps"]
        
        if frame_rate_str in valid_frame_rates:
            mc.currentUnit(time=frame_rate_str)
            print(f"Frame rate set to {force_frame_rate}")
        else:
            print(f"Warning: Invalid frame rate {force_frame_rate}. Skipping frame rate setting.")

#initializing outside of function
text_field = None

def populate_text(selection):
    global text_field
    global group_name
    global start_frame
    global end_frame
    global text_field_value

    if not selection:
        mc.warning("Please select an object.")
        return

    #if text_field:
        #mc.textField(text_field, edit=True, text='')

    # clear some stuff
    group_name = None
    start_frame = None
    end_frame = None
    #text_field = None

    group_name = mc.ls(selection=True)[0]
    group_name = group_name.strip("[]'")
    print(group_name)
    
    alembic_node_fn = "*_AlembicNode.fn"

    if not mc.objExists(alembic_node_fn):
        mc.warning("AlembicNode not found.")
        return
    
    fn_value = mc.getAttr(alembic_node_fn)
    print(f"{alembic_node_fn} value: {fn_value}")

    alembic_node_sf = "*_AlembicNode.sf"
    alembic_node_ef = "*_AlembicNode.ef"

    if not mc.objExists(alembic_node_sf) or not mc.objExists(alembic_node_ef):
        mc.warning("Start frame or end frame not found.")
        return
    
    start_frame = mc.getAttr(alembic_node_sf)
    end_frame = mc.getAttr(alembic_node_ef)
    mc.playbackOptions(min=start_frame, max=end_frame)
    print(f"Frame range set: Start Frame - {start_frame}, End Frame - {end_frame}")

    # Update the text field with AlembicNode.fn value
    if text_field:
        text_field = mc.textField(text_field, edit=True, text=str(fn_value))
        text_field_value = mc.textField(text_field, query=True, text=True)
        print (text_field)
        print (text_field_value)

def publish_confirmation_dialog():
    result = mc.confirmDialog(title="Publish New Version",
                                message="Are you sure you wish to publish a new version?",
                                button=["Yes", "No"],
                                defaultButton="Yes",
                                cancelButton="No",
                                dismissString="No")
    if result == "Yes":
        print("Publishing new version !")
        # Add your publish logic here
        start_frame = mc.playbackOptions(query=True, minTime=True)
        end_frame = mc.playbackOptions(query=True, maxTime=True)
        final_alembic_export()  # Call final_alembic_export function after confirmation
        find_and_run_script_sculpt()
        export_groom_caches()
        print ('Shotsculpt complete... :)')
    else:
        print("Publishing new version canceled.")

def create_gui():
    global text_field
    if mc.window("Shotsculpt Tool", exists=True):
        mc.deleteUI("Shotsculpt Tool")

    window = mc.window(title="Shotsculpt Tool", widthHeight=(900, 200))
    mc.columnLayout(adjustableColumn=True)

    #mc.button(label="Set Frame Rate to 23.976", command=lambda *args: stone_importer(23.976))
    mc.button(label="Remove Namespaces", command=lambda *args: delete_Namespaces())
    mc.button(label="Populate", command=lambda *args: populate_text(mc.ls(selection=True)[0] if mc.ls(selection=True) else None))


    
    text_field = mc.textField(editable=False)
    
    mc.button(label="Publish New Version", command=lambda *args: publish_confirmation_dialog(), backgroundColor=[0.5, 0, 0])
    
    mc.showWindow(window)

def split_path(path):
    # Split the path into two parts, 2 levels from the end
    base_path, filename = os.path.split(os.path.dirname(path))
    return base_path

def split_path_name(path):
    # Extract the filename from the path
    filename = os.path.basename(path)
    
    # Split the filename by hyphens and remove the last two parts
    parts = filename.split('-')[:-2]
    
    # Join the remaining parts back together to form the scene_name
    scene_name = '-'.join(parts)

    # The base path is not required for this logic, so it's not included here
    return scene_name

def groom_export(result_string, full_export_path):
    command = (' -file ' + full_export_path +
               ' -df "ogawa" -fr ' + str(start_frame) +
               ' ' + str(end_frame) + ' -step 1 -wfw'
               )

    if result_string:
        command = (result_string + command)

    mc.xgmSplineCache(export=True, j=command)

def final_alembic_export():
    global fileName_d
    global version
    global export_dir
    global text_field
    global text_field_value

    cfx_work = split_path(text_field_value)
    cfx_work = cfx_work + '/'
    scene_name = split_path_name(text_field_value)
    print("scene_name:", scene_name)

    parts = text_field_value.split('-')
    print (text_field)
    print (text_field_value)
    fileName_d = parts[-3]

    # Construct the alembic export directory with a placeholder for version
    export_dir_template = os.path.join(cfx_work, 'v{:04d}')

    match = re.search(r'v(\d+)\.abc$', text_field_value)
 
    if match:
        version = int(match.group(1))  # Convert the matched version number to an integer
        print("Version:", version)
    else:
        print("Version number not found in the file path.")

    #version = 1

    # Find the correct version number and construct the final export directory
    while True:
        export_dir = export_dir_template.format(version)
        print (export_dir)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            break
        print (export_dir)
        version += 1

    # After finding the right version we cab construct the export file name with the final version
    export_file_name = '{}-skin-v{:04d}.abc'.format(scene_name, version)
    print (export_file_name)
    full_export_path = os.path.join(export_dir, export_file_name)
    print (full_export_path)

    # Checking for simGeo group, we don't want this, lets remove it
    if mc.objExists('simGeo'):
        mc.delete('simGeo')

    #mc.AbcExport(j='-frameRange {0} {1} -uvWrite -worldSpace -writeVisibility -writeUVSets -stripNamespaces -writeFaceSets -file {2}'.format(start_frame, end_frame, full_export_path))
    mc.AbcExport(j='-frameRange {0} {1} -uvWrite -worldSpace -writeVisibility -writeUVSets -stripNamespaces -writeFaceSets -root {2} -file {3}'.format(start_frame, end_frame, group_name, full_export_path))

def export_groom_caches():
    
    hero_model_top = group_name
    
    # List all objects in the scene with "_groom" suffix
    groom_objects = mc.ls("*_groom", dag=True)
    
    # Filter out Shape nodes and ShapeOrig nodes
    groom_objects = [obj for obj in groom_objects if not mc.nodeType(obj).startswith('shape')]
    
    # Check if there are groom objects
    if groom_objects:
        # Get the value of the "groom_version" attribute on the first groom object
        groom_version_attr = groom_objects[0] + ".groom_version"
        
        # Check if the attribute exists
        if mc.attributeQuery('groom_version', node=groom_objects[0], exists=True):
            groom_version_value = mc.getAttr(groom_version_attr, asString=True)
            print("Groom Version Attribute Value:", groom_version_value)
        else:
            print("The 'groom_version' attribute does not exist on", groom_objects[0])
    else:
        print("No groom objects found in the scene.")
    
    if mc.objExists("*_groom"):
        # Find_and_select_models_with_groom_suffix()
        drive_groom()
        
        ############################################
        
        export_file_name = '{}-{}-{}-groom-v{:04d}.abc'.format(hero_model_top, groom_version_value, fileName_d, version)
        
        full_export_path = os.path.join(export_dir, export_file_name)
        
        full_export_path = full_export_path.replace('\\', '/')
        
        spline_description_nodes = mc.ls('*_splineDescription')
        
        if not spline_description_nodes:
            print("No groom selected.")
        else:
            # Initialize an empty string to store the result
            result_string = ""
        
            # Loop through the selected models and add "-obj" with spaces to the start and end of each name
            for groom in spline_description_nodes:
                modified_name = " -obj " + groom + " "
                result_string += modified_name
            print(start_frame)
            print(end_frame)
            # Create the final command string with dynamic frame range
            #final_command = f'mc.xgmSplineCache(export=True, j="-file {full_export_path} -fr {start_frame} {end_frame} {result_string}")'
        
            # Execute the final command (if needed)
            #exec(final_command)
            groom_export(result_string, full_export_path)

    else:
        print('no grooms to apply, skipping')

def find_and_run_script_sculpt():
    #project = 'FR00066_SURV'
    #group_name = mc.ls(selection=True)[0]
    #group_name = group_name.strip("[]'")
    # get username from windows
    username = getpass.getuser()

    # Form python file name
    base_python_file_name = "{}.py".format(group_name)
    
    # Form python file name
    user_specific_file_name = "{}_{}.py".format(group_name, username)
    
    # Specify the path to look for the python file    
    search_path = 'E:/Files/Dropbox/Resources/Assets/cfx_builds/ProjectMan/creature_control/sculpt_scripts'

    # Check if the user-specific file exists, otherwise fall back to the base file name
    if os.path.exists(os.path.join(search_path, user_specific_file_name)):
        python_file_name = user_specific_file_name
    else:
        python_file_name = base_python_file_name

    full_path = os.path.join(search_path, python_file_name)
    
    if not os.path.exists(full_path):
        print("CFX TD should setup the matching creature file")
        return
    # Finally, execute the python script
    print (full_path)

    with open(full_path, 'r') as python_file:
        exec(python_file.read())

def drive_groom():
    # Find the target object by searching for the first object with the naming convention "*_groom"
    target_objects = mc.ls("*_groom")
    if not target_objects:
        mc.warning("No objects matching the naming convention '*_groom' found.")
    else:
        # Use the first matching object
        target_object = target_objects[0]

        # Remove the "_groom" suffix from the target object's name to get the base_object name
        base_object = target_object.replace("_groom", "")

        # Get the long name of the base_object
        base_object_long = mc.ls(base_object, long=True)[0]

        # Create a blend shape node
        blendshape_node = mc.blendShape(base_object_long, target_object, name=base_object + "_blendShape")[0]

        # Set the weight of the blend shape to 1 for the target object
        mc.setAttr(blendshape_node + "." + base_object, 1)

        # Optionally, you can rename the weight attribute for clarity
        blendshape_attr = blendshape_node + "." + target_object
        new_attr_name = base_object_long + "_blendWeight"
        
        # List all objects with the suffix '_groom'
        groom_objects = mc.ls('*_groom')

        if groom_objects:
            # Create a scale constraint from 'scaleLocator' to each '_groom' object
            for groom_object in groom_objects:
                #connectLocatorToGroupScalePivot(groom_objects)

                source_scale_pivot = mc.xform(group_name, query=True, scalePivot=True, worldSpace=True)
 
                # Set the scale pivot position of the target object to match the source object
                mc.xform(groom_object, scalePivot=source_scale_pivot, worldSpace=True)
                 
                # Step 2: Connect the Scale Pivot
                # For each axis, connect the scale pivot attributes from the source to the target
                for axis in ['X', 'Y', 'Z']:
                    mc.connectAttr(f'{group_name}.scalePivot{axis}', f'{groom_object}.scalePivot{axis}', force=True)
                    mc.connectAttr(f'{group_name}.scalePivotTranslate{axis}', f'{groom_object}.scalePivotTranslate{axis}', force=True)

                #mc.connectAttr(group_name + '.translate',groom_object + '.scalePivot')
                #move_groom_pivot_to_locator(groom_object, 'scaleLocator')
                mc.connectAttr(group_name + '.scaleX', groom_object + '.scaleX')
                mc.connectAttr(group_name + '.scaleY', groom_object + '.scaleY')
                mc.connectAttr(group_name + '.scaleZ', groom_object + '.scaleZ')
                
