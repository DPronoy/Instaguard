'''#  ___________________________________________________________________________
# |                                                                           |
# |  PROJECT: InstaGuard Enterprise                                           |
# |  MODULE : analyzer.py                                                     |
# |  AUTHOR : Pronoy Das                                                      |
# |___________________________________________________________________________|

import re
import pandas as pd
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

MODEL_PATH = "./engine/model_v1"
LEXICON_PATH = "raw_data/hinglish.csv"

# Backward compatibility
HybridAnalyzer = InstaGuardAnalyzer


class InstaGuardAnalyzer:
    def __init__(self):
        # Load ML engine
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)
        self.model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
        self.model.eval()
        self.model.to("cuda" if torch.cuda.is_available() else "cpu")

        # Load curse lexicon
        df = pd.read_csv(LEXICON_PATH)
        df.columns = df.columns.str.strip().str.lower()

        # Auto-detect text column
        text_col = None
        for col in df.columns:
            if col in ["text", "word", "phrase", "abuse", "curse"]:
                text_col = col
                break

        if text_col is None:
            raise Exception("❌ No curse column found in hinglish.csv")

        self.toxic_phrases = (
            df[text_col]
            .dropna()
            .astype(str)
            .str.lower()
            .str.strip()
            .unique()
            .tolist()
        )

        print(f"🧠 Analyzer loaded {len(self.toxic_phrases)} Hinglish curse terms")

    # -------------------------------------
    def normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z\s]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # -------------------------------------
    def lexicon_scan(self, text: str):
        normalized = self.normalize(text)
        compact = normalized.replace(" ", "")
        hits = set()

        for phrase in self.toxic_phrases:
            # Whole-word / phrase match
            if re.search(rf"(?:^|\s){re.escape(phrase)}(?:\s|$)", normalized):
                hits.add(phrase)
                continue

            # Joined abuse detection
            if phrase.replace(" ", "") in compact:
                hits.add(phrase)

        return hits

    # -------------------------------------
    def ml_score(self, text: str) -> float:
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=32
        )

        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=1)
            return probs[0][1].item()  # toxic probability

    # -------------------------------------
    def analyze(self, text: str):
        lex_hits = self.lexicon_scan(text)
        ml_prob = self.ml_score(text)

        if lex_hits:
            severity = "high" if len(lex_hits) >= 2 else "medium"
            score = min(1.0, 0.6 + 0.2 * len(lex_hits))
        else:
            severity = "low"
            score = ml_prob

        return {
            "input": text,
            "is_toxic": bool(lex_hits or ml_prob > 0.7),
            "matched_terms": list(lex_hits),
            "ml_score": round(ml_prob, 3),
            "final_score": round(score, 3),
            "severity": severity
        }


# -------------------------------
if __name__ == "__main__":
    analyzer = InstaGuardAnalyzer()

    tests = [
        "chutiya",
        "chaman chutiya",
        "tu chamanchutiya hai",
        "bhai tu pagal hai",
        "hello dost"
    ]

    for t in tests:
        print(analyzer.analyze(t))
'''



'''import pandas as pd
import os
import re

class HybridAnalyzer:
    def __init__(self):
        print("🧠 Initializing Hybrid Analyzer (Production Grade)...")
        self.toxic_words = set()
        self.toxic_phrases = set()
        
        # 1. Load Data
        self.load_database()
        
        # 2. SAFETY NET: Manually inject core words to guarantee detection
        # This fixes your "direct word" issue immediately.
        manual_blocklist = {
            "chutiya", "bhadwa", "madarchod", "bsdk", "bhosdike", 
            "kutta", "kamina", "saala", "harami", "randi", "gandu",
            "ass", "bastard", "bitch" # English examples
        }
        self.toxic_words.update(manual_blocklist)
        
        print(f"✅ Total Toxic words loaded : {len(self.toxic_words)}")

    def load_database(self):
        path = os.path.join("raw_data", "hinglish.csv")

        if not os.path.exists(path):
            print("⚠️ CSV not found. Relying on manual blocklist only.")
            return

        try:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip().str.lower()
            
            # Smart column detection
            text_col = "text" if "text" in df.columns else "content"
            label_col = "hate_label" if "hate_label" in df.columns else "label"

            # Strict filtering: Convert column to string to catch "1", 1, "yes", "true"
            toxic_df = df[df[label_col].astype(str).isin(["1", "1.0", "yes", "true"])]

            for raw in toxic_df[text_col].astype(str):
                clean = self.normalize_standard(raw)
                
                # Add full phrase
                if len(clean) > 3:
                    self.toxic_phrases.add(clean)

                # Add individual words (Only > 2 chars to avoid banning "is", "it")
                for word in clean.split():
                    if len(word) > 2:
                        self.toxic_words.add(word)
                        
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")

    def normalize_standard(self, text: str) -> str:
        """
        Standard cleaning. Preserves spaces.
        Used to distinguish 'assistant' from 'ass'.
        """
        text = text.lower()
        # Remove invisible unicode
        text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", text)
        # Turn punctuation into SPACES (important!)
        # "hello!chutiya" -> "hello chutiya"
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        # Normalize spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def normalize_aggressive(self, text: str) -> str:
        """
        Aggressive cleaning. Removes all symbols and spaces.
        Used to catch 'c.h.u.t.i.y.a' or 'ch*tiya'.
        """
        text = text.lower()
        # Remove ALL non-alphanumeric characters
        text = re.sub(r"[^a-z0-9]", "", text)
        return text

    def scan(self, text: str):
        # --- PHASE 1: STANDARD CHECK (High Precision) ---
        # This handles normal sentences and prevents the "Assistant" bug.
        
        clean_std = self.normalize_standard(text)
        tokens = clean_std.split() # Split into list: ['assistant', 'manager']

        for word in tokens:
            # We check if the EXACT word exists in our bad list
            if word in self.toxic_words:
                return {
                    "is_toxic": True, 
                    "reason": f"Direct Word Match: '{word}'", 
                    "score": 1.0
                }
        
        # --- PHASE 2: PHRASE CHECK ---
        # Checks for multi-word insults (e.g. "go to hell")
        for phrase in self.toxic_phrases:
            # Use regex to match whole phrase boundaries
            if re.search(r"\b" + re.escape(phrase) + r"\b", clean_std):
                return {
                    "is_toxic": True, 
                    "reason": f"Phrase Match: '{phrase}'", 
                    "score": 1.0
                }

        # --- PHASE 3: AGGRESSIVE/EVASION CHECK (Low Precision, High Recall) ---
        # This catches "c.h.u.t.i.y.a" or "ch*tiya"
        # Only runs if Phase 1 and 2 found nothing.
        
        clean_aggr = self.normalize_aggressive(text) # "youareachutiya"
        
        # We check if any HIGH PRIORITY bad word is hidden inside the string
        # We verify length > 3 to avoid matching "as" inside "please"
        for toxic in self.toxic_words:
            if len(toxic) > 4 and toxic in clean_aggr:
                return {
                    "is_toxic": True, 
                    "reason": f"Hidden/Obfuscated Match: '{toxic}' in '{clean_aggr}'", 
                    "score": 0.8
                }

        return {"is_toxic": False, "reason": "Safe", "score": 0.0}

# ==========================================
# TEST RUNNER (Copy this part to test instantly)
# ==========================================
if __name__ == "__main__":
    # 1. Create dummy data for testing (So it works on your machine immediately)
    if not os.path.exists("raw_data"):
        os.makedirs("raw_data")
    
    # Writing a temporary CSV to simulate your file
    with open("raw_data/hinglish.csv", "w") as f:
        f.write("text,hate_label\ntera baap chor hai,1\nI love you,0\n")

    # 2. Initialize
    analyzer = HybridAnalyzer()

    # 3. Test Cases
    comments = [
        "chutiya",                  # Direct standalone (Your main issue)
        "You are a chutiya",        # Sentence context
        "I need an assistant",      # The "Assistant" Trap (Should be GREEN/Safe)
        "You are a c.h.u.t.i.y.a",  # Evasion (Dots)
        "ch*tiya log",              # Evasion (Symbol)
        "bsdk",                     # Direct slang
        "class assignment",         # "ass" inside "assignment" (Should be GREEN/Safe)
    ]

    print("\n--- 🔍 SCAN RESULTS ---")
    for c in comments:
        res = analyzer.scan(c)
        status = "🔴 TOXIC" if res["is_toxic"] else "🟢 SAFE "
        print(f"[{status}] '{c}' \n\t\t👉 {res['reason']}")'''


#  ___________________________________________________________________________
# |                                                                           |
# |  PROJECT: InstaGuard Enterprise (Brain Module)                            |
# |  AUTHOR:  Pronoy Das                                                      |
# |  LICENSE: MIT (Copyright © 2026 Pronoy Das)                               |
# |___________________________________________________________________________|

import pandas as pd
import os
import re

class HybridAnalyzer:
    def __init__(self):
        print("🛡️ Initializing Forensic Engine...")
        
        # 1. Master Set (Everything combined)
        self.toxic_phrases = set()

        # 2. HIGH RISK / LOOSE SET (Hinglish): 
        # These are detected even inside other words (e.g. "aaachutiyaaa")
        # HARDCODED to ensure they work even if CSV fails.
        self.loose_phrases = {
            "chutiya", "chutia", "bhadwa", "madarchod", "bsdk", "kutta", "kamina", 
            "saale", "randi", "gandu", "mc", "bc", "bhosdike", "hijda", "chinaal",
            "haramkhor", "suar", "jhaatu"
        }
        
        # 3. STRICT SET (English): 
        # These need word boundaries (e.g. detect "kill" but ignore "skill")
        self.strict_phrases = set()
        
        # Initialize
        self.toxic_phrases.update(self.loose_phrases)
        self.load_database()

    def load_database(self):
        """Loads external CSVs and sorts words into Strict or Loose categories"""
        # Config: (Filename, Text Column, Label Column)
        files_config = [
            ("hinglish.csv", "text", "hate_label"), 
            ("english.csv", "tweet", "class"),
            ("hindi.csv", "text", "label")
        ]
        
        raw_path = "raw_data"
        if not os.path.exists(raw_path):
            print(f"⚠️ Warning: '{raw_path}' folder not found. Using hardcoded list.")
            # We continue anyway because we have the hardcoded list!

        for filename, text_col, label_col in files_config:
            path = os.path.join(raw_path, filename)
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    df.columns = df.columns.str.strip().str.lower()
                    
                    if text_col in df.columns and label_col in df.columns:
                        # Filter for toxic rows
                        bad_rows = df[df[label_col].astype(str).str.lower().isin(['1', 'toxic', 'yes', 'hate', 'offensive'])]
                        phrases = bad_rows[text_col].astype(str).str.lower().str.strip().tolist()
                        
                        for p in phrases:
                            if len(p) < 2: continue 
                            
                            self.toxic_phrases.add(p)

                            # Logic: If it matches our known Hinglish list, keep it loose.
                            # Otherwise, treat it as Strict English to prevent false positives.
                            if any(risk in p for risk in self.loose_phrases):
                                continue 
                            else:
                                self.strict_phrases.add(p)
                except: pass
        
        print(f"✅ Database Ready: {len(self.toxic_phrases)} active patterns.")

    def normalize_text(self, text):
        """
        Advanced cleaning to catch evasive spellings.
        1. 'c.h.u.t.i.y.a' -> 'chutiya' (Removes special chars)
        2. 'chuuutiya' -> 'chutiya' (Collapses repeated chars)
        """
        # Remove non-alphanumeric chars (dots, commas, etc) but keep spaces
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Collapse repeated characters (e.g. "uuu" -> "u")
        text = re.sub(r'(.)\1+', r'\1', text) 
        
        return text

    def scan(self, text):
        if not text: return {"is_toxic": False, "reason": "Safe", "score": 0.0}

        # 1. Prepare Variations
        raw_clean = text.lower().strip()
        normalized = self.normalize_text(raw_clean)
        
        # We check both the original and the normalized version
        variants = [raw_clean, normalized]

        # --- PHASE 1: HIGH RISK (Hinglish) CHECK ---
        # This uses "Substring Matching".
        # It finds "chutiya" inside "aaachutiyaaa" or "yehchutiyahai"
        for v in variants:
            for phrase in self.loose_phrases:
                if phrase in v:
                    return {
                        "is_toxic": True, 
                        "reason": f"Direct Match (High Risk): '{phrase}'", 
                        "score": 1.0
                    }

        # --- PHASE 2: STRICT (English) CHECK ---
        # This uses "Word Boundaries" (\b).
        # It finds "kill" but ignores "skill".
        if self.strict_phrases:
            pattern_str = r'\b(' + '|'.join(re.escape(p) for p in self.strict_phrases) + r')\b'
            for v in variants:
                match = re.search(pattern_str, v)
                if match:
                    return {
                        "is_toxic": True, 
                        "reason": f"Exact Match: '{match.group(0)}'", 
                        "score": 1.0
                    }

        return {"is_toxic": False, "reason": "Safe", "score": 0.0}