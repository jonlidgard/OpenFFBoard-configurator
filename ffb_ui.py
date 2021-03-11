from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QWidget,QToolButton 
from PyQt5.QtWidgets import QMessageBox,QVBoxLayout,QCheckBox,QButtonGroup,QGridLayout,QSpinBox
from PyQt5 import uic
from helper import res_path,classlistToIds
from PyQt5.QtCore import QTimer,QEvent
import main
import buttonconf_ui
import analogconf_ui
from base_ui import WidgetUI

class FfbUI(WidgetUI):

    btnClasses = {}
    btnIds = []

    axisClasses = {}
    axisIds = []

    

    buttonbtns = QButtonGroup()
    buttonconfbuttons = []

    axisbtns = QButtonGroup()
    axisconfbuttons = []


    def __init__(self, main=None):
        WidgetUI.__init__(self, main,'ffbclass.ui')
    
        self.timer = QTimer(self)
#        self.ffbAxis = QSpinBox(self)
        self.buttonbtns.setExclusive(False)
        self.axisbtns.setExclusive(False)

        self.timer.timeout.connect(self.updateTimer)
        
        if(self.initUi()):
            tabId = self.main.addTab(self,"FFB Wheel")
            self.main.selectTab(tabId)

        self.spinBox_ffbAxes.valueChanged.connect(self.ffbAxesSpinBoxChanged)
        self.buttonbtns.buttonClicked.connect(self.buttonsChanged)
        self.axisbtns.buttonClicked.connect(self.axesChanged)
        


    def initUi(self):
        try:
            self.main.comms.serialGetAsync("axis?",self.spinBox_ffbAxes.setValue,int)
            self.getButtonSources()
            self.getAxisSources()
            
        except:
            self.main.log("Error initializing FFB tab")
            return False
        return True

    # Tab is currently shown
    def showEvent(self,event):
        self.timer.start(500)

    # Tab is hidden
    def hideEvent(self,event):
        self.timer.stop()

 
    def updateTimer(self):
        try:
            def f(d):
                rate,active = d
                if active == 1:
                    act = "FFB ON"
                elif active == -1:
                    act = "EMERGENCY STOP"
                else:
                    act = "FFB OFF"
                self.label_HIDrate.setText(str(rate)+"Hz" + " (" + act + ")")
            self.main.comms.serialGetAsync(["hidrate","ffbactive"],f,int)
        except:
            self.main.log("Update error")
    
    # FFB Axis Spinbox
    def ffbAxesSpinBoxChanged(self,val):
        self.main.comms.serialWrite("axis="+str(val)+"\n")

    # Button selector
    def buttonsChanged(self,id):
        mask = 0
        for b in self.buttonbtns.buttons():
            if(b.isChecked()):
                mask |= 1 << self.buttonbtns.id(b)

        self.main.comms.serialWrite("btntypes="+str(mask)+"\n")

    # Axis selector
    def axesChanged(self,id):
        mask = 0
        for b in self.axisbtns.buttons():
            if(b.isChecked()):
                mask |= 1 << self.axisbtns.id(b)

        self.main.comms.serialWrite("aintypes="+str(mask)+"\n")
        

    def getButtonSources(self):
        
        def cb_buttonSources(dat):
            btns = dat[0]
            types = int(dat[1])
            
            self.btnIds,self.btnClasses = classlistToIds(btns)
            if(types == None):
                self.main.log("Error getting buttons")
                return
            types = int(types)
            layout = QGridLayout()
            #clear
            for b in self.buttonconfbuttons:
                del b
            for b in self.buttonbtns.buttons():
                self.buttonbtns.removeButton(b)
                del b
            #add buttons
            row = 0
            for c in self.btnClasses:
                btn=QCheckBox(str(c[1]),self.groupBox_buttons)
                self.buttonbtns.addButton(btn,c[0])
                layout.addWidget(btn,row,0)
                enabled = types & (1<<c[0]) != 0
                btn.setChecked(enabled)

                confbutton = QToolButton(self)
                confbutton.setText(">")
                layout.addWidget(confbutton,row,1)
                self.buttonconfbuttons.append((confbutton,buttonconf_ui.ButtonOptionsDialog(str(c[1]),c[0],self.main)))
                confbutton.clicked.connect(self.buttonconfbuttons[row][1].exec)
                confbutton.setEnabled(enabled)
                self.buttonbtns.button(c[0]).stateChanged.connect(confbutton.setEnabled)
                row+=1

            self.groupBox_buttons.setLayout(layout)
        self.main.comms.serialGetAsync(["lsbtn","btntypes?"],cb_buttonSources)


    def getAxisSources(self):
        
        def cb_axisSources(dat):
            btns = dat[0]
            types = int(dat[1])
            
            self.axisIds,self.axisClasses = classlistToIds(btns)
            if(types == None):
                self.main.log("Error getting buttons")
                return
            types = int(types)
            layout = QGridLayout()
            #clear
            for b in self.axisconfbuttons:
                del b
            for b in self.axisbtns.buttons():
                self.axisbtns.removeButton(b)
                del b
            #add buttons
            row = 0
            for c in self.axisClasses:
                btn=QCheckBox(str(c[1]),self.groupBox_buttons)
                self.axisbtns.addButton(btn,c[0])
                layout.addWidget(btn,row,0)
                enabled = types & (1<<c[0]) != 0
                btn.setChecked(enabled)

                confbutton = QToolButton(self)
                confbutton.setText(">")
                layout.addWidget(confbutton,row,1)
                self.axisconfbuttons.append((confbutton,analogconf_ui.AnalogOptionsDialog(str(c[1]),c[0],self.main)))
                confbutton.clicked.connect(self.axisconfbuttons[row][1].exec)
                confbutton.setEnabled(enabled)
                self.axisbtns.button(c[0]).stateChanged.connect(confbutton.setEnabled)
                row+=1

            self.groupBox_analogaxes.setLayout(layout)
        self.main.comms.serialGetAsync(["lsain","aintypes?"],cb_axisSources)
        

        