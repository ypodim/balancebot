import time
import serial

class PID:
    def __init__(self, port='/dev/tty.usbmodem221101'):
        self.ser = serial.Serial(port, 9600)
        self.error_previous = 0
        self.lastPIDtime = time.time()
        self.stepperPos = 0
        self.motorState = True
        self.send(1) # turn on motor
        self.send(5) # MS 3

    def toggleMotor(self):
        self.motorState = not self.motorState
        if self.motorState:
            self.send(1)
        else:
            self.send(0)
        
    def send(self, val):
        char = chr(val)
        self.ser.write(char.encode())

    def close(self):
        self.send(0)
        self.ser.close()

    def move(self, val):
        if abs(val) > 50 or val == 0:
            return

        self.stepperPos += val
        if val < 0:
            self.send(10 + abs(val))
        else:
            self.send(60 + abs(val))
    
    def calibrate(self, tilt):
        if tilt > 1:
            self.move(-5)
        if tilt < 1:
            self.move(5)
        self.stepperPos = 0

    def process(self, pos):
        return
        target = 0.5
        threshold = 0.02

        kp = 20
        kd = 1
        ki = 0
        error = target - pos
        dedt = 1.0*(error - self.error_previous) / (time.time() - self.lastPIDtime)
        self.error_previous = error
        self.lastPIDtime = time.time()

        P = kp * error
        I = ki
        D = kd * dedt
        action = P+I+D
        
        # debugging
        template = "P:{:.3f}\t\t I:{:.3f}\t D:{:.3f}\t action:{:.3f}\t pos:{:.3f}"
        print(template.format(P,I,D, action, pos))

        # take action
        if abs(action) > threshold:
            self.move(int(action))

    def testMove(self, keyRead):
        if keyRead == 'a':
            self.move(2)
        if keyRead == 's':
            self.move(-2)
        if keyRead == 'z':
            self.move(20)
        if keyRead == 'x':
            self.move(-20)
        if keyRead == 'e':
            self.send(1)
            self.send(5)
            print("motor on")
        if keyRead == 'r':
            self.send(0)
            print("motor off")

