"""
BIOS Simulator for Windows 7 - Controls system behavior, boot process, and hardware settings
"""
import tkinter as tk
import json
import os
from config import BIOS_DEFAULTS, AERO_BLUE, AERO_LIGHT, AERO_DARK

class BIOSSimulator:
    """Manages simulated BIOS settings and Windows 7 system control."""
    
    def __init__(self, config_file='bios_config.json'):
        self.config_file = config_file
        self.settings = self._load_settings()
        self.boot_count = 0
        self.system_uptime = 0
        self.hardware_state = {
            'cpu_temp': 45,
            'gpu_temp': 50,
            'fan_speed': 2000,
            'power_usage': 65,
        }
        
    def _load_settings(self):
        """Load BIOS settings from file or use defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return BIOS_DEFAULTS.copy()
        return BIOS_DEFAULTS.copy()
    
    def save_settings(self):
        """Persist BIOS settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True, "Settings saved successfully."
        except Exception as e:
            return False, str(e)
    
    def toggle_feature(self, feature_name):
        """Toggle BIOS feature on/off."""
        if feature_name in self.settings:
            self.settings[feature_name] = not self.settings[feature_name]
            self.save_settings()
            return self.settings[feature_name]
        return None
    
    def set_boot_order(self, order_list):
        """Set system boot device order."""
        self.settings['boot_order'] = order_list
        self.save_settings()
        return True
    
    def get_hardware_status(self):
        """Get real-time hardware status."""
        return self.hardware_state.copy()
    
    def diagnose_system(self):
        """Run system diagnostic and return health report."""
        report = {
            'secure_boot': self.settings['secure_boot'],
            'virtualization': self.settings['virtualization'],
            'tpm': self.settings['tpm'],
            'cpu_temp': self.hardware_state['cpu_temp'],
            'gpu_temp': self.hardware_state['gpu_temp'],
            'fan_speed': self.hardware_state['fan_speed'],
            'power_usage': self.hardware_state['power_usage'],
            'boot_count': self.boot_count,
        }
        return report
    
    def show_bios_ui(self, root):
        """Display BIOS setup interface."""
        bios_win = tk.Toplevel(root)
        bios_win.title('BIOS Setup Utility')
        bios_win.geometry('700x550')
        bios_win.configure(bg='#000080')
        
        # Title
        tk.Label(bios_win, text='Phoenix BIOS v8.0 - Windows 7 Ultimate',
                 bg='#000080', fg='#00ff00', font=('Courier', 12, 'bold')).pack(pady=10)
        tk.Label(bios_win, text='System Control & Hardware Configuration',
                 bg='#000080', fg='#00ff00', font=('Courier', 9)).pack()
        
        # Main content
        content = tk.Frame(bios_win, bg='#000080')
        content.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Security Settings
        tk.Label(content, text='SECURITY:', bg='#000080', fg='#00ff00', font=('Courier', 11, 'bold')).pack(anchor='w')
        
        for feature in ['Secure Boot', 'Virtualization', 'TPM']:
            key = feature.lower().replace(' ', '_')
            state = 'Enabled' if self.settings.get(key, True) else 'Disabled'
            row = tk.Frame(content, bg='#000080')
            row.pack(fill='x', pady=4)
            tk.Label(row, text=f'{feature}:', bg='#000080', fg='#00ff00', font=('Courier', 10)).pack(side='left')
            tk.Label(row, text=state, bg='#000080', fg='#ffff00', font=('Courier', 10)).pack(side='right')
        
        # Boot Settings
        tk.Label(content, text='\\nBOOT SETTINGS:', bg='#000080', fg='#00ff00', font=('Courier', 11, 'bold')).pack(anchor='w')
        
        boot_info = ', '.join(self.settings['boot_order'])
        tk.Label(content, text=f'Boot Order: {boot_info}',
                 bg='#000080', fg='#00ff00', font=('Courier', 9)).pack(anchor='w', pady=4)
        
        # Hardware Status
        tk.Label(content, text='\\nHARDWARE STATUS:', bg='#000080', fg='#00ff00', font=('Courier', 11, 'bold')).pack(anchor='w')
        
        hw_status = self.get_hardware_status()
        for key, value in hw_status.items():
            label_text = key.upper().replace('_', ' ')
            if isinstance(value, (int, float)):
                value_text = f'{value}' + (' C' if 'temp' in key else ' RPM' if 'fan' in key else '%')
            else:
                value_text = str(value)
            tk.Label(content, text=f'{label_text}: {value_text}',
                     bg='#000080', fg='#00ff00', font=('Courier', 9)).pack(anchor='w', pady=2)
        
        # Buttons
        btn_frame = tk.Frame(bios_win, bg='#000080')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text='Save & Exit', bg='#00ff00', fg='#000080', 
                  command=lambda: [self.save_settings(), bios_win.destroy()],
                  font=('Courier', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text='Diagnostics', bg='#ffff00', fg='#000080',
                  command=lambda: self._show_diagnostics(root),
                  font=('Courier', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text='Exit', bg='#ff0000', fg='#ffffff',
                  command=bios_win.destroy,
                  font=('Courier', 10, 'bold')).pack(side='left', padx=5)
    
    def _show_diagnostics(self, root):
        """Show system diagnostics."""
        diag_win = tk.Toplevel(root)
        diag_win.title('System Diagnostics')
        diag_win.geometry('600x400')
        diag_win.configure(bg='#000080')
        
        tk.Label(diag_win, text='System Health Report',
                 bg='#000080', fg='#00ff00', font=('Courier', 12, 'bold')).pack(pady=10)
        
        report = self.diagnose_system()
        report_text = tk.Text(diag_win, bg='#000000', fg='#00ff00', font=('Courier', 9), height=18, width=70)
        report_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        report_str = ''
        for key, value in report.items():
            report_str += f'{key.upper()}: {value}\n'
        
        report_text.insert('1.0', report_str)
        report_text.config(state='disabled')
        
        tk.Button(diag_win, text='Close', bg='#00ff00', fg='#000080',
                  command=diag_win.destroy,
                  font=('Courier', 10, 'bold')).pack(pady=10)


class WindowsRepairSystem:
    """Automated Windows 7 repair and maintenance system."""
    
    def __init__(self, bios_sim):
        self.bios = bios_sim
        self.repair_log = []
    
    def auto_repair(self):
        """Automatically repair Windows system issues."""
        repairs = []
        
        # Check critical systems
        if not self.bios.settings['secure_boot']:
            repairs.append('⚠ Secure Boot is disabled. Enabling...')
            self.bios.toggle_feature('secure_boot')
        
        if self.bios.hardware_state['cpu_temp'] > 80:
            repairs.append('⚠ High CPU temperature detected. Optimizing...')
        
        # Hardware diagnostics
        if self.bios.hardware_state['fan_speed'] < 1500:
            repairs.append('⚠ Fan speed abnormal. Check cooling system.')
        
        self.repair_log.extend(repairs)
        return repairs
    
    def get_recommendations(self):
        """Generate system recommendations based on BIOS and hardware state."""
        recommendations = []
        hw = self.bios.get_hardware_status()
        
        if hw['cpu_temp'] > 70:
            recommendations.append('🔥 CPU temperature is high. Consider cleaning vents.')
        
        if hw['power_usage'] > 80:
            recommendations.append('⚡ High power consumption detected. Close unused apps.')
        
        if not self.bios.settings['virtualization']:
            recommendations.append('💻 Virtualization is disabled. Enable for better VM performance.')
        
        return recommendations


# Global BIOS instance
_bios_instance = None

def get_bios():
    """Get or create global BIOS simulator instance."""
    global _bios_instance
    if _bios_instance is None:
        _bios_instance = BIOSSimulator()
    return _bios_instance

def get_repair_system():
    """Get repair system instance."""
    return WindowsRepairSystem(get_bios())
