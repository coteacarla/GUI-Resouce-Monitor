import os
import tkinter as tk
import threading
from datetime import datetime, timedelta
from tkinter import ttk, filedialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class HistoryAnalysisWindow:
    """Window for analyzing historical resource monitoring data with plots and visualizations."""

    def __init__(self, parent, monitor, colors):
        """
        Initialize the History Analysis window.
        
        Args:
            parent: Parent tkinter window
            monitor: Monitor object with database access
            colors: Dictionary containing color scheme for UI elements
        """
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
        """
        Build the control panel for plot configuration.
        
        Creates UI elements for:
        - Resource selection (CPU, Memory, Disk, Network, All)
        - Plot button
        - Date and time range inputs
        """
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
        """
        Handle plot button click event.
        
        Validates date inputs and launches plotting in a background thread
        to prevent UI freezing.
        """
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
        """
        Background thread for generating plot data.
        
        Retrieves metrics from database and generates appropriate plot
        based on selected resource type. Updates UI on main thread.
        
        Args:
            resource: Type of resource to plot ('cpu', 'memory', 'disk', 'network', 'all')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
        """
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
        """
        Filter historical data by time range.
        
        Args:
            history: List of metric records with timestamps
            
        Returns:
            Filtered list of records within specified hour:minute range
        """
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
        """
        Display matplotlib figure in the window with toolbar.
        
        Creates or updates canvas, toolbar, and save buttons.
        Cleans up previous plot if it exists.
        
        Args:
            fig: Matplotlib Figure object to display
        """
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if hasattr(self, 'toolbar_frame') and self.toolbar_frame:
            self.toolbar_frame.destroy()
        
       
        self.toolbar_frame = tk.Frame(self.plot_frame, bg=self.colors['dark'])
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        
        button_frame = tk.Frame(self.toolbar_frame, bg=self.colors['dark'])
        button_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Save JPEG", command=lambda: self._save_plot(fig, 'jpeg'),
                  bg=self.colors['accent'], fg=self.colors['bg'], padx=5).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Save PDF", command=lambda: self._save_plot(fig, 'pdf'),
                  bg=self.colors['accent'], fg=self.colors['bg'], padx=5).pack(side=tk.LEFT, padx=2)
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
    
    def _show_message(self, message):
        """
        Display a message in the plot area.
        
        Args:
            message: Text message to display
        """
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
        """
        Generate plot for a single resource type.
        
        Args:
            history: List of metric records
            resource: Resource type ('cpu', 'memory', 'disk', or 'network')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            Matplotlib Figure object
        """
        fig = Figure(figsize=(9, 6), dpi=100, facecolor=self.colors['bg'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.colors['dark'])
        
        timestamps = [datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S') for r in history]
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        start_time = self.start_time_var.get().strip()
        end_time = self.end_time_var.get().strip()
        
        if not start_time and not end_time:
            x_positions = [(ts - start_dt).total_seconds() / 3600 for ts in timestamps]
            total_hours = (end_dt - start_dt).total_seconds() / 3600 + 24
        else:
            start_hour, start_min = map(int, start_time.split(':'))
            start_dt_with_time = start_dt.replace(hour=start_hour, minute=start_min)
            x_positions = [(ts - start_dt_with_time).total_seconds() / 3600 for ts in timestamps]
            if x_positions:
                total_hours = max(x_positions)
            else:
                total_hours = 1
        
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
        
        ax.set_xlim(0, total_hours)
        ax.set_xlabel('Time (hours)', color='#a0a0a0', fontsize=10)
        self._style_axis(ax, label)
        
        return fig
    
    def _plot_all(self, history, start_date, end_date):
        """
        Generate plot with all resource types in subplots.
        
        Creates a 4-subplot figure with CPU, Memory, Disk, and Network data.
        
        Args:
            history: List of metric records
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            Matplotlib Figure object with 4 subplots
        """
        fig = Figure(figsize=(9, 8), dpi=100, facecolor=self.colors['bg'])
        
        timestamps = [datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S') for r in history]
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        start_time = self.start_time_var.get().strip()
        end_time = self.end_time_var.get().strip()
        
        if not start_time and not end_time:
            x_positions = [(ts - start_dt).total_seconds() / 3600 for ts in timestamps]
            total_hours = (end_dt - start_dt).total_seconds() / 3600 + 24
        else: 
            start_hour, start_min = map(int, start_time.split(':'))
            start_dt_with_time = start_dt.replace(hour=start_hour, minute=start_min)
            x_positions = [(ts - start_dt_with_time).total_seconds() / 3600 for ts in timestamps]
            if x_positions:
                total_hours = max(x_positions)
            else:
                total_hours = 1
        
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
            ax.set_xlim(0, total_hours)
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
        ax.set_xlim(0, total_hours)
        self._style_axis_compact(ax)
        ax.legend(loc='upper left', fontsize=8)
        
        fig.suptitle('All Resources', color='#ffffff', fontsize=12, fontweight='bold')
        
        return fig
    
   
    
    def _style_axis(self, ax, label):
        """
        Apply styling to a single plot axis.
        
        Args:
            ax: Matplotlib axis object
            label: Title/label for the axis
        """
        ax.set_title(label, color='#ffffff', fontsize=12, fontweight='bold')
        ax.tick_params(colors='#a0a0a0', labelsize=9)
        ax.spines['bottom'].set_color(self.colors['grid'])
        ax.spines['left'].set_color(self.colors['grid'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.2, color=self.colors['grid'], linestyle='--')
    
    def _style_axis_compact(self, ax):
        """
        Apply compact styling to subplot axes.
        
        Used for multi-plot figures with limited space.
        
        Args:
            ax: Matplotlib axis object
        """
        ax.tick_params(colors='#a0a0a0', labelsize=8)
        ax.spines['bottom'].set_color(self.colors['grid'])
        ax.spines['left'].set_color(self.colors['grid'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.2, color=self.colors['grid'], linestyle='--')


    def _save_plot(self, fig, file_format):
        """
        Save the current plot to a file.
        
        Generates filename with timestamp and opens save dialog.
        Supports JPEG and PDF formats.
        
        Args:
            fig: Matplotlib Figure object to save
            file_format: Format string ('jpeg' or 'pdf')
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        resource = self.resource_var.get()
        
        filename = f"plot_{resource}_{start_date}_{end_date}_{timestamp}.{file_format}"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{file_format}",
            filetypes=[(file_format.upper(), f"*.{file_format}")],
            initialfile=filename
        )
        
        if file_path:
            try:
                fig.savefig(file_path, format=file_format, dpi=150, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot saved successfully as {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save plot: {e}")
