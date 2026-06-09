# Mandarin Chinese Flashcard Application

A cross-platform (Linux/Windows) desktop application for learning Mandarin Chinese, inspired by ZDT - Zhongwen Development Tool.

## Features

- **HSK Vocabulary**: Pre-loaded flashcards for HSK levels 1-6
- **CEDICT Dictionary Integration**: Download and search the complete CEDICT Chinese-English dictionary (100,000+ entries)
- **Spaced Repetition**: SM-2 algorithm for optimal learning retention
- **Study Mode**: Self-assessment with "Again" and "Good" buttons
- **Quiz Mode**: Multiple choice questions to test your knowledge
- **Browse Mode**: View all cards with search functionality
- **Statistics**: Track your progress and mastery levels
- **Custom Decks**: Create your own vocabulary decks from dictionary search results
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

### CEDICT Dictionary

The application integrates with the CEDICT Chinese-English dictionary:

#### Download the Dictionary

1. Go to **Dictionary → Download CEDICT Database**
2. Confirm the download (~3MB compressed)
3. Wait for download and parsing to complete (~100,000+ entries)

The dictionary is stored at:
- **Linux**: `~/.mandarin_flashcards/cedict/cedict_ts.u8`
- **Windows**: `C:\Users\<username>\.mandarin_flashcards\cedict\cedict_ts.u8`

#### Search the Dictionary

1. Go to **Dictionary → Search Dictionary**
2. Enter a search term:
   - Chinese characters (simplified or traditional)
   - Pinyin (with or without tone marks)
   - English meanings
3. Browse results (up to 200 per search)
4. Double-click an entry to see full details
5. Select entries and click "Add Selected to Custom Deck" to create flashcards

#### Check Database Status

Go to **Dictionary → Database Status** to see:
- Whether the database file exists
- Number of loaded entries
- File location

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

**Method 1: From Dictionary Search**
1. Go to **Dictionary → Search Dictionary**
2. Search for words you want to learn
3. Select one or more entries
4. Click "Add Selected to Custom Deck"
5. Enter a deck name

**Method 2: Manual Entry**
1. Go to **Decks → Create Custom Deck**
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

CEDICT dictionary files:
- **Linux**: `~/.mandarin_flashcards/cedict/`
- **Windows**: `C:\Users\<username>\.mandarin_flashcards\cedict\`

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

## CEDICT Dictionary Source

The CEDICT dictionary is provided by:
- [CC-CEDICT](https://cc-cedict.org/wiki/)
- [MDBG Chinese Dictionary](https://www.mdbg.net/chinese/dictionary?page=cc-cedict)

The dictionary is released under the Creative Commons Attribution-ShareAlike License.

## License

MIT License

## Credits

Inspired by [ZDT - Zhongwen Development Tool](https://marketplace.eclipse.org/content/zdt-zhongwen-development-tool)

CEDICT dictionary data from [CC-CEDICT](https://cc-cedict.org/wiki/)

---

**Happy Learning! 学习快乐!**
