#!/usr/bin/env python3
"""
HSK Character Data Downloader

Downloads HSK character data (all levels 1-6) and stroke order data from open sources:
- HSK vocabulary from HSK Academy / Chinese-Tools.com
- Stroke order data from MakeMeAHanZI project
"""

import json
import urllib.request
import gzip
from pathlib import Path
from typing import Dict, List, Optional
import re


class HSKDataDownloader:
    """Downloads and processes HSK character data from open sources."""
    
    # Source URLs for HSK data - using alternative reliable sources
    HSK_SOURCES = {
        "hsk_1": "https://raw.githubusercontent.com/linjingwei/hsk/master/hsk1.json",
        "hsk_2": "https://raw.githubusercontent.com/linjingwei/hsk/master/hsk2.json", 
        "hsk_3": "https://raw.githubusercontent.com/linjingwei/hsk/master/hsk3.json",
        "hsk_4": "https://raw.githubusercontent.com/linjingwei/hsk/master/hsk4.json",
        "hsk_5": "https://raw.githubusercontent.com/linjingwei/hsk/master/hsk5.json",
        "hsk_6": "https://raw.githubusercontent.com/linjingwei/hsk/master/hsk6.json",
    }
    
    # Alternative source - static HSK word lists (backup)
    HSK_BACKUP_DATA = {
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
            {"character": "是", "pinyin": "shì", "meaning": "To be"},
            {"character": "的", "pinyin": "de", "meaning": "Possessive particle"},
            {"character": "在", "pinyin": "zài", "meaning": "At; in; on"},
            {"character": "吗", "pinyin": "ma", "meaning": "Question particle"},
            {"character": "有", "pinyin": "yǒu", "meaning": "To have"},
            {"character": "这", "pinyin": "zhè", "meaning": "This"},
            {"character": "那", "pinyin": "nà", "meaning": "That"},
            {"character": "不", "pinyin": "bù", "meaning": "Not"},
            {"character": "了", "pinyin": "le", "meaning": "Particle (completed action)"},
            {"character": "他", "pinyin": "tā", "meaning": "He; him"},
            {"character": "她", "pinyin": "tā", "meaning": "She; her"},
            {"character": "们", "pinyin": "men", "meaning": "Plural marker for people"},
            {"character": "大", "pinyin": "dà", "meaning": "Big; large"},
            {"character": "小", "pinyin": "xiǎo", "meaning": "Small"},
            {"character": "多", "pinyin": "duō", "meaning": "Many; much"},
            {"character": "少", "pinyin": "shǎo", "meaning": "Few; little"},
            {"character": "日", "pinyin": "rì", "meaning": "Day; sun"},
            {"character": "月", "pinyin": "yuè", "meaning": "Month; moon"},
            {"character": "年", "pinyin": "nián", "meaning": "Year"},
            {"character": "今天", "pinyin": "jīn tiān", "meaning": "Today"},
            {"character": "明天", "pinyin": "míng tiān", "meaning": "Tomorrow"},
            {"character": "昨天", "pinyin": "zuó tiān", "meaning": "Yesterday"},
            {"character": "点", "pinyin": "diǎn", "meaning": "O'clock; point"},
            {"character": "分", "pinyin": "fēn", "meaning": "Minute; part"},
            {"character": "现在", "pinyin": "xiàn zài", "meaning": "Now"},
            {"character": "什么", "pinyin": "shén me", "meaning": "What"},
            {"character": "谁", "pinyin": "shuí", "meaning": "Who"},
            {"character": "哪", "pinyin": "nǎ", "meaning": "Which"},
            {"character": "几", "pinyin": "jǐ", "meaning": "How many"},
            {"character": "多少", "pinyin": "duō shao", "meaning": "How many/much"},
            {"character": "一", "pinyin": "yī", "meaning": "One"},
            {"character": "二", "pinyin": "èr", "meaning": "Two"},
            {"character": "三", "pinyin": "sān", "meaning": "Three"},
            {"character": "四", "pinyin": "sì", "meaning": "Four"},
            {"character": "五", "pinyin": "wǔ", "meaning": "Five"},
            {"character": "六", "pinyin": "liù", "meaning": "Six"},
            {"character": "七", "pinyin": "qī", "meaning": "Seven"},
            {"character": "八", "pinyin": "bā", "meaning": "Eight"},
            {"character": "九", "pinyin": "jiǔ", "meaning": "Nine"},
            {"character": "十", "pinyin": "shí", "meaning": "Ten"},
            {"character": "百", "pinyin": "bǎi", "meaning": "Hundred"},
            {"character": "千", "pinyin": "qiān", "meaning": "Thousand"},
            {"character": "万", "pinyin": "wàn", "meaning": "Ten thousand"},
            {"character": "个", "pinyin": "gè", "meaning": "Measure word"},
            {"character": "口", "pinyin": "kǒu", "meaning": "Mouth"},
            {"character": "中", "pinyin": "zhōng", "meaning": "Middle; center"},
            {"character": "上", "pinyin": "shàng", "meaning": "Up; above"},
            {"character": "下", "pinyin": "xià", "meaning": "Down; below"},
            {"character": "来", "pinyin": "lái", "meaning": "To come"},
            {"character": "去", "pinyin": "qù", "meaning": "To go"},
            {"character": "回", "pinyin": "huí", "meaning": "To return"},
            {"character": "出", "pinyin": "chū", "meaning": "To go out"},
            {"character": "进", "pinyin": "jìn", "meaning": "To enter"},
            {"character": "过", "pinyin": "guò", "meaning": "To pass; to cross"},
            {"character": "起", "pinyin": "qǐ", "meaning": "To rise; to get up"},
            {"character": "走", "pinyin": "zǒu", "meaning": "To walk"},
            {"character": "跑", "pinyin": "pǎo", "meaning": "To run"},
            {"character": "跳", "pinyin": "tiào", "meaning": "To jump"},
            {"character": "坐", "pinyin": "zuò", "meaning": "To sit"},
            {"character": "站", "pinyin": "zhàn", "meaning": "To stand"},
            {"character": "睡", "pinyin": "shuì", "meaning": "To sleep"},
            {"character": "觉", "pinyin": "jiào", "meaning": "To feel; sleep"},
            {"character": "吃", "pinyin": "chī", "meaning": "To eat"},
            {"character": "喝", "pinyin": "hē", "meaning": "To drink"},
            {"character": "水", "pinyin": "shuǐ", "meaning": "Water"},
            {"character": "饭", "pinyin": "fàn", "meaning": "Rice; meal"},
            {"character": "菜", "pinyin": "cài", "meaning": "Vegetable; dish"},
            {"character": "肉", "pinyin": "ròu", "meaning": "Meat"},
            {"character": "鱼", "pinyin": "yú", "meaning": "Fish"},
            {"character": "蛋", "pinyin": "dàn", "meaning": "Egg"},
            {"character": "面", "pinyin": "miàn", "meaning": "Noodles; face"},
            {"character": "茶", "pinyin": "chá", "meaning": "Tea"},
            {"character": "咖啡", "pinyin": "kā fēi", "meaning": "Coffee"},
            {"character": "酒", "pinyin": "jiǔ", "meaning": "Alcohol; wine"},
            {"character": "牛奶", "pinyin": "niú nǎi", "meaning": "Milk"},
            {"character": "水果", "pinyin": "shuǐ guǒ", "meaning": "Fruit"},
            {"character": "苹果", "pinyin": "píng guǒ", "meaning": "Apple"},
            {"character": "香蕉", "pinyin": "xiāng jiāo", "meaning": "Banana"},
            {"character": "家", "pinyin": "jiā", "meaning": "Home; family"},
            {"character": "爸爸", "pinyin": "bà ba", "meaning": "Father"},
            {"character": "妈妈", "pinyin": "mā ma", "meaning": "Mother"},
            {"character": "哥哥", "pinyin": "gē ge", "meaning": "Older brother"},
            {"character": "弟弟", "pinyin": "dì di", "meaning": "Younger brother"},
            {"character": "姐姐", "pinyin": "jiě jie", "meaning": "Older sister"},
            {"character": "妹妹", "pinyin": "mèi mei", "meaning": "Younger sister"},
            {"character": "儿子", "pinyin": "ér zi", "meaning": "Son"},
            {"character": "女儿", "pinyin": "nǚ ér", "meaning": "Daughter"},
            {"character": "先生", "pinyin": "xiān sheng", "meaning": "Mr.; husband"},
            {"character": "老师", "pinyin": "lǎo shī", "meaning": "Teacher"},
            {"character": "学生", "pinyin": "xué sheng", "meaning": "Student"},
            {"character": "同学", "pinyin": "tóng xué", "meaning": "Classmate"},
            {"character": "学校", "pinyin": "xué xiào", "meaning": "School"},
            {"character": "教室", "pinyin": "jiào shì", "meaning": "Classroom"},
            {"character": "上课", "pinyin": "shàng kè", "meaning": "To attend class"},
            {"character": "下课", "pinyin": "xià kè", "meaning": "To finish class"},
            {"character": "书", "pinyin": "shū", "meaning": "Book"},
            {"character": "本", "pinyin": "běn", "meaning": "Book; measure word"},
            {"character": "笔", "pinyin": "bǐ", "meaning": "Pen; pencil"},
            {"character": "字", "pinyin": "zì", "meaning": "Character; word"},
            {"character": "汉语", "pinyin": "hàn yǔ", "meaning": "Chinese language"},
            {"character": "英文", "pinyin": "yīng wén", "meaning": "English language"},
            {"character": "说", "pinyin": "shuō", "meaning": "To speak; to say"},
            {"character": "话", "pinyin": "huà", "meaning": "Word; speech"},
            {"character": "听", "pinyin": "tīng", "meaning": "To listen"},
            {"character": "读", "pinyin": "dú", "meaning": "To read"},
            {"character": "写", "pinyin": "xiě", "meaning": "To write"},
            {"character": "看", "pinyin": "kàn", "meaning": "To look; to watch"},
            {"character": "见", "pinyin": "jiàn", "meaning": "To see"},
            {"character": "知道", "pinyin": "zhī dao", "meaning": "To know"},
            {"character": "想", "pinyin": "xiǎng", "meaning": "To think; to want"},
            {"character": "要", "pinyin": "yào", "meaning": "To want; to need"},
            {"character": "爱", "pinyin": "ài", "meaning": "To love"},
            {"character": "喜欢", "pinyin": "xǐ huan", "meaning": "To like"},
            {"character": "高兴", "pinyin": "gāo xìng", "meaning": "Happy"},
            {"character": "忙", "pinyin": "máng", "meaning": "Busy"},
            {"character": "累", "pinyin": "lèi", "meaning": "Tired"},
            {"character": "冷", "pinyin": "lěng", "meaning": "Cold"},
            {"character": "热", "pinyin": "rè", "meaning": "Hot"},
            {"character": "天气", "pinyin": "tiān qì", "meaning": "Weather"},
            {"character": "时间", "pinyin": "shí jian", "meaning": "Time"},
            {"character": "时候", "pinyin": "shí hou", "meaning": "When; time"},
            {"character": "地方", "pinyin": "dì fang", "meaning": "Place"},
            {"character": "名字", "pinyin": "míng zi", "meaning": "Name"},
            {"character": "问题", "pinyin": "wèn tí", "meaning": "Question; problem"},
            {"character": "答案", "pinyin": "dá àn", "meaning": "Answer"},
            {"character": "电话", "pinyin": "diàn huà", "meaning": "Telephone"},
            {"character": "电脑", "pinyin": "diàn nǎo", "meaning": "Computer"},
            {"character": "手机", "pinyin": "shǒu jī", "meaning": "Mobile phone"},
            {"character": "钱", "pinyin": "qián", "meaning": "Money"},
            {"character": "块", "pinyin": "kuài", "meaning": "Yuan (currency); piece"},
            {"character": "元", "pinyin": "yuán", "meaning": "Yuan (currency)"},
            {"character": "贵", "pinyin": "guì", "meaning": "Expensive"},
            {"character": "便宜", "pinyin": "pián yi", "meaning": "Cheap"},
            {"character": "买", "pinyin": "mǎi", "meaning": "To buy"},
            {"character": "卖", "pinyin": "mài", "meaning": "To sell"},
            {"character": "东西", "pinyin": "dōng xi", "meaning": "Thing; stuff"},
            {"character": "商店", "pinyin": "shāng diàn", "meaning": "Shop; store"},
            {"character": "超市", "pinyin": "chāo shì", "meaning": "Supermarket"},
            {"character": "医院", "pinyin": "yī yuàn", "meaning": "Hospital"},
            {"character": "医生", "pinyin": "yī sheng", "meaning": "Doctor"},
            {"character": "病", "pinyin": "bìng", "meaning": "Illness; sick"},
            {"character": "药", "pinyin": "yào", "meaning": "Medicine"},
            {"character": "身体", "pinyin": "shēn tǐ", "meaning": "Body; health"},
            {"character": "头", "pinyin": "tóu", "meaning": "Head"},
            {"character": "手", "pinyin": "shǒu", "meaning": "Hand"},
            {"character": "脚", "pinyin": "jiǎo", "meaning": "Foot"},
            {"character": "眼睛", "pinyin": "yǎn jing", "meaning": "Eye"},
            {"character": "耳朵", "pinyin": "ěr duo", "meaning": "Ear"},
            {"character": "鼻子", "pinyin": "bí zi", "meaning": "Nose"},
            {"character": "嘴", "pinyin": "zuǐ", "meaning": "Mouth"},
            {"character": "衣服", "pinyin": "yī fu", "meaning": "Clothes"},
            {"character": "穿", "pinyin": "chuān", "meaning": "To wear"},
            {"character": "颜色", "pinyin": "yán se", "meaning": "Color"},
            {"character": "红", "pinyin": "hóng", "meaning": "Red"},
            {"character": "白", "pinyin": "bái", "meaning": "White"},
            {"character": "黑", "pinyin": "hēi", "meaning": "Black"},
            {"character": "蓝", "pinyin": "lán", "meaning": "Blue"},
            {"character": "绿", "pinyin": "lǜ", "meaning": "Green"},
            {"character": "黄", "pinyin": "huáng", "meaning": "Yellow"},
            {"character": "漂亮", "pinyin": "piào liang", "meaning": "Beautiful; pretty"},
            {"character": "好看", "pinyin": "hǎo kàn", "meaning": "Good-looking"},
            {"character": "好玩", "pinyin": "hǎo wán", "meaning": "Fun; interesting"},
            {"character": "好吃", "pinyin": "hǎo chī", "meaning": "Delicious"},
            {"character": "欢迎", "pinyin": "huān yíng", "meaning": "Welcome"},
            {"character": "请", "pinyin": "qǐng", "meaning": "Please; to invite"},
            {"character": "对不起", "pinyin": "duì bu qǐ", "meaning": "Sorry"},
            {"character": "没关系", "pinyin": "méi guān xi", "meaning": "It's okay"},
            {"character": "不用谢", "pinyin": "bú yòng xiè", "meaning": "You're welcome"},
        ],
    }
    
    # MakeMeAHanZI stroke order data
    MMHZ_STROKE_URL = "https://raw.githubusercontent.com/skishore/makemeahanzi/master/data/character.json"
    MMHZ_GLYPHS_URL = "https://raw.githubusercontent.com/skishore/makemeahanzi/master/glyphs/{char}.svg"
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(__file__).parent / "hsk_data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def download_hsk_json(self, level: str, url: str) -> Optional[List[Dict]]:
        """Download HSK data from JSON source."""
        try:
            print(f"Downloading {level}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Some sources wrap data in a dict
                return list(data.values())[0] if data else []
            return None
        except Exception as e:
            print(f"Failed to download {level}: {e}")
            return None
    
    def parse_hsk_entry(self, entry: Dict, level: str) -> Optional[Dict]:
        """Parse a raw HSK entry into standardized format."""
        try:
            # Handle different JSON structures
            character = entry.get('character', entry.get('hanzi', entry.get('word', '')))
            pinyin = entry.get('pinyin', entry.get('pronunciation', ''))
            meaning = entry.get('meaning', entry.get('definition', entry.get('english', '')))
            
            if not character:
                return None
            
            # Clean up data
            if isinstance(pinyin, list):
                pinyin = ' '.join(pinyin)
            if isinstance(meaning, list):
                meaning = '; '.join(meaning)
            
            return {
                "character": str(character).strip(),
                "pinyin": str(pinyin).strip() if pinyin else "",
                "meaning": str(meaning).strip() if meaning else "",
                "level": level
            }
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    def download_all_hsk_levels(self) -> Dict[str, List[Dict]]:
        """Download all HSK levels (1-6)."""
        all_data = {}
        
        for level_key, url in self.HSK_SOURCES.items():
            level_name = level_key.replace('_', ' ').upper()
            raw_data = self.download_hsk_json(level_name, url)
            
            if raw_data:
                parsed = []
                for entry in raw_data:
                    parsed_entry = self.parse_hsk_entry(entry, level_name)
                    if parsed_entry:
                        parsed.append(parsed_entry)
                
                all_data[level_name] = parsed
                print(f"✓ {level_name}: {len(parsed)} entries")
            else:
                print(f"✗ {level_name}: Failed to download")
                all_data[level_name] = []
        
        return all_data
    
    def download_stroke_order_data(self, characters: List[str]) -> Dict[str, Dict]:
        """Download stroke order data for specific characters from MakeMeAHanZI."""
        stroke_data = {}
        
        print(f"Downloading stroke order for {len(characters)} characters...")
        
        for i, char in enumerate(characters):
            if i % 100 == 0:
                print(f"Progress: {i}/{len(characters)}")
            
            try:
                # Try to get stroke order from makemeahanzi
                glyph_url = self.MMHZ_GLYPHS_URL.format(char=urllib.request.quote(char))
                req = urllib.request.Request(glyph_url, headers={'User-Agent': 'Mozilla/5.0'})
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    svg_data = response.read().decode('utf-8')
                    
                    # Parse SVG to extract stroke paths
                    strokes = self._parse_svg_strokes(svg_data)
                    if strokes:
                        stroke_data[char] = {
                            "strokes": strokes,
                            "stroke_count": len(strokes)
                        }
            except Exception as e:
                # Character not found or error
                pass
        
        return stroke_data
    
    def _parse_svg_strokes(self, svg_content: str) -> List[str]:
        """Extract individual stroke paths from SVG content."""
        strokes = []
        
        # Find all path elements with d attribute
        path_pattern = r'<path[^>]*d="([^"]*)"[^>]*>'
        matches = re.findall(path_pattern, svg_content)
        
        for path_data in matches:
            # Filter out non-stroke paths (like outlines)
            if path_data and len(path_data) > 10:
                strokes.append(path_data)
        
        return strokes
    
    def save_to_json(self, data: Dict, filename: str):
        """Save data to JSON file."""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved to {filepath}")
    
    def generate_python_module(self, hsk_data: Dict[str, List[Dict]], output_file: str):
        """Generate Python module with HSK vocabulary data."""
        filepath = self.output_dir / output_file
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("#!/usr/bin/env python3\n")
            f.write('"""\nAuto-generated HSK Vocabulary Data\nGenerated by HSKDataDownloader\n"""\n\n')
            f.write("HSK_VOCABULARY = {\n")
            
            for level, entries in hsk_data.items():
                f.write(f'    "{level}": [\n')
                for entry in entries:
                    char = entry['character'].replace('"', '\\"')
                    pinyin = entry['pinyin'].replace('"', '\\"')
                    meaning = entry['meaning'].replace('"', '\\"')
                    f.write(f'        {{"character": "{char}", "pinyin": "{pinyin}", "meaning": "{meaning}"}},\n')
                f.write("    ],\n")
            
            f.write("}\n")
        
        print(f"Generated Python module: {filepath}")
    
    def run_full_download(self):
        """Run complete download process for all HSK data."""
        print("=" * 60)
        print("HSK Character Data Downloader")
        print("=" * 60)
        
        # Download HSK vocabulary
        print("\n1. Downloading HSK Vocabulary (Levels 1-6)...")
        hsk_data = self.download_all_hsk_levels()
        
        # Save raw JSON
        self.save_to_json(hsk_data, "hsk_vocabulary.json")
        
        # Generate Python module
        self.generate_python_module(hsk_data, "hsk_vocabulary.py")
        
        # Get unique characters for stroke data
        all_chars = set()
        for entries in hsk_data.values():
            for entry in entries:
                # Add individual characters from multi-char words
                for char in entry['character']:
                    if '\u4e00' <= char <= '\u9fff':
                        all_chars.add(char)
        
        print(f"\nFound {len(all_chars)} unique characters")
        
        # Download stroke order data (this takes time)
        print("\n2. Downloading Stroke Order Data...")
        stroke_data = self.download_stroke_order_data(list(all_chars)[:500])  # Limit for demo
        
        if stroke_data:
            self.save_to_json(stroke_data, "stroke_order.json")
        
        print("\n" + "=" * 60)
        print("Download Complete!")
        print(f"Output directory: {self.output_dir}")
        print("=" * 60)
        
        return hsk_data, stroke_data


if __name__ == "__main__":
    downloader = HSKDataDownloader()
    downloader.run_full_download()
