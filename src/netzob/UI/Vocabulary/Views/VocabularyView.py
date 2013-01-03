# -*- coding: utf-8 -*-

#+---------------------------------------------------------------------------+
#|          01001110 01100101 01110100 01111010 01101111 01100010            |
#|                                                                           |
#|               Netzob : Inferring communication protocols                  |
#+---------------------------------------------------------------------------+
#| Copyright (C) 2011 Georges Bossert and Frédéric Guihéry                   |
#| This program is free software: you can redistribute it and/or modify      |
#| it under the terms of the GNU General Public License as published by      |
#| the Free Software Foundation, either version 3 of the License, or         |
#| (at your option) any later version.                                       |
#|                                                                           |
#| This program is distributed in the hope that it will be useful,           |
#| but WITHOUT ANY WARRANTY; without even the implied warranty of            |
#| MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              |
#| GNU General Public License for more details.                              |
#|                                                                           |
#| You should have received a copy of the GNU General Public License         |
#| along with this program. If not, see <http://www.gnu.org/licenses/>.      |
#+---------------------------------------------------------------------------+
#| @url      : http://www.netzob.org                                         |
#| @contact  : contact@netzob.org                                            |
#| @sponsors : Amossys, http://www.amossys.fr                                |
#|             Supélec, http://www.rennes.supelec.fr/ren/rd/cidre/           |
#+---------------------------------------------------------------------------+

#+---------------------------------------------------------------------------+
#| Standard library imports
#+---------------------------------------------------------------------------+
from gettext import gettext as _
import os
import logging

#+---------------------------------------------------------------------------+
#| Related third party imports
#+---------------------------------------------------------------------------+
from gi.repository import Gtk, Gdk
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from collections import OrderedDict

#+---------------------------------------------------------------------------+
#| Local application imports
#+---------------------------------------------------------------------------+
from netzob.Common.ResourcesConfiguration import ResourcesConfiguration
from netzob.UI.Vocabulary.Controllers.ResearchController import ResearchController
from netzob.UI.Vocabulary.Controllers.FilterMessagesController import FilterMessagesController
from netzob.UI.Vocabulary.Controllers.MessageTableController import MessageTableController
from netzob.Common.SignalsManager import SignalsManager
from netzob.Common.Type.TypeConvertor import TypeConvertor
from netzob.UI.Vocabulary.Controllers.MessagesDistributionController import MessagesDistributionController
from netzob.UI.Common.Controllers.MoveMessageController import MoveMessageController
from netzob.UI.Vocabulary.Controllers.VariableDisplayerController import VariableDisplayerController


class VocabularyView(object):
    SYMBOLLISTSTORE_SELECTED_COLUMN = 0
    SYMBOLLISTSTORE_TOPLEVEL_COLUMN = 1
    SYMBOLLISTSTORE_NAME_COLUMN = 2
    SYMBOLLISTSTORE_MESSAGE_COLUMN = 3
    SYMBOLLISTSTORE_FIELD_COLUMN = 4
    SYMBOLLISTSTORE_ID_COLUMN = 5

    SESSIONLISTSTORE_SELECTED_COLUMN = 0
    SESSIONLISTSTORE_TOPLEVEL_COLUMN = 1
    SESSIONLISTSTORE_NAME_COLUMN = 2
    SESSIONLISTSTORE_MESSAGE_COLUMN = 3
    SESSIONLISTSTORE_ID_COLUMN = 4

    SEQUENCELISTSTORE_SELECTED_COLUMN = 0
    SEQUENCELISTSTORE_TOPLEVEL_COLUMN = 1
    SEQUENCELISTSTORE_NAME_COLUMN = 2
    SEQUENCELISTSTORE_MESSAGE_COLUMN = 3
    SEQUENCELISTSTORE_ID_COLUMN = 4

    PROJECTPROPERTIESLISTSTORE_NAME_COLUMN = 0
    PROJECTPROPERTIESLISTSTORE_VALUE_COLUMN = 1
    PROJECTPROPERTIESLISTSTORE_EDITABLE_COLUMN = 2
    PROJECTPROPERTIESLISTSTORE_MODEL_COLUMN = 3

    SYMBOLPROPERTIESLISTSTORE_NAME_COLUMN = 0
    SYMBOLPROPERTIESLISTSTORE_VALUE_COLUMN = 1
    SYMBOLPROPERTIESLISTSTORE_EDITABLE_COLUMN = 2
    SYMBOLPROPERTIESLISTSTORE_MODEL_COLUMN = 3

    SESSIONPROPERTIESLISTSTORE_NAME_COLUMN = 0
    SESSIONPROPERTIESLISTSTORE_VALUE_COLUMN = 1
    SESSIONPROPERTIESLISTSTORE_EDITABLE_COLUMN = 2
    SESSIONPROPERTIESLISTSTORE_MODEL_COLUMN = 3

    SEQUENCEPROPERTIESLISTSTORE_NAME_COLUMN = 0
    SEQUENCEPROPERTIESLISTSTORE_VALUE_COLUMN = 1
    SEQUENCEPROPERTIESLISTSTORE_EDITABLE_COLUMN = 2
    SEQUENCEPROPERTIESLISTSTORE_MODEL_COLUMN = 3

    MESSAGEPROPERTIESLISTSTORE_NAME_COLUMN = 0
    MESSAGEPROPERTIESLISTSTORE_VALUE_COLUMN = 1
    MESSAGEPROPERTIESLISTSTORE_EDITABLE_COLUMN = 2
    MESSAGEPROPERTIESLISTSTORE_MODEL_COLUMN = 3

    FIELDPROPERTIESLISTSTORE_NAME_COLUMN = 0
    FIELDPROPERTIESLISTSTORE_VALUE_COLUMN = 1

    def __init__(self, controller):
        self.controller = controller
        self.netzob = self.controller.netzob
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(
            ResourcesConfiguration.getStaticResources(),
            "ui", "vocabulary",
            "vocabularyView.glade"))
        self._getObjects(self.builder, ["vocabularyPanel", "symbolListStore", "sessionListStore", "sequenceListStore",
                                        "concatSymbolButton", "deleteSymbolButton", "newMessageList",
                                        "sequenceAlignmentButton",
                                        "partitioningForceButton",
                                        "partitioningSimpleButton",
                                        "partitioningSmoothButton",
                                        "partitioningResetButton",
                                        "messagesDistributionButton",
                                        "projectTreeview", "symbolTreeview", "messageTreeview", "fieldTreeview",
                                        "projectPropertiesListstore", "symbolPropertiesListstore", "messagePropertiesListstore",
                                        "messageTableBox", "symbolListTreeView", "sessionListTreeView", "sequenceListTreeView",
                                        "symbolListTreeViewSelection", "sessionListTreeViewSelection", "sequenceListTreeViewSelection", 
                                        "messagesDistributionSymbolViewport", "messageTableBoxAndResearchBox"
                                        ])
        self._loadActionGroupUIDefinition()
        self.builder.connect_signals(self.controller)

        # List of currently displayed message tables
        self.messageTableList = []
        self.selectedMessageTable = None
        # add the netzobBegin label attribute
        self.netzobBegin = None
        # add the researchBar
        self.researchController = ResearchController(self.controller)
        self.messageTableBoxAndResearchBox.pack_end(self.researchController._view.researchBar, False, False, 0)
        self.researchController._view.research_format.set_active(4)
        self.researchController.hide()

        # add the filterBar
        self.filterMessagesController = FilterMessagesController(self.controller)
        self.messageTableBoxAndResearchBox.pack_end(self.filterMessagesController._view.filterBar, False, False, 0)
        self.filterMessagesController.hide()
        self.registerSignalListeners()

    def registerSignalListeners(self):
        # Register signal processing on toolbar elements
        signalManager = self.netzob.getSignalsManager()
        if signalManager is None:
            self.log.warning("No signal manager has been found.")
            return

        signalManager.attach(self.projectStatusHasChanged_cb, [SignalsManager.SIG_PROJECT_OPEN, SignalsManager.SIG_PROJECT_CLOSE])
        signalManager.attach(self.symbolCheckedHasChanged_cb, [SignalsManager.SIG_SYMBOLS_NONE_CHECKED, SignalsManager.SIG_SYMBOLS_SINGLE_CHECKED, SignalsManager.SIG_SYMBOLS_MULTIPLE_CHECKED])
        signalManager.attach(self.symbolSelectionHasChanged_cb, [SignalsManager.SIG_SYMBOLS_NO_SELECTION, SignalsManager.SIG_SYMBOLS_SINGLE_SELECTION, SignalsManager.SIG_SYMBOLS_MULTIPLE_SELECTION])
        signalManager.attach(self.fieldSelectionHasChanged_cb, [SignalsManager.SIG_FIELDS_NO_SELECTION, SignalsManager.SIG_FIELDS_SINGLE_SELECTION, SignalsManager.SIG_FIELDS_MULTIPLE_SELECTION])
        signalManager.attach(self.messageSelectionHasChanged_cb, [SignalsManager.SIG_MESSAGES_NO_SELECTION, SignalsManager.SIG_MESSAGES_SINGLE_SELECTION, SignalsManager.SIG_MESSAGES_MULTIPLE_SELECTION])

    def messageSelectionHasChanged_cb(self, signal):
        """messageSelectionHasChanged_cb:
            Callback executed when none, single or multiple messages are selected"""
        if signal == SignalsManager.SIG_MESSAGES_NO_SELECTION:
            self._actionGroup.get_action('moveMessagesToOtherSymbol').set_sensitive(False)
            self._actionGroup.get_action('deleteMessages').set_sensitive(False)

        elif signal == SignalsManager.SIG_MESSAGES_SINGLE_SELECTION:
            self._actionGroup.get_action('moveMessagesToOtherSymbol').set_sensitive(True)
            self._actionGroup.get_action('deleteMessages').set_sensitive(True)

        elif signal == SignalsManager.SIG_MESSAGES_MULTIPLE_SELECTION:
            self._actionGroup.get_action('moveMessagesToOtherSymbol').set_sensitive(True)
            self._actionGroup.get_action('deleteMessages').set_sensitive(True)

    def fieldSelectionHasChanged_cb(self, signal):
        """fieldSelectionHasChanhed_cb:
            Callback executed when none, single or multiple fields are selected."""
        if signal == SignalsManager.SIG_FIELDS_NO_SELECTION:
            self._actionGroup.get_action('concatField').set_sensitive(False)
            self._actionGroup.get_action('split').set_sensitive(False)
            self._actionGroup.get_action('editVariable').set_sensitive(False)
        elif signal == SignalsManager.SIG_FIELDS_SINGLE_SELECTION:
            self._actionGroup.get_action('concatField').set_sensitive(False)
            self._actionGroup.get_action('split').set_sensitive(True)
            self._actionGroup.get_action('editVariable').set_sensitive(True)
        elif signal == SignalsManager.SIG_FIELDS_MULTIPLE_SELECTION:
            self._actionGroup.get_action('concatField').set_sensitive(True)
            self._actionGroup.get_action('split').set_sensitive(False)
            self._actionGroup.get_action('editVariable').set_sensitive(False)

    def symbolCheckedHasChanged_cb(self, signal):
        """symbolCheckedHasChanged_cb:
        callback executed when none, one or multiple symbols are checked."""
        if signal == SignalsManager.SIG_SYMBOLS_NONE_CHECKED:
            self._actionGroup.get_action('partitioningSimple').set_sensitive(False)
            self._actionGroup.get_action('partitioningSmooth').set_sensitive(False)
            self._actionGroup.get_action('partitioningReset').set_sensitive(False)
            self._actionGroup.get_action('editVariable').set_sensitive(False)
            self._actionGroup.get_action('environmentDep').set_sensitive(False)
            self._actionGroup.get_action('messagesDistribution').set_sensitive(False)
            self._actionGroup.get_action('partitioningForce').set_sensitive(False)
            self._actionGroup.get_action('sequenceAlignment').set_sensitive(False)
        elif signal == SignalsManager.SIG_SYMBOLS_SINGLE_CHECKED or signal == SignalsManager.SIG_SYMBOLS_MULTIPLE_CHECKED:
            self._actionGroup.get_action('partitioningSimple').set_sensitive(True)
            self._actionGroup.get_action('partitioningSmooth').set_sensitive(True)
            self._actionGroup.get_action('partitioningReset').set_sensitive(True)
            self._actionGroup.get_action('environmentDep').set_sensitive(True)
            self._actionGroup.get_action('messagesDistribution').set_sensitive(True)
            self._actionGroup.get_action('partitioningForce').set_sensitive(True)
            self._actionGroup.get_action('sequenceAlignment').set_sensitive(True)
            if signal == SignalsManager.SIG_SYMBOLS_SINGLE_CHECKED:
                self._actionGroup.get_action('editVariable').set_sensitive(False)

    def symbolSelectionHasChanged_cb(self, signal):
        """symbolSelectionHasChanged_cb:
        callback executed when none, one or multiple symbols are selected."""
        if signal == SignalsManager.SIG_SYMBOLS_NO_SELECTION or signal == SignalsManager.SIG_SYMBOLS_MULTIPLE_SELECTION:
            self._actionGroup.get_action('filterMessages').set_sensitive(False)
        elif signal == SignalsManager.SIG_SYMBOLS_SINGLE_SELECTION:
            self._actionGroup.get_action('filterMessages').set_sensitive(True)

    def projectStatusHasChanged_cb(self, signal):
        """projectStatusHasChanged_cb:
        Callback executed when a signal is emitted."""

        actions = ["importMessagesFromFile",
                   "captureMessages",
                   "relationsViewer",
                   "searchMenu",
                   "searchText",
                   "variableTable",
                   "automaticToolMenu",
                   "manualToolMenu",
                   ]

        if signal == SignalsManager.SIG_PROJECT_OPEN:
            for action in actions:
                self._actionGroup.get_action(action).set_sensitive(True)

        elif signal == SignalsManager.SIG_PROJECT_CLOSE:
            for action in actions:
                self._actionGroup.get_action(action).set_sensitive(False)

    def _loadActionGroupUIDefinition(self):
        """Loads the action group and the UI definition of menu items
        . This method should only be called in the constructor"""
        # Load actions
        actionsBuilder = Gtk.Builder()
        actionsBuilder.add_from_file(os.path.join(
            ResourcesConfiguration.getStaticResources(),
            "ui", "vocabulary",
            "vocabularyActions.glade"))
        self._actionGroup = actionsBuilder.get_object("vocabularyActionGroup")
        actionsBuilder.connect_signals(self.controller)
        uiDefinitionFilePath = os.path.join(
            ResourcesConfiguration.getStaticResources(),
            "ui", "vocabulary",
            "vocabularyMenuToolbar.ui")
        with open(uiDefinitionFilePath, "r") as uiDefinitionFile:
            self._uiDefinition = uiDefinitionFile.read()

        # Attach actions from the vocabularyActionGroup to the small panel on top of symbols
        sequenceAlignmentAction = self._actionGroup.get_action('sequenceAlignment')
        self.sequenceAlignmentButton.set_related_action(sequenceAlignmentAction)

        partitioningForceAction = self._actionGroup.get_action('partitioningForce')
        self.partitioningForceButton.set_related_action(partitioningForceAction)

        partitioningSimpleAction = self._actionGroup.get_action('partitioningSimple')
        self.partitioningSimpleButton.set_related_action(partitioningSimpleAction)

        partitioningSmoothAction = self._actionGroup.get_action('partitioningSmooth')
        self.partitioningSmoothButton.set_related_action(partitioningSmoothAction)

        partitioningResetAction = self._actionGroup.get_action('partitioningReset')
        self.partitioningResetButton.set_related_action(partitioningResetAction)

        messagesDistributionAction = self._actionGroup.get_action('messagesDistribution')
        self.messagesDistributionButton.set_related_action(messagesDistributionAction)

    def _getObjects(self, builder, objectsList):
        for object in objectsList:
            setattr(self, object, builder.get_object(object))

    ## Mandatory view methods
    def getPanel(self):
        return self.vocabularyPanel

    # Return the actions
    def getActionGroup(self):
        return self._actionGroup

    # Return toolbar and menu
    def getMenuToolbarUIDefinition(self):
        return self._uiDefinition

    def updateListCapturerPlugins(self, pluginsExtensions):
        """Update the menu"""
        pluginMenu = self.netzob.view.uiManager.get_widget("/mainMenuBar/fileMenu/fileMenuAdditions/captureMessages").get_submenu()

        # Update the list of exporters
        for i in pluginMenu.get_children():
            pluginMenu.remove(i)

        for pluginExtension in pluginsExtensions:
            pluginEntry = Gtk.MenuItem(pluginExtension.menuText)
            pluginEntry.connect("activate", pluginExtension.executeAction, self)
            pluginMenu.append(pluginEntry)
        pluginMenu.show_all()

    def drag_data_received_event(self, widget, drag_context, x, y, data, info, time):
        """Callback executed when the user drops
        some data in the treeview of symbols."""
        receivedData = data.get_text()

        if widget is None:
            logging.debug("No widget selected, cannot move the message")
            return

        # retrieve the drop row
        path, position = widget.get_dest_row_at_pos(x, y)
        targetSymbol = None
        if path is not None:
            layerID = widget.get_model()[path][VocabularyView.SYMBOLLISTSTORE_ID_COLUMN]
            if layerID is not None:
                targetField = self.controller.getCurrentProject().getVocabulary().getFieldByID(layerID)
                targetSymbol = targetField.getSymbol()
        if targetSymbol is None:
            return

        if receivedData is not None and len(receivedData) > 2:
            if targetSymbol is not None and receivedData[:2] == "m:":
                for msgID in receivedData[2:].split(","):
                    message = self.controller.getCurrentProject().getVocabulary().getMessageByID(msgID)
                    # verify if the target symbol's regex is valid according to the message
                    if message is not None:
                        if targetSymbol.getField().isRegexValidForMessage(message):
                            self.controller.moveMessage(message, targetSymbol)
                        else:
                            self.drag_receivedMessages(targetSymbol, message)
                        self.updateSelectedMessageTable()
                        self.controller.updateLeftPanel()

    def drag_receivedMessages(self, targetSymbol, message):
        """Executed by the drop callback which has discovered
        some messages (identified by their ID) to be moved from their
        current symbol to the selected symbol"""
        if message is not None:
            moveMessageController = MoveMessageController(self.controller, [message], targetSymbol)
            moveMessageController.run()

    ## Message Tables management
    def addMessageTable(self):
        """ Create a new message table and selects it"""
        messageTableController = MessageTableController(self)
        messageTable = messageTableController.view
        self.messageTableList.append(messageTable)
        self.setSelectedMessageTable(messageTable)
        self.messageTableBox.pack_start(messageTable.getPanel(), True, True, 0)

    def removeMessageTable(self, messageTable):
        self.messageTableBox.remove(messageTable.getPanel())
        messageTable.destroy()
        self.messageTableList = [mTable for mTable in self.messageTableList
                                 if mTable != messageTable]
        # Select a new table in messageTable was the selected message table
        if len(self.messageTableList) > 0:
            self.setSelectedMessageTable(self.messageTableList[0])

    def removeAllMessageTables(self):
        for child in self.messageTableBox.get_children():
            self.messageTableBox.remove(child)

        self.messageTableList = []

    def emptyMessageTableDisplayingSymbols(self, symbolList):
        toBeRemovedTables = [mTable for mTable in self.messageTableList
                             if mTable.getDisplayedField() in symbolList]
        for mTable in toBeRemovedTables:
            mTable.setDisplayedField(None)

    def updateSelectedMessageTable(self):
        if self.selectedMessageTable is not None:
            self.selectedMessageTable.update()

    def updateMessageTableDisplayingSymbols(self, symbolList):
        toBeUpdatedTables = [mTable for mTable in self.messageTableList
                             if mTable.getDisplayedField() in symbolList]
        for mTable in toBeUpdatedTables:
            mTable.update()

    def setSelectedMessageTable(self, selectedMessageTable):
        """Set provided message table as selected"""

        if selectedMessageTable == self.selectedMessageTable:
            return

        # Update appearance of old and new selected message table
        if self.selectedMessageTable is not None:
            self.selectedMessageTable.setSelected(False)

        # Update current selected message table and
        self.selectedMessageTable = selectedMessageTable
        self.selectedMessageTable.setSelected(True)

    def setDisplayedFieldInSelectedMessageTable(self, symbol):
        """Show the definition of provided symbol on the selected
        message table"""
        logging.debug("Update the displayed symbol in selected table message")

        # Open a message table if none is available
        if len(self.messageTableList) == 0:
            self.addMessageTable()

        # if a message table is selected we update its symbol
        self.selectedMessageTable.setDisplayedField(symbol)

    def getDisplayedFieldInSelectedMessageTable(self):
        if self.selectedMessageTable is None:
            return None
        else:
            return self.selectedMessageTable.displayedField

    def getCurrentProject(self):
        return self.controller.netzob.getCurrentProject()

    def getDisplayedField(self):
        if self.selectedMessageTable is None:
            return None
        return self.selectedMessageTable.getDisplayedField()
