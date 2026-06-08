# Mandarin Chinese Flashcard Application

A cross-platform (Linux/Windows) desktop application for learning Mandarin Chinese, inspired by ZDT - Zhongwen Development Tool.

## Features

- **HSK Vocabulary**: Pre-loaded flashcards for HSK levels 1-6
- **Spaced Repetition**: SM-2 algorithm for optimal learning retention
- **Study Mode**: Self-assessment with "Again" and "Good" buttons
- **Quiz Mode**: Multiple choice questions to test your knowledge
- **Browse Mode**: View all cards with search functionality
- **Statistics**: Track your progress and mastery levels
- **Custom Decks**: Create your own vocabulary decks
- **Import/Export**: Save and share your progress

## Installation

### Requirements

- Python 3.8 or higher
- PyQt6

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Run the Application

```bash
python main.py
```

### Study Mode

1. Select an HSK level from the dropdown
2. View the Chinese character
3. Click "Show Answer" to reveal pinyin and meaning
4. Rate your recall: "Again" (if you forgot) or "Good" (if you remembered)
5. The app schedules reviews using spaced repetition

### Quiz Mode

1. Select "Quiz" from the mode dropdown
2. Choose the correct meaning from multiple choices
3. Get immediate feedback on your answer
4. Progress is tracked automatically

### Browse Mode

1. View all cards in the current deck
2. Use the search box to filter by character, pinyin, or meaning

### Creating Custom Decks

1. Go to Decks → Create Custom Deck
2. Enter a deck name
3. Add cards in format: `character | pinyin | meaning` (one per line)
4. Click OK to save

### Statistics

View your overall progress:
- Total cards studied
- Total reviews completed
- Accuracy percentage
- Mastery level distribution (New, Learning, Reviewing, Mastered)

## File Structure

```
mandarin-flashcards/
├── main.py                 # Main application code
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Data Storage

User progress and custom decks are stored in:
- **Linux**: `~/.mandarin_flashcards/progress.json`
- **Windows**: `C:\Users\<username>\.mandarin_flashcards\progress.json`

## Spaced Repetition Algorithm

The app uses the SM-2 algorithm:
- Correct answers increase the interval between reviews
- Incorrect answers reset the card to "learning" status
- Cards progress through: New → Learning → Reviewing → Mastered

## Extending Vocabulary

To add more HSK levels, edit the `HSK_VOCABULARY` dictionary in `main.py`:

```python
HSK_VOCABULARY = {
    "HSK 3": [
        {"character": "...", "pinyin": "...", "meaning": "..."},
        # ... more words
    ],
}
```

## License

MIT License

## Credits

Inspired by [ZDT - Zhongwen Development Tool](https://marketplace.eclipse.org/content/zdt-zhongwen-development-tool)

---

**Happy Learning! 学习快乐!**
