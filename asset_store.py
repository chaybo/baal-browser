import os
import maya.cmds as cmds
from PySide2 import QtWidgets, QtGui, QtCore
import json

"""
asset_store.py

This an asset store for saving and versioning up asset files

- can be used for multiple shows/projects via drop down menu
- can add notes per publish
- will check for dirty scenes, namespaces etc before publish
- can swap between .mb or .ma
- can import files into current scene
- generates out a single line importer that can be used in automatically picking up the asset for baking/pipeline work
- Can navigate and browse other defined folders on the machine it is on

By Chay

#create_gui()

"""

class FolderBrowserUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(FolderBrowserUI, self).__init__(parent)

        # Get the directory of the current script
        script_directory = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path to the settings.json file
        settings_file = os.path.join(script_directory, 'settings.json')

        # Load settings from the JSON file
        try:
            with open(settings_file, 'r') as file:
                settings = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"{settings_file} not found. Please provide the settings file.")
        except json.JSONDecodeError:
            raise ValueError(f"Error decoding JSON from {settings_file}. Please check the file format.")

        # Retrieve settings
        try:
            self.asset_directory = settings["asset_directory"]
            self.current_directory = settings["current_directory"]
            self.archive_directory = settings["archive_directory"]
            window_icon_path = settings["window_icon"]
        except KeyError as e:
            raise KeyError(f"Missing key in {settings_file}: {e}. Please ensure all required settings are provided.")

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QtGui.QIcon(window_icon_path))
        self.setWindowTitle("Baal Browser")
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)

        # Add tabs
        self.tabs = QtWidgets.QTabWidget(self)
        main_layout.addWidget(self.tabs)

        # Create tabs
        self.create_assets_tab()
        self.create_simple_browser_tab("Current", self.current_directory)
        self.create_simple_browser_tab("Archives", self.archive_directory)

        # Importer line edit
        self.importer_line_edit = QtWidgets.QLineEdit(self)
        main_layout.addWidget(self.importer_line_edit)

        # Load initial project
        self.populate_projects()
        if self.project_selector.count() > 0:
            self.update_directory()

    def create_assets_tab(self):
        tab_widget = QtWidgets.QWidget(self)
        tab_layout = QtWidgets.QVBoxLayout(tab_widget)

        # Project selector and buttons layout
        project_layout = QtWidgets.QHBoxLayout()
        tab_layout.addLayout(project_layout)

        # Project selector
        self.project_selector = QtWidgets.QComboBox(self)
        self.project_selector.setStyleSheet("background-color: rgb(42, 46, 50);")
        self.project_selector.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        project_layout.addWidget(self.project_selector)

        # Add a "+" button with a menu
        self.plus_button = QtWidgets.QPushButton("+", self)
        self.plus_button.setMaximumWidth(50)
        project_layout.addWidget(self.plus_button)

        self.plus_menu = QtWidgets.QMenu(self)
        self.add_project_action = self.plus_menu.addAction("Add New Project")
        self.add_creature_action = self.plus_menu.addAction("Add New Creature")
        self.plus_button.setMenu(self.plus_menu)

        # Splitter for the main sections
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        tab_layout.addWidget(main_splitter)

        # Splitter for the file and folder sections
        top_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        main_splitter.addWidget(top_splitter)

        # Folder list
        folder_list_widget = QtWidgets.QWidget(self)
        folder_list_layout = QtWidgets.QVBoxLayout(folder_list_widget)
        folder_label = QtWidgets.QLabel('Creature Name', self)
        folder_list_layout.addWidget(folder_label)
        self.folder_list = QtWidgets.QListWidget(self)
        self.folder_list.setStyleSheet("background-color: rgb(37, 37, 37);")
        folder_list_layout.addWidget(self.folder_list)
        top_splitter.addWidget(folder_list_widget)

        # File list
        file_list_widget = QtWidgets.QWidget(self)
        file_list_layout = QtWidgets.QVBoxLayout(file_list_widget)
        file_label = QtWidgets.QLabel('Creature Asset', self)
        file_list_layout.addWidget(file_label)
        self.file_list = QtWidgets.QListWidget(self)
        self.file_list.setStyleSheet("background-color: rgb(37, 37, 37);")
        file_list_layout.addWidget(self.file_list)
        top_splitter.addWidget(file_list_widget)

        # Versions list
        versions_list_widget = QtWidgets.QWidget(self)
        versions_list_layout = QtWidgets.QVBoxLayout(versions_list_widget)
        versions_label = QtWidgets.QLabel('Versions', self)
        versions_list_layout.addWidget(versions_label)
        self.versions_list = QtWidgets.QListWidget(self)
        self.versions_list.setStyleSheet("background-color: rgb(37, 37, 37);")
        versions_list_layout.addWidget(self.versions_list)
        top_splitter.addWidget(versions_list_widget)

        # Notes editor
        notes_widget = QtWidgets.QWidget(self)
        notes_layout = QtWidgets.QVBoxLayout(notes_widget)
        notes_label = QtWidgets.QLabel('Notes', self)
        notes_layout.addWidget(notes_label)
        self.notes_editor = QtWidgets.QTextEdit(self)
        self.notes_editor.setStyleSheet("background-color: rgb(37, 37, 37);")
        self.notes_editor.setReadOnly(True)
        notes_layout.addWidget(self.notes_editor)
        main_splitter.addWidget(notes_widget)

        # New elements section
        new_elements_widget = QtWidgets.QWidget(self)
        self.new_elements_layout = QtWidgets.QVBoxLayout(new_elements_widget)
        self.setup_new_elements(self.new_elements_layout)
        main_splitter.addWidget(new_elements_widget)

        self.tabs.addTab(tab_widget, "Assets")

        # Set connections
        self.project_selector.currentIndexChanged.connect(self.update_directory)
        self.add_project_action.triggered.connect(self.add_new_project)
        self.add_creature_action.triggered.connect(self.add_new_creature)
        self.folder_list.itemClicked.connect(self.on_folder_selected)
        self.file_list.itemClicked.connect(self.on_file_selected)
        self.versions_list.itemClicked.connect(self.on_version_selected)
        self.publish_button.clicked.connect(self.on_publish_clicked)
        self.open_button.clicked.connect(self.on_open_clicked)
        self.import_button.clicked.connect(self.on_import_clicked)
        self.file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.versions_list.itemDoubleClicked.connect(self.on_version_double_clicked)

    def create_simple_browser_tab(self, tab_name, directory):
        tab_widget = QtWidgets.QWidget(self)
        tab_layout = QtWidgets.QVBoxLayout(tab_widget)

        # Directory browser
        dir_model = QtWidgets.QFileSystemModel()
        dir_model.setRootPath(directory)
        dir_model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)

        dir_view = QtWidgets.QTreeView()
        dir_view.setModel(dir_model)
        dir_view.setRootIndex(dir_model.index(directory))
        dir_view.setColumnWidth(0, 250)
        dir_view.clicked.connect(lambda index, d=directory: self.on_directory_clicked(index, d, file_list))
        tab_layout.addWidget(dir_view)

        # File list
        file_list = QtWidgets.QListWidget(self)
        file_list.setStyleSheet("background-color: rgb(37, 37, 37);")
        file_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        file_list.customContextMenuRequested.connect(self.on_file_context_menu)
        file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        tab_layout.addWidget(file_list)

        # Open and Import buttons
        button_layout = QtWidgets.QHBoxLayout()
        open_button = QtWidgets.QPushButton("Open")
        open_button.clicked.connect(lambda: self.open_file(file_list.currentItem()))
        import_button = QtWidgets.QPushButton("Import")
        import_button.clicked.connect(lambda: self.import_file(file_list.currentItem()))
        button_layout.addWidget(open_button)
        button_layout.addWidget(import_button)
        tab_layout.addLayout(button_layout)

        self.tabs.addTab(tab_widget, tab_name)

    def on_directory_clicked(self, index, base_path, file_list):
        dir_model = index.model()
        folder_path = dir_model.filePath(index)

        file_list.clear()
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            for file in files:
                if file.endswith(('.ma', '.mb', '.obj')):
                    item = QtWidgets.QListWidgetItem(file)
                    file_path = os.path.join(folder_path, file)
                    item.setData(QtCore.Qt.UserRole, file_path)
                    if file.endswith('.ma') or file.endswith('.mb'):
                        item.setIcon(QtGui.QIcon('E:/Files/Dropbox/Resources/Assets/Icons/maya_icon.png'))
                    elif file.endswith('.obj'):
                        item.setIcon(QtGui.QIcon('E:/Files/Dropbox/Resources/Assets/Icons/obj_icon.png'))
                    file_list.addItem(item)

    def on_file_context_menu(self, position):
        file_list = self.sender()
        menu = QtWidgets.QMenu()

        open_action = menu.addAction("Open")
        import_action = menu.addAction("Import")

        open_action.triggered.connect(lambda: self.open_file(file_list.currentItem()))
        import_action.triggered.connect(lambda: self.import_file(file_list.currentItem()))

        menu.exec_(file_list.mapToGlobal(position))

    def on_file_double_clicked(self, item):
        self.open_file(item)

    def open_file(self, item):
        if item:
            file_path = item.data(QtCore.Qt.UserRole)
            if file_path.endswith(('.ma', '.mb')):
                cmds.file(file_path, o=True, f=True)
                QtWidgets.QMessageBox.information(self, 'Open', f'{file_path} opened successfully.')

    def import_file(self, item):
        if item:
            file_path = item.data(QtCore.Qt.UserRole)
            if file_path.endswith(('.ma', '.mb', '.obj')):
                cmds.file(file_path, i=True)
                QtWidgets.QMessageBox.information(self, 'Import', f'{file_path} imported successfully.')

    def populate_projects(self):
        self.project_selector.clear()
        if os.path.exists(self.asset_directory):
            projects = [f for f in os.listdir(self.asset_directory) if os.path.isdir(os.path.join(self.asset_directory, f))]
            self.project_selector.addItems(projects)

    def setup_new_elements(self, layout):
        self.text_box = QtWidgets.QLineEdit(self)
        layout.addWidget(self.text_box)
        self.file_type_checkbox = QtWidgets.QCheckBox('.mb', self)
        self.file_type_checkbox.setChecked(True)
        layout.addWidget(self.file_type_checkbox)

        buttons_layout = QtWidgets.QHBoxLayout()

        self.publish_button = QtWidgets.QPushButton('Publish', self)
        self.publish_button.setStyleSheet("background-color: rgb(33, 157, 208);")
        buttons_layout.addWidget(self.publish_button)

        self.open_button = QtWidgets.QPushButton('Open', self)
        buttons_layout.addWidget(self.open_button)

        self.import_button = QtWidgets.QPushButton('Import', self)
        buttons_layout.addWidget(self.import_button)

        layout.addLayout(buttons_layout)

        self.new_notes_label = QtWidgets.QLabel('New Notes', self)
        layout.addWidget(self.new_notes_label)
        self.new_notes_editor = QtWidgets.QTextEdit(self)
        self.new_notes_editor.setText('No new notes set by user, how lazy...')
        layout.addWidget(self.new_notes_editor)

    def save_version(self, creature_name, base_name, notes, save_as_binary=False):
        creature_directory = os.path.join(self.directory, creature_name)
        version_directory = os.path.join(creature_directory, f"{base_name}_versions")
        notes_directory = os.path.join(creature_directory, f"{base_name}_notes")

        if not os.path.exists(version_directory):
            os.makedirs(version_directory)
        if not os.path.exists(notes_directory):
            os.makedirs(notes_directory)

        file_extension = ".mb" if save_as_binary else ".ma"
        latest_version = 0
        for file_name in os.listdir(version_directory):
            if file_name.startswith(base_name) and file_name.endswith(file_extension):
                try:
                    version = int(file_name.split('_v')[-1].split(file_extension)[0])
                    if version > latest_version:
                        latest_version = version
                except ValueError:
                    pass

        new_version = latest_version + 1
        new_file_name = f"{base_name}_v{new_version:04d}{file_extension}"
        new_file_path = os.path.join(version_directory, new_file_name)

        cmds.file(rename=new_file_path)
        cmds.file(save=True, type='mayaBinary' if save_as_binary else 'mayaAscii')

        master_file_name = f"{base_name}_master{file_extension}"
        master_file_path = os.path.join(creature_directory, master_file_name)

        # Overwrite the master file if it exists
        if os.path.exists(master_file_path):
            os.remove(master_file_path)

        cmds.file(rename=master_file_path)
        cmds.file(save=True, type='mayaBinary' if save_as_binary else 'mayaAscii')

        notes_file_name = f"{base_name}_v{new_version:04d}.txt"
        notes_file_path = os.path.join(notes_directory, notes_file_name)
        with open(notes_file_path, 'w') as notes_file:
            notes_file.write(notes)

        print(f"Saved: {new_file_path}, {master_file_path}, {notes_file_path}")

        # Update UI after saving
        self.update_directory()

    def update_directory(self):
        selected_project = self.project_selector.currentText()
        self.directory = os.path.join(self.asset_directory, selected_project)
        self.folder_path = os.path.join(self.asset_directory, selected_project)

        self.project_name = os.path.basename(self.directory)
        self.file_list.clear()
        self.versions_list.clear()
        self.notes_editor.clear()
        self.text_box.clear()
        self.importer_line_edit.clear()
        self.populate_folders()

    def add_new_project(self):
        project_name, ok = QtWidgets.QInputDialog.getText(self, 'Add New Project', 'Enter new project name:')
        if ok and project_name:
            new_project_path = os.path.join(self.asset_directory, project_name)
            if not os.path.exists(new_project_path):
                os.makedirs(new_project_path)
                self.populate_projects()
                self.project_selector.setCurrentText(project_name)
                QtWidgets.QMessageBox.information(self, 'Success', f'New project "{project_name}" added successfully.')
            else:
                QtWidgets.QMessageBox.warning(self, 'Warning', f'Project "{project_name}" already exists.')

    def add_new_creature(self):
        creature_name, ok = QtWidgets.QInputDialog.getText(self, 'Add New Creature', 'Enter new creature name:')
        if ok and creature_name:
            new_folder_path = os.path.join(self.directory, creature_name)
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
                self.populate_folders()
                QtWidgets.QMessageBox.information(self, 'Success', f'New creature "{creature_name}" added successfully.')
            else:
                QtWidgets.QMessageBox.warning(self, 'Warning', f'Creature "{creature_name}" already exists.')

    def on_version_double_clicked(self, item):
        selected_folder_item = self.folder_list.currentItem()
        if not selected_folder_item:
            return
        base_name = self.text_box.text()
        selected_folder = os.path.join(self.folder_path, selected_folder_item.text(), f"{base_name}_versions")
        file_path = os.path.join(selected_folder, item.text())
        if not os.path.exists(file_path):
            return
        reply = QtWidgets.QMessageBox.question(self, 'Open', f'Are you sure you wish to open {item.text()}?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            cmds.file(file_path, o=True, f=True)

    def on_file_double_clicked(self, item):
        selected_folder_item = self.folder_list.currentItem()
        if not selected_folder_item:
            return
        selected_folder = os.path.join(self.folder_path, selected_folder_item.text())
        file_path = os.path.join(selected_folder, item.text())
        if not os.path.exists(file_path):
            return
        reply = QtWidgets.QMessageBox.question(self, 'Open', f'Are you sure you wish to open {item.text()}?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            cmds.file(file_path, o=True, f=True)

    def populate_folders(self):
        self.folder_list.clear()
        if os.path.exists(self.folder_path):
            folders = [f for f in os.listdir(self.folder_path) if os.path.isdir(os.path.join(self.folder_path, f))]
            self.folder_list.addItems(folders)

    def populate_files(self):
        self.file_list.clear()
        selected_folder_item = self.folder_list.currentItem()
        if not selected_folder_item:
            return
        selected_folder = os.path.join(self.folder_path, selected_folder_item.text())
        files = [f for f in os.listdir(selected_folder) if os.path.isfile(os.path.join(selected_folder, f)) and f.endswith(('.ma', '.mb'))]
        for file in files:
            item = QtWidgets.QListWidgetItem(file)
            file_path = os.path.join(selected_folder, file)
            item.setData(QtCore.Qt.UserRole, file_path)
            self.file_list.addItem(item)

    def populate_versions(self, base_name):
        self.versions_list.clear()
        selected_folder_item = self.folder_list.currentItem()
        if not selected_folder_item:
            return
        selected_folder = os.path.join(self.folder_path, selected_folder_item.text(), f"{base_name}_versions")
        if not os.path.exists(selected_folder):
            return
        versions = [f for f in os.listdir(selected_folder) if os.path.isfile(os.path.join(selected_folder, f)) and f.endswith(('.ma', '.mb'))]
        for version in versions:
            item = QtWidgets.QListWidgetItem(version)
            file_path = os.path.join(selected_folder, version)
            item.setData(QtCore.Qt.UserRole, file_path)
            item.setIcon(QtGui.QIcon('E:/Files/Dropbox/Resources/Assets/Icons/version_icon.png'))
            self.versions_list.addItem(item)

    def populate_notes(self, base_name):
        selected_folder_item = self.folder_list.currentItem()
        if not selected_folder_item:
            return
        selected_folder = os.path.join(self.folder_path, selected_folder_item.text(), f"{base_name}_notes")
        if not os.path.exists(selected_folder):
            return
        notes_files = [f for f in os.listdir(selected_folder) if f.endswith('.txt')]
        if not notes_files:
            return
        latest_note_file = max(notes_files, key=lambda f: int(f.split('_v')[-1].split('.txt')[0]))
        note_file_path = os.path.join(selected_folder, latest_note_file)
        if not os.path.exists(note_file_path):
            return
        with open(note_file_path, 'r') as note_file:
            notes_content = note_file.read()
            creation_time = os.path.getctime(note_file_path)
            creation_date = QtCore.QDateTime.fromSecsSinceEpoch(int(creation_time)).toString("dd MMM yyyy hh:mm:ss")
            self.notes_editor.setText(f"Created on: {creation_date}\n\n{notes_content}")

    def on_folder_selected(self, item):
        self.file_list.clear()
        self.versions_list.clear()
        self.notes_editor.clear()
        self.text_box.clear()
        self.populate_files()
        self.update_importer_line()

    def on_file_selected(self, item):
        self.versions_list.clear()
        self.notes_editor.clear()
        base_name = item.text().replace('_master.ma', '').replace('_master.mb', '')
        self.text_box.setText(base_name)
        self.populate_versions(base_name)
        self.populate_notes(base_name)
        self.update_importer_line()

    def on_version_selected(self, item):
        self.notes_editor.clear()
        selected_folder_item = self.folder_list.currentItem()
        if not selected_folder_item:
            return
        base_name = self.text_box.text()
        selected_folder = os.path.join(self.folder_path, selected_folder_item.text(), f"{base_name}_notes")
        if not os.path.exists(selected_folder):
            return
        note_file_name = item.text().replace('.ma', '.txt').replace('.mb', '.txt')
        note_file_path = os.path.join(selected_folder, note_file_name)
        if not os.path.exists(note_file_path):
            return

        with open(note_file_path, 'r') as note_file:
            notes_content = note_file.read()
            creation_time = os.path.getctime(note_file_path)
            creation_date = QtCore.QDateTime.fromSecsSinceEpoch(creation_time).toString("dd MMM yyyy hh:mm:ss")
            self.notes_editor.setText(f"Created on: {creation_date}\n\n{notes_content}")
        self.update_importer_line()

    def update_importer_line(self):
        selected_folder_item = self.folder_list.currentItem()
        selected_file_item = self.file_list.currentItem() or self.versions_list.currentItem()
        if not selected_folder_item or not selected_file_item:
            self.importer_line_edit.clear()
            return
        project_name = self.project_name
        creature_name = selected_folder_item.text()
        file_name = selected_file_item.text()
        frame_rate = '24'
        importer_line = f"stone_importer('{project_name}', '{creature_name}', '{file_name}', '{frame_rate}')"
        self.importer_line_edit.setText(importer_line)

    def on_publish_clicked(self):
        creature_name_item = self.folder_list.currentItem()
        if not creature_name_item:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please select a creature.')
            return
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        default_namespaces = ['UI', 'shared']
        custom_namespaces = [namespace for namespace in namespaces if namespace not in default_namespaces]
        if custom_namespaces:
            reply = QtWidgets.QMessageBox.warning(self, 'Warning',
                                                  'There are namespaces in the scene, messy!\nContinue?',
                                                  QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                  QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                return
        creature_name = creature_name_item.text()
        base_name = self.text_box.text().strip()
        if not base_name or base_name == "_master":
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please add a file name.')
            return
        notes = self.new_notes_editor.toPlainText()
        save_as_binary = self.file_type_checkbox.isChecked()
        reply = QtWidgets.QMessageBox.question(self, 'Publish', 'Are you sure you wish to save?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.save_version(creature_name, base_name, notes, save_as_binary)

    def on_open_clicked(self):
        selected_folder_item = self.folder_list.currentItem()
        if not selected_folder_item:
            return
        base_name = self.text_box.text()
        selected_version_item = self.versions_list.currentItem()
        if selected_version_item:
            directory = os.path.join(self.folder_path, selected_folder_item.text(), f"{base_name}_versions")
            file_path = os.path.join(directory, selected_version_item.text())
        else:
            selected_file_item = self.file_list.currentItem()
            if not selected_file_item:
                return
            directory = os.path.join(self.folder_path, selected_folder_item.text())
            file_path = os.path.join(directory, selected_file_item.text())
        if not os.path.exists(file_path):
            return
        reply = QtWidgets.QMessageBox.question(self, 'Open', f'Are you sure you wish to open {os.path.basename(file_path)}?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            cmds.file(file_path, o=True, f=True)

    def on_import_clicked(self):
        selected_folder_item = self.folder_list.currentItem()
        if not selected_folder_item:
            return
        base_name = self.text_box.text()
        selected_version_item = self.versions_list.currentItem()
        if selected_version_item:
            directory = os.path.join(self.folder_path, selected_folder_item.text(), f"{base_name}_versions")
            file_path = os.path.join(directory, selected_version_item.text())
        else:
            selected_file_item = self.file_list.currentItem()
            if not selected_file_item:
                return
            directory = os.path.join(self.folder_path, selected_folder_item.text())
            file_path = os.path.join(directory, selected_file_item.text())
        if not os.path.exists(file_path):
            return
        reply = QtWidgets.QMessageBox.question(self, 'Import', f'Are you sure you wish to Import {os.path.basename(file_path)}?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            cmds.file(file_path, i=True)


def stone_importer(project_name, folder_name, maya_file, force_frame_rate, new_scene=True):
    base_dir = "E:\\Files\\Dropbox\\Resources\\Assets\\asset_store"
    full_path = os.path.join(base_dir, project_name, folder_name, maya_file)
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return
    if new_scene:
        cmds.file(new=True, force=True)
    cmds.file(full_path, i=True)
    if force_frame_rate:
        frame_rate_str = str(force_frame_rate) + "fps"
        valid_frame_rates = ["game", "film", "pal", "ntsc", "show", "palf", "ntscf", "23.976fps", "29.97fps", "59.94fps",
                             "48fps", "30fps", "25fps", "24fps"]
        if frame_rate_str in valid_frame_rates:
            cmds.currentUnit(time=frame_rate_str)
        else:
            print(f"Warning: Invalid frame rate {force_frame_rate}. Skipping frame rate setting.")


def show_ui():
    global folder_browser_ui
    try:
        folder_browser_ui.close()
    except NameError:
        pass
    folder_browser_ui = FolderBrowserUI(parent=QtWidgets.QApplication.activeWindow())
    folder_browser_ui.show()
