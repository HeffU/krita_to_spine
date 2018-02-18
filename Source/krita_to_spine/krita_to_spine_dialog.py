# Grab what we need from QT
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QFormLayout, QListWidget, QHBoxLayout,
                             QDialogButtonBox, QVBoxLayout, QFrame,
                             QPushButton, QAbstractScrollArea, QLineEdit,
                             QMessageBox, QFileDialog, QCheckBox, QSpinBox,
                             QComboBox, QLabel)

import os
import errno
import json
import krita


class SpineExportDialog(QDialog):

    def __init__(self, parent=None):
        # Initialize parent
        super(SpineExportDialog, self).__init__(parent)
        
        # Get a Krita API instance
        self.kritaInstance = krita.Krita.instance()
        
        # Main dialog
        self.dialogLayout = QVBoxLayout(self)
        self.setWindowModality(Qt.NonModal)
        
        # Dialog buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.confirmButton)
        self.buttonBox.rejected.connect(self.close)
        
        # Form for the rows
        self.upperFormLayout = QFormLayout()
        self.lowerFormLayout = QFormLayout()
        
        # Document list and refresh button
        self.documentsList = []
        self.documentsLayout = QVBoxLayout()
        self.widgetDocuments = QListWidget()
        self.widgetDocuments.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.refreshButton = QPushButton("Refresh Documents")
        self.refreshButton.clicked.connect(self.refreshDocuments)
        
        # Directory field and browse button
        self.directorySelectorLayout = QHBoxLayout()
        self.directoryTextField = QLineEdit()
        self.directoryDialogButton = QPushButton("...")
        self.directoryDialogButton.clicked.connect(self.selectDir)
        
        # Option checkboxes
        self.optionsLayout = QVBoxLayout()
        self.ignoreFilterLayersCheckBox = QCheckBox("Ignore filter layers")
        self.ignoreFilterLayersCheckBox.setChecked(True)
        self.ignoreInvisibleLayersCheckBox = QCheckBox("Ignore invisible layers")
        self.ignoreInvisibleLayersCheckBox.setChecked(True)
        self.batchmodeCheckBox = QCheckBox("Export in batchmode")
        self.batchmodeCheckBox.setChecked(True)
        self.subdirectoryCheckBox = QCheckBox("Use sub directory for images")
        self.subdirectoryCheckBox.setChecked(True)
        self.groupdirectoriesCheckBox = QCheckBox("Create sub directories for group layers")
        self.groupSlotCheckBox = QCheckBox("Treat Group Layers as skin slots. (Child layers must belong to unique skins)")
        # Help text for skin option
        self.skinHelpLine = QLabel()
        
        # Format box
        self.formatsComboBox = QComboBox()

    
    def initialize(self):
        # Document list and refresh button
        self.refreshDocuments()
        self.documentsLayout.addWidget(self.widgetDocuments)
        self.documentsLayout.addWidget(self.refreshButton)
        
        # Directory field and browse button
        self.directorySelectorLayout.addWidget(self.directoryTextField)
        self.directorySelectorLayout.addWidget(self.directoryDialogButton)
        
        # Option checkboxes
        self.optionsLayout.addWidget(self.ignoreFilterLayersCheckBox)
        self.optionsLayout.addWidget(self.batchmodeCheckBox)
        self.optionsLayout.addWidget(self.ignoreInvisibleLayersCheckBox)
        self.optionsLayout.addWidget(self.subdirectoryCheckBox)
        self.optionsLayout.addWidget(self.groupdirectoriesCheckBox)
        self.optionsLayout.addWidget(self.groupSlotCheckBox)
        
        self.skinHelpLine.setText("      Tag layers with skin names: layerName (skinName) | No tag = default skin")
        
        # Format box
        self.formatsComboBox.addItem("jpeg")
        self.formatsComboBox.addItem("png")
        
        # Add sub-layout rows into the forms
        self.upperFormLayout.addRow('Documents', self.documentsLayout)
        
        self.lowerFormLayout.addRow('Base directory', self.directorySelectorLayout)
        self.lowerFormLayout.addRow('Export options', self.optionsLayout)
        self.lowerFormLayout.addRow(' ', self.skinHelpLine)
        self.lowerFormLayout.addRow('Extensions', self.formatsComboBox)
        
        # Separator after documents
        self.upperLine = QFrame()
        self.upperLine.setFrameShape(QFrame.HLine)
        self.upperLine.setFrameShadow(QFrame.Sunken)
        
        # Separator before dialog buttons
        self.lowerLine = QFrame()
        self.lowerLine.setFrameShape(QFrame.HLine)
        self.lowerLine.setFrameShadow(QFrame.Sunken)
        
        # Add form and separators to the main layout
        self.dialogLayout.addLayout(self.upperFormLayout)
        self.dialogLayout.addWidget(self.upperLine)
        self.dialogLayout.addLayout(self.lowerFormLayout)
        self.dialogLayout.addWidget(self.lowerLine)
        self.dialogLayout.addWidget(self.buttonBox)
        
        # Show main dialog
        self.resize(500, 300)
        self.setWindowTitle("Export for Spine")
        self.setSizeGripEnabled(True)
        self.show()
        self.activateWindow()
    
    def refreshDocuments(self):
        self.widgetDocuments.clear()
        self.documentsList = [document for document in self.kritaInstance.documents() if document.fileName()]
        for document in self.documentsList:
            self.widgetDocuments.addItem(document.fileName())    
        
    def confirmButton(self):
        selectedPaths = [item.text() for item in self.widgetDocuments.selectedItems()]
        selectedDocuments = [document for document in self.documentsList for path in selectedPaths if path == document.fileName()]

        # Sanity checks
        self.msgBox = QMessageBox(self)
        if not selectedDocuments:
            self.msgBox.setText("Select one document.")
        elif not self.directoryTextField.text():
            self.msgBox.setText("Select a base directory.")
        else:
            self.export(selectedDocuments[0])
            self.msgBox.setText("All layers has been exported.")
        self.msgBox.exec_()
        
    def closeEvent(self, event):
        event.accept()
        
    def createDir(self, directory):
        try:
            os.makedirs(self.directoryTextField.text() + directory)
        except OSError as e:
            # If an error pops up that is not "folder already exists"
            if e.errno != errno.EEXIST:
                raise
        
    def selectDir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select a folder", os.path.expanduser("~"), QFileDialog.ShowDirsOnly)
        self.directoryTextField.setText(directory)
        
    def export(self, document):
        self.currentDocument = document
    
        # Basic structure
        data = {
            'skeleton': {},
            'bones': [{'name': 'root'}],
            'slots': [],
            'skins': {'default': {}},
            'animations': {}
        }
        self.slots = data['slots']
        self.attachments = data['skins']
        
        # Set up Krita
        Application.setBatchmode(self.batchmodeCheckBox.isChecked())
        documentName = document.fileName() if document.fileName() else 'Untitled'
        fileName, extension = str(documentName).rsplit('/', maxsplit=1)[-1].split('.', maxsplit=1)
        
        imageDir = fileName
        # Set up directories
        self.createDir('/' + fileName)
        if self.subdirectoryCheckBox.isChecked():
            imageDir += '/images'
            self.createDir('/' + imageDir)
            data['skeleton']['images'] = './images/'
        
        # Recursively process and export layers
        self._exportLayers(document.rootNode(), self.formatsComboBox.currentText(), '/' + imageDir)
        
        # Export resulting json to spine file
        with open(os.path.join(self.directoryTextField.text(), fileName, '%s.json' % fileName), 'w') as json_file:
            json.dump(data, json_file, indent=4, separators=(',', ': '))
        
        # Reset Krita
        Application.setBatchmode(True)
        
        
    def _exportLayers(self, parentNode, fileFormat, parentDir):
        for node in parentNode.childNodes():
            newDir = ''
            nodeName = node.name()
            # Handle filter layers
            if self.ignoreFilterLayersCheckBox.isChecked() and 'filter' in node.type():
                continue
            # Handle invisible layers
            elif self.ignoreInvisibleLayersCheckBox.isChecked() and not node.visible():
                continue
            # Ignore krita's selection layer
            elif nodeName == 'selection':
                continue
            # Handle Group layers
            if node.type() == 'grouplayer':
                if self.groupdirectoriesCheckBox.isChecked():
                    newDir = parentDir + '/' + node.name()
                    self.createDir(newDir)
                else:
                    newDir = parentDir
                # Create a slot for the whole group, with no setup attachment
                if self.groupSlotCheckBox.isChecked():
                    self.slots.insert(0, {
                        'name': nodeName,
                        'bone': 'root',
                        'attachment': nodeName,
                    })
            # Handle normal layers
            else:
                _fileFormat = self.formatsComboBox.currentText()
                bounds = node.bounds()
                
                layerFileName = '{0}{1}/{2}.{3}'.format(self.directoryTextField.text(), parentDir, node.name(), _fileFormat)
                image = node.save(layerFileName, bounds.width(), bounds.height())
                
                # Construct the attachment data
                attachment = {nodeName: {
                    'x': bounds.center().x(),
                    # Spine uses bottom left as origin rather than top left, so we convert
                    'y': self.currentDocument.height() - bounds.center().y(),
                    'rotation': 0,
                    'width': bounds.width(),
                    'height': bounds.height(),
                }}
                
                # Handle children of group layers
                if self.groupSlotCheckBox.isChecked() and parentNode.type() == 'grouplayer' and not parentNode.name() == 'root':
                    skinName = 'default'
                    a = nodeName.find('(')
                    b = nodeName.find(')')
                    if not a == -1 and b > a:
                        skinName = nodeName[a+1:b]
                    if not skinName in self.attachments:
                        self.attachments[skinName] = {}
                    self.attachments[skinName][parentNode.name()] = attachment
                else:
                    self.slots.insert(0, {
                        'name': nodeName,
                        'bone': 'root',
                        'attachment': nodeName,
                    })
                    self.attachments['default'][nodeName] = attachment

            # Recursively handle child layers
            if node.childNodes():
                self._exportLayers(node, fileFormat, newDir)
        
        