import wx
import sys
import os
import webbrowser
import json

# --- WICHTIGE ÄNDERUNG FÜR EXE ---
# Pfad nur anpassen, wenn wir NICHT als EXE (frozen) laufen.
# In der EXE findet Python die Module automatisch, manuelles Pfad-Ändern führt zum Crash.
if not getattr(sys, 'frozen', False):
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.calculator import evaluiere
# ---------------------------------
from core.calculator import evaluiere

class SettingsDialog(wx.Dialog):
    def __init__(self, parent, current_decimals, current_angle_mode):
        super().__init__(parent, title="Einstellungen", size=(350, 250))
        
        self.result_decimals = current_decimals
        self.result_mode = current_angle_mode

        panel = wx.Panel(self)
        
        lbl_dec = wx.StaticText(panel, label="Dezimalstellen:")
        choices = [str(i) for i in range(1, 21)]
        self.combo_dec = wx.Choice(panel, choices=choices)
        
        safe_index = max(0, min(current_decimals - 1, 19))
        self.combo_dec.SetSelection(safe_index)
        
        self.radio_angle = wx.RadioBox(panel, label="Winkelmaß (Trigonometrie)", 
                                       choices=["Gradmaß (Deg)", "Bogenmaß (Rad)"])
        self.radio_angle.SetSelection(0 if current_angle_mode == 'deg' else 1)
        
        vbox_content = wx.BoxSizer(wx.VERTICAL)
        
        hbox_dec = wx.BoxSizer(wx.HORIZONTAL)
        hbox_dec.Add(lbl_dec, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        hbox_dec.Add(self.combo_dec, proportion=1, flag=wx.EXPAND)
        
        vbox_content.Add(hbox_dec, flag=wx.EXPAND | wx.ALL, border=10)
        vbox_content.Add(self.radio_angle, flag=wx.EXPAND | wx.ALL, border=10)
        
        panel.SetSizer(vbox_content)
        
        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND)
        main_sizer.Add(btns, 0, wx.EXPAND | wx.ALL, border=10)
        
        self.SetSizer(main_sizer)
        
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)
        
        self.Layout()
        self.CentreOnParent()

    def on_ok(self, event):
        try:
            sel_idx = self.combo_dec.GetSelection()
            if sel_idx != wx.NOT_FOUND:
                val_str = self.combo_dec.GetString(sel_idx)
                self.result_decimals = int(val_str)
            
            self.result_mode = 'deg' if self.radio_angle.GetSelection() == 0 else 'rad'
        except Exception as e:
            pass

        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def get_settings(self):
        return self.result_decimals, self.result_mode


class CalculatorFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Mathmax", size=(500, 220))
        
        # --- WICHTIGE ÄNDERUNG: PFAD-ERMITTLUNG ---
        self.settings_file = self.get_config_path()
        self.load_settings()

        self.init_ui()
        self.init_menu()
        
        self.Center()
        self.Show()

    def get_config_path(self):
        """Ermittelt den korrekten Pfad für die Konfigurationsdatei."""
        if getattr(sys, 'frozen', False):
            # Wenn als EXE gestartet: Speicherort ist neben der .exe Datei
            application_path = os.path.dirname(sys.executable)
        else:
            # Wenn als Skript gestartet: Speicherort ist im Projektordner (eine Ebene über ui/)
            application_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        return os.path.join(application_path, 'settings.json')

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.decimals = data.get('decimals', 10)
                    self.angle_mode = data.get('angle_mode', 'deg')
            else:
                self.decimals = 10
                self.angle_mode = 'deg'
        except Exception:
            self.decimals = 10
            self.angle_mode = 'deg'

    def save_settings(self):
        data = {
            'decimals': self.decimals,
            'angle_mode': self.angle_mode
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            wx.MessageBox(f"Konnte Einstellungen nicht speichern: {e}", "Fehler", wx.ICON_ERROR)

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        label_input = wx.StaticText(panel, label="Eingabe:")
        font = label_input.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        label_input.SetFont(font)
        
        self.input_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        
        label_output = wx.StaticText(panel, label="Ergebnis:")
        label_output.SetFont(font)
        
        self.output_ctrl = wx.TextCtrl(panel, style=wx.TE_READONLY)
        
        vbox.Add(label_input, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add(self.input_ctrl, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        vbox.Add(label_output, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add(self.output_ctrl, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)
        
        self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_calculate)
        self.input_ctrl.Bind(wx.EVT_SET_FOCUS, self.on_focus_input)
        self.input_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_input)
        self.output_ctrl.Bind(wx.EVT_SET_FOCUS, self.on_focus_output)
        
        self.input_ctrl.SetFocus()

    def init_menu(self):
        menubar = wx.MenuBar()

        file_menu = wx.Menu()
        item_quit = file_menu.Append(wx.ID_EXIT, "Beenden", "Beendet das Programm")
        
        settings_menu = wx.Menu()
        item_settings = settings_menu.Append(wx.ID_ANY, "Einstellungen...", "Öffnet den Einstellungsdialog")
        
        help_menu = wx.Menu()
        item_help = help_menu.Append(wx.ID_HELP, "Hilfe\tF1", "Öffnet die Hilfe")
        help_menu.AppendSeparator()
        item_about = help_menu.Append(wx.ID_ABOUT, "Über", "Informationen zum Programm")
        
        menubar.Append(file_menu, "&Datei")
        menubar.Append(settings_menu, "&Einstellungen")
        menubar.Append(help_menu, "&Hilfe")
        
        self.SetMenuBar(menubar)
        
        self.Bind(wx.EVT_MENU, self.on_quit, item_quit)
        self.Bind(wx.EVT_MENU, self.on_settings, item_settings)
        self.Bind(wx.EVT_MENU, self.on_help_open, item_help)
        self.Bind(wx.EVT_MENU, self.on_about, item_about)
        
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_NORMAL, wx.WXK_F1, item_help.GetId())
        ])
        self.SetAcceleratorTable(accel_tbl)

    # --- Event Handler ---

    def on_calculate(self, event):
        ausdruck = self.input_ctrl.GetValue()
        ergebnis = evaluiere(ausdruck, decimals=self.decimals, angle_mode=self.angle_mode)
        self.output_ctrl.SetValue(str(ergebnis))
        self.output_ctrl.SetFocus()

    def on_settings(self, event):
        dlg = SettingsDialog(self, self.decimals, self.angle_mode)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.decimals, self.angle_mode = dlg.get_settings()
                self.save_settings()
        except Exception as e:
            wx.MessageBox(f"Fehler: {e}", "Fehler", wx.ICON_ERROR)
        finally:
            dlg.Destroy()

    def on_quit(self, event):
        self.Close()

    def on_about(self, event):
        info = wx.MessageDialog(self, 
            "Mathmax\n\nEntwickler: Jakob Strasser\nVersion: 1.0",
            "Über Mathmax", wx.OK | wx.ICON_INFORMATION)
        info.ShowModal()
        info.Destroy()

    def on_help_open(self, event):
        # Auch für die Hilfe müssen wir den Pfad anpassen
        if getattr(sys, 'frozen', False):
             base_dir = os.path.dirname(sys.executable)
        else:
             base_dir = os.path.dirname(os.path.abspath(__file__))
             base_dir = os.path.join(base_dir, '..') # Raus aus ui/
             
        help_path = os.path.join(base_dir, 'help.html')
        
        if os.path.exists(help_path):
            webbrowser.open(f'file://{os.path.abspath(help_path)}')
        else:
            wx.MessageBox(f"Hilfedatei nicht gefunden:\n{help_path}", "Fehler", wx.ICON_ERROR)

    def on_focus_input(self, event):
        event.Skip()
        wx.CallAfter(self.input_ctrl.SelectAll)

    def on_focus_output(self, event):
        event.Skip()
        wx.CallAfter(self.output_ctrl.SelectAll)

    def on_key_input(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_TAB and not event.ShiftDown():
            self.output_ctrl.SetFocus()
        else:
            event.Skip()