import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from datetime import datetime, timedelta
import threading


class HistoryAnalysisWindow:
    def __init__(self, parent, monitor, colors):
        self.parent = parent
        self.monitor = monitor
        self.colors = colors
        self.canvas = None
        self.toolbar = None
        self.plotting = False
        
        self.window = tk.Toplevel(parent)
        self.window.title("Analysis")
        self.window.geometry("900x700")
        self.window.configure(bg=self.colors['bg'])
        
        self._build_controls()
        
        self.plot_frame = tk.Frame(self.window, bg=self.colors['dark'])
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _build_controls(self):
        ctrl = tk.Frame(self.window, bg=self.colors['bg'])
        ctrl.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(ctrl, text="Resource:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.resource_var = tk.StringVar(value='cpu')
        for label, value in [('CPU', 'cpu'), ('Memory', 'memory'), ('Disk', 'disk'), ('Network', 'network'), ('All', 'all')]:
            tk.Radiobutton(ctrl, text=label, variable=self.resource_var, value=value, bg=self.colors['bg'], fg=self.colors['fg'], selectcolor=self.colors['dark']).pack(side=tk.LEFT, padx=5)
        
        tk.Button(ctrl, text="Plot", command=self._plot, bg=self.colors['accent'], fg=self.colors['bg'], padx=10).pack(side=tk.LEFT, padx=10)
        
        date_ctrl = tk.Frame(self.window, bg=self.colors['bg'])
        date_ctrl.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(date_ctrl, text="Start Date:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
        tk.Entry(date_ctrl, textvariable=self.start_date_var, width=12, bg=self.colors['dark'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_ctrl, text="Start Hour:Min:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.start_time_var = tk.StringVar(value='')
        tk.Entry(date_ctrl, textvariable=self.start_time_var, width=8, bg=self.colors['dark'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_ctrl, text="End Date:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=20)
        self.end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        tk.Entry(date_ctrl, textvariable=self.end_date_var, width=12, bg=self.colors['dark'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_ctrl, text="End Hour:Min:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.end_time_var = tk.StringVar(value='')
        tk.Entry(date_ctrl, textvariable=self.end_time_var, width=8, bg=self.colors['dark'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
    
    def _plot(self):
        if self.plotting:
            return
        
        resource = self.resource_var.get()
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        
        if not start_date or not end_date:
            self._show_message("Please enter both start and end dates")
            return
        
        self.plotting = True
        thread = threading.Thread(target=self._plot_thread, args=(resource, start_date, end_date), daemon=True)
        thread.start()
    
    def _plot_thread(self, resource, start_date, end_date):
        try:
            history = self.monitor.db.get_metrics_by_date_range(start_date, end_date)
            
            if not history:
                self.window.after(0, self._show_message, f"No data available for {start_date} to {end_date}")
                self.plotting = False
                return
            
            history = self._filter_by_time(history)
            
            if not history:
                self.window.after(0, self._show_message, f"No data in selected time range")
                self.plotting = False
                return
            
            if resource == 'all':
                fig = self._plot_all(history, start_date, end_date)
            else:
                fig = self._plot_single(history, resource, start_date, end_date)
            
            self.window.after(0, self._display_plot, fig)
            self.plotting = False
        except Exception as e:
            print(f"Error: {e}")
            self.plotting = False
    
    def _filter_by_time(self, history):
        start_time = self.start_time_var.get().strip()
        end_time = self.end_time_var.get().strip()
        
        if not start_time and not end_time:
            return history
        
        filtered = []
        for record in history:
            ts = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
            time_str = ts.strftime('%H:%M')
            
            include = True
            if start_time:
                include = include and time_str >= start_time
            if end_time:
                include = include and time_str <= end_time
            
            if include:
                filtered.append(record)
        
        return filtered
    
    def _display_plot(self, fig):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.destroy()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
    
    def _show_message(self, message):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        fig = Figure(figsize=(9, 6), dpi=100, facecolor=self.colors['bg'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.colors['dark'])
        ax.axis('off')
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=14, color='#ffffff', transform=ax.transAxes)
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
    
    def _plot_single(self, history, resource, start_date, end_date):
        fig = Figure(figsize=(9, 6), dpi=100, facecolor=self.colors['bg'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.colors['dark'])
        
        timestamps = [datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S') for r in history]
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        x_positions = [(ts - start_dt).total_seconds() / 3600 for ts in timestamps]
        
        if resource == 'cpu':
            values = [r['cpu_percent'] for r in history]
            color, label = '#00d4ff', 'CPU (%)'
            ax.set_ylim(0, 100)
        elif resource == 'memory':
            values = [r['memory_percent'] for r in history]
            color, label = '#00ff88', 'Memory (%)'
            ax.set_ylim(0, 100)
        elif resource == 'disk':
            values = [r['disk_percent'] for r in history]
            color, label = '#ffaa00', 'Disk (%)'
            ax.set_ylim(0, 100)
        else:
            sent = [r['net_sent'] for r in history]
            recv = [r['net_recv'] for r in history]
            ax.plot(x_positions, sent, color='#ff6b6b', linewidth=2, label='Sent')
            ax.plot(x_positions, recv, color='#b366ff', linewidth=2, label='Recv')
            ax.fill_between(x_positions, sent, alpha=0.2, color='#ff6b6b')
            ax.fill_between(x_positions, recv, alpha=0.2, color='#b366ff')
            ax.legend(loc='upper left', fontsize=9)
            label = 'Network (KB/s)'
            values = None
        
        if values:
            ax.plot(x_positions, values, color=color, linewidth=2)
            ax.fill_between(x_positions, values, alpha=0.2, color=color)
        
        ax.set_xlabel('Time (hours)', color='#a0a0a0', fontsize=10)
        self._style_axis(ax, label)
        
        return fig
    
    def _plot_all(self, history, start_date, end_date):
        fig = Figure(figsize=(9, 8), dpi=100, facecolor=self.colors['bg'])
        
        timestamps = [datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S') for r in history]
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        x_positions = [(ts - start_dt).total_seconds() / 3600 for ts in timestamps]
        
        resources = [
            ('cpu', 'CPU (%)', '#00d4ff', [r['cpu_percent'] for r in history]),
            ('memory', 'Memory (%)', '#00ff88', [r['memory_percent'] for r in history]),
            ('disk', 'Disk (%)', '#ffaa00', [r['disk_percent'] for r in history]),
        ]
        
        for idx, (_, label, color, values) in enumerate(resources, 1):
            ax = fig.add_subplot(4, 1, idx)
            ax.set_facecolor(self.colors['dark'])
            ax.plot(x_positions, values, color=color, linewidth=2)
            ax.fill_between(x_positions, values, alpha=0.2, color=color)
            ax.set_title(label, color='#ffffff', fontsize=10, fontweight='bold')
            ax.set_ylim(0, 100)
            self._style_axis_compact(ax)
            ax.set_xticks([])
        
        ax = fig.add_subplot(4, 1, 4)
        ax.set_facecolor(self.colors['dark'])
        sent = [r['net_sent'] for r in history]
        recv = [r['net_recv'] for r in history]
        ax.plot(x_positions, sent, color='#ff6b6b', linewidth=2, label='Sent')
        ax.plot(x_positions, recv, color='#b366ff', linewidth=2, label='Recv')
        ax.fill_between(x_positions, sent, alpha=0.2, color='#ff6b6b')
        ax.fill_between(x_positions, recv, alpha=0.2, color='#b366ff')
        ax.set_title('Network (KB/s)', color='#ffffff', fontsize=10, fontweight='bold')
        ax.set_xlabel('Time (hours)', color='#a0a0a0', fontsize=9)
        self._style_axis_compact(ax)
        ax.legend(loc='upper left', fontsize=8)
        
        fig.suptitle('All Resources', color='#ffffff', fontsize=12, fontweight='bold')
        
        return fig
    
    def _style_axis(self, ax, label):
        ax.set_title(label, color='#ffffff', fontsize=12, fontweight='bold')
        ax.tick_params(colors='#a0a0a0', labelsize=9)
        ax.spines['bottom'].set_color(self.colors['grid'])
        ax.spines['left'].set_color(self.colors['grid'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.2, color=self.colors['grid'], linestyle='--')
    
    def _style_axis_compact(self, ax):
        ax.tick_params(colors='#a0a0a0', labelsize=8)
        ax.spines['bottom'].set_color(self.colors['grid'])
        ax.spines['left'].set_color(self.colors['grid'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.2, color=self.colors['grid'], linestyle='--')
