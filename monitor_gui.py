import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from main import ResourceMonitor  


class ResourceMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Resource Monitor")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e1e1e")

       
        self.monitor = ResourceMonitor(interval=1)
        self.monitor.start()

        self.create_gui()
        self.update_plots()

    def create_gui(self):
        style = ttk.Style()
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))

        ttk.Label(self.root, text="System Resource Monitor", style="Header.TLabel").pack(pady=10)

       
        self.fig, self.axes = plt.subplots(2, 2, figsize=(10, 6), facecolor="#1e1e1e")
        self.ax_cpu, self.ax_mem, self.ax_disk, self.ax_net = self.axes.flatten()
        self.fig.tight_layout(pad=3)

        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_plots(self):
        data = self.monitor.get_latest_data()
        if not data:
            self.root.after(1000, self.update_plots)
            return

        timestamps = [d.timestamp for d in data]
        cpu = [d.cpu_percent for d in data]
        mem = [d.memory_percent for d in data]
        disk = [d.disk_percent for d in data]
        sent = [d.net_sent for d in data]
        recv = [d.net_recv for d in data]

        
        self.ax_cpu.clear()
        self.ax_cpu.plot(timestamps, cpu, color="lime")
        self.ax_cpu.set_title("CPU Usage (%)", color="white")
        self.ax_cpu.tick_params(colors="white")
        self.ax_cpu.set_ylim(0, 100)

       
        self.ax_mem.clear()
        self.ax_mem.plot(timestamps, mem, color="deepskyblue")
        self.ax_mem.set_title("Memory Usage (%)", color="white")
        self.ax_mem.tick_params(colors="white")
        self.ax_mem.set_ylim(0, 100)

      
        self.ax_disk.clear()
        self.ax_disk.plot(timestamps, disk, color="orange")
        self.ax_disk.set_title("Disk Usage (%)", color="white")
        self.ax_disk.tick_params(colors="white")
        self.ax_disk.set_ylim(0, 100)

      
        self.ax_net.clear()
        self.ax_net.plot(timestamps, sent, color="violet", label="Sent (KB/s)")
        self.ax_net.plot(timestamps, recv, color="yellow", label="Recv (KB/s)")
        self.ax_net.set_title("Network (KB/s)", color="white")
        self.ax_net.legend(facecolor="#1e1e1e", edgecolor="white", labelcolor="white")
        self.ax_net.tick_params(colors="white")

        self.fig.tight_layout()
        self.canvas.draw()

       
        self.root.after(1000, self.update_plots)

    def on_close(self):
        self.monitor.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ResourceMonitorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
