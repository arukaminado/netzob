from gettext import gettext as _
import os
import uuid
import logging

from gi.repository import Gtk, Gdk
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject

from netzob.UI.Vocabulary.Views.NewVocabularyView import NewVocabularyView
from netzob.Common.ResourcesConfiguration import ResourcesConfiguration
from netzob.Common.Symbol import Symbol

class NewVocabularyController(object):

    def __init__(self, netzob):
        self.netzob = netzob
        self._view = NewVocabularyView(self)
        self.log = logging.getLogger(__name__)
        self.view.update()

    @property
    def view(self):
        return self._view

    ## Symbol List toolbar callbacks
    def selectAllSymbolsButton_clicked_cb(self, toolButton):
        """
        select all the symbol in the symbol list
        @type  widget: boolean
        @param widget: if selected symbol
        """
        for row in self.view.symbolListStore:
            row[self.view.SYMBOLLISTSTORE_SELECTED_COLUMN] = True
        self.view.updateSymbolListToolbar()

    def unselectAllSymbolsButton_clicked_cb(self, toolButton):
        """
        unselect all the symbol in the symbol list
        @type  widget: boolean
        @param widget: if selected symbol
        """
        for row in self.view.symbolListStore:
            row[self.view.SYMBOLLISTSTORE_SELECTED_COLUMN] = False
        self.view.updateSymbolListToolbar()

    def createSymbolButton_clicked_cb(self, toolButton):
        builder2 = Gtk.Builder()
        builder2.add_from_file(os.path.join(
            ResourcesConfiguration.getStaticResources(),
            "ui",
            "dialogbox.glade"))
        dialog = builder2.get_object("createsymbol")
        #button apply
        applybutton = builder2.get_object("button1")
        applybutton.set_sensitive(False)
        dialog.add_action_widget(applybutton, 0)
        #button cancel
        cancelbutton = builder2.get_object("button435")
        dialog.add_action_widget(cancelbutton, 1)
        #disable apply button if no text
        entry = builder2.get_object("entry1")
        entry.connect("changed", self.entry_disableButtonIfEmpty_cb, applybutton)
        #run the dialog window and wait for the result
        result = dialog.run()

        if (result == 0):
            #apply
            newSymbolName = entry.get_text()
            newSymbolId = str(uuid.uuid4())
            self.log.debug("A new symbol will be created with the given name : {0}".format(newSymbolName))
            currentProject = self.netzob.getCurrentProject()
            newSymbol = Symbol(newSymbolId, newSymbolName, currentProject)
            currentProject.getVocabulary().addSymbol(newSymbol)
            self.view.update()
            dialog.destroy()
        if (result == 1):
            #cancel
            dialog.destroy()

    def entry_disableButtonIfEmpty_cb(self, widget, button):
        if(len(widget.get_text()) > 0):
            button.set_sensitive(True)
        else:
            button.set_sensitive(False)

    def concatSymbolButton_clicked_cb(self, toolButton):
        #concat the message of all selected symbols
        symbols = self.view.getCheckedSymbolList()
        message = []
        for sym in symbols:
            message.extend(sym.getMessages())
        #give the message to the first symbol
        concatSymbol = symbols[0]
        concatSymbol.setMessages(message)
        currentProject = self.netzob.getCurrentProject()
        #delete all selected symbols
        self.view.emptyMessageTableDisplayingSymbols(symbols[1:])
        for sym in symbols:
            currentProject.getVocabulary().removeSymbol(sym)
        #add the concatenate symbol
        currentProject.getVocabulary().addSymbol(concatSymbol)
        #refresh view
        self.view.updateMessageTableDisplayingSymbols([concatSymbol])
        self.view.update()

    #possible que si on selectionne un unique symbol
    def renameSymbolButton_clicked_cb(self, widget):
        symbol = self.view.getCheckedSymbolList()[0]
        builder2 = Gtk.Builder()
        builder2.add_from_file(os.path.join(
            ResourcesConfiguration.getStaticResources(),
            "ui",
            "dialogbox.glade"))
        dialog = builder2.get_object("renamesymbol")
        dialog.set_title("Rename the symbol " + symbol.getName())

        #button apply
        applybutton = builder2.get_object("button10")
        applybutton.set_sensitive(False)
        dialog.add_action_widget(applybutton, 0)
        #button cancel
        cancelbutton = builder2.get_object("button2")
        dialog.add_action_widget(cancelbutton, 1)
        #disable apply button if no text
        entry = builder2.get_object("entry3")
        entry.connect("changed", self.entry_disableButtonIfEmpty_cb, applybutton)
        #run the dialog window and wait for the result
        result = dialog.run()

        if (result == 0):
            #apply
            newSymbolName = entry.get_text()
            self.log.debug(_("Renamed symbol {0} to {1}").format(symbol.getName(), newSymbolName))
            currentProject = self.netzob.getCurrentProject()
            currentProject.getVocabulary().getSymbolByID(symbol.getID()).setName(newSymbolName)
            self.view.update()
            self.view.updateMessageTableDisplayingSymbols([symbol])
            dialog.destroy()
        if (result == 1):
            #cancel
            dialog.destroy()

    def deleteSymbolButton_clicked_cb(self, toolButton):
        # Delete symbol
        for sym in self.view.getCheckedSymbolList():
            currentProject = self.netzob.getCurrentProject()
            currentVocabulary = currentProject.getVocabulary()
            for mess in sym.getMessages():
                currentVocabulary.removeMessage(mess)
            currentVocabulary.removeSymbol(sym)
            self.view.emptyMessageTableDisplayingSymbols([sym])
        # Update view
        self.view.update()

    def newMessageTableButton_clicked_cb(self, toolButton):
        self.view.addMessageTable()

    def toggleCellRenderer_toggled_cb(self, widget, buttonid):
        model = self.view.symbolListStore
        model[buttonid][0] = not model[buttonid][0]
        self.view.updateSymbolListToolbar()

    def symbolListTreeViewSelection_changed_cb(self, selection):
        print "Selection changed"
        model, iter = selection.get_selected()
        currentVocabulary = self.netzob.getCurrentProject().getVocabulary()
        if iter is not None:
            symID = model[iter][self.view.SYMBOLLISTSTORE_ID_COLUMN]
            symbol = currentVocabulary.getSymbolByID(symID)
            self.view.setDisplayedSymbolInSelectedMessageTable(symbol)

################ TO BE FIXED
    def button_newview_cb(self, widget):
        self.focus = self.addSpreadSheet("empty", 0)
        self.focus.idsymbol = None


    def button_closeview_cb(self, widget, spreadsheet):
        spreadsheet.destroy()

        #refresh focus
        if self.focus.get_object("spreadsheet") == spreadsheet :
            self.focus = None

    def selectiontreeview_switchSymbol_cb(self, widget):
        if self.focus != None :
            model, itera = widget.get_selected()
            row = model[itera]
            self.focus.idsymbol = row[6]
            #set the text for label
            self.focus.get_object("label1").set_text(row[1])
            #set field for treeview
            '''
            treemessage = self.focus.get_object("treemessage")
            column = Gtk.TreeViewColumn('Column Title', Gtk.CellRenderer(), text=0)
            treemessage.append_column(column)
            #add the message to the store
            messagestore = self.focus.get_object("liststoremessage")
            for mess in self.getCurrentProject().getVocabulary().getMessages():
                m = messagestore.append()
                messagestore.set(m,0,mess)
            '''

        #reste a switcher les messages du treeview

    def button_focusview_cb(self, widget, builder):
        self.focus = builder
###############
