import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from main import ResourceMonitor
import threading
from datetime import datetime
from analysis import HistoryAnalysisWindow


class ResourceMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Resource Monitor")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1a1a")
        
        self.monitor = ResourceMonitor(interval=1, max_data_points=60)
        self.monitor.start()
        self.running = True
        
        self._setup_styles()
        self._build_ui()
        self._start_updates()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        self.colors = {
            'bg': '#1a1a1a',
            'fg': '#e0e0e0',
            'accent': '#00d4ff',
            'dark': '#262626',
            'grid': '#404040'
        }
        
        style.configure("TLabel", background=self.colors['bg'], foreground=self.colors['fg'], font=("Arial", 10))
        style.configure("TLabel", background=self.colors['bg'], foreground=self.colors['fg'], font=("Arial", 11, "bold"))
        style.configure("Value", font=("Arial", 10), foreground=self.colors['accent'], background=self.colors['bg'])
        style.configure("TFrame", background=self.colors['bg'])

    def _build_ui(self):
        self._build_menu()
        self._build_header()
        self._build_content()
    
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Metrics", command=self._export_metrics)
        file_menu.add_command(label="View History (1H)", command=lambda: self._show_history(60))
        file_menu.add_command(label="View History (24H)", command=lambda: self._show_history(1440))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Custom Analysis", command=self._open_analysis_window)
    
    def _build_header(self):
        header = tk.Frame(self.root, bg=self.colors['bg'])
        header.pack(side=tk.TOP, fill=tk.X, padx=2, pady=5)
        
        title = tk.Label(
            header,
            text="━━━  System Resource Monitor  ━━━",
            font=("Arial", 16, "bold"),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        title.pack(pady=5)
    
    def _build_content(self):
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self._build_sidebar(content)
        self._build_graphs(content)
    
    def _build_sidebar(self, parent):
        self.stats_frame = ttk.Frame(parent)
        self.stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        
        self.stat_labels = {}
        self._add_stat_card("CPU", "cpu")
        self._add_stat_card("Memory", "memory")
        self._add_stat_card("Disk", "disk")
        self._add_stat_card("Network", "network")

    def _add_stat_card(self, title, metric_type):
        card = ttk.Frame(self.stats_frame)
        card.pack(fill=tk.X, pady=5)
        
        card_title = ttk.Label(card, text=f"● {title}")
        card_title.configure(font=("Arial", 11, "bold"), foreground="#b0b0b0")
        card_title.pack(anchor=tk.W)
        
        self.stat_labels[metric_type] = {}
        
        if metric_type == "network":
            self._add_value_label(card, metric_type, "sent_current", "Sent: -- KB/s")
            self._add_value_label(card, metric_type, "recv_current", "Recv: -- KB/s")
            self._add_value_label(card, metric_type, "avg", "Avg Sent: -- KB/s | Recv: -- KB/s")
        else:
            self._add_value_label(card, metric_type, "current", "Current: --%")
            self._add_value_label(card, metric_type, "avg", "Average: --%")
            self._add_value_label(card, metric_type, "max", "Max: --%")
            self._add_value_label(card, metric_type, "min", "Min: --%")
    
    def _add_value_label(self, parent, metric_type, key, text):
        label = ttk.Label(parent, text=text)
        label.configure(font=("Arial", 10), foreground=self.colors['accent'])
        label.pack(anchor=tk.W, padx=(10, 0))
        self.stat_labels[metric_type][key] = label
    
    def _build_graphs(self, parent):
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(10, 6), dpi=100, facecolor=self.colors['bg'])
        self.fig.patch.set_alpha(1.0)
        
        self.ax_cpu = self.fig.add_subplot(2, 2, 1)
        self.ax_mem = self.fig.add_subplot(2, 2, 2)
        self.ax_disk = self.fig.add_subplot(2, 2, 3)
        self.ax_net = self.fig.add_subplot(2, 2, 4)
        
        for ax in [self.ax_cpu, self.ax_mem, self.ax_disk, self.ax_net]:
            self._style_axis(ax)
        
        self.fig.tight_layout(pad=2)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _style_axis(self, ax):
        ax.set_facecolor(self.colors['dark'])
        ax.tick_params(colors="#a0a0a0", labelsize=9)
        ax.spines['bottom'].set_color(self.colors['grid'])
        ax.spines['left'].set_color(self.colors['grid'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.2, color=self.colors['grid'], linestyle="--")

    def _start_updates(self):
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def _update_loop(self):
        while self.running:
            try:
                self.root.after(0, self._refresh_display)
            except:
                pass
            import time
            time.sleep(1)
    
    def _refresh_display(self):
        data = self.monitor.get_latest_data()
        stats = self.monitor.get_statistics()
        
        if not data:
            return
        
        self._update_stats(stats)
        self._update_graphs(data)
        
        try:
            self.canvas.draw_idle()
        except:
            pass
    
    def _update_stats(self, stats):
        if not stats:
            return
        
        if 'cpu' in stats:
            self._update_metric_labels('cpu', stats['cpu'])
        if 'memory' in stats:
            self._update_metric_labels('memory', stats['memory'])
        if 'disk' in stats:
            self._update_metric_labels('disk', stats['disk'])
        if 'network' in stats:
            self._update_network_labels(stats['network'])
    
    def _update_metric_labels(self, metric_type, data):
        labels = self.stat_labels[metric_type]
        labels['current'].config(text=f"Current: {data['current']:.1f}%")
        labels['avg'].config(text=f"Average: {data['avg']:.1f}%")
        labels['max'].config(text=f"Max: {data['max']:.1f}%")
        labels['min'].config(text=f"Min: {data['min']:.1f}%")
    
    def _update_network_labels(self, data):
        labels = self.stat_labels['network']
        labels['sent_current'].config(text=f"Sent: {data['sent_current']:.2f} KB/s")
        labels['recv_current'].config(text=f"Recv: {data['recv_current']:.2f} KB/s")
        labels['avg'].config(text=f"Avg Sent: {data['sent_avg']:.2f} | Recv: {data['recv_avg']:.2f} KB/s")

    def _update_graphs(self, data):
        cpu = [d.cpu_percent for d in data]
        mem = [d.memory_percent for d in data]
        disk = [d.disk_percent for d in data]
        sent = [d.net_sent for d in data]
        recv = [d.net_recv for d in data]
        
        self._plot_cpu(cpu)
        self._plot_memory(mem)
        self._plot_disk(disk)
        self._plot_network(sent, recv)
    
    def _plot_cpu(self, data):
        self.ax_cpu.clear()
        self.ax_cpu.fill_between(range(len(data)), data, alpha=0.3, color="#00d4ff")
        self.ax_cpu.plot(range(len(data)), data, color="#00d4ff", linewidth=2, marker='o', markersize=3)
        self.ax_cpu.set_title("CPU Usage (%)", color="#ffffff", fontsize=12, fontweight="bold")
        self.ax_cpu.set_ylim(0, 100)
        self._style_axis(self.ax_cpu)
    
    def _plot_memory(self, data):
        self.ax_mem.clear()
        self.ax_mem.fill_between(range(len(data)), data, alpha=0.3, color="#00ff88")
        self.ax_mem.plot(range(len(data)), data, color="#00ff88", linewidth=2, marker='s', markersize=3)
        self.ax_mem.set_title("Memory Usage (%)", color="#ffffff", fontsize=12, fontweight="bold")
        self.ax_mem.set_ylim(0, 100)
        self._style_axis(self.ax_mem)
    
    def _plot_disk(self, data):
        self.ax_disk.clear()
        self.ax_disk.fill_between(range(len(data)), data, alpha=0.3, color="#ffaa00")
        self.ax_disk.plot(range(len(data)), data, color="#ffaa00", linewidth=2, marker='^', markersize=3)
        self.ax_disk.set_title("Disk Usage (%)", color="#ffffff", fontsize=12, fontweight="bold")
        self.ax_disk.set_ylim(0, 100)
        self._style_axis(self.ax_disk)
    
    def _plot_network(self, sent, recv):
        self.ax_net.clear()
        self.ax_net.plot(range(len(sent)), sent, color="#ff6b6b", linewidth=2, marker='o', markersize=3, label="Sent (KB/s)")
        self.ax_net.plot(range(len(recv)), recv, color="#b366ff", linewidth=2, marker='s', markersize=3, label="Recv (KB/s)")
        self.ax_net.fill_between(range(len(sent)), sent, alpha=0.2, color="#ff6b6b")
        self.ax_net.fill_between(range(len(recv)), recv, alpha=0.2, color="#b366ff")
        self.ax_net.set_title("Network Usage (KB/s)", color="#ffffff", fontsize=12, fontweight="bold")
        self.ax_net.legend(facecolor=self.colors['dark'], edgecolor=self.colors['grid'], labelcolor="#ffffff", loc="upper left", fontsize=9)
        self._style_axis(self.ax_net)

    def on_close(self):
        self.running = False
        self.monitor.stop()
        self.root.destroy()
    
    def get_historical_data(self, minutes=60):
        return self.monitor.get_historical_data(minutes)
    
    def export_metrics(self):
        filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        success = self.monitor.export_history(filename)
        return filename if success else None
    
    def _export_metrics(self):
        try:
            filename = self.export_metrics()
            if filename:
                print(f"Metrics exported to {filename}")
        except Exception as e:
            print(f"Export failed: {e}")
    
    def _show_history(self, minutes):
        try:
            history = self.get_historical_data(minutes)
            count = len(history)
            
            history_window = tk.Toplevel(self.root)
            history_window.title(f"History ({minutes} minutes) - {count} records")
            history_window.geometry("600x400")
            history_window.configure(bg=self.colors['bg'])
            
            text_widget = tk.Text(history_window, bg=self.colors['dark'], fg=self.colors['fg'], font=("Courier", 9))
            text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            if not history:
                text_widget.insert(tk.END, "No historical data available.")
            else:
                header = f"{'Timestamp':<20} {'CPU%':>8} {'MEM%':>8} {'DISK%':>8} {'Sent':>10} {'Recv':>10}\n"
                text_widget.insert(tk.END, header)
                text_widget.insert(tk.END, "-" * len(header) + "\n")
                
                for record in history[-50:]:
                    line = f"{record['timestamp']:<20} {record['cpu_percent']:>7.1f}% {record['memory_percent']:>7.1f}% {record['disk_percent']:>7.1f}% {record['net_sent']:>9.2f} {record['net_recv']:>9.2f}\n"
                    text_widget.insert(tk.END, line)
            
            text_widget.config(state=tk.DISABLED)
            
            scrollbar = ttk.Scrollbar(history_window, command=text_widget.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.config(yscrollcommand=scrollbar.set)
            
        except Exception as e:
            print(f"History view failed: {e}")
    
    def _open_analysis_window(self):
        try:
            HistoryAnalysisWindow(self.root, self.monitor, self.colors)
        except Exception as e:
            print(f"Analysis window failed: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ResourceMonitorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
