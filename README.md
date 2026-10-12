# System Resource Monitor

A desktop system resource monitor built with Python and Tkinter. It collects CPU, memory, disk, and network activity in the background, displays live charts, and stores measurements in SQLite for later analysis.

## Features

- Real-time CPU, memory, disk, and network monitoring
- Live Matplotlib charts with a dark interface
- Current, average, minimum, and maximum statistics
- Configurable in-memory history through `ResourceMonitor`
- SQLite persistence in `metrics.db`
- One-hour and 24-hour history views
- Custom historical analysis by resource, date, and time range
- Export historical plots as JPEG or PDF
- Thread-safe collection, database writes, and UI updates
- Built-in unit and integration tests

## Requirements

- Python 3.8 or newer
- Tkinter, usually included with Python
- `psutil`
- `matplotlib`

## Installation

1. Clone or download this repository, then open its directory in a terminal.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   On macOS or Linux, activate it with:

   ```bash
   source .venv/bin/activate
   ```

3. Install the Python dependencies:

   ```bash
   python -m pip install psutil matplotlib
   ```

## Run the application

Start the graphical monitor with:

```bash
python monitor_gui.py
```

The application begins collecting metrics at one-second intervals. The main window shows live charts and summary statistics. Use the **File** menu to view recent history or the **Analysis** menu to create a custom historical plot.

To close the application, close the window or choose **File > Exit**. The monitor stops its background thread before the window closes.

## Run the tests

Run the complete test suite with:

```bash
python run_tests.py
```

The tests cover resource collection, thread lifecycle, statistics, database persistence, concurrent writes, and GUI data integration. Temporary test databases are created and removed during the test run.

## Project structure

| File | Purpose |
| --- | --- |
| `monitor_gui.py` | Tkinter application window, live charts, menus, and status bar |
| `main.py` | Background resource collection and statistics |
| `database.py` | Thread-safe SQLite storage and historical queries |
| `analysis.py` | Historical plotting and JPEG/PDF export |
| `run_tests.py` | Test-suite runner |
| `test_main.py` | Resource monitor tests |
| `test_database.py` | SQLite database tests |
| `test_gui.py` | GUI data integration tests |

## Generated files

When the application runs, it creates or updates:

- `metrics.db` - SQLite database containing collected measurements
- `resource_monitor.log` - application log file

These files are runtime data and can be deleted if you want to start with an empty history.

## Notes

- Network values are displayed in KB/s and are calculated from the change in total network counters between samples.
- CPU, memory, and disk percentages are reported on a 0-100 scale.
- The default disk path is `/`, which is supported by `psutil` on Windows and Unix-like systems.
