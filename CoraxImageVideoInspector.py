
from qgis.PyQt.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QLabel, QScrollArea,
                                 QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QComboBox,
                                 QAction, QMessageBox, QGroupBox)
from qgis.PyQt.QtCore import Qt, QUrl, QTimer
from qgis.PyQt.QtGui import QPixmap, QKeySequence, QShortcut, QDesktopServices, QIcon
from qgis.core import QgsProject
import os

class ImageVideoInspectorDock(QDockWidget):
    def __init__(self):
        super().__init__("Image/Video Inspector")
        self.layer = None
        self.features = []
        self.current_index = 0
        self.current_scale = 1.0
        self.slideshow_timer = QTimer()
        self.slideshow_timer.timeout.connect(self.next_record)

        # Lookup for species and shortcodes
        self.species_map = {}
        lut_layers = QgsProject.instance().mapLayersByName("bird_pest_lut")
        if lut_layers:
            lut_layer = lut_layers[0]
            fields = [f.name() for f in lut_layer.fields()]
            species_field = "species" if "species" in fields else fields[0]
            shortcode_field = "shortcode" if "shortcode" in fields else fields[-1]
            for feat in lut_layer.getFeatures():
                self.species_map[str(feat[species_field])] = str(feat[shortcode_field])

        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Layer selector
        self.layer_selector = QComboBox()
        point_layers = [layer.name() for layer in QgsProject.instance().mapLayers().values()
                        if layer.type() == layer.VectorLayer and layer.geometryType() == 0]
        if point_layers:
            self.layer_selector.addItems(point_layers)
        else:
            self.layer_selector.addItem("No point layers available")
            self.layer_selector.setEnabled(False)
        self.layer_selector.currentIndexChanged.connect(self.load_layer)
        main_layout.addWidget(self.layer_selector)

        # Viewer area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.viewer_container = QWidget()
        self.viewer_layout = QVBoxLayout(self.viewer_container)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        # Status bar
        self.status_label = QLabel("No records loaded")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Buttons
        self.play_video_btn = QPushButton("Play Video")
        self.play_video_btn.hide()
        self.play_video_btn.clicked.connect(self.play_video)

        self.popout_btn = QPushButton("Pop Out Image")
        self.popout_btn.clicked.connect(self.show_fullscreen_image)

        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_out_btn = QPushButton("Zoom Out")
        self.fit_btn = QPushButton("Fit")
        self.slideshow_btn = QPushButton("Start Slideshow")

        self.save_btn = QPushButton("Save")
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.first_btn = QPushButton("First")
        self.last_btn = QPushButton("Last")
        self.jump_btn = QPushButton("Jump to FID")
        self.clear_btn = QPushButton("Clear Fields")
        self.clear_btn.clicked.connect(self.clear_fields)

        help_btn = QPushButton("Help")
        help_path = os.path.join(os.path.dirname(__file__), "help.chm")
        help_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(help_path)))

        about_btn = QPushButton("About")
        about_btn.clicked.connect(self.show_about)

        # Group buttons
        viewer_group = QGroupBox("Viewer Controls")
        viewer_layout = QHBoxLayout()
        viewer_layout.addWidget(self.popout_btn)
        viewer_layout.addWidget(self.play_video_btn)
        viewer_group.setLayout(viewer_layout)

        zoom_group = QGroupBox("Zoom & Slideshow")
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(self.zoom_in_btn)
        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(self.fit_btn)
        zoom_layout.addWidget(self.slideshow_btn)
        zoom_group.setLayout(zoom_layout)

        action_group = QGroupBox("Actions")
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.prev_btn)
        action_layout.addWidget(self.next_btn)
        action_layout.addWidget(self.first_btn)
        action_layout.addWidget(self.last_btn)
        action_layout.addWidget(self.jump_btn)
        action_layout.addWidget(self.clear_btn)
        action_group.setLayout(action_layout)

        info_group = QGroupBox("Info")
        info_layout = QHBoxLayout()
        info_layout.addWidget(help_btn)
        info_layout.addWidget(about_btn)
        info_group.setLayout(info_layout)

        # Two-column layout for button groups
        button_columns = QHBoxLayout()
        left_column = QVBoxLayout()
        left_column.addWidget(viewer_group)
        left_column.addWidget(action_group)

        right_column = QVBoxLayout()
        right_column.addWidget(zoom_group)
        right_column.addWidget(info_group)

        button_columns.addLayout(left_column)
        button_columns.addLayout(right_column)

        # Add groups to layout
        self.viewer_layout.addWidget(self.image_label)
        self.scroll_area.setWidget(self.viewer_container)
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(button_columns)

        # Editable fields (collapsible)
        self.form_layout = QFormLayout()
        self.field_edits = {}
        self.fields_container = QWidget()
        self.fields_container.setLayout(self.form_layout)
        self.fields_container.setVisible(False)

        toggle_btn = QPushButton("Show/Hide Fields")
        toggle_btn.clicked.connect(lambda: self.fields_container.setVisible(not self.fields_container.isVisible()))
        main_layout.addWidget(toggle_btn)
        main_layout.addWidget(self.fields_container)

        # Disable navigation until layer is loaded
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.first_btn.setEnabled(False)
        self.last_btn.setEnabled(False)
        self.jump_btn.setEnabled(False)

        self.setWidget(main_widget)

        # Connect signals
        self.prev_btn.clicked.connect(self.prev_record)
        self.next_btn.clicked.connect(self.next_record)
        self.first_btn.clicked.connect(self.go_first)
        self.last_btn.clicked.connect(self.go_last)
        self.jump_btn.clicked.connect(self.jump_to_fid)
        self.save_btn.clicked.connect(self.save_changes)
        self.zoom_in_btn.clicked.connect(lambda: self.adjust_zoom(1.2))
        self.zoom_out_btn.clicked.connect(lambda: self.adjust_zoom(0.8))
        self.fit_btn.clicked.connect(self.fit_to_window)
        self.slideshow_btn.clicked.connect(self.toggle_slideshow)

        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.Key_Left), self, self.prev_record)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.next_record)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_changes)

        # Auto-load first layer if available
        if point_layers:
            self.load_layer()

    def load_layer(self):
        layer_name = self.layer_selector.currentText()
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if not layers:
            self.status_label.setText(f"Layer '{layer_name}' not found")
            return

        self.layer = layers[0]
        if self.layer.type() != self.layer.VectorLayer or self.layer.geometryType() != 0:
            self.status_label.setText("Invalid layer type")
            return

        self.features = list(self.layer.getFeatures())
        print(f"DEBUG: Loading layer '{layer_name}' with {len(self.features)} features")

        # Build form fields
        for i in reversed(range(self.form_layout.count())):
            self.form_layout.removeRow(i)
        self.field_edits.clear()

        self.species_dropdown = QComboBox()
        self.species_dropdown.addItem("")
        self.species_dropdown.addItems([str(k) for k in self.species_map.keys()])
        self.species_dropdown.currentTextChanged.connect(self.update_shortcodes)

        self.species_second_dropdown = QComboBox()
        self.species_second_dropdown.addItem("")
        self.species_second_dropdown.addItems([str(k) for k in self.species_map.keys()])
        self.species_second_dropdown.currentTextChanged.connect(self.update_shortcodes)

        self.form_layout.addRow("species", self.species_dropdown)
        self.field_edits["species"] = self.species_dropdown

        species_count_edit = QLineEdit()
        species_count_edit.setText("0")
        self.form_layout.addRow("species_count", species_count_edit)
        self.field_edits["species_count"] = species_count_edit

        self.form_layout.addRow("species_second", self.species_second_dropdown)
        self.field_edits["species_second"] = self.species_second_dropdown

        comment_edit = QLineEdit()
        self.form_layout.addRow("comment", comment_edit)
        self.field_edits["comment"] = comment_edit

        shortcode_edit = QLineEdit()
        shortcode_edit.setReadOnly(True)
        self.form_layout.addRow("shortcode", shortcode_edit)
        self.field_edits["shortcode"] = shortcode_edit

        shortcode2_edit = QLineEdit()
        shortcode2_edit.setReadOnly(True)
        self.form_layout.addRow("shortcode2", shortcode2_edit)
        self.field_edits["shortcode2"] = shortcode2_edit

        fid_edit = QLineEdit()
        fid_edit.setReadOnly(False)  # Editable for jump
        self.form_layout.addRow("fid", fid_edit)
        self.field_edits["fid"] = fid_edit

        if self.features:
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.first_btn.setEnabled(True)
            self.last_btn.setEnabled(True)
            self.jump_btn.setEnabled(True)
            self.load_record()
        else:
            self.status_label.setText("No records found")

    def load_record(self):
        feature = self.features[self.current_index]
        media_path = feature["media_path"] if "media_path" in feature.fields().names() else None

        self.status_label.setText(f"Record {self.current_index + 1} of {len(self.features)}")

        self.image_label.hide()
        self.play_video_btn.hide()

        if media_path and media_path.lower().endswith((".jpg", ".jpeg", ".png")):
            pixmap = QPixmap(media_path)
            scaled = pixmap.scaled(pixmap.size() * self.current_scale, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.image_label.show()
        elif media_path and media_path.lower().endswith(".mp4"):
            self.image_label.setText("Video Preview")
            self.image_label.show()
            self.play_video_btn.show()
        else:
            self.image_label.setText("No media linked")
            self.image_label.show()

        self.species_dropdown.setCurrentText(str(feature["species"]) if feature["species"] else "")
        self.species_second_dropdown.setCurrentText(str(feature["species_second"]) if feature["species_second"] else "")
        self.field_edits["species_count"].setText(str(feature["species_count"]) if feature["species_count"] else "0")
        self.field_edits["comment"].setText(str(feature["comment"]) if feature["comment"] else "")
        self.field_edits["fid"].setText(str(feature["fid"]) if feature["fid"] else "")
        self.update_shortcodes()

    def update_shortcodes(self):
        species_val = self.species_dropdown.currentText()
        species_second_val = self.species_second_dropdown.currentText()
        self.field_edits["shortcode"].setText(self.species_map.get(species_val, ""))
        self.field_edits["shortcode2"].setText(self.species_map.get(species_second_val, ""))
        if species_val and self.field_edits["species_count"].text() == "0":
            self.field_edits["species_count"].setText("1")

    def clear_fields(self):
        self.species_dropdown.setCurrentText("")
        self.species_second_dropdown.setCurrentText("")
        self.field_edits["shortcode"].setText("")
        self.field_edits["shortcode2"].setText("")
        self.field_edits["species_count"].setText("0")
        self.field_edits["comment"].setText("")
        self.status_label.setText(f"Record {self.current_index + 1} of {len(self.features)}")

    def jump_to_fid(self):
        try:
            target_fid = int(self.field_edits["fid"].text())
            for i, feature in enumerate(self.features):
                if feature["fid"] == target_fid:
                    self.save_changes()
                    self.current_index = i
                    self.load_record()
                    return
            QMessageBox.information(self, "FID Not Found", f"No record with FID {target_fid}.")
        except ValueError:
            QMessageBox.warning(self, "Invalid FID", "Please enter a valid numeric FID.")

    def go_first(self):
        self.save_changes()
        self.current_index = 0
        self.load_record()

    def go_last(self):
        self.save_changes()
        self.current_index = len(self.features) - 1
        self.load_record()

    def play_video(self):
        feature = self.features[self.current_index]
        media_path = feature["media_path"]
        if os.path.exists(media_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(media_path))

    def show_fullscreen_image(self):
        feature = self.features[self.current_index]
        media_path = feature["media_path"]
        if os.path.exists(media_path) and media_path.lower().endswith((".jpg", ".jpeg", ".png")):
            dlg = QWidget()
            dlg.setWindowTitle("Full Image View")
            dlg.showMaximized()
            layout = QVBoxLayout(dlg)
            label = QLabel()
            pixmap = QPixmap(media_path)
            label.setPixmap(pixmap.scaled(dlg.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            dlg.show()

    def save_changes(self):
        feature = self.features[self.current_index]
        self.layer.startEditing()
        feature["species"] = self.species_dropdown.currentText() if self.species_dropdown.currentText() else None
        feature["species_second"] = self.species_second_dropdown.currentText() if self.species_second_dropdown.currentText() else None
        try:
            val = self.field_edits["species_count"].text()
            feature["species_count"] = int(val) if val else None
        except ValueError:
            feature["species_count"] = None
        feature["comment"] = self.field_edits["comment"].text()
        self.layer.updateFeature(feature)
        self.layer.commitChanges()

    def next_record(self):
        self.save_changes()
        if self.current_index < len(self.features) - 1:
            self.current_index += 1
            self.load_record()
        else:
            self.slideshow_timer.stop()
            self.slideshow_btn.setText("Start Slideshow")

    def prev_record(self):
        self.save_changes()
        if self.current_index > 0:
            self.current_index -= 1
            self.load_record()

    def adjust_zoom(self, factor):
        self.current_scale *= factor
        self.load_record()

    def fit_to_window(self):
        self.current_scale = 1.0
        self.load_record()

    def toggle_slideshow(self):
        if self.slideshow_timer.isActive():
            self.slideshow_timer.stop()
            self.slideshow_btn.setText("Start Slideshow")
        else:
            self.slideshow_timer.start(2000)
            self.slideshow_btn.setText("Stop Slideshow")

    def show_about(self):
        QMessageBox.information(self, "About Corax Image/Video Inspector",
                                "Version 3.1\nAuthor: Kim Ollivier\nHelp file included in plugin folder.\n")

# Plugin entry point
def classFactory(iface):
    return CoraxImageVideoInspectorPlugin(iface)

class CoraxImageVideoInspectorPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dock = None
        self.action = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        self.action = QAction(QIcon(icon_path), "Image/Video Inspector", self.iface.mainWindow())
        self.action.triggered.connect(self.show_dock)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Corax Tools", self.action)
        self.dock = ImageVideoInspectorDock()
        self.dock.hide()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

    def show_dock(self):
        self.dock.show()

    def unload(self):
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu("&Corax Tools", self.action)
        if self.dock:
            self.iface.removeDockWidget(self.dock)
