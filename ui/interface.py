import wx
import sys
import os
import locale
import json
import webbrowser

# --- WICHTIGE ÄNDERUNG FÜR EXE ---
if not getattr(sys, 'frozen', False):
	sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.calculator import evaluiere

class SettingsDialog(wx.Dialog):
	def __init__(self, parent, current_decimals, current_angle_mode, current_lang):
		title = "Einstellungen" if current_lang == 'de' else "Settings"
		super().__init__(parent, title=title, size=(380, 300))
		
		self.result_decimals = current_decimals
		self.result_mode = current_angle_mode
		self.result_lang = current_lang

		panel = wx.Panel(self)
		
		lbl_dec_txt = "Dezimalstellen:" if current_lang == 'de' else "Decimal places:"
		lbl_dec = wx.StaticText(panel, label=lbl_dec_txt)
		choices_dec = [str(i) for i in range(1, 21)]
		self.combo_dec = wx.Choice(panel, choices=choices_dec)
		
		safe_index = max(0, min(current_decimals - 1, 19))
		self.combo_dec.SetSelection(safe_index)
		
		angle_title = "Winkelmaß (Trigonometrie)" if current_lang == 'de' else "Angle mode (Trigonometry)"
		angle_choices = ["Gradmaß (Deg)", "Bogenmaß (Rad)"] if current_lang == 'de' else ["Degrees (Deg)", "Radians (Rad)"]
		self.radio_angle = wx.RadioBox(panel, label=angle_title, choices=angle_choices)
		self.radio_angle.SetSelection(0 if current_angle_mode == 'deg' else 1)
		
		lang_title = "Sprache / Language"
		self.radio_lang = wx.RadioBox(panel, label=lang_title, choices=["Deutsch", "English"])
		self.radio_lang.SetSelection(0 if current_lang == 'de' else 1)
		
		vbox_content = wx.BoxSizer(wx.VERTICAL)
		
		hbox_dec = wx.BoxSizer(wx.HORIZONTAL)
		hbox_dec.Add(lbl_dec, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
		hbox_dec.Add(self.combo_dec, proportion=1, flag=wx.EXPAND)
		
		vbox_content.Add(hbox_dec, flag=wx.EXPAND | wx.ALL, border=10)
		vbox_content.Add(self.radio_angle, flag=wx.EXPAND | wx.ALL, border=10)
		vbox_content.Add(self.radio_lang, flag=wx.EXPAND | wx.ALL, border=10)
		
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
			self.result_lang = 'de' if self.radio_lang.GetSelection() == 0 else 'en'
		except Exception:
			pass

		self.EndModal(wx.ID_OK)

	def on_cancel(self, event):
		self.EndModal(wx.ID_CANCEL)

	def get_settings(self):
		return self.result_decimals, self.result_mode, self.result_lang


class CalculatorFrame(wx.Frame):
	def __init__(self):
		super().__init__(None, title="Mathmax", size=(520, 220))
		
		self.settings_file = self.get_config_path()
		
		# System language fallback
		sys_lang = locale.getdefaultlocale()[0]
		self.default_lang = 'de' if sys_lang and sys_lang.startswith('de') else 'en'
		
		self.load_settings()

		self.init_ui()
		self.init_menu()
		
		self.Center()
		self.Show()

	def get_config_path(self):
		if getattr(sys, 'frozen', False):
			application_path = os.path.dirname(sys.executable)
		else:
			application_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
		
		return os.path.join(application_path, 'settings.json')

	def load_settings(self):
		try:
			if os.path.exists(self.settings_file):
				with open(self.settings_file, 'r') as f:
					data = json.load(f)
					self.decimals = data.get('decimals', 10)
					self.angle_mode = data.get('angle_mode', 'deg')
					self.app_lang = data.get('language', self.default_lang)
			else:
				self.decimals = 10
				self.angle_mode = 'deg'
				self.app_lang = self.default_lang
		except Exception:
			self.decimals = 10
			self.angle_mode = 'deg'
			self.app_lang = self.default_lang

	def save_settings(self):
		data = {
			'decimals': self.decimals,
			'angle_mode': self.angle_mode,
			'language': self.app_lang
		}
		try:
			with open(self.settings_file, 'w') as f:
				json.dump(data, f)
		except Exception as e:
			err_title = "Fehler" if self.app_lang == 'de' else "Error"
			wx.MessageBox(f"Settings error: {e}", err_title, wx.ICON_ERROR)

	def init_ui(self):
		self.panel = wx.Panel(self)
		self.vbox = wx.BoxSizer(wx.VERTICAL)
		
		input_txt = "Eingabe:" if self.app_lang == 'de' else "Input:"
		self.label_input = wx.StaticText(self.panel, label=input_txt)
		font = self.label_input.GetFont()
		font.SetWeight(wx.FONTWEIGHT_BOLD)
		self.label_input.SetFont(font)
		
		self.input_ctrl = wx.TextCtrl(self.panel, style=wx.TE_PROCESS_ENTER)
		
		output_txt = "Ergebnis:" if self.app_lang == 'de' else "Result:"
		self.label_output = wx.StaticText(self.panel, label=output_txt)
		self.label_output.SetFont(font)
		
		self.output_ctrl = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
		
		self.vbox.Add(self.label_input, flag=wx.LEFT | wx.TOP, border=10)
		self.vbox.Add(self.input_ctrl, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
		self.vbox.Add(self.label_output, flag=wx.LEFT | wx.TOP, border=10)
		self.vbox.Add(self.output_ctrl, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
		
		self.panel.SetSizer(self.vbox)
		
		self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_calculate)
		self.input_ctrl.Bind(wx.EVT_SET_FOCUS, self.on_focus_input)
		self.input_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_input)
		self.output_ctrl.Bind(wx.EVT_SET_FOCUS, self.on_focus_output)
		
		self.input_ctrl.SetFocus()

	def init_menu(self):
		self.menubar = wx.MenuBar()

		file_menu = wx.Menu()
		file_str = "Beenden" if self.app_lang == 'de' else "Exit"
		file_desc = "Beendet das Programm" if self.app_lang == 'de' else "Exits the application"
		self.item_quit = file_menu.Append(wx.ID_EXIT, file_str, file_desc)
		
		settings_menu = wx.Menu()
		set_str = "Einstellungen..." if self.app_lang == 'de' else "Settings..."
		self.item_settings = settings_menu.Append(wx.ID_ANY, set_str, set_str)
		
		help_menu = wx.Menu()
		help_str = "Hilfe\tF1" if self.app_lang == 'de' else "Help\tF1"
		self.item_help = help_menu.Append(wx.ID_HELP, help_str, help_str)
		help_menu.AppendSeparator()
		
		about_str = "Über" if self.app_lang == 'de' else "About"
		self.item_about = help_menu.Append(wx.ID_ABOUT, about_str, about_str)
		
		menu_file = "&Datei" if self.app_lang == 'de' else "&File"
		menu_set = "&Einstellungen" if self.app_lang == 'de' else "&Settings"
		menu_help = "&Hilfe" if self.app_lang == 'de' else "&Help"

		self.menubar.Append(file_menu, menu_file)
		self.menubar.Append(settings_menu, menu_set)
		self.menubar.Append(help_menu, menu_help)
		
		self.SetMenuBar(self.menubar)
		
		self.Bind(wx.EVT_MENU, self.on_quit, self.item_quit)
		self.Bind(wx.EVT_MENU, self.on_settings, self.item_settings)
		self.Bind(wx.EVT_MENU, self.on_help_open, self.item_help)
		self.Bind(wx.EVT_MENU, self.on_about, self.item_about)
		
		accel_tbl = wx.AcceleratorTable([
			(wx.ACCEL_NORMAL, wx.WXK_F1, self.item_help.GetId())
		])
		self.SetAcceleratorTable(accel_tbl)

	def update_ui_language(self):
		input_txt = "Eingabe:" if self.app_lang == 'de' else "Input:"
		output_txt = "Ergebnis:" if self.app_lang == 'de' else "Result:"
		self.label_input.SetLabel(input_txt)
		self.label_output.SetLabel(output_txt)
		
		menu_file = "&Datei" if self.app_lang == 'de' else "&File"
		menu_set = "&Einstellungen" if self.app_lang == 'de' else "&Settings"
		menu_help = "&Hilfe" if self.app_lang == 'de' else "&Help"
		
		self.menubar.SetMenuLabel(0, menu_file)
		self.menubar.SetMenuLabel(1, menu_set)
		self.menubar.SetMenuLabel(2, menu_help)

		self.item_quit.SetItemLabel("Beenden" if self.app_lang == 'de' else "Exit")
		self.item_settings.SetItemLabel("Einstellungen..." if self.app_lang == 'de' else "Settings...")
		self.item_help.SetItemLabel("Hilfe\tF1" if self.app_lang == 'de' else "Help\tF1")
		self.item_about.SetItemLabel("Über" if self.app_lang == 'de' else "About")

	def on_calculate(self, event):
		ausdruck = self.input_ctrl.GetValue()
		ergebnis = evaluiere(ausdruck, decimals=self.decimals, angle_mode=self.angle_mode, lang=self.app_lang)
		self.output_ctrl.SetValue(str(ergebnis))
		self.output_ctrl.SetFocus()

	def on_settings(self, event):
		dlg = SettingsDialog(self, self.decimals, self.angle_mode, self.app_lang)
		try:
			if dlg.ShowModal() == wx.ID_OK:
				self.decimals, self.angle_mode, new_lang = dlg.get_settings()
				if new_lang != self.app_lang:
					self.app_lang = new_lang
					self.update_ui_language()
				self.save_settings()
		except Exception as e:
			err_title = "Fehler" if self.app_lang == 'de' else "Error"
			wx.MessageBox(f"Fehler/Error: {e}", err_title, wx.ICON_ERROR)
		finally:
			dlg.Destroy()

	def on_quit(self, event):
		self.Close()

	def on_about(self, event):
		title = "Über Mathmax" if self.app_lang == 'de' else "About Mathmax"
		dev = "Entwickler" if self.app_lang == 'de' else "Developer"
		info = wx.MessageDialog(self, 
			f"Mathmax\n\n{dev}: Jakob Strasser\nVersion: 1.0",
			title, wx.OK | wx.ICON_INFORMATION)
		info.ShowModal()
		info.Destroy()

	def on_help_open(self, event):
		if getattr(sys, 'frozen', False):
			base_dir = os.path.dirname(sys.executable)
		else:
			base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
			
		help_path = os.path.join(base_dir, 'help.html')
		
		if os.path.exists(help_path):
			url = f"file://{os.path.abspath(help_path)}"
			webbrowser.open(url)
		else:
			err_title = "Fehler" if self.app_lang == 'de' else "Error"
			err_msg = f"Hilfedatei nicht gefunden:\n{help_path}" if self.app_lang == 'de' else f"Help file not found:\n{help_path}"
			wx.MessageBox(err_msg, err_title, wx.ICON_ERROR)

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