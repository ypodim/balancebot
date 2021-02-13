import tkinter as tk
# from PIL import Image, ImageTk
from vision import Vision
from pid import PID

class MainWindow():
    def __init__(self, window, vision, pid):
        self.w = window
        self.vision = vision
        self.pid = pid
        self.interval = 2 # Interval in ms to get the latest frame
        self.calibrated = False
        self.displayPreview = False

        self.powerBtn = tk.Button(self.w, text="motor off", command=self.powerBtn)
        self.previewBtn = tk.Button(self.w, text="toggle preview", command=self.togglePreview)
        self.leftBtn = tk.Button(self.w, text="left", command=lambda: self.pid.move(2))
        self.rightBtn = tk.Button(self.w, text="right", command=lambda: self.pid.move(-2))
        self.l1 = tk.Label(self.w, text='none', borderwidth=1)
        self.l2 = tk.Label(self.w, text='none', borderwidth=2)

        self.powerBtn.grid(row=0, column=0)
        self.previewBtn.grid(row=0, column=1)
        self.leftBtn.grid(row=0, column=2)
        self.rightBtn.grid(row=0, column=3)
        self.l1.grid(row=1,column=0)
        self.l2.grid(row=1,column=1)

        self.canvas = tk.Canvas(self.w, width=vision.width, height=vision.height)
        self.canvas.grid(row=2, column=0, columnspan=4)
        
        self.w.bind_all('<Key>', self.onKey)
        self.w.protocol("WM_DELETE_WINDOW", self.onClose)
        
        # Update image on canvas
        self.process()
        self.updateLabels()
    
    def powerBtn(self):
        self.pid.toggleMotor()
        newLabel = "off" if self.pid.motorState else "on"
        self.powerBtn["text"] = "turn motor {}".format(newLabel)
        if not self.pid.motorState:
            self.calibrated = False
            print("lost calibration")

    def togglePreview(self):
        self.displayPreview = not self.displayPreview

    def onKey(self, key):
        # print("key:", key)
        if key.char in "re":
            self.pid.testMove(key.char)
        if key.char in "q":
            self.onClose()

    def onClose(self):
        self.vision.close()
        self.pid.close()
        self.w.destroy()

    def updateLabels(self):
        self.l1.config(text="stepper pos: {}".format(self.pid.stepperPos))
        self.l2.config(text="my_text2")
        self.w.after(self.interval, self.updateLabels)

    def process(self):
        result = self.vision.processFrame()

        if self.calibrated:
            if result == 2:
                self.pid.process(self.vision.pos)
            else:
                print("calibrated but I don't see the ball")
        else:
            if result == 0:
                print("no markers to calibrate!")
            else:
                if self.vision.isTilted:
                    self.pid.calibrate(self.vision.getTilt())
                else:
                    if self.pid.motorState:
                        self.calibrated = True
                        print("now calibrated")
                    else:
                        print("calibration point reached, ignoring")
        
        if result > 0 and self.displayPreview:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.vision.image)

        # Repeat every 'interval' ms
        self.w.after(self.interval, self.process)

if __name__ == "__main__":
    root = tk.Tk()
    vis = Vision()
    pid = PID()
    MainWindow(root, vis, pid)
    root.mainloop()