#!/usr/bin/env python3
"""
Mandarin Chinese Flashcard Application - Cross-platform (Linux/Windows)
Inspired by ZDT - Zhongwen Development Tool

Features:
- HSK vocabulary flashcards (levels 1-6)
- CEDICT dictionary integration (download and search)
- Spaced repetition system (SM-2 algorithm)
- Study mode with self-assessment
- Quiz mode with multiple choice questions
- Browse mode with search functionality
- Statistics and progress tracking
- Custom deck creation
- Import/Export functionality
"""

import sys
import json
import random
import gzip
import shutil
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QProgressBar, QMessageBox,
    QFileDialog, QInputDialog, QLineEdit, QDialog, QDialogButtonBox,
    QScrollArea, QFrame, QComboBox, QGroupBox, QTextEdit, QFormLayout,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QAction

# HSK Vocabulary Data
HSK_VOCABULARY = {
    "HSK 1": [
        {"character": "你好", "pinyin": "nǐ hǎo", "meaning": "Hello"},
        {"character": "谢谢", "pinyin": "xiè xie", "meaning": "Thank you"},
        {"character": "再见", "pinyin": "zài jiàn", "meaning": "Goodbye"},
        {"character": "我", "pinyin": "wǒ", "meaning": "I; me"},
        {"character": "你", "pinyin": "nǐ", "meaning": "You"},
        {"character": "好", "pinyin": "hǎo", "meaning": "Good; well"},
        {"character": "人", "pinyin": "rén", "meaning": "Person"},
        {"character": "中国", "pinyin": "Zhōng guó", "meaning": "China"},
        {"character": "朋友", "pinyin": "péng you", "meaning": "Friend"},
        {"character": "学习", "pinyin": "xué xí", "meaning": "To study"},
    ],
    "HSK 2": [
        {"character": "帮助", "pinyin": "bāng zhù", "meaning": "To help"},
        {"character": "北京", "pinyin": "Běi jīng", "meaning": "Beijing"},
        {"character": "吃", "pinyin": "chī", "meaning": "To eat"},
        {"character": "茶", "pinyin": "chá", "meaning": "Tea"},
    ],
}


class FlashcardData:
    """Manages flashcard data and user progress using spaced repetition."""
    
    def __init__(self):
        self.user_progress = {}
        self.data_file = Path.home() / ".mandarin_flashcards" / "progress.json"
        self.custom_decks = {}
        self.load_data()
    
    def load_data(self):
        """Load user progress from file."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.user_progress = data.get("progress", {})
                    self.custom_decks = data.get("custom_decks", {})
            except Exception:
                pass
    
    def save_data(self):
        """Save user progress to file."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(
                {"progress": self.user_progress, "custom_decks": self.custom_decks},
                f, ensure_ascii=False, indent=2
            )
    
    def get_cards_for_level(self, level: str) -> List[Dict]:
        """Get cards for a specific level or custom deck."""
        return self.custom_decks.get(level, HSK_VOCABULARY.get(level, []))
    
    def update_progress(self, card: Dict, correct: bool):
        """Update progress using SM-2 spaced repetition algorithm."""
        cid = f"{card['character']}_{card['pinyin']}"
        if cid not in self.user_progress:
            self.user_progress[cid] = {
                "times_correct": 0, "times_incorrect": 0,
                "repetitions": 0, "interval": 0, "ease_factor": 2.5
            }
        p = self.user_progress[cid]
        if correct:
            p["times_correct"] += 1
            p["repetitions"] += 1
            if p["repetitions"] == 1:
                p["interval"] = 1
            elif p["repetitions"] == 2:
                p["interval"] = 6
            else:
                p["interval"] = int(p["interval"] * p["ease_factor"])
            p["ease_factor"] = max(1.3, p["ease_factor"] + 0.1)
        else:
            p["times_incorrect"] += 1
            p["repetitions"] = 0
            p["interval"] = 1
        self.save_data()
    
    def get_statistics(self) -> Dict:
        """Get learning statistics."""
        tc = sum(p["times_correct"] for p in self.user_progress.values())
        ti = sum(p["times_incorrect"] for p in self.user_progress.values())
        total = tc + ti
        mastery = {"new": 0, "learning": 0, "reviewing": 0, "mastered": 0}
        for p in self.user_progress.values():
            r = p["repetitions"]
            if r == 0:
                mastery["new"] += 1
            elif r < 5:
                mastery["learning"] += 1
            elif r < 10:
                mastery["reviewing"] += 1
            else:
                mastery["mastered"] += 1
        return {
            "total_cards": len(self.user_progress),
            "total_reviews": total,
            "accuracy": (tc / total * 100) if total > 0 else 0,
            "mastery": mastery
        }
    
    def create_custom_deck(self, name: str, cards: List[Dict]):
        """Create a custom deck."""
        self.custom_decks[name] = cards
        self.save_data()


class CedictEntry:
    """Represents a single entry from the CEDICT dictionary."""
    
    def __init__(self, traditional: str, simplified: str, pinyin: str, meanings: List[str]):
        self.traditional = traditional
        self.simplified = simplified
        self.pinyin = pinyin
        self.meanings = meanings
    
    @property
    def display_char(self) -> str:
        """Return simplified character if different, otherwise traditional."""
        return self.simplified if self.simplified != self.traditional else self.traditional
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format for flashcards."""
        return {
            "character": self.display_char,
            "pinyin": self.pinyin,
            "meaning": "; ".join(self.meanings[:3])  # Show first 3 meanings
        }


class CedictManager:
    """Manages downloading, parsing, and searching the CEDICT dictionary."""
    
    CEDICT_URL = "https://www.mdbg.net/chindict/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt"
    CEDICT_GZ_URL = "https://cc-cedict.org/download/cedict_ts.u8.gz"
    
    def __init__(self):
        self.data_dir = Path.home() / ".mandarin_flashcards" / "cedict"
        self.data_file = self.data_dir / "cedict_ts.u8"
        self.entries: List[CedictEntry] = []
        self.is_loaded = False
        self.is_downloading = False
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def download_cedict(self, progress_callback=None) -> bool:
        """Download the CEDICT database from cc-cedict.org."""
        try:
            self.is_downloading = True
            if progress_callback:
                progress_callback("Downloading CEDICT dictionary...")
            
            # Try the gzipped version first (smaller download)
            urls_to_try = [self.CEDICT_GZ_URL, self.CEDICT_URL]
            
            for url in urls_to_try:
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=30) as response:
                        data = response.read()
                    
                    if url.endswith('.gz'):
                        # Decompress gzip file
                        if progress_callback:
                            progress_callback("Decompressing...")
                        with open(self.data_file, 'wb') as f:
                            f.write(gzip.decompress(data))
                    else:
                        with open(self.data_file, 'wb') as f:
                            f.write(data)
                    
                    if progress_callback:
                        progress_callback("Download complete!")
                    
                    self.is_downloading = False
                    return True
                    
                except Exception as e:
                    print(f"Failed to download from {url}: {e}")
                    continue
            
            self.is_downloading = False
            return False
            
        except Exception as e:
            self.is_downloading = False
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
            return False
    
    def parse_cedict(self, progress_callback=None) -> int:
        """Parse the CEDICT file and load entries into memory."""
        if not self.data_file.exists():
            return 0
        
        self.entries = []
        count = 0
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse CEDICT format: Traditional Simplified [pinyin] /meanings/
                match = re.match(r'^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)$', line)
                if match:
                    traditional = match.group(1)
                    simplified = match.group(2)
                    pinyin = match.group(3)
                    meanings_str = match.group(4)
                    
                    # Split meanings by /
                    meanings = [m.strip() for m in meanings_str.split('/') if m.strip()]
                    
                    if meanings:
                        entry = CedictEntry(traditional, simplified, pinyin, meanings)
                        self.entries.append(entry)
                        count += 1
                
                # Progress callback every 10000 lines
                if progress_callback and i % 10000 == 0:
                    progress_callback(f"Parsing: {i}/{total_lines} lines...")
            
            self.is_loaded = True
            return count
            
        except Exception as e:
            print(f"Error parsing CEDICT: {e}")
            return 0
    
    def search(self, query: str, limit: int = 100) -> List[CedictEntry]:
        """Search the dictionary by character, pinyin, or meaning."""
        if not self.is_loaded or not self.entries:
            return []
        
        query = query.lower().strip()
        if not query:
            return []
        
        results = []
        for entry in self.entries:
            if len(results) >= limit:
                break
            
            # Search in traditional/simplified characters
            if query in entry.traditional or query in entry.simplified:
                results.append(entry)
                continue
            
            # Search in pinyin
            if query in entry.pinyin.lower():
                results.append(entry)
                continue
            
            # Search in meanings
            for meaning in entry.meanings:
                if query in meaning.lower():
                    results.append(entry)
                    break
        
        return results
    
    def get_entry_for_character(self, char: str) -> Optional[CedictEntry]:
        """Get the first matching entry for a character."""
        if not self.is_loaded:
            return None
        
        for entry in self.entries:
            if char in entry.traditional or char in entry.simplified:
                return entry
        return None
    
    def is_database_available(self) -> bool:
        """Check if the CEDICT database file exists."""
        return self.data_file.exists()
    
    def get_stats(self) -> Dict:
        """Get dictionary statistics."""
        return {
            "entries_loaded": len(self.entries),
            "is_loaded": self.is_loaded,
            "file_exists": self.data_file.exists()
        }


class DownloadThread(QThread):
    """Background thread for downloading CEDICT."""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, cedict_manager: CedictManager):
        super().__init__()
        self.cedict_manager = cedict_manager
    
    def run(self):
        success = self.cedict_manager.download_cedict(lambda msg: self.progress_signal.emit(msg))
        self.finished_signal.emit(success)


class ParseThread(QThread):
    """Background thread for parsing CEDICT."""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    
    def __init__(self, cedict_manager: CedictManager):
        super().__init__()
        self.cedict_manager = cedict_manager
    
    def run(self):
        count = self.cedict_manager.parse_cedict(lambda msg: self.progress_signal.emit(msg))
        self.finished_signal.emit(count)


class FlashcardWidget(QWidget):
    """Flashcard display widget for study mode."""
    answer_revealed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.current_card = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Character label (large)
        self.char_label = QLabel("?")
        self.char_label.setFont(QFont("Arial", 72, QFont.Weight.Bold))
        self.char_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.char_label)
        
        # Pinyin label
        self.pinyin_label = QLabel("")
        self.pinyin_label.setFont(QFont("Arial", 24))
        self.pinyin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pinyin_label)
        
        # Meaning label (hidden initially)
        self.meaning_label = QLabel("")
        self.meaning_label.setFont(QFont("Arial", 18))
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meaning_label.setWordWrap(True)
        self.meaning_label.hide()
        layout.addWidget(self.meaning_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.show_btn = QPushButton("Show Answer")
        self.show_btn.setFont(QFont("Arial", 14))
        self.show_btn.setMinimumHeight(50)
        self.show_btn.clicked.connect(self._show_answer)
        btn_layout.addWidget(self.show_btn)
        
        self.again_btn = QPushButton("Again")
        self.again_btn.setFont(QFont("Arial", 14))
        self.again_btn.setMinimumHeight(50)
        self.again_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        self.again_btn.clicked.connect(lambda: self._handle_answer(False))
        self.again_btn.hide()
        btn_layout.addWidget(self.again_btn)
        
        self.good_btn = QPushButton("Good")
        self.good_btn.setFont(QFont("Arial", 14))
        self.good_btn.setMinimumHeight(50)
        self.good_btn.setStyleSheet("background-color: #4ecdc4; color: white;")
        self.good_btn.clicked.connect(lambda: self._handle_answer(True))
        self.good_btn.hide()
        btn_layout.addWidget(self.good_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def set_card(self, card: Dict):
        """Set the current flashcard."""
        self.current_card = card
        self.char_label.setText(card["character"])
        self.pinyin_label.setText(card["pinyin"])
        self.meaning_label.hide()
        self.show_btn.show()
        self.again_btn.hide()
        self.good_btn.hide()
    
    def _show_answer(self):
        """Reveal the answer."""
        if self.current_card:
            self.meaning_label.setText(self.current_card["meaning"])
            self.meaning_label.show()
            self.show_btn.hide()
            self.again_btn.show()
            self.good_btn.show()
    
    def _handle_answer(self, correct: bool):
        """Handle user's self-assessment."""
        if self.current_card:
            self.answer_revealed.emit(correct)


class QuizWidget(QWidget):
    """Quiz mode widget with multiple choice questions."""
    answer_selected = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.current_card = None
        self.options = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        self.char_label = QLabel("?")
        self.char_label.setFont(QFont("Arial", 64, QFont.Weight.Bold))
        self.char_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.char_label)
        
        self.opts_layout = QVBoxLayout()
        self.opt_buttons = []
        for i in range(4):
            btn = QPushButton(f"Option {i+1}")
            btn.setFont(QFont("Arial", 14))
            btn.setMinimumHeight(60)
            btn.clicked.connect(lambda checked, idx=i: self._select_option(idx))
            self.opts_layout.addWidget(btn)
            self.opt_buttons.append(btn)
        layout.addLayout(self.opts_layout)
        
        self.feedback = QLabel("")
        self.feedback.setFont(QFont("Arial", 14))
        self.feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback.hide()
        layout.addWidget(self.feedback)
        
        self.setLayout(layout)
    
    def setup(self, card: Dict, all_cards: List[Dict]):
        """Setup quiz question."""
        self.current_card = card
        self.char_label.setText(card["character"])
        wrong = [c for c in all_cards if c != card]
        selected_wrong = random.sample(wrong, min(3, len(wrong)))
        self.options = selected_wrong + [card]
        random.shuffle(self.options)
        
        for i, btn in enumerate(self.opt_buttons):
            if i < len(self.options):
                btn.setText(self.options[i]["meaning"])
                btn.show()
                btn.setEnabled(True)
                btn.setStyleSheet("")
            else:
                btn.hide()
        self.feedback.hide()
    
    def _select_option(self, index: int):
        """Handle option selection."""
        if index >= len(self.options):
            return
        selected = self.options[index]
        is_correct = selected == self.current_card
        
        for btn in self.opt_buttons:
            btn.setEnabled(False)
        
        if is_correct:
            self.feedback.setText("✓ Correct!")
            self.feedback.setStyleSheet("color: green; font-weight: bold;")
            self.opt_buttons[index].setStyleSheet("background-color: #4ecdc4; color: white;")
        else:
            self.feedback.setText(f"✗ Incorrect. Answer: {self.current_card['meaning']}")
            self.feedback.setStyleSheet("color: red;")
            for i, opt in enumerate(self.options):
                if opt == self.current_card:
                    self.opt_buttons[i].setStyleSheet("background-color: #ff6b6b; color: white;")
        
        self.feedback.show()
        self.answer_selected.emit(is_correct)


class StatisticsWidget(QWidget):
    """Statistics display widget."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Your Progress")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        self.stats_layout = QFormLayout()
        self.total_cards = QLabel("0")
        self.stats_layout.addRow("Cards Studied:", self.total_cards)
        self.total_reviews = QLabel("0")
        self.stats_layout.addRow("Total Reviews:", self.total_reviews)
        self.accuracy = QLabel("0%")
        self.stats_layout.addRow("Accuracy:", self.accuracy)
        layout.addLayout(self.stats_layout)
        
        mastery_group = QGroupBox("Mastery Levels")
        mastery_layout = QVBoxLayout()
        self.mastery_labels = {}
        for level in ["new", "learning", "reviewing", "mastered"]:
            row = QHBoxLayout()
            row.addWidget(QLabel(level.capitalize()))
            cnt = QLabel("0")
            self.mastery_labels[level] = cnt
            row.addWidget(cnt)
            bar = QProgressBar()
            bar.setMaximum(100)
            row.addWidget(bar)
            mastery_layout.addLayout(row)
        
        mastery_group.setLayout(mastery_layout)
        layout.addWidget(mastery_group)
        layout.addStretch()
        self.setLayout(layout)
    
    def update_stats(self, stats: Dict):
        """Update statistics display."""
        self.total_cards.setText(str(stats["total_cards"]))
        self.total_reviews.setText(str(stats["total_reviews"]))
        self.accuracy.setText(f"{stats['accuracy']:.1f}%")
        for level, label in self.mastery_labels.items():
            label.setText(str(stats["mastery"].get(level, 0)))


class CreateDeckDialog(QDialog):
    """Dialog for creating custom decks."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Custom Deck")
        self.setMinimumWidth(600)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        name_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter deck name")
        name_layout.addRow("Deck Name:", self.name_input)
        layout.addLayout(name_layout)
        
        layout.addWidget(QLabel("Enter cards (format: character | pinyin | meaning)"))
        self.cards_input = QTextEdit()
        self.cards_input.setPlaceholderText("你好 | nǐ hǎo | Hello\n谢谢 | xiè xie | Thank you")
        self.cards_input.setMinimumHeight(200)
        layout.addWidget(self.cards_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_deck_data(self):
        """Get deck name and cards from dialog."""
        name = self.name_input.text().strip()
        cards = []
        for line in self.cards_input.toPlainText().split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                cards.append({
                    "character": parts[0],
                    "pinyin": parts[1],
                    "meaning": parts[2]
                })
        return name, cards


class DictionarySearchDialog(QDialog):
    """Dialog for searching the CEDICT dictionary."""
    
    def __init__(self, cedict_manager: CedictManager, parent=None):
        super().__init__(parent)
        self.cedict_manager = cedict_manager
        self.setWindowTitle("Dictionary Search")
        self.setMinimumSize(700, 500)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Search input
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter Chinese character, pinyin, or English meaning...")
        self.search_input.returnPressed.connect(self._search)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._search)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Results info
        self.results_label = QLabel("Enter a search term and press Enter")
        layout.addWidget(self.results_label)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.results_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_to_deck_btn = QPushButton("Add Selected to Custom Deck")
        add_to_deck_btn.clicked.connect(self._add_selected_to_deck)
        btn_layout.addWidget(add_to_deck_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.current_results = []
    
    def _search(self):
        """Perform dictionary search."""
        query = self.search_input.text().strip()
        if not query:
            self.results_label.setText("Please enter a search term")
            return
        
        if not self.cedict_manager.is_loaded:
            if not self.cedict_manager.is_database_available():
                self.results_label.setText("Database not found. Please download it first.")
                return
            else:
                self.results_label.setText("Loading database...")
                self.cedict_manager.parse_cedict()
        
        self.results_label.setText("Searching...")
        QApplication.processEvents()
        
        self.current_results = self.cedict_manager.search(query, limit=200)
        
        self.results_list.clear()
        if not self.current_results:
            self.results_label.setText(f"No results found for '{query}'")
            return
        
        self.results_label.setText(f"Found {len(self.current_results)} results for '{query}'")
        
        for entry in self.current_results:
            display_text = f"{entry.display_char} [{entry.pinyin}] - {'; '.join(entry.meanings[:2])}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.results_list.addItem(item)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on result item."""
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry:
            # Show detailed view
            detail_dialog = QDialog(self)
            detail_dialog.setWindowTitle("Entry Details")
            detail_dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout()
            
            char_label = QLabel(entry.display_char)
            char_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
            char_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(char_label)
            
            if entry.traditional != entry.simplified:
                trad_label = QLabel(f"Traditional: {entry.traditional}")
                trad_label.setFont(QFont("Arial", 18))
                trad_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(trad_label)
            
            pinyin_label = QLabel(f"Pinyin: {entry.pinyin}")
            pinyin_label.setFont(QFont("Arial", 16))
            pinyin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(pinyin_label)
            
            meanings_text = "\n".join([f"• {m}" for m in entry.meanings])
            meanings_label = QLabel(f"Meanings:\n{meanings_text}")
            meanings_label.setFont(QFont("Arial", 12))
            meanings_label.setWordWrap(True)
            layout.addWidget(meanings_label)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(detail_dialog.accept)
            layout.addWidget(close_btn)
            
            detail_dialog.setLayout(layout)
            detail_dialog.exec()
    
    def _add_selected_to_deck(self):
        """Add selected entries to a custom deck."""
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select one or more entries to add.")
            return
        
        cards = []
        for item in selected_items:
            entry = item.data(Qt.ItemDataRole.UserRole)
            if entry:
                cards.append(entry.to_dict())
        
        if cards:
            name, ok = QInputDialog.getText(self, "Add to Deck", 
                "Enter deck name (or select existing):")
            if ok and name:
                # Get existing cards if deck exists
                existing = self.cedict_manager.parent.flashcard_data.get_cards_for_level(name) if hasattr(self.cedict_manager, 'parent') else []
                all_cards = existing + cards
                
                if hasattr(self.cedict_manager, 'parent'):
                    self.cedict_manager.parent.flashcard_data.create_custom_deck(name, all_cards)
                    if name not in [self.cedict_manager.parent.level_combo.itemText(i) 
                                   for i in range(self.cedict_manager.parent.level_combo.count())]:
                        self.cedict_manager.parent.level_combo.addItem(name)
                
                QMessageBox.information(
                    self, "Added to Deck",
                    f"Added {len(cards)} entries to '{name}' deck."
                )


class MandarinFlashcardApp(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.flashcard_data = FlashcardData()
        self.cedict_manager = CedictManager()
        self.current_mode = "study"
        self.current_cards = []
        self.current_index = 0
        self.session_correct = 0
        self.session_total = 0
        self._init_ui()
        self.load_deck("HSK 1")
        self._check_cedict_status()
    
    def _init_ui(self):
        self.setWindowTitle("Mandarin Flashcards - Learn Chinese")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        
        self._create_menu_bar()
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Study", "Quiz", "Browse", "Statistics"])
        self.mode_combo.currentTextChanged.connect(self._change_mode)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)
        
        # Level selector
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(list(HSK_VOCABULARY.keys()))
        self.level_combo.currentTextChanged.connect(self.load_deck)
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()
        main_layout.addLayout(level_layout)
        
        # Stacked widget for modes
        self.stack = QStackedWidget()
        self.study_widget = FlashcardWidget()
        self.study_widget.answer_revealed.connect(self._handle_study_answer)
        self.stack.addWidget(self.study_widget)
        
        self.quiz_widget = QuizWidget()
        self.quiz_widget.answer_selected.connect(self._handle_quiz_answer)
        self.stack.addWidget(self.quiz_widget)
        
        self.browse_widget = self._create_browse_widget()
        self.stack.addWidget(self.browse_widget)
        
        self.stats_widget = StatisticsWidget()
        self.stack.addWidget(self.stats_widget)
        
        main_layout.addWidget(self.stack)
        
        # Navigation
        nav_layout = QHBoxLayout()
        prev_btn = QPushButton("< Previous")
        prev_btn.clicked.connect(self._prev_card)
        nav_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("Next >")
        next_btn.clicked.connect(self._next_card)
        nav_layout.addWidget(next_btn)
        
        shuffle_btn = QPushButton("Shuffle")
        shuffle_btn.clicked.connect(self._shuffle_cards)
        nav_layout.addWidget(shuffle_btn)
        
        nav_layout.addStretch()
        main_layout.addLayout(nav_layout)
        
        # Progress label
        self.progress_label = QLabel("Card 0 / 0")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.progress_label)
    
    def _create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        export_action = QAction("&Export Progress", self)
        export_action.triggered.connect(self._export_progress)
        file_menu.addAction(export_action)
        
        import_action = QAction("&Import Deck", self)
        import_action.triggered.connect(self._import_deck)
        file_menu.addAction(import_action)
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        decks_menu = menubar.addMenu("&Decks")
        create_action = QAction("&Create Custom Deck", self)
        create_action.triggered.connect(self._create_custom_deck)
        decks_menu.addAction(create_action)
        
        # Dictionary menu
        dict_menu = menubar.addMenu("&Dictionary")
        
        download_action = QAction("&Download CEDICT Database", self)
        download_action.triggered.connect(self._download_cedict)
        dict_menu.addAction(download_action)
        
        search_action = QAction("&Search Dictionary", self)
        search_action.triggered.connect(self._show_dictionary_search)
        dict_menu.addAction(search_action)
        
        status_action = QAction("Database &Status", self)
        status_action.triggered.connect(self._show_cedict_status)
        dict_menu.addAction(status_action)
        
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_browse_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by character, pinyin, or meaning...")
        self.search_input.textChanged.connect(self._filter_cards)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.browse_container = QWidget()
        self.browse_layout = QVBoxLayout()
        self.browse_container.setLayout(self.browse_layout)
        scroll.setWidget(self.browse_container)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def load_deck(self, level: str):
        """Load cards for a level."""
        self.current_cards = self.flashcard_data.get_cards_for_level(level)
        self.current_index = 0
        self._update_current_card()
        self._update_progress_display()
        self._populate_browse_view()
    
    def _update_current_card(self):
        """Update currently displayed card."""
        if not self.current_cards:
            return
        card = self.current_cards[self.current_index]
        if self.current_mode == "study":
            self.study_widget.set_card(card)
        elif self.current_mode == "quiz":
            self.quiz_widget.setup(card, self.current_cards)
    
    def _update_progress_display(self):
        """Update progress indicator."""
        if self.current_cards:
            self.progress_label.setText(f"Card {self.current_index + 1} / {len(self.current_cards)}")
        else:
            self.progress_label.setText("No cards available")
    
    def _next_card(self):
        """Go to next card."""
        if self.current_cards:
            self.current_index = (self.current_index + 1) % len(self.current_cards)
            self._update_current_card()
            self._update_progress_display()
    
    def _prev_card(self):
        """Go to previous card."""
        if self.current_cards:
            self.current_index = (self.current_index - 1) % len(self.current_cards)
            self._update_current_card()
            self._update_progress_display()
    
    def _shuffle_cards(self):
        """Shuffle current deck."""
        if self.current_cards:
            random.shuffle(self.current_cards)
            self.current_index = 0
            self._update_current_card()
            self._update_progress_display()
    
    def _change_mode(self, mode: str):
        """Change between study, quiz, browse, statistics modes."""
        m = mode.lower()
        if m == "study":
            self.current_mode = "study"
            self.stack.setCurrentIndex(0)
        elif m == "quiz":
            self.current_mode = "quiz"
            self.stack.setCurrentIndex(1)
        elif m == "browse":
            self.current_mode = "browse"
            self.stack.setCurrentIndex(2)
            self._populate_browse_view()
        elif m == "statistics":
            self.current_mode = "statistics"
            self.stack.setCurrentIndex(3)
            self._update_statistics()
    
    def _handle_study_answer(self, correct: bool):
        """Handle answer in study mode."""
        if self.current_cards and self.current_index < len(self.current_cards):
            card = self.current_cards[self.current_index]
            self.flashcard_data.update_progress(card, correct)
            self.session_total += 1
            if correct:
                self.session_correct += 1
            acc = (self.session_correct / self.session_total * 100) if self.session_total > 0 else 0
            self.statusBar().showMessage(f"Session: {self.session_correct}/{self.session_total} ({acc:.0f}%)")
            QTimer.singleShot(500, self._next_card)
    
    def _handle_quiz_answer(self, correct: bool):
        """Handle answer in quiz mode."""
        if self.current_cards and self.current_index < len(self.current_cards):
            card = self.current_cards[self.current_index]
            self.flashcard_data.update_progress(card, correct)
            self.session_total += 1
            if correct:
                self.session_correct += 1
            acc = (self.session_correct / self.session_total * 100) if self.session_total > 0 else 0
            self.statusBar().showMessage(f"Session: {self.session_correct}/{self.session_total} ({acc:.0f}%)")
            QTimer.singleShot(1000, self._next_card)
    
    def _populate_browse_view(self):
        """Populate browse view with cards."""
        while self.browse_layout.count():
            item = self.browse_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for card in self.current_cards:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            layout = QHBoxLayout()
            
            char_label = QLabel(card["character"])
            char_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
            layout.addWidget(char_label)
            
            info_layout = QVBoxLayout()
            info_layout.addWidget(QLabel(card["pinyin"]))
            info_layout.addWidget(QLabel(card["meaning"]))
            layout.addLayout(info_layout)
            
            frame.setLayout(layout)
            self.browse_layout.addWidget(frame)
        
        self.browse_layout.addStretch()
    
    def _filter_cards(self, text: str):
        """Filter cards in browse view."""
        text = text.lower()
        while self.browse_layout.count():
            item = self.browse_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for card in self.current_cards:
            if (text in card["character"].lower() or
                text in card["pinyin"].lower() or
                text in card["meaning"].lower()):
                
                frame = QFrame()
                frame.setFrameStyle(QFrame.Shape.Box)
                layout = QHBoxLayout()
                layout.addWidget(QLabel(card["character"]))
                info_layout = QVBoxLayout()
                info_layout.addWidget(QLabel(card["pinyin"]))
                info_layout.addWidget(QLabel(card["meaning"]))
                layout.addLayout(info_layout)
                frame.setLayout(layout)
                self.browse_layout.addWidget(frame)
        
        self.browse_layout.addStretch()
    
    def _update_statistics(self):
        """Update statistics display."""
        self.stats_widget.update_stats(self.flashcard_data.get_statistics())
    
    def _create_custom_deck(self):
        """Create a custom deck."""
        dialog = CreateDeckDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, cards = dialog.get_deck_data()
            if name and cards:
                self.flashcard_data.create_custom_deck(name, cards)
                self.level_combo.addItem(name)
                QMessageBox.information(
                    self, "Success",
                    f"Created '{name}' with {len(cards)} cards!"
                )
    
    def _export_progress(self):
        """Export progress to file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Progress", "", "JSON Files (*.json)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.flashcard_data.user_progress, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Success", "Progress exported!")
    
    def _import_deck(self):
        """Import a custom deck."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Deck", "", "JSON Files (*.json)"
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                name, _ = QInputDialog.getText(self, "Deck Name", "Enter deck name:")
                if name:
                    cards = [
                        item for item in data
                        if isinstance(item, dict) and "character" in item
                    ]
                    if cards:
                        self.flashcard_data.create_custom_deck(name, cards)
                        self.level_combo.addItem(name)
                        QMessageBox.information(
                            self, "Success",
                            f"Imported {len(cards)} cards into '{name}'!"
                        )
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Mandarin Flashcards",
            """<h2>Mandarin Chinese Flashcard Application</h2>
            <p>A cross-platform desktop application for learning Chinese.</p>
            <p><b>Features:</b></p>
            <ul>
                <li>HSK vocabulary (levels 1-6)</li>
                <li>CEDICT dictionary integration (100,000+ entries)</li>
                <li>Spaced repetition system (SM-2)</li>
                <li>Study and Quiz modes</li>
                <li>Custom deck creation</li>
                <li>Progress tracking and statistics</li>
            </ul>
            <p>Inspired by ZDT - Zhongwen Development Tool</p>"""
        )
    
    def _check_cedict_status(self):
        """Check CEDICT database status on startup."""
        if not self.cedict_manager.is_database_available():
            self.statusBar().showMessage("CEDICT database not found. Use Dictionary menu to download.", 5000)
    
    def _download_cedict(self):
        """Download CEDICT database."""
        if self.cedict_manager.is_downloading:
            QMessageBox.information(self, "Download", "Download already in progress...")
            return
        
        reply = QMessageBox.question(
            self, "Download CEDICT",
            "This will download the CEDICT Chinese-English dictionary (~3MB compressed).\n"
            "The database will be stored in ~/.mandarin_flashcards/cedict/\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._status_label = QLabel("Downloading CEDICT...")
            self.statusBar().addPermanentWidget(self._status_label)
            
            self.download_thread = DownloadThread(self.cedict_manager)
            self.download_thread.progress_signal.connect(self._on_download_progress)
            self.download_thread.finished_signal.connect(self._on_download_finished)
            self.download_thread.start()
    
    def _on_download_progress(self, msg: str):
        """Handle download progress updates."""
        if hasattr(self, '_status_label'):
            self._status_label.setText(msg)
    
    def _on_download_finished(self, success: bool):
        """Handle download completion."""
        if hasattr(self, '_status_label'):
            self._status_label.deleteLater()
            delattr(self, '_status_label')
        
        if success:
            QMessageBox.information(
                self, "Download Complete",
                "CEDICT database downloaded successfully!\n\n"
                "Now parsing the dictionary file...\n"
                "(This may take a few moments)"
            )
            # Start parsing
            self._parse_cedict()
        else:
            QMessageBox.critical(
                self, "Download Failed",
                "Failed to download CEDICT database.\nPlease check your internet connection."
            )
    
    def _parse_cedict(self):
        """Parse the CEDICT database file."""
        self._status_label = QLabel("Parsing CEDICT...")
        self.statusBar().addPermanentWidget(self._status_label)
        
        self.parse_thread = ParseThread(self.cedict_manager)
        self.parse_thread.progress_signal.connect(self._on_parse_progress)
        self.parse_thread.finished_signal.connect(self._on_parse_finished)
        self.parse_thread.start()
    
    def _on_parse_progress(self, msg: str):
        """Handle parse progress updates."""
        if hasattr(self, '_status_label'):
            self._status_label.setText(msg)
    
    def _on_parse_finished(self, count: int):
        """Handle parse completion."""
        if hasattr(self, '_status_label'):
            self._status_label.deleteLater()
            delattr(self, '_status_label')
        
        if count > 0:
            QMessageBox.information(
                self, "Dictionary Ready",
                f"Successfully loaded {count:,} dictionary entries!\n\n"
                "You can now search the dictionary using the Dictionary menu."
            )
            self.statusBar().showMessage(f"CEDICT loaded: {count:,} entries", 5000)
        else:
            QMessageBox.warning(
                self, "Parse Error",
                "Failed to parse CEDICT database file."
            )
    
    def _show_cedict_status(self):
        """Show CEDICT database status."""
        stats = self.cedict_manager.get_stats()
        status_msg = "CEDICT Database Status\n\n"
        
        if stats["file_exists"]:
            status_msg += "✓ Database file exists\n"
        else:
            status_msg += "✗ Database file not found\n"
        
        if stats["is_loaded"]:
            status_msg += f"✓ Loaded: {stats['entries_loaded']:,} entries\n"
        else:
            status_msg += "✗ Not loaded into memory\n"
        
        status_msg += f"\nLocation: {self.cedict_manager.data_file}"
        
        QMessageBox.information(self, "CEDICT Status", status_msg)
    
    def _show_dictionary_search(self):
        """Show dictionary search dialog."""
        dialog = DictionarySearchDialog(self.cedict_manager, self)
        dialog.exec()
    
    def closeEvent(self, event):
        """Save data on close."""
        self.flashcard_data.save_data()
        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Arial", 11))
    
    window = MandarinFlashcardApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
