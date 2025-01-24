import sys
import json
from PyQt5 import QtCore, QtWidgets
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List, Tuple, Union
from enum import Enum, auto
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np


class PlotType(Enum):
    """Enumeration of supported plot types"""
    IMAGE = auto()
    LINE = auto()
    MULTILINE = auto()

@dataclass
class PlotConfig:
    """Configuration for a plot, including its display properties and artists"""
    ax: plt.Axes
    title: str
    plot_type: PlotType
    xlabel: str = ''
    ylabel: str = ''
    cmap: Optional[str] = None
    clim: Optional[Tuple[float, float]] = None
    grid: bool = True
    animated: bool = True
    overlay_artists: List[Any] = field(default_factory=list)
    artists: List[Any] = field(default_factory=list)
    background: Optional[Any] = None

class PlotManager:
    """Manages plot configurations, initialization and updates with blitting support"""
    
    def __init__(self, fig: Figure):
        self.fig = fig
        self.plots: Dict[str, PlotConfig] = {}
        self.initialized = False
    
    def add_plot(self, name: str, config: PlotConfig) -> None:
        """Register a new plot configuration"""
        self.plots[name] = config
    
    def initialize_plots(self) -> None:
        """Initialize all registered plots with dummy data"""
        if self.initialized:
            return
            
        for name, cfg in self.plots.items():
            # Set common properties
            cfg.ax.set_title(cfg.title)
            cfg.ax.set_xlabel(cfg.xlabel)
            cfg.ax.set_ylabel(cfg.ylabel)
            if cfg.grid:
                cfg.ax.grid(True)
            
            # Create appropriate artists based on plot type
            if cfg.plot_type == PlotType.IMAGE:
                dummy_data = np.zeros((100, 100))
                artist = cfg.ax.imshow(
                    dummy_data,
                    animated=cfg.animated,
                    cmap=cfg.cmap
                )
                if cfg.clim:
                    artist.set_clim(*cfg.clim)
                cfg.artists.append(artist)
            elif cfg.plot_type == PlotType.LINE:
                artist, = cfg.ax.plot([], [], animated=cfg.animated)
                cfg.artists.append(artist)
            elif cfg.plot_type == PlotType.MULTILINE:
                for _ in range(3):  # For 1D potential plot
                    artist, = cfg.ax.plot([], [], animated=cfg.animated)
                    cfg.artists.append(artist)
        
        # Store backgrounds for blitting
        self.fig.canvas.draw()
        for cfg in self.plots.values():
            cfg.background = self.fig.canvas.copy_from_bbox(cfg.ax.bbox)
        
        self.initialized = True
    
    def restore_backgrounds(self) -> None:
        """Restore the background for all plots"""
        for cfg in self.plots.values():
            self.fig.canvas.restore_region(cfg.background)
    
    def update_plot(self, name: str, data: Union[np.ndarray, Tuple[np.ndarray, np.ndarray], List[Tuple[np.ndarray, np.ndarray]]], 
                   extent: Optional[Tuple[float, float, float, float]] = None, clim: Optional[Tuple[float, float]] = None) -> None:
        """Update a plot with new data"""
        if not self.initialized:
            raise RuntimeError("Plots must be initialized before updating")
            
        cfg = self.plots[name]
        
        if cfg.plot_type == PlotType.IMAGE:
            cfg.artists[0].set_data(data)
            if extent is not None:
                cfg.artists[0].set_extent(extent)
            if clim is not None:
                cfg.artists[0].set_clim(*clim)
        elif cfg.plot_type == PlotType.LINE:
            if not isinstance(data, tuple) or len(data) != 2:
                raise ValueError("Line plots require x and y data as tuple")
            x, y = data
            cfg.artists[0].set_data(x, y)
            cfg.ax.relim()
            cfg.ax.autoscale_view()
        elif cfg.plot_type == PlotType.MULTILINE:
            if not isinstance(data, list) or len(data) != len(cfg.artists):
                raise ValueError(f"Multiline plots require {len(cfg.artists)} data series")
            for artist, (x, y) in zip(cfg.artists, data):
                artist.set_data(x, y)
            cfg.ax.relim()
            cfg.ax.autoscale_view()
        
        # Draw main artists and any overlays
        for artist in cfg.artists:
            cfg.ax.draw_artist(artist)
        for artist in cfg.overlay_artists:
            cfg.ax.draw_artist(artist)
    
    def blit(self) -> None:
        """Perform final blitting update"""
        self.fig.canvas.blit(self.fig.bbox)
        self.fig.canvas.flush_events()


class GUITemplate(QtWidgets.QMainWindow):
    def __init__(self, title="Application GUI"):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(title)
        self.main_widget = QtWidgets.QWidget(self)
        
        # Initialize parameter specifications
        self.param_specs = {}
        self.param_widgets = {}
        
        # Create GUI
        #self.create_gui()
        
    def create_gui(self):
        """Create the main GUI layout and widgets"""
        # Main layout
        l00 = QtWidgets.QHBoxLayout(self.main_widget)
        
        # Control panel layout
        l0 = QtWidgets.QVBoxLayout()
        l00.addLayout(l0)
        
        # Create widgets for each parameter group
        current_group = None
        current_layout = None
        
        for param_name, spec in self.param_specs.items():
            # Create new group if needed
            if spec['group'] != current_group:
                current_group = spec['group']
                gb = QtWidgets.QGroupBox(current_group)
                l0.addWidget(gb)
                current_layout = QtWidgets.QVBoxLayout(gb)
            
            # Create widget layout
            hb = QtWidgets.QHBoxLayout()
            current_layout.addLayout(hb)
            hb.addWidget(QtWidgets.QLabel(f"{param_name}:"))
            
            # Create appropriate widget type
            if spec['widget'] == 'double':
                widget = QtWidgets.QDoubleSpinBox()
                widget.setRange(*spec['range'])
                widget.setValue(spec['value'])
                widget.setSingleStep(spec['step'])
                if 'decimals' in spec:
                    widget.setDecimals(spec['decimals'])
            elif spec['widget'] == 'int':
                widget = QtWidgets.QSpinBox()
                widget.setRange(*spec['range'])
                widget.setValue(spec['value'])
                if 'step' in spec:
                    widget.setSingleStep(spec['step'])
            
            widget.valueChanged.connect(self.on_parameter_change)
            hb.addWidget(widget)
            self.param_widgets[param_name] = widget
        
        # Add common controls
        self.add_common_controls(l0)
        
        # Set the central widget
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
    
    def add_common_controls(self, layout):
        """Add common control buttons"""
        # Auto-update checkbox
        hb = QtWidgets.QHBoxLayout()
        layout.addLayout(hb)
        self.cbAutoUpdate = QtWidgets.QCheckBox("Auto-update")
        self.cbAutoUpdate.setChecked(True)
        hb.addWidget(self.cbAutoUpdate)
        
        # Run Button
        btn = QtWidgets.QPushButton("Run")
        btn.clicked.connect(self.run)
        hb.addWidget(btn)
        
        # Save/Load buttons
        hb = QtWidgets.QHBoxLayout()
        layout.addLayout(hb)
        btnSave = QtWidgets.QPushButton("Save Parameters")
        btnSave.clicked.connect(self.save_parameters)
        hb.addWidget(btnSave)
        btnLoad = QtWidgets.QPushButton("Load Parameters")
        btnLoad.clicked.connect(self.load_parameters)
        hb.addWidget(btnLoad)
    
    def get_param_values(self):
        """Get current values of all parameters"""
        return {name: widget.value() for name, widget in self.param_widgets.items()}
    
    def set_param_values(self, values):
        """Set values for all parameters"""
        for name, value in values.items():
            if name in self.param_widgets:
                self.param_widgets[name].setValue(value)
    
    def save_parameters(self):
        """Save parameters to JSON file"""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Parameters", "", "JSON files (*.json)")
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            with open(filename, 'w') as f:
                json.dump(self.get_param_values(), f, indent=4)
    
    def load_parameters(self):
        """Load parameters from JSON file"""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Parameters", "", "JSON files (*.json)")
        if filename:
            with open(filename, 'r') as f:
                values = json.load(f)
                self.set_param_values(values)
                self.run()
    
    def on_parameter_change(self):
        """Handle parameter changes"""
        if self.cbAutoUpdate.isChecked():
            self.run()
    
    def run(self):
        """Main execution method to be implemented by child classes"""
        raise NotImplementedError("Child classes must implement run() method")

if __name__ == "__main__":
    qApp = QtWidgets.QApplication(sys.argv)
    aw = GUITemplate()
    aw.show()
    sys.exit(qApp.exec_())
