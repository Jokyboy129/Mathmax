import wx
from ui.interface import CalculatorFrame

if __name__ == "__main__":
    app = wx.App()
    frame = CalculatorFrame()
    app.MainLoop()