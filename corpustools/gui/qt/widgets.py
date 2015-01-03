import string
from itertools import combinations

from .imports import *

from .views import TableWidget

from .models import SegmentPairModel, EnvironmentModel, FilterModel

class ThumbListWidget(QListWidget):
    def __init__(self, ordering, parent=None):
        super(ThumbListWidget, self).__init__(parent)
        self.ordering = ordering
        #self.setIconSize(QSize(124, 124))
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)


    def dropEvent(self, event):
        event.setDropAction(Qt.MoveAction)
        super(ThumbListWidget, self).dropEvent(event)

class FactorFilter(QWidget):
    def __init__(self, attribute,parent=None):

        QWidget.__init__(self,parent)

        layout = QHBoxLayout()
        levels = attribute.range
        self.sourceWidget = ThumbListWidget(levels)
        for l in levels:
            self.sourceWidget.addItem(l)

        sourceFrame = QGroupBox('Available levels')
        l = QVBoxLayout()
        l.addWidget(self.sourceWidget)
        sourceFrame.setLayout(l)

        layout.addWidget(sourceFrame)

        buttonLayout = QVBoxLayout()
        self.addOneButton = QPushButton('>')
        self.addOneButton.clicked.connect(self.addOne)
        self.addAllButton = QPushButton('>>')
        self.addAllButton.clicked.connect(self.addAll)

        self.clearOneButton = QPushButton('<')
        self.clearOneButton.clicked.connect(self.clearOne)
        self.clearAllButton = QPushButton('<<')
        self.clearAllButton.clicked.connect(self.clearAll)

        buttonLayout.addWidget(self.addOneButton, alignment = Qt.AlignCenter)
        buttonLayout.addWidget(self.addAllButton, alignment = Qt.AlignCenter)
        buttonLayout.addWidget(self.clearOneButton, alignment = Qt.AlignCenter)
        buttonLayout.addWidget(self.clearAllButton, alignment = Qt.AlignCenter)

        buttonFrame = QFrame()
        buttonFrame.setLayout(buttonLayout)
        layout.addWidget(buttonFrame, alignment = Qt.AlignCenter)

        self.targetWidget = ThumbListWidget(levels)

        targetFrame = QGroupBox('Included levels')
        l = QVBoxLayout()
        l.addWidget(self.targetWidget)
        targetFrame.setLayout(l)

        layout.addWidget(targetFrame)

        self.setLayout(layout)

    def addOne(self):
        items = self.sourceWidget.selectedItems()
        for i in items:
            item = self.sourceWidget.takeItem(self.sourceWidget.row(i))
            self.targetWidget.addItem(item)

    def addAll(self):
        items = [self.sourceWidget.item(i) for i in range(self.sourceWidget.count())]
        for i in items:
            item = self.sourceWidget.takeItem(self.sourceWidget.row(i))
            self.targetWidget.addItem(item)

    def clearOne(self):
        items = self.targetWidget.selectedItems()
        for i in items:
            item = self.targetWidget.takeItem(self.targetWidget.row(i))
            self.sourceWidget.addItem(item)

    def clearAll(self):
        items = [self.targetWidget.item(i) for i in range(self.targetWidget.count())]
        for i in items:
            item = self.targetWidget.takeItem(self.targetWidget.row(i))
            self.sourceWidget.addItem(item)

    def value(self):
        items = [self.targetWidget.item(i).text() for i in range(self.targetWidget.count())]
        return items

class NumericFilter(QWidget):
    conditionalDisplay = ('equals','does not equal','greater than',
                    'greater than or equal to', 'less than',
                    'less than or equal to')
    conditionals = ('__eq__', '__neq__', '__gt__', '__gte__', '__lt__', '__lte__')
    def __init__(self,parent=None):

        QWidget.__init__(self,parent)

        layout = QHBoxLayout()

        self.conditionalSelect = QComboBox()
        for c in self.conditionalDisplay:
            self.conditionalSelect.addItem(c)

        layout.addWidget(self.conditionalSelect)

        self.valueEdit = QLineEdit()

        layout.addWidget(self.valueEdit)

        self.setLayout(layout)

    def value(self):
        ind = self.conditionalSelect.currentIndex()

        return self.conditionals[ind], self.valueEdit.text()

class AttributeFilterDialog(QDialog):
    def __init__(self, attributes,parent=None):
        QDialog.__init__(self,parent)

        self.attributes = list()

        layout = QVBoxLayout()

        mainlayout = QHBoxLayout()

        self.selectWidget = QComboBox()
        for a in attributes:
            if a.att_type in ['factor','numeric']:
                self.attributes.append(a)
                self.selectWidget.addItem(a.display_name)

        self.selectWidget.currentIndexChanged.connect(self.updateFrame)

        selectFrame = QGroupBox('Attribute to filter')

        selectlayout = QVBoxLayout()
        selectlayout.addWidget(self.selectWidget)
        selectFrame.setLayout(selectlayout)

        mainlayout.addWidget(selectFrame)


        self.filterWidget = NumericFilter()
        filterLayout = QVBoxLayout()
        filterLayout.addWidget(self.filterWidget)

        self.filterFrame = QGroupBox('Filter')
        self.filterFrame.setLayout(filterLayout)

        mainlayout.addWidget(self.filterFrame)

        mainframe = QFrame()

        mainframe.setLayout(mainlayout)

        layout.addWidget(mainframe)

        self.oneButton = QPushButton('Add')
        self.anotherButton = QPushButton('Add and create another')
        self.cancelButton = QPushButton('Cancel')
        acLayout = QHBoxLayout()
        acLayout.addWidget(self.oneButton, alignment = Qt.AlignLeft)
        acLayout.addWidget(self.anotherButton, alignment = Qt.AlignLeft)
        acLayout.addWidget(self.cancelButton, alignment = Qt.AlignLeft)
        self.oneButton.clicked.connect(self.one)
        self.anotherButton.clicked.connect(self.another)
        self.cancelButton.clicked.connect(self.reject)

        acFrame = QFrame()
        acFrame.setLayout(acLayout)

        layout.addWidget(acFrame, alignment = Qt.AlignLeft)

        self.setLayout(layout)
        #self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Create {}'.format(parent.name))

    def updateFrame(self):
        index = self.selectWidget.currentIndex()
        a = self.attributes[index]
        self.filterWidget.deleteLater()
        if a.att_type == 'numeric':
            self.filterWidget = NumericFilter()
            self.filterFrame.layout().addWidget(self.filterWidget)
        elif a.att_type == 'factor':
            self.filterWidget = FactorFilter(a)
            self.filterFrame.layout().addWidget(self.filterWidget)
        self.resize(self.sizeHint())

    def one(self):
        self.addOneMore = False
        self.accept()

    def another(self):
        self.addOneMore = True
        self.accept()

    def accept(self):
        index = self.selectWidget.currentIndex()
        a = self.attributes[index]
        val = self.filterWidget.value()
        if a.att_type == 'numeric':
            comp = val[0]
            try:
                value = float(val[1])
            except ValueError:
                reply = QMessageBox.critical(self,
                        "Invalid information", "Please specify a number.")
                return
            if (comp in ['__gt__', '__gte__'] and value > a.range[1]) or \
                (comp in ['__lt__','__lte__'] and value < a.range[0]) or \
                (comp in ['__eq__','__neq__'] and (value < a.range[0] or value > a.range[1])):
                reply = QMessageBox.critical(self,
                        "Invalid information", "The value specified ({}) for column '{}' is outside its range of {}-{}.".format(value,str(a),a.range[0],a.range[1]))
                return
            self.filter = (a, comp, value)
        elif a.att_type == 'factor':
            self.filter = (a, val)

        QDialog.accept(self)

    def reject(self):
        self.addOneMore = False
        QDialog.reject(self)

class AttributeFilterWidget(QGroupBox):
    name = 'filter'
    def __init__(self, corpus, parent = None):
        QGroupBox.__init__(self,'Filter corpus',parent)
        self.attributes = corpus.attributes

        vbox = QVBoxLayout()

        self.addButton = QPushButton('Add {}'.format(self.name))
        self.addButton.clicked.connect(self.filtPopup)
        self.removeButton = QPushButton('Remove selected {}s'.format(self.name))
        self.removeButton.clicked.connect(self.removeFilt)
        self.addButton.setAutoDefault(False)
        self.addButton.setDefault(False)
        self.removeButton.setAutoDefault(False)
        self.removeButton.setDefault(False)

        self.table = TableWidget()
        self.table.setModel(FilterModel())
        self.table.resizeColumnsToContents()

        vbox.addWidget(self.addButton)
        vbox.addWidget(self.removeButton)
        vbox.addWidget(self.table)

        self.setLayout(vbox)

    def filtPopup(self):
        dialog = AttributeFilterDialog(self.attributes,self)
        addOneMore = True
        while addOneMore:
            result = dialog.exec_()
            if result:
                self.table.model().addRow([dialog.filter])
            addOneMore = dialog.addOneMore

    def removeFilt(self):
        select = self.table.selectionModel()
        if select.hasSelection():
            selected = select.selectedRows()
            for s in selected:
                self.table.model().removeRow(s.row())

    def value(self):
        return [x[0] for x in self.table.model().filters]


class TierWidget(QGroupBox):
    def __init__(self, corpus, parent = None, include_spelling = False):
        QGroupBox.__init__(self,'Tier',parent)

        layout = QVBoxLayout()

        self.tierSelect = QComboBox()
        self.atts = list()
        if include_spelling:
            self.atts.append(corpus.attributes[0])
            self.tierSelect.addItem(corpus.attributes[0].display_name)
        for a in corpus.attributes:
            if corpus.has_transcription and a.att_type == 'tier':
                self.atts.append(a)
                self.tierSelect.addItem(a.display_name)
        layout.addWidget(self.tierSelect)
        self.setLayout(layout)

    def value(self):
        index = self.tierSelect.currentIndex()
        return self.atts[index].name

    def displayValue(self):
        index = self.tierSelect.currentIndex()
        return self.atts[index].display_name

class PunctuationWidget(QGroupBox):
    def __init__(self,parent = None):
        QGroupBox.__init__(self,'Punctuation to ignore',parent)

        self.btnGroup = QButtonGroup()
        self.btnGroup.setExclusive(False)
        layout = QVBoxLayout()
        box = QGridLayout()

        row = 0
        col = 0
        for s in string.punctuation:
            btn = QPushButton(s)
            btn.setCheckable(True)
            btn.setAutoExclusive(False)
            btn.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
            btn.setMaximumWidth(btn.fontMetrics().boundingRect(s).width() + 14)

            box.addWidget(btn,row,col)
            self.btnGroup.addButton(btn)
            col += 1
            if col > 11:
                col = 0
                row += 1
        boxFrame = QFrame()
        boxFrame.setLayout(box)
        layout.addWidget(boxFrame)

        buttonlayout = QHBoxLayout()
        self.checkAll = QPushButton('Check all')
        self.checkAll.clicked.connect(self.check)
        self.uncheckAll = QPushButton('Uncheck all')
        self.uncheckAll.clicked.connect(self.uncheck)
        buttonlayout.addWidget(self.checkAll, alignment = Qt.AlignLeft)
        buttonlayout.addWidget(self.uncheckAll, alignment = Qt.AlignLeft)
        buttonframe = QFrame()
        buttonframe.setLayout(buttonlayout)

        layout.addWidget(buttonframe)
        self.setLayout(layout)

    def check(self):
        for b in self.btnGroup.buttons():
            b.setChecked(True)

    def uncheck(self):
        for b in self.btnGroup.buttons():
            b.setChecked(False)

    def value(self):
        value = []
        for b in self.btnGroup.buttons():
            if b.isChecked():
                value.append(b.text())
        return value

class DigraphDialog(QDialog):
    def __init__(self, characters, parent = None):
        QDialog.__init__(self, parent)
        layout = QFormLayout()
        self.digraphLine = QLineEdit()
        layout.addRow(QLabel('Digraph'),self.digraphLine)
        symbolframe = QGroupBox('Characters')
        box = QGridLayout()

        row = 0
        col = 0
        for s in characters:
            btn = QPushButton(s)
            btn.clicked.connect(self.addCharacter)
            btn.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
            btn.setMaximumWidth(btn.fontMetrics().boundingRect(s).width() + 14)

            box.addWidget(btn,row,col)
            col += 1
            if col > 11:
                col = 0
                row += 1
        symbolframe.setLayout(box)
        layout.addRow(symbolframe)
        self.oneButton = QPushButton('Add')
        self.anotherButton = QPushButton('Add and create another')
        self.cancelButton = QPushButton('Cancel')
        acLayout = QHBoxLayout()
        acLayout.addWidget(self.oneButton, alignment = Qt.AlignLeft)
        acLayout.addWidget(self.anotherButton, alignment = Qt.AlignLeft)
        acLayout.addWidget(self.cancelButton, alignment = Qt.AlignLeft)
        self.oneButton.clicked.connect(self.one)
        self.anotherButton.clicked.connect(self.another)
        self.cancelButton.clicked.connect(self.reject)

        acFrame = QFrame()
        acFrame.setLayout(acLayout)

        layout.addRow(acFrame)
        self.setLayout(layout)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Construct Digraph')

    def addCharacter(self):
        self.digraphLine.setText(self.digraphLine.text()+self.sender().text())

    def one(self):
        self.addOneMore = False
        self.accept()

    def another(self):
        self.addOneMore = True
        self.accept()

    def value(self):
        return self.digraphLine.text()

    def reject(self):
        self.addOneMore = False
        QDialog.reject(self)



class DigraphWidget(QGroupBox):
    def __init__(self,parent = None):
        self._parent = parent
        QGroupBox.__init__(self,'Digraphs',parent)
        layout = QVBoxLayout()

        self.editField = QLineEdit()
        layout.addWidget(self.editField)
        self.button = QPushButton('Construct a digraph')
        self.button.clicked.connect(self.construct)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def construct(self):
        minus = set(self._parent.ignoreList())
        wd, td = self._parent.delimiters()
        delims = []
        if wd is None:
            delims.extend([' ','\t','\n'])
        else:
            delims.append(wd)
        if td is not None:
            delims.append(td)
        minus.update(delims)
        possible = sorted(self._parent.characters - minus, key = lambda x: x.lower())
        dialog = DigraphDialog(possible,self)
        addOneMore = True
        while addOneMore:
            if dialog.exec_():
                v = dialog.value()
                if v != '' and v not in self.value():
                    val = self.value() + [v]
                    self.editField.setText(','.join(val))
            dialog.digraphLine.setText('')
            addOneMore = dialog.addOneMore


    def value(self):
        text = self.editField.text()
        values = [x.strip() for x in text.split(',') if x.strip() != '']
        return values

class FileWidget(QFrame):
    def __init__(self,title,filefilter,parent=None):
        QFrame.__init__(self,parent)

        self.title = title

        self.filefilter = filefilter

        pathLayout = QHBoxLayout()
        self.pathEdit = QLineEdit()
        pathButton = QPushButton('Choose file...')
        pathButton.setAutoDefault(False)
        pathButton.setDefault(False)
        pathButton.clicked.connect(self.pathSet)
        pathLayout.addWidget(self.pathEdit)
        pathLayout.addWidget(pathButton)
        self.setLayout(pathLayout)

        self.textChanged = self.pathEdit.textChanged

    def pathSet(self):
        filename = QFileDialog.getOpenFileName(self,self.title, filter=self.filefilter)
        if filename:
            self.pathEdit.setText(filename[0])

    def value(self):
        return self.pathEdit.text()

class SaveFileWidget(QFrame):
    def __init__(self,title,filefilter,parent=None):
        QFrame.__init__(self,parent)

        self.title = title

        self.filefilter = filefilter

        pathLayout = QHBoxLayout()
        self.pathEdit = QLineEdit()
        pathButton = QPushButton('Choose file...')
        pathButton.setAutoDefault(False)
        pathButton.setDefault(False)
        pathButton.clicked.connect(self.pathSet)
        pathLayout.addWidget(self.pathEdit)
        pathLayout.addWidget(pathButton)
        self.setLayout(pathLayout)

        self.textChanged = self.pathEdit.textChanged

    def pathSet(self):
        filename = QFileDialog.getSaveFileName(self,self.title, filter=self.filefilter)
        if filename:
            self.pathEdit.setText(filename[0])

    def value(self):
        return self.pathEdit.text()

class DirectoryWidget(QFrame):
    def __init__(self,parent=None):
        QFrame.__init__(self,parent)

        pathLayout = QHBoxLayout()
        self.pathEdit = QLineEdit()
        pathButton = QPushButton('Choose directory...')
        pathButton.setAutoDefault(False)
        pathButton.setDefault(False)
        pathButton.clicked.connect(self.pathSet)
        pathLayout.addWidget(self.pathEdit)
        pathLayout.addWidget(pathButton)
        self.setLayout(pathLayout)

        self.textChanged = self.pathEdit.textChanged

    def pathSet(self):
        filename = QFileDialog.getExistingDirectory(self,"Choose a directory")
        if filename:
            self.pathEdit.setText(filename)

    def value(self):
        return self.pathEdit.text()

class InventoryTable(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)
        try:
            self.horizontalHeader().setSectionsClickable(False)
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.verticalHeader().setSectionsClickable(False)
            self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        except AttributeError:
            self.horizontalHeader().setClickable(False)
            self.horizontalHeader().setResizeMode(QHeaderView.Fixed)
            self.verticalHeader().setClickable(False)
            self.verticalHeader().setResizeMode(QHeaderView.Fixed)

        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def resize(self):
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        hor = self.horizontalHeader()
        ver = self.verticalHeader()
        width = ver.sizeHint().width()
        for i in range(hor.count()):
            width += hor.sectionSize(i)
        height = hor.sizeHint().height()
        for i in range(ver.count()):
            height += ver.sectionSize(i)
        self.setFixedSize(width, height)


class InventoryBox(QGroupBox):
    consonantColumns = ['Labial','Labiodental','Dental','Alveolar','Alveopalatal','Retroflex',
                    'Palatal','Velar','Uvular','Pharyngeal','Epiglottal','Glottal']

    consonantRows = ['Stop','Nasal','Fricative','Affricate','Approximate','Trill','Tap',
                    'Lateral fricative','Lateral approximate','Lateral flap']

    vowelColumns = ['Front','Near front','Central','Near back','Back']

    vowelRows = ['Close','Near close','Close mid','Mid','Open mid','Near open','Open']

    def __init__(self, title,inventory,parent=None):
        QGroupBox.__init__(self,title,parent)

        self.inventory = inventory
        #find cats
        consColumns = set()
        consRows = set()
        vowColumns = set()
        vowRows = set()
        for s in self.inventory:
            c = s.category
            if c is not None:
                if c[0] == 'Vowel':
                    vowColumns.add(c[2])
                    vowRows.add(c[1])
                elif c[0] == 'Consonant':
                    consColumns.add(c[1])
                    consRows.add(c[2])

        self.btnGroup = QButtonGroup()
        self.btnGroup.setExclusive(False)
        if len(consColumns) and len(vowColumns):
            box = QVBoxLayout()
            smallbox = QVBoxLayout()
            cons = QGroupBox('Consonants')
            consBox = QVBoxLayout()
            consTable = InventoryTable()
            consBox.addWidget(consTable)
            cons.setLayout(consBox)

            consColumns = [ x for x in self.consonantColumns if x in consColumns]
            consColMapping = {x:i for i,x in enumerate(consColumns)}
            consRows = [ x for x in self.consonantRows if x in consRows]
            consRowMapping = {x:i for i,x in enumerate(consRows)}

            consTable.setColumnCount(len(consColumns))
            consTable.setRowCount(len(consRows))
            consTable.setHorizontalHeaderLabels(consColumns)
            consTable.setVerticalHeaderLabels(consRows)

            for i in range(len(consColumns)):
                for j in range(len(consRows)):
                    wid = QWidget()
                    b = QGridLayout()
                    b.setAlignment(Qt.AlignCenter)
                    b.setContentsMargins(0, 0, 0, 0)
                    l = QWidget()
                    lb = QVBoxLayout()
                    lb.setAlignment(Qt.AlignCenter)
                    lb.setContentsMargins(0, 0, 0, 0)
                    lb.setSpacing(0)
                    l.setLayout(lb)
                    b.addWidget(l,0,0, alignment = Qt.AlignCenter)
                    r = QWidget()
                    rb = QVBoxLayout()
                    rb.setAlignment(Qt.AlignCenter)
                    rb.setContentsMargins(0, 0, 0, 0)
                    rb.setSpacing(0)
                    r.setLayout(rb)
                    b.addWidget(r,0,1, alignment = Qt.AlignCenter)
                    wid.setLayout(b)
                    consTable.setCellWidget(j,i,wid)

            vow = QGroupBox('Vowels')
            vowBox = QGridLayout()
            vowBox.setAlignment(Qt.AlignTop)
            vowTable = InventoryTable()
            vowBox.addWidget(vowTable,0, Qt.AlignLeft|Qt.AlignTop)
            vow.setLayout(vowBox)
            vowColumns = [ x for x in self.vowelColumns if x in vowColumns]
            vowColMapping = {x:i for i,x in enumerate(vowColumns)}
            vowRows = [ x for x in self.vowelRows if x in vowRows]
            vowRowMapping = {x:i for i,x in enumerate(vowRows)}

            vowTable.setColumnCount(len(vowColumns))
            vowTable.setRowCount(len(vowRows) + 1)
            vowTable.setHorizontalHeaderLabels(vowColumns)
            vowTable.setVerticalHeaderLabels(vowRows + ['Diphthongs'])

            for i in range(len(vowColumns)):
                for j in range(len(vowRows)):
                    wid = QWidget()
                    b = QGridLayout()
                    b.setAlignment(Qt.AlignCenter)
                    b.setContentsMargins(0, 0, 0, 0)
                    l = QWidget()
                    lb = QVBoxLayout()
                    lb.setAlignment(Qt.AlignCenter)
                    lb.setContentsMargins(0, 0, 0, 0)
                    lb.setSpacing(0)
                    l.setLayout(lb)
                    b.addWidget(l,0,0, alignment = Qt.AlignCenter)
                    r = QWidget()
                    rb = QVBoxLayout()
                    rb.setAlignment(Qt.AlignCenter)
                    rb.setContentsMargins(0, 0, 0, 0)
                    rb.setSpacing(0)
                    r.setLayout(rb)
                    b.addWidget(r,0,1, alignment = Qt.AlignCenter)

                    wid.setLayout(b)
                    vowTable.setCellWidget(j,i,wid)

            vowTable.setSpan(len(vowRows),0,1,len(vowColumns))
            wid = QWidget()
            diphBox = QHBoxLayout()
            diphBox.setAlignment(Qt.AlignCenter)
            diphBox.setContentsMargins(0, 0, 0, 0)
            wid.setLayout(diphBox)
            vowTable.setCellWidget(len(vowRows),0,wid)

            unk = QGroupBox('Other')
            unkBox = QGridLayout()
            unk.setLayout(unkBox)

            unkRow = 0
            unkCol = -1
            for s in inventory:
                cat = s.category
                btn = QPushButton(s.symbol)
                btn.setCheckable(True)
                btn.setAutoExclusive(False)
                btn.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                btn.setMaximumWidth(btn.fontMetrics().boundingRect(s.symbol).width() + 14)
                btn.setMaximumHeight(btn.fontMetrics().boundingRect(s.symbol).height() + 14)
                btn.setMinimumWidth(btn.fontMetrics().boundingRect(s.symbol).width() + 14)
                btn.setMinimumHeight(btn.fontMetrics().boundingRect(s.symbol).height() + 14)
                self.btnGroup.addButton(btn)
                if cat is None:
                    unkCol += 1
                    if unkCol > 11:
                        unkCol = 0
                        unkRow += 1
                    unkBox.addWidget(btn,unkRow,unkCol)

                elif cat[0] == 'Vowel':
                    col = vowColMapping[cat[2]]
                    row = vowRowMapping[cat[1]]
                    if cat[3] == 'Unrounded':
                        colTwo = 0
                    else:
                        colTwo = 1
                    cell = vowTable.cellWidget(row,col)

                    cell.layout().addWidget(btn,0,colTwo)
                elif cat[0] == 'Consonant':
                    col = consColMapping[cat[1]]
                    row = consRowMapping[cat[2]]
                    if cat[3] == 'Voiceless':
                        colTwo = 0
                    else:
                        colTwo = 1
                    cell = consTable.cellWidget(row,col).layout().itemAtPosition(0,colTwo).widget()

                    cell.layout().addWidget(btn, alignment = Qt.AlignCenter)
                    cell.setFixedSize(cell.sizeHint())
                elif cat[0] == 'Diphthong':
                    diphBox.addWidget(btn)
            consTable.resize()
            vowTable.resize()
            smallbox.addWidget(cons)

            smallbox.addWidget(vow)
            b = QFrame()
            b.setLayout(smallbox)
            box.addWidget(b, alignment = Qt.AlignLeft | Qt.AlignTop)
            box.addWidget(unk, alignment = Qt.AlignLeft | Qt.AlignTop)
        else:
            box = QGridLayout()

            row = 0
            col = 0
            for s in inventory:
                btn = QPushButton(s.symbol)
                btn.setCheckable(True)
                btn.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                btn.setMaximumWidth(btn.fontMetrics().boundingRect(s.symbol).width() + 14)

                box.addWidget(btn,row,col)
                self.btnGroup.addButton(btn)
                col += 1
                if col > 11:
                    col = 0
                    row += 1

        self.setLayout(box)

    def clearAll(self):
        reexc = self.btnGroup.exclusive()
        if reexc:
            self.setExclusive(False)
        for btn in self.btnGroup.buttons():
            btn.setChecked(False)
        if reexc:
            self.setExclusive(True)

    def setExclusive(self, b):
        self.btnGroup.setExclusive(b)
        for btn in self.btnGroup.buttons():
            btn.setAutoExclusive(b)

    def value(self):
        if self.btnGroup.exclusive():
            checked = self.btnGroup.checkedButton()
            if checked is None:
                return ''
            return checked.text()
        else:
            value = []
            for b in self.btnGroup.buttons():
                if b.isChecked():
                    value.append(b.text())
            return value

class FeatureBox(QGroupBox):
    def __init__(self, title,inventory,parent=None):
        QGroupBox.__init__(self,title,parent)

        self.inventory = inventory
        self.inspectInventory()
        layout = QHBoxLayout()

        self.featureList = QListWidget()

        for f in self.features:
            self.featureList.addItem(f)
        layout.addWidget(self.featureList)

        buttonLayout = QVBoxLayout()
        buttonLayout.setSpacing(0)
        self.buttons = list()
        for v in self.values:
            b = QPushButton('Add [{}feature]'.format(v))
            b.value = v
            b.clicked.connect(self.addFeature)
            buttonLayout.addWidget(b, alignment = Qt.AlignCenter)
            self.buttons.append(b)

        self.clearOneButton = QPushButton('Remove selected')
        self.clearOneButton.clicked.connect(self.clearOne)
        buttonLayout.addWidget(self.clearOneButton, alignment = Qt.AlignCenter)

        self.clearButton = QPushButton('Remove all')
        self.clearButton.clicked.connect(self.clearAll)
        buttonLayout.addWidget(self.clearButton, alignment = Qt.AlignCenter)

        buttonFrame = QFrame()
        buttonFrame.setLayout(buttonLayout)
        layout.addWidget(buttonFrame, alignment = Qt.AlignCenter)

        self.envList = QListWidget()
        self.envList.setSelectionMode(QAbstractItemView.ExtendedSelection)

        layout.addWidget(self.envList)

        self.setLayout(layout)

    def inspectInventory(self):
        self.features = sorted(self.inventory[-1].features.keys())
        self.values = set()
        for v in self.inventory:
            self.values.update(v.features.values())
        self.values = sorted([x for x in self.values if x != ''])

    def addFeature(self):
        curFeature = self.featureList.currentItem()
        if curFeature:
            self.envList.addItem(self.sender().value+curFeature.text())

    def clearOne(self):
        items = self.envList.selectedItems()
        for i in items:
            item = self.envList.takeItem(self.envList.row(i))
            #self.sourceWidget.addItem(item)

    def clearAll(self):
        self.envList.clear()

    def value(self):
        val = [self.envList.item(i).text() for i in range(self.envList.count())]
        if not val:
            return ''
        return '[{}]'.format(','.join(val))


class SegmentPairDialog(QDialog):
    def __init__(self, inventory,parent=None):
        QDialog.__init__(self,parent)

        layout = QVBoxLayout()

        segFrame = QFrame()

        segLayout = QHBoxLayout()

        self.segFrame = InventoryBox('Segments',inventory)

        segLayout.addWidget(self.segFrame)

        segFrame.setLayout(segLayout)

        layout.addWidget(segFrame)


        self.oneButton = QPushButton('Add')
        self.anotherButton = QPushButton('Add and create another')
        self.cancelButton = QPushButton('Cancel')
        acLayout = QHBoxLayout()
        acLayout.addWidget(self.oneButton, alignment = Qt.AlignLeft)
        acLayout.addWidget(self.anotherButton, alignment = Qt.AlignLeft)
        acLayout.addWidget(self.cancelButton, alignment = Qt.AlignLeft)
        self.oneButton.clicked.connect(self.one)
        self.anotherButton.clicked.connect(self.another)
        self.cancelButton.clicked.connect(self.reject)

        acFrame = QFrame()
        acFrame.setLayout(acLayout)

        layout.addWidget(acFrame, alignment = Qt.AlignLeft)

        self.setLayout(layout)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Select segment pair')

    def one(self):
        self.addOneMore = False
        self.accept()

    def another(self):
        self.addOneMore = True
        self.accept()

    def reset(self):
        self.segFrame.clearAll()

    def reject(self):
        self.addOneMore = False
        QDialog.reject(self)

    def accept(self):
        selected = self.segFrame.value()
        self.pairs = combinations(selected,2)
        QDialog.accept(self)


class SegmentPairSelectWidget(QGroupBox):
    def __init__(self,inventory,parent=None):
        QGroupBox.__init__(self,'Segments',parent)

        self.inventory = inventory

        vbox = QVBoxLayout()

        self.addButton = QPushButton('Add pair of sounds')
        self.addButton.clicked.connect(self.segPairPopup)
        self.removeButton = QPushButton('Remove selected sound pair')
        self.removeButton.clicked.connect(self.removePair)
        self.addButton.setAutoDefault(False)
        self.addButton.setDefault(False)
        self.removeButton.setAutoDefault(False)
        self.removeButton.setDefault(False)

        self.table = TableWidget()
        self.table.setModel(SegmentPairModel())
        self.table.resizeColumnsToContents()

        vbox.addWidget(self.addButton)
        vbox.addWidget(self.removeButton)
        vbox.addWidget(self.table)
        self.setLayout(vbox)

    def segPairPopup(self):
        dialog = SegmentPairDialog(self.inventory)
        addOneMore = True
        while addOneMore:
            dialog.reset()
            result = dialog.exec_()
            if result:
                for p in dialog.pairs:
                    self.table.model().addRow(p)
            addOneMore = dialog.addOneMore


    def removePair(self):
        select = self.table.selectionModel()
        if select.hasSelection():
            selected = [s.row() for s in select.selectedRows()]
            self.table.model().removeRows(selected)

    def value(self):
        return self.table.model().pairs

class EnvironmentDialog(QDialog):
    def __init__(self, inventory,parent=None):
        QDialog.__init__(self,parent)

        self.inventory = inventory
        self.features = inventory[-1].features.keys()

        layout = QVBoxLayout()
        if parent.name == 'environment':
            self.envType = QComboBox()
            self.envType.addItem('Segments')
            if len(self.features) > 0:
                self.envType.addItem('Features')
            else:
                layout.addWidget(QLabel('Features for {} selection are not available without a feature system.'.format(parent.name)))

            self.envType.currentIndexChanged.connect(self.generateFrames)

            layout.addWidget(QLabel('Basis for building {}:'.format(parent.name)))
            layout.addWidget(self.envType, alignment = Qt.AlignLeft)

        self.lhs = InventoryBox('Left hand side',self.inventory)
        self.lhs.setExclusive(True)

        self.rhs = InventoryBox('Right hand side',self.inventory)
        self.rhs.setExclusive(True)

        self.envFrame = QFrame()

        self.envLayout = QHBoxLayout()

        self.envLayout.addWidget(self.lhs)
        self.envLayout.addWidget(self.rhs)

        self.envFrame.setLayout(self.envLayout)

        layout.addWidget(self.envFrame)

        self.oneButton = QPushButton('Add')
        self.anotherButton = QPushButton('Add and create another')
        self.cancelButton = QPushButton('Cancel')
        acLayout = QHBoxLayout()
        acLayout.addWidget(self.oneButton, alignment = Qt.AlignLeft)
        acLayout.addWidget(self.anotherButton, alignment = Qt.AlignLeft)
        acLayout.addWidget(self.cancelButton, alignment = Qt.AlignLeft)
        self.oneButton.clicked.connect(self.one)
        self.anotherButton.clicked.connect(self.another)
        self.cancelButton.clicked.connect(self.reject)

        acFrame = QFrame()
        acFrame.setLayout(acLayout)

        layout.addWidget(acFrame, alignment = Qt.AlignLeft)

        self.setLayout(layout)
        #self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Create {}'.format(parent.name))


    def createFeatureFrame(self):
        self.lhs.deleteLater()
        self.rhs.deleteLater()

        self.lhs = FeatureBox('Left hand side',self.inventory)
        self.envLayout.addWidget(self.lhs)

        self.rhs = FeatureBox('Right hand side',self.inventory)
        self.envLayout.addWidget(self.rhs)

    def createSegmentFrame(self):
        self.lhs.deleteLater()
        self.rhs.deleteLater()
        self.lhs = InventoryBox('Left hand side',self.inventory)
        self.lhs.setExclusive(True)
        self.envLayout.addWidget(self.lhs)

        self.rhs = InventoryBox('Right hand side',self.inventory)
        self.lhs.setExclusive(True)
        self.envLayout.addWidget(self.rhs)

    def generateFrames(self,ind=0):
        if self.envType.currentText() == 'Segments':
            self.createSegmentFrame()
        elif self.envType.currentText() == 'Features':
            self.createFeatureFrame()

    def one(self):
        self.addOneMore = False
        self.accept()

    def another(self):
        self.addOneMore = True
        self.accept()

    def reset(self):
        self.lhs.clearAll()
        self.rhs.clearAll()

    def accept(self):
        if self.parent().name == 'environment':
            self.env = '{}_{}'.format(self.lhs.value(),self.rhs.value())
        else:
            lhs = self.lhs.value()
            if lhs == '':
                reply = QMessageBox.critical(self,
                        "Missing information", "Please specify a left hand of the bigram.")
                return
            rhs = self.rhs.value()
            if rhs == '':
                reply = QMessageBox.critical(self,
                        "Missing information", "Please specify a right hand of the bigram.")
                return

            self.env = '{}{}'.format(lhs,rhs)
        QDialog.accept(self)

    def reject(self):
        self.addOneMore = False
        QDialog.reject(self)

class EnvironmentSelectWidget(QGroupBox):
    name = 'environment'
    def __init__(self,inventory,parent=None):
        QGroupBox.__init__(self,'{}s'.format(self.name.title()),parent)

        self.inventory = inventory

        vbox = QVBoxLayout()

        self.addButton = QPushButton('Add {}'.format(self.name))
        self.addButton.clicked.connect(self.envPopup)
        self.removeButton = QPushButton('Remove selected {}s'.format(self.name))
        self.removeButton.clicked.connect(self.removeEnv)
        self.addButton.setAutoDefault(False)
        self.addButton.setDefault(False)
        self.removeButton.setAutoDefault(False)
        self.removeButton.setDefault(False)

        self.table = TableWidget()
        self.table.setModel(EnvironmentModel())
        self.table.resizeColumnsToContents()

        vbox.addWidget(self.addButton)
        vbox.addWidget(self.removeButton)
        vbox.addWidget(self.table)

        self.setLayout(vbox)

    def envPopup(self):
        dialog = EnvironmentDialog(self.inventory,self)
        addOneMore = True
        while addOneMore:
            dialog.reset()
            result = dialog.exec_()
            if result:
                self.table.model().addRow([dialog.env])
            addOneMore = dialog.addOneMore

    def removeEnv(self):
        select = self.table.selectionModel()
        if select.hasSelection():
            selected = select.selectedRows()
            for s in selected:
                self.table.model().removeRow(s.row())

    def value(self):
        return [x[0] for x in self.table.model().environments]

class BigramWidget(EnvironmentSelectWidget):
    name = 'bigram'

class RadioSelectWidget(QGroupBox):
    def __init__(self,title,options, actions=None, enabled=None,parent=None):
        QGroupBox.__init__(self,title,parent)

        self.options = options
        vbox = QVBoxLayout()
        self.widgets = []
        for key in options.keys():
            w = QRadioButton(key)
            if actions is not None:
                w.clicked.connect(actions[key])
            if enabled is not None:
                w.setEnabled(enabled[key])
            self.widgets.append(w)
            vbox.addWidget(w)
        self.widgets[0].setChecked(True)
        self.setLayout(vbox)

    def initialClick(self):
        self.widgets[0].click()

    def value(self):
        for w in self.widgets:
            if w.isChecked():
                return self.options[w.text()]
        return None

    def displayValue(self):
        for w in self.widgets:
            if w.isChecked():
                return w.text()
        return ''

    def disable(self):
        for w in self.widgets:
            w.setEnabled(False)

    def enable(self):
        for w in self.widgets:
            w.setEnabled(True)
