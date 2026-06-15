#!/usr/bin/env python3
"""
Stroke Animation Widget for Chinese Characters

Displays animated stroke order for Chinese characters using SVG paths.
Uses data from MakeMeAHanZI project.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSlider
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QColor, QFont, QBrush
from PyQt6.QtSvg import QSvgWidget
import json
from pathlib import Path
from typing import Dict, List, Optional


class StrokeAnimationWidget(QWidget):
    """Widget that displays animated stroke order for Chinese characters."""
    
    stroke_completed = pyqtSignal(int)  # Emits current stroke number
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_char = ""
        self.strokes: List[str] = []
        self.current_stroke_index = 0
        self.is_playing = False
        self.animation_speed = 500  # ms per stroke
        
        self._init_ui()
        self._setup_timer()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Character display label
        self.char_label = QLabel("?")
        self.char_label.setFont(QFont("Arial", 80, QFont.Weight.Bold))
        self.char_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.char_label.setMinimumHeight(150)
        layout.addWidget(self.char_label)
        
        # SVG widget for stroke rendering
        self.svg_widget = QSvgWidget()
        self.svg_widget.setMinimumSize(200, 200)
        self.svg_widget.setMaximumSize(300, 300)
        layout.addWidget(self.svg_widget)
        
        # Stroke counter
        self.stroke_counter = QLabel("Stroke: 0/0")
        self.stroke_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stroke_counter.setFont(QFont("Arial", 14))
        layout.addWidget(self.stroke_counter)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setFont(QFont("Arial", 12))
        self.play_btn.setMinimumHeight(40)
        self.play_btn.clicked.connect(self.toggle_play)
        btn_layout.addWidget(self.play_btn)
        
        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.setFont(QFont("Arial", 12))
        self.reset_btn.setMinimumHeight(40)
        self.reset_btn.clicked.connect(self.reset_animation)
        btn_layout.addWidget(self.reset_btn)
        
        layout.addLayout(btn_layout)
        
        # Speed slider
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Speed:")
        speed_label.setFont(QFont("Arial", 10))
        speed_layout.addWidget(speed_label)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(2000)
        self.speed_slider.setValue(500)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.valueChanged.connect(self.update_speed)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_value_label = QLabel("500ms")
        self.speed_value_label.setFont(QFont("Arial", 10))
        self.speed_value_label.setMinimumWidth(60)
        speed_layout.addWidget(self.speed_value_label)
        
        layout.addLayout(speed_layout)
        
        self.setLayout(layout)
    
    def _setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_stroke)
    
    def set_character(self, char: str, stroke_data: Optional[Dict] = None):
        """Set the character to display with optional stroke data."""
        self.current_char = char
        self.char_label.setText(char)
        
        if stroke_data and "strokes" in stroke_data:
            self.strokes = stroke_data["strokes"]
        else:
            self.strokes = []
        
        self.reset_animation()
        self.stroke_counter.setText(f"Stroke: 0/{len(self.strokes)}")
    
    def load_stroke_data(self, stroke_file: Path):
        """Load stroke data from JSON file."""
        try:
            with open(stroke_file, 'r', encoding='utf-8') as f:
                all_stroke_data = json.load(f)
            
            if self.current_char in all_stroke_data:
                self.set_character(self.current_char, all_stroke_data[self.current_char])
        except Exception as e:
            print(f"Error loading stroke data: {e}")
    
    def toggle_play(self):
        """Toggle animation play/pause."""
        if self.is_playing:
            self.pause_animation()
        else:
            self.start_animation()
    
    def start_animation(self):
        """Start stroke animation."""
        if not self.strokes:
            return
        
        self.is_playing = True
        self.play_btn.setText("⏸ Pause")
        self.timer.start(self.animation_speed)
    
    def pause_animation(self):
        """Pause stroke animation."""
        self.is_playing = False
        self.play_btn.setText("▶ Play")
        self.timer.stop()
    
    def reset_animation(self):
        """Reset animation to beginning."""
        self.pause_animation()
        self.current_stroke_index = 0
        self.play_btn.setText("▶ Play")
        self.stroke_counter.setText(f"Stroke: 0/{len(self.strokes)}")
        
        # Clear SVG
        self.svg_widget.load(b'')
    
    def next_stroke(self):
        """Animate next stroke."""
        if self.current_stroke_index >= len(self.strokes):
            self.pause_animation()
            self.animation_finished.emit()
            return
        
        stroke_path = self.strokes[self.current_stroke_index]
        self._render_stroke(stroke_path)
        
        self.current_stroke_index += 1
        self.stroke_counter.setText(f"Stroke: {self.current_stroke_index}/{len(self.strokes)}")
        self.stroke_completed.emit(self.current_stroke_index)
    
    def _render_stroke(self, path_data: str):
        """Render a single stroke as SVG."""
        # Build SVG with cumulative strokes
        svg_content = self._build_svg([self.strokes[i] for i in range(self.current_stroke_index + 1)])
        self.svg_widget.load(svg_content.encode('utf-8'))
    
    def _build_svg(self, paths: List[str]) -> str:
        """Build SVG content from stroke paths."""
        path_elements = ''.join([f'<path d="{p}" fill="#000000" stroke="#000000" stroke-width="2"/>' 
                                  for p in paths])
        
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
            <rect width="200" height="200" fill="#ffffff"/>
            {path_elements}
        </svg>'''
        
        return svg
    
    def update_speed(self, value: int):
        """Update animation speed."""
        self.animation_speed = value
        self.speed_value_label.setText(f"{value}ms")
        
        if self.is_playing:
            self.timer.setInterval(value)


class SimpleStrokeWidget(QWidget):
    """Simplified stroke display without animation (fallback option)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_char = ""
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Large character display
        self.char_label = QLabel("?")
        self.char_label.setFont(QFont("Arial", 120, QFont.Weight.Bold))
        self.char_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.char_label.setMinimumHeight(200)
        layout.addWidget(self.char_label)
        
        # Stroke count info
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
    
    def set_character(self, char: str, stroke_count: int = 0):
        """Display character with stroke count info."""
        self.current_char = char
        self.char_label.setText(char)
        
        if stroke_count > 0:
            self.info_label.setText(f"{stroke_count} strokes")
        else:
            self.info_label.setText("")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Stroke Animation Demo")
    window.setGeometry(100, 100, 400, 600)
    
    widget = StrokeAnimationWidget()
    widget.set_character("永", {"strokes": [
        "M 50 50 L 100 100",
        "M 100 100 L 150 150",
    ]})
    
    window.setCentralWidget(widget)
    window.show()
    
    sys.exit(app.exec())
