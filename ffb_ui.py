from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QWidget,QToolButton 
from PyQt5.QtWidgets import QMessageBox,QVBoxLayout,QCheckBox,QButtonGroup,QGridLayout
from PyQt5 import uic
from helper import res_path,classlistToIds
from PyQt5.QtCore import QTimer
import main
import tmc4671_ui
import buttonconf_ui
from base_ui import WidgetUI

class FfbUI(WidgetUI):
    drvClasses = {}
    drvIds = []

    encClasses = {}
    encIds = []

    btnClasses = {}
    btnIds = []

    drvId = 0
    encId = 0

    axes = 6

    analogbtns = QButtonGroup()
    buttonbtns = QButtonGroup()
    buttonconfbuttons = []
    def __init__(self, main=None):
        WidgetUI.__init__(self, main,'ffbclass.ui')
    
        

        self.analogbtns.setExclusive(False)
        self.buttonbtns.setExclusive(False)

        self.horizontalSlider_power.valueChanged.connect(self.sliderPowerChanged)
        self.horizontalSlider_degrees.valueChanged.connect(self.sliderDegreesChanged)
        self.main.save.connect(self.save)

        #self.comboBox_driver.currentIndexChanged.connect(self.driverChanged)
        #self.comboBox_encoder.currentIndexChanged.connect(self.encoderChanged)
        self.pushButton_submit_hw.clicked.connect(self.submitHw)

        if(self.initUi()):
            tabId = self.main.addTab(self,"FFB Wheel")
            self.main.selectTab(tabId)

        self.analogbtns.buttonClicked.connect(self.axesChanged)
        self.buttonbtns.buttonClicked.connect(self.buttonsChanged)
        self.pushButton_center.clicked.connect(lambda : self.main.serialWrite("zeroenc\n"))
        
        #self.spinBox_ppr.valueChanged.connect(lambda v : self.main.serialWrite("ppr="+str(v)+";"))



    def initUi(self):
        try:
            self.main.setSaveBtn(True)
            self.getMotorDriver()
            self.getEncoder()
            self.updateSliders()

            layout = QVBoxLayout()

            # Clear if reloaded
            for b in self.analogbtns.buttons():
                self.analogbtns.removeButton(b)
                del b
            for i in range(self.axes):
                btn=QCheckBox(str(i+1),self.groupBox_analogaxes)
                self.analogbtns.addButton(btn,i)
                layout.addWidget(btn)

            self.groupBox_analogaxes.setLayout(layout)
            self.updateAxes()
            self.getButtonSources()
        except:
            self.main.log("Error initializing FFB tab")
            return False
        return True

    def updateAxes(self):
        axismask = int(self.main.serialGet("axismask?\n"))
        for i in range(self.axes):
            self.analogbtns.button(i).setChecked(axismask & (1 << i))

    # Axis checkboxes
    def axesChanged(self,id):
        mask = 0
        for i in range(self.axes):
            if (self.analogbtns.button(i).isChecked()):
                mask |= 1 << i
        self.main.serialWrite("axismask="+str(mask)+"\n")

    # Button selector
    def buttonsChanged(self,id):
        mask = 0
        for b in self.buttonbtns.buttons():
            if(b.isChecked()):
                mask |= 1 << self.buttonbtns.id(b)

        self.main.serialWrite("btntypes="+str(mask)+"\n")

    def submitHw(self):
        val = self.spinBox_ppr.value()
        self.driverChanged(self.comboBox_driver.currentIndex())
        self.encoderChanged(self.comboBox_encoder.currentIndex())
        self.main.serialWrite("ppr="+str(val)+"\n")

    def save(self):
        self.main.serialWrite("save\n")
        

    def driverChanged(self,idx):
        if idx == -1:
            return
        id = self.drvClasses[idx][0]
        if(self.drvId != id):
            self.main.serialWrite("drvtype="+str(id)+"\n")
            self.getMotorDriver()
            self.getEncoder()

        
   
    def encoderChanged(self,idx):
        if idx == -1:
            return
        id = self.encClasses[idx][0]
        if(self.encId != id):
            self.main.serialWrite("enctype="+str(id)+"\n")
            self.getEncoder()
        
    
    def sliderPowerChanged(self,val):
        self.main.serialWrite("power="+str(val)+"\n")
        
    def sliderDegreesChanged(self,val):
        self.main.serialWrite("degrees="+str(val)+"\n")

    def updateSliders(self):
        power = self.main.serialGet("power?\n",150)
        degrees = self.main.serialGet("degrees?\n",150)

        if not(power and degrees):
            main.log("Error getting values")
            return
        power = int(power)
        degrees = int(degrees)
        self.horizontalSlider_power.setValue(power)
        self.horizontalSlider_degrees.setValue(degrees)
        self.label_power.setNum(power)
        self.label_range.setNum(degrees)


    def getMotorDriver(self):
        #self.comboBox_driver.currentIndexChanged.disconnect()
        dat = self.main.serialGet("drvtype!\n")
        self.comboBox_driver.clear()
        self.drvIds,self.drvClasses = classlistToIds(dat)
        id = self.main.serialGet("drvtype?\n")
        if(id == None):
            self.main.log("Error getting driver")
            return
        self.drvId = int(id)
        for c in self.drvClasses:
            self.comboBox_driver.addItem(c[1])

        if(self.drvId in self.drvIds and self.comboBox_driver.currentIndex() != self.drvIds[self.drvId][0]):
            self.comboBox_driver.setCurrentIndex(self.drvIds[self.drvId][0])
        # else:
        #     self.comboBox_driver.setCurrentIndex(0)
        #self.comboBox_driver.currentIndexChanged.connect(self.driverChanged)
        # TMC

        if(self.drvId == 1):
            if not self.main.hasTab("TMC4671"):
                tmc = tmc4671_ui.TMC4671Ui(self.main)
                if(tmc.initUi()):
                    tabId = self.main.addTab(tmc,"TMC4671")
                    if(int(self.main.serialGet("mtype\n")) == 0):
                        self.main.selectTab(tabId)
                        msg = QMessageBox(QMessageBox.Information,"TMC4671","Please setup the motor driver first!")
                        msg.exec_()
        
        

    def getEncoder(self):
        #self.comboBox_encoder.currentIndexChanged.disconnect()
        self.spinBox_ppr.setEnabled(True)

        dat = self.main.serialGet("enctype!\n")
        self.comboBox_encoder.clear()
        self.encIds,self.encClasses = classlistToIds(dat)
        id = self.main.serialGet("enctype?\n")
        if(id == None):
            self.main.log("Error getting encoder")
            return
        self.encId = int(id)
        for c in self.encClasses:
            self.comboBox_encoder.addItem(c[1])

        idx = self.encIds[self.encId][0] if self.encId in self.encIds else 0
        self.comboBox_encoder.setCurrentIndex(idx)
        
        ppr = self.main.serialGet("ppr?\n")
        self.spinBox_ppr.setValue(int(ppr))

        if(self.encId == 1):
            self.spinBox_ppr.setEnabled(False)
       # self.comboBox_encoder.currentIndexChanged.connect(self.encoderChanged)
        

    def getButtonSources(self):
        dat = self.main.serialGet("lsbtn\n")
        
        self.btnIds,self.btnClasses = classlistToIds(dat)
        types = self.main.serialGet("btntypes?\n")
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
            #confbutton.setPopupMode(QToolButton.InstantPopup)
            layout.addWidget(confbutton,row,1)
            self.buttonconfbuttons.append((confbutton,buttonconf_ui.ButtonOptionsDialog(str(c[1]),c[0],self.main)))
            confbutton.clicked.connect(self.buttonconfbuttons[row][1].exec)
            confbutton.setEnabled(enabled)
            self.buttonbtns.button(c[0]).stateChanged.connect(confbutton.setEnabled)
            row+=1

        self.groupBox_buttons.setLayout(layout)
        # TODO add UIs
        

        