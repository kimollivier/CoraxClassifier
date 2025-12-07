# autofill_table_photos.py v5
# timestamp: 2025-12-06T20:05
# Creates or appends to a GeoPackage layer based on a template.
# Populates it with media metadata (images/videos) from a folder.
# Uses camera location data for geotagging.
# Stores FULL PATH in a single 'media_path' field.
# Skips duplicates if media_path already exists.
# Times stored as local (Pacific/Auckland).

from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog
import os
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsFeature,
    QgsGeometry,
    QgsPointXY
)
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

# --- SELECT FOLDER ---
folder = QFileDialog.getExistingDirectory(None, "Select Media Folder")
if not folder:
    print("No folder selected. Operation cancelled.")
else:
    # --- ASK FOR NEW TABLE NAME ---
    new_table_name, ok = QInputDialog.getText(None, "New Table Name", "Enter name for new layer:")
    if not ok or not new_table_name.strip():
        print("No table name provided. Operation cancelled.")
    else:
        # --- CONFIG ---
        template_layer_name = "image_classification"  # Template layer
        camera_layer_name = "camera_loc"  # Camera location layer

        # Check template layer
        template_layers = QgsProject.instance().mapLayersByName(template_layer_name)
        if not template_layers:
            raise Exception(f"Template layer '{template_layer_name}' not found.")
        template_layer = template_layers[0]

        # Check camera layer
        camera_layers = QgsProject.instance().mapLayersByName(camera_layer_name)
        if not camera_layers:
            raise Exception(f"Camera layer '{camera_layer_name}' not found.")
        camera_layer = camera_layers[0]

        # GeoPackage path
        gpkg_path = template_layer.dataProvider().dataSourceUri().split("|")[0]

        # Check if layer already exists
        existing_layer = None
        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.name() == new_table_name:
                existing_layer = lyr
                break

        if existing_layer:
            print(f"Layer '{new_table_name}' exists. Appending new records...")
            new_layer = existing_layer
        else:
            # Create new layer from template
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = new_table_name
            options.fileEncoding = "UTF-8"
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

            transform_context = QgsProject.instance().transformContext()
            error = QgsVectorFileWriter.writeAsVectorFormatV2(template_layer, gpkg_path, transform_context, options)
            if error[0] != QgsVectorFileWriter.NoError:
                raise Exception(f"Error creating new layer: {error}")
            else:
                new_layer_path = f"{gpkg_path}|layername={new_table_name}"
                new_layer = QgsVectorLayer(new_layer_path, new_table_name, "ogr")
                QgsProject.instance().addMapLayer(new_layer)

        # --- BUILD CAMERA LOOKUP ---
        camera_lookup = {}
        for feat in camera_layer.getFeatures():
            cam_id = feat["name"]
            geom = feat.geometry().asPoint()
            camera_lookup[cam_id] = (geom.x(), geom.y())

        # Fields
        folder_field = "folder_path"
        media_field = "media_path"
        camera_field = "camera_id"
        datetime_field = "datetime"
        local_time_field = "local_time"
        timezone_field = "timezone"
        local_tz = "Pacific/Auckland"

        image_ext = (".jpg", ".jpeg", ".png")
        video_ext = (".mp4", ".mov", ".avi", ".mpeg", ".mpg")

        # Build set of existing media paths for duplicate check
        existing_paths = set()
        for feat in new_layer.getFeatures():
            val = feat[media_field]
            if val:
                existing_paths.add(val)

        added_count = 0
        new_layer.startEditing()

        # Extract camera ID from folder name prefix
        folder_name = os.path.basename(folder)
        camera_id = folder_name.split("-")[0]
        camera_id = camera_id if camera_id in camera_lookup else None

        if not camera_id:
            camera_id, ok = QInputDialog.getText(None, "Camera ID Missing",
                                                 f"Folder name '{folder_name}' does not match any camera.\nEnter camera ID:")
            if not ok or camera_id not in camera_lookup:
                raise Exception("No valid camera ID provided. Operation cancelled.")

        cam_x, cam_y = camera_lookup[camera_id]

        # Process files
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename).replace("\\", "/")
            ext = filename.lower()

            # Skip if already exists
            if file_path in existing_paths:
                print(f"Skipping duplicate: {file_path}")
                continue

            exif_datetime = None
            local_time_str = None

            if ext.endswith(image_ext):
                try:
                    img = Image.open(file_path)
                    exif_data = img._getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            if TAGS.get(tag_id) == "DateTimeOriginal":
                                exif_datetime = value
                    img.close()
                except Exception as e:
                    print(f"No EXIF for {filename}: {e}")

                if exif_datetime:
                    try:
                        dt_obj = datetime.strptime(exif_datetime, "%Y:%m:%d %H:%M:%S")
                        exif_datetime = dt_obj.isoformat(sep=' ')
                        local_time_str = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
                    except:
                        exif_datetime = None
                        local_time_str = None

            elif ext.endswith(video_ext):
                try:
                    mod_time = os.path.getmtime(file_path)
                    dt_obj = datetime.fromtimestamp(mod_time)
                    exif_datetime = dt_obj.isoformat(sep=' ')
                    local_time_str = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    exif_datetime = None
                    local_time_str = None
            else:
                continue

            # Add feature
            feat = QgsFeature(new_layer.fields())
            feat.setAttribute(folder_field, folder.replace("\\", "/"))
            feat.setAttribute(media_field, file_path)
            feat.setAttribute(camera_field, camera_id)
            feat.setAttribute(timezone_field, local_tz)
            if exif_datetime: feat.setAttribute(datetime_field, exif_datetime)
            if local_time_str: feat.setAttribute(local_time_field, local_time_str)
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(cam_x, cam_y)))

            new_layer.addFeature(feat)
            added_count += 1

        new_layer.commitChanges()
        print(f"Appended {added_count} new media files to layer '{new_table_name}'.")
