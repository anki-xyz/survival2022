from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, \
    QFileDialog, QMessageBox, QPushButton
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def getMetadata(s):
    meta = []
    
    # Separate all meta information from each other
    for i in s.split(" "):
        meta.extend(i.split("_"))
        
    # Convert time to an integer
    meta[2] = int(meta[2][:-1])

    # Unstained events are not indicate, indicate them!
    if meta[4] != "unstained":
        meta.insert(4, "stained")
        
    # Solve double IDs --> remove additional 001
    if meta[5] == "001":
        if meta[6] != None:
            meta.pop(5)
            
    # Solve special case for multiple gates
    if len(meta) > 6:
        # State additional gate at beginning
        meta[0] = meta[-1]
        
        # Processing and cleaning
        meta.pop(6)
        meta.pop(6)
        meta[-1] = meta[-1].split("/")[0]
        
    # Remove file ending
    meta[-1] = meta[-1].replace(".fcs", "")
        
    return meta

class Interface(QWidget):
    def __init__(self, fn):
        super().__init__()
        self.l = QGridLayout(self)

        # No data has been processed...
        self.final = None

        ### We want to open the file
        self.df = pd.read_excel(fn).fillna('')

        self.b = QPushButton("Process data")
        self.b.clicked.connect(self.process)
        self.l.addWidget(self.b)

    def process(self):
        """This is what needs to happen
        """
        self.getEntries()
        self.overview = self.getOverview()
        self.getMeanAndMedian()
        self.final = self.computeStatistics()

        sns.pointplot(x='t', y='ratio', hue='Type', data=self.final)
        plt.show()

        # QMessageBox.information(self, "Works!", "This works in theory")
        pass

    def getEntries(self):
        cur_item = 0
        cur_depth = 0

        self.entry_ids = [0]

        for i, row in self.df.iterrows():

            ######
            ## Know we know all your secrets
            if row['Depth'].count('>') > cur_depth:
                cur_depth += 1
                
            elif row['Depth'].count('>') == cur_depth:
                pass
                
            else:
                self.entry_ids.append(i)
                cur_item += 1
                cur_depth = row['Depth'].count('>')
               
    def getOverview(self):
        to_df = []

        for i in self.entry_ids:
            meta = getMetadata(self.df.loc[i]['Name'])
            
            to_df.append([i] + meta)          

        overview = pd.DataFrame(to_df)
        overview.columns = "EntryId", "Gate", "Type", "t", "Treatment", "Stained", "Id"

        return overview

    def getMeanAndMedian(self):
        means = []

        for i, row in self.overview.iterrows():
        #     print(i, row['EntryId'])
            # I AM LOOKING AT EACH ENTRY
            
            # GIVE ME IN THE ORIGINAL DATASET THE NEXT COUPLE OF ENTRIES (~ 10)
            for j, row2 in self.df.loc[row['EntryId']:row['EntryId']+10].iterrows():
                # IF we found the Mean, get the desired number
                if "Mean" in row2['Name']:
                    means.append(row2['Statistic'])
                    # Let's stop here, because we found what we needed
                    break
                    
        self.overview['mean'] = means

        medians = []

        for i, row in self.overview.iterrows():
        #     print(i, row['EntryId'])
            # I AM LOOKING AT EACH ENTRY
            
            # GIVE ME IN THE ORIGINAL DATASET THE NEXT COUPLE OF ENTRIES (~ 10)
            for j, row2 in self.df.loc[row['EntryId']:row['EntryId']+10].iterrows():
                # IF we found the Mean, get the desired number
                if "Median" in row2['Name']:
                    medians.append(row2['Statistic'])
                    # Let's stop here, because we found what we needed
                    break
                    
        self.overview['median'] = medians

    def computeStatistics(self):
        ov = self.overview.query("(Stained == 'stained') & Gate != 'HSP70'")
        control = ov.sort_values(["Type", "t", "Treatment"]).query("Treatment!='treated'")
        treated = ov.sort_values(["Type", "t", "Treatment"]).query("Treatment=='treated'")
                
        final = control[list(control.columns[:4])+list(control.columns[5:])].reset_index()

        final['ratio'] = treated['mean'].values/control['mean'].values

        return final

    def keyPressEvent(self, e):
        modifiers = QApplication.keyboardModifiers()

        # Checks for a specific key ("I") and if Ctrl is pressed
        if e.key() == Qt.Key_I and modifiers == Qt.ControlModifier:
            QMessageBox.information(self, "Shortcut", "Shortcut recognized!")

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.status = self.statusBar()
        self.menu = self.menuBar()

        self.fn = None

        # Main top menu
        self.file = self.menu.addMenu("&File")
        self.file.addAction("Open", self.open)
        self.file.addAction("Save", self.save)
        self.file.addAction("Close", self.close)

        # Central widget
        self.w = None

        # Title
        self.setWindowTitle("Hanna's Magic GUI")
        self.setGeometry(100, 100, 800, 600)

    def open(self):
        self.fn = QFileDialog.getOpenFileName(filter="*.xls")[0]

        if self.fn:
            self.status.showMessage(self.fn)
            self.w = Interface(self.fn)
            self.setCentralWidget(self.w)

    def save(self):
        if self.fn is not None and self.w.final is not None:
            fn = QFileDialog.getSaveFileName(filter="*.xlsx")[0]
            self.w.final.to_excel(fn)
        else:
            QMessageBox.critical(self, "Nothing there!", "No file is opened!")

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    m = Main()
    m.show()

    sys.exit(app.exec_())