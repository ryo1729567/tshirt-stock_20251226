import streamlit as st
import pandas as pd
import openpyxl
from datetime import datetime, timedelta, date
import json
import os
import io
import re
from pathlib import Path
import unicodedata

# --- 基本設定 ---
st.set_page_config(page_title="Tシャツ＆タグ在庫管理システム", page_icon="👕", layout="wide")

# --- 定数 ---
TSHIRT_TYPES = [
    'パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし',
    'パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし',
    'パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり',
    'パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり'
]
SIZES = ['150cm', '160cm', 'S', 'M', 'L', 'XL', 'XXL']

# --- 解析済み確定データ (2025/12/14 - 2026/01/04) ---
# 全Excelファイルから抽出した正確な数値
RAW_INITIAL_RECORDS = [
  {"date": "2026-01-04", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2026-01-03", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2026-01-02", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2026-01-01", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-31", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-30", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-29", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-28", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-27", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-26", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-25", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-24", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 2, "L": 3, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 3, "160cm": 2, "S": 3, "M": 5, "L": 5, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-23", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 3, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 1, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-22", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-21", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-20", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-19", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-18", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-17", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-16", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-15", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-14", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 1, "160cm": 0, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 8, "M": 0, "L": 3, "XL": 9, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 10, "160cm": 5, "S": 0, "M": 14, "L": 12, "XL": 1, "XXL": 3}}}
]

# --- データ管理クラス ---
class InventoryManager:
    DATA_DIR = Path("data")
    RECORDS_FILE = DATA_DIR / "daily_records.json"
    TAG_FILE = DATA_DIR / "tag_data.json"

    @classmethod
    def initialize(cls):
        cls.DATA_DIR.mkdir(exist_ok=True)

    @classmethod
    def load_records(cls):
        if cls.RECORDS_FILE.exists():
            try:
                with open(cls.RECORDS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return cls._generate_initial_records()

    @classmethod
    def _generate_initial_records(cls):
        """確定ポイントをベースに期間中の全日程を補完生成"""
        points = {r['date']: r['inventory'] for r in RAW_INITIAL_RECORDS}
        start_date = date(2025, 12, 14)
        end_date = date(2026, 1, 4)
        records = []
        last_inv = points["2025-12-14"]
        curr = start_date
        while curr <= end_date:
            d_str = curr.strftime("%Y-%m-%d")
            if d_str in points: last_inv = points[d_str]
            records.append({"date": d_str, "timestamp": f"{d_str}T23:59:59", "inventory": json.loads(json.dumps(last_inv)), "note": "初期確定データ"})
            curr += timedelta(days=1)
        records.sort(key=lambda x: x['date'], reverse=True)
        return records

    @classmethod
    def auto_fill(cls, records):
        """当日までの未入力日を自動補完"""
        if not records: return records
        today = date.today()
        latest = datetime.strptime(records[0]['date'], "%Y-%m-%d").date()
        curr = latest + timedelta(days=1)
        while curr < today:
            d_str = curr.strftime("%Y-%m-%d")
            records.insert(0, {"date": d_str, "timestamp": datetime.now().isoformat(), "inventory": json.loads(json.dumps(records[0]['inventory'])), "note": "自動補完"})
            curr += timedelta(days=1)
        return records

    @classmethod
    def save_records(cls, records):
        records.sort(key=lambda x: x['date'], reverse=True)
        with open(cls.RECORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_tags(cls):
        if cls.TAG_FILE.exists():
            try:
                with open(cls.TAG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"current_stock": 0, "history": []}

    @classmethod
    def save_tags(cls, data):
        with open(cls.TAG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def normalize_size(val):
        val = unicodedata.normalize('NFKC', str(val))
        if '150' in val: return '150cm'
        if '160' in val: return '160cm'
        if 'XXL' in val or '3L' in val: return 'XXL'
        if 'XL' in val or 'LL' in val: return 'XL'
        if 'L' in val: return 'L'
        if 'M' in val: return 'M'
        if 'S' in val: return 'S'
        return None

    @staticmethod
    def determine_type(filename, sheet_name=""):
        text = filename + sheet_name
        color = "ブラック" if ("黒" in text or "ブラック" in text) else "ホワイト"
        mark = "なし" if "なし" in text else "あり"
        return f"パンクラス×禅道会コラボTシャツ({color})ゼンプロマーク{mark}"

    @classmethod
    def fast_import_matrix(cls, uploaded_files):
        all_records = {r['date']: r['inventory'] for r in cls.load_records()}
        processed_count = 0
        for up_file in uploaded_files:
            try:
                if up_file.name.endswith('.csv'):
                    sheets = {up_file.name: pd.read_csv(up_file, header=None)}
                else:
                    sheets = pd.read_excel(up_file, sheet_name=None, header=None, engine='openpyxl')
                
                for s_name, df in sheets.items():
                    target_type = cls.determine_type(up_file.name, s_name)
                    
                    header_idx = None
                    date_cols = {}
                    
                    # ヘッダー行探索 (YYYY-MM-DDを含む行)
                    for idx, row in df.iterrows():
                        row_date_map = {}
                        for col_idx, val in row.items():
                            val_str = str(val).strip()
                            if re.match(r'^\d{4}-\d{2}-\d{2}$', val_str):
                                row_date_map[col_idx] = val_str
                        if len(row_date_map) > 2:
                            date_cols = row_date_map
                            header_idx = idx
                            break
                    
                    if header_idx is None: continue
                    
                    data_df = df.iloc[header_idx+1:]
                    
                    for _, row in data_df.iterrows():
                        # サイズ列の特定 (通常は1列目か0列目)
                        size_raw = row.get(1) if not pd.isna(row.get(1)) else row.get(0)
                        size = cls.normalize_size(size_raw)
                        if not size: continue
                        
                        for col_idx, d_str in date_cols.items():
                            try:
                                count = int(float(row.get(col_idx))) if pd.notnull(row.get(col_idx)) else 0
                            except: count = 0
                            
                            if d_str not in all_records:
                                all_records[d_str] = {t: {s: 0 for s in SIZES} for t in TSHIRT_TYPES}
                            
                            all_records[d_str][target_type][size] = count
                            processed_count += 1
            except: pass
            
        new_records = [{"date": d, "timestamp": f"{d}T23:59:59", "inventory": inv, "note": "Excel一括反映"} for d, inv in all_records.items()]
        cls.save_records(new_records)
        return processed_count

# --- UI部品 ---
def init():
    InventoryManager.initialize()
    if 'records' not in st.session_state:
        recs = InventoryManager.load_records()
        st.session_state.records = InventoryManager.auto_fill(recs)
    if 'tags' not in st.session_state: st.session_state.tags = InventoryManager.load_tags()
    if 'show_nag' not in st.session_state: st.session_state.show_nag = False

def main():
    init()
    with st.sidebar:
        st.error("⚠️ **重要：バックアップ**")
        st.write("作業終了時に必ず「データ管理」からJSONを保存してください。")
        if st.session_state.records: st.info(f"最新記録日: {st.session_state.records[0]['date']}")

    st.title("👕 Tシャツ＆タグ在庫管理システム")
    if st.session_state.show_nag:
        st.warning("🚨 **データが更新されました！** 消失を防ぐため「データ管理」タブからバックアップを保存してください。")
        if st.button("了解（メッセージを消す）"): st.session_state.show_nag = False; st.rerun()

    tabs = st.tabs(["📦 在庫入力", "🏷️ タグ管理", "📈 履歴・グラフ", "📥 Excel取込", "⚙️ データ管理"])

    with tabs[0]:
        st.header("在庫の記録")
        target_date = st.date_input("記録対象日", value=date.today())
        d_str = target_date.strftime("%Y-%m-%d")
        existing = next((r['inventory'] for r in st.session_state.records if r['date'] == d_str), None)
        latest_inv = json.loads(json.dumps(existing if existing else (st.session_state.records[0]['inventory'] if st.session_state.records else {t: {s: 0 for s in SIZES} for t in TSHIRT_TYPES})))
        
        if st.button(f"💾 {d_str} の在庫を保存", type="primary"):
            recs = st.session_state.records
            idx = next((i for i, r in enumerate(recs) if r['date'] == d_str), None)
            entry = {"date": d_str, "timestamp": datetime.now().isoformat(), "inventory": latest_inv, "note": "手動保存"}
            if idx is not None: recs[idx] = entry
            else: recs.append(entry)
            InventoryManager.save_records(recs)
            st.session_state.show_nag = True
            st.rerun()

        for ttype in TSHIRT_TYPES:
            with st.expander(ttype, expanded=True):
                cols = st.columns(len(SIZES))
                for i, s in enumerate(SIZES):
                    latest_inv[ttype][s] = cols[i].number_input(s, min_value=0, value=int(latest_inv[ttype].get(s, 0)), key=f"{d_str}{ttype}{s}")

    with tabs[1]:
        st.header("タグ管理")
        tags = st.session_state.tags
        st.metric("現在のタグ在庫", f"{tags['current_stock']}枚")
        with st.form("tag_f", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            m = c1.selectbox("区分", ["入荷(+)", "使用(-)", "不良(-)"])
            a = c2.number_input("枚数", min_value=1, value=1)
            n = c3.text_input("備考")
            if st.form_submit_button("記録"):
                tags['current_stock'] += a if "入荷" in m else -a
                tags['history'].insert(0, {"date": date.today().isoformat(), "action": m, "amount": a, "note": n})
                InventoryManager.save_tags(tags)
                st.session_state.show_nag = True
                st.rerun()
        st.table(pd.DataFrame(tags['history']).head(10))

    with tabs[2]:
        st.header("在庫推移と履歴")
        if not st.session_state.records:
            st.info("データがありません。")
        else:
            # グラフ用データ整形
            graph_list = []
            table_list = []
            for r in st.session_state.records:
                d = r['date']
                daily_sums = {"日付": d}
                for ttype, sizes in r['inventory'].items():
                    clean_name = ttype.replace('パンクラス×禅道会コラボTシャツ', '')
                    daily_sums[clean_name] = sum(sizes.values())
                    # 履歴テーブル用
                    row = {"日付": d, "種類": clean_name}
                    row.update(sizes)
                    table_list.append(row)
                graph_list.append(daily_sums)
            
            # 折れ線グラフ表示
            st.subheader("📈 在庫推移（合計枚数）")
            df_graph = pd.DataFrame(graph_list).set_index("日付").sort_index()
            st.line_chart(df_graph)
            
            st.divider()
            
            # 種類別フィルタ付きテーブル表示
            st.subheader("📋 詳細履歴データ")
            selected_type = st.selectbox("表示する種類を選択", ["すべて表示"] + [t.replace('パンクラス×禅道会コラボTシャツ', '') for t in TSHIRT_TYPES])
            df_table = pd.DataFrame(table_list)
            if selected_type != "すべて表示":
                df_table = df_table[df_table["種類"] == selected_type]
            
            st.dataframe(df_table, use_container_width=True)
            st.download_button("📥 表示中のデータをCSV出力", df_table.to_csv(index=False).encode('utf-8-sig'), f"inventory_{selected_type}.csv")

    with tabs[3]:
        st.header("Excel/CSV 一括取込")
        st.info("横軸が日付、縦軸がサイズの管理表に対応しています。")
        files = st.file_uploader("ファイルを選択", accept_multiple_files=True)
        if st.button("🚀 解析・反映") and files:
            count = InventoryManager.fast_import_matrix(files)
            st.success(f"解析完了！ {count}件のデータを反映しました。")
            st.session_state.show_nag = True
            st.session_state.records = InventoryManager.load_records()
            st.rerun()

    with tabs[4]:
        st.header("⚙️ データ一括管理")
        full_backup = {"records": st.session_state.records, "tags": st.session_state.tags, "at": datetime.now().isoformat()}
        st.subheader("1. バックアップの保存")
        st.download_button("📦 全データをJSONで保存", json.dumps(full_backup, ensure_ascii=False, indent=2), f"full_backup_{date.today()}.json", type="primary")
        
        st.subheader("2. バックアップの復元")
        up = st.file_uploader("JSONファイルをアップロード", type="json")
        if up and st.button("📥 データを復元"):
            data = json.load(up)
            InventoryManager.save_records(data['records'])
            InventoryManager.save_tags(data['tags'])
            st.session_state.records = data['records']
            st.session_state.tags = data['tags']
            st.success("復元しました！")
            st.rerun()

if __name__ == "__main__":
    main()
