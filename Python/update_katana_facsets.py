""" Tool for rebuilding Katana Faceset Selections post subdivision updates on a single mesh. """

import maya.cmds as cmds
import re


def expand_facesets(faceset_str):
    faces = []

    for part in faceset_str.split(','):
        part = part.strip()

        if '-' in part:
            start, end = map(int, part.split('-'))
            faces.extend(range(start, end + 1))
        else:
            faces.append(int(part))

    return faces

def faces_to_range_string():
    # Get selected faces (flatten to individual components)
    selection = cmds.ls(sl=True, fl=True)

    if not selection:
        return ""

    # Extract mesh name (assumes single mesh selection)
    mesh = selection[0].split('.')[0]

    # Extract face indices
    face_ids = []
    # Extract face indices
    for f in selection:
        match = re.search(r'\[(\d+)\]', f)
        if match:
            face_ids.append(int(match.group(1)))

    if not face_ids:
        return ""

    # Sort and remove duplicates
    face_ids = sorted(set(face_ids))

    # Build ranges
    ranges = []
    start = prev = face_ids[0]

    for i in face_ids[1:]:
        if i == prev + 1:
            prev = i
        else:
            # Close current range
            if start == prev:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{prev}")
            start = prev = i

    # Final range
    if start == prev:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{prev}")

    # Join into string
    return ",".join(ranges)

def smooth_mesh(meshes, divisions=1):

    if not meshes:
        cmds.warning("No mesh selected.")
        return

    # Get transform nodes (since polySmooth works on transforms)
    transforms = list(set(cmds.listRelatives(meshes, parent=True, fullPath=True)))

    for obj in transforms:
        cmds.polySmooth(
            obj,
            mth=0,          # 0 = Catmull-Clark
            dv=divisions,   # divisions (1 = one level)
            c=1,            # continuity
            kb=1,           # keep borders
            ksb=1,          # keep selection border
            khe=0,          # keep hard edges
            kt=1,           # keep topology
            kmb=1,          # keep map borders
            suv=1,          # smooth UVs
            peh=0,          # propagate edge hardness
            sl=1            # smooth level
        )


def create_face_selection_set(face_indices, set_name="quickFaceSet"):
    """
    Creates a Quick Selection Set from given face indices on the selected mesh.

    :param face_indices: List of integers (face IDs)
    :param set_name: Name of the selection set to create
    """

    # Get selected objects
    selection = cmds.ls(selection=True, long=True)

    if not selection:
        cmds.error("Please select a mesh object.")
        return

    mesh = selection[0]

    # Build face component list
    face_components = [f"{mesh}.f[{i}]" for i in face_indices]

    # Filter out invalid faces (optional safety)
    valid_faces = cmds.filterExpand(face_components, selectionMask=34) or []

    cmds.select(valid_faces)

    if not valid_faces:
        cmds.warning("No valid faces found from provided indices.")
        return

    # Create selection set
    if cmds.objExists(set_name):
        cmds.delete(set_name)

    face_set = cmds.sets(valid_faces, name=set_name)

    print(f"Created Quick Selection Set: {face_set}")
    return face_set

def show_faces_result_copyable(face_string):
    if cmds.window("facesResultWin", exists=True):
        cmds.deleteUI("facesResultWin")

    win = cmds.window("facesResultWin",
                       title="Face Ranges Result",
                       sizeable=True,
                       widthHeight=(800, 250)
    )
    cmds.columnLayout(adj=True, rs=8)

    cmds.text(label="Generated Face IDs (copyable):")

    cmds.scrollField(
        text=face_string,
        editable=False,
        wordWrap=True
    )

    cmds.button(label="Close", c=lambda *_: cmds.deleteUI(win))

    cmds.showWindow(win)

def faceset_ui():
    if cmds.window("facesetWin", exists=True):
        cmds.deleteUI("facesetWin")

    win = cmds.window("facesetWin",
                      title="FaceSet + Smooth",
                      sizeable=False,
                      widthHeight=(500, 200)
    )

    cmds.columnLayout(adj=True, rs=8)

    cmds.text(label="Face IDs / Ranges (e.g. 1-4,8,10-12)")
    face_field = cmds.textField()

    cmds.text(label="Subdivision Level")
    div_field = cmds.intField(value=1, min=0)

    def on_ok(*args):
        faces = cmds.textField(face_field, q=True, text=True)
        divisions = cmds.intField(div_field, q=True, value=True)

        cmds.deleteUI(win)

        # expand faces, select, smooth, etc.
        face_ids = expand_facesets(faces)
        face_selection_set = create_face_selection_set(face_ids, set_name="myFaceSet")

        # subdivide
        smooth_meshes(selection, divisions=1)

        # select face_selection_set
        cmds.select(face_selection_set)

        # list new faces
        faceset_selection = faces_to_range_string()
        print("FACESET_SELECTION_RESULT:", faceset_selection)
        show_faces_result_copyable(faceset_selection)


    cmds.button(label="OK", c=on_ok)
    cmds.button(label="Cancel", c=lambda *_: cmds.deleteUI(win))

    cmds.showWindow(win)



# main program
faceset_ui()
