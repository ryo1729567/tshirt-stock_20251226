import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime, timedelta, date
import json
import os
import io
import re
from pathlib import Path
import unicodedata

# --- 設定 ---
PAGE_TITLE = "Tシャツ＆タグ在庫管理システム"
PAGE_ICON = "👕"

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 定数 ---
TSHIRT_TYPES = [
    'パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし',
    'パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし',
    'パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり',
    'パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり'
]
SIZES = ['150cm', '160cm', 'S', 'M', 'L', 'XL', 'XXL']

# --- 解析済み初期データ (2025/12/14 - 2026/01/04) ---
# 提供されたCSVから全日程の数値を抽出しました
RAW_INITIAL_RECORDS = [
  {"date": "2026-01-04", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2026-01-03", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2026-01-02", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 3, "M": 0, "L": 0, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2026-01-01", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-31", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 0, "L": 2, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 0, "M": 0, "L": 0, "XL": 6, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-24", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 0, "160cm": 1, "S": 13, "M": 2, "L": 3, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 3, "160cm": 2, "S": 3, "M": 5, "L": 5, "XL": 7, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 9, "160cm": 5, "S": 0, "M": 12, "L": 11, "XL": 0, "XXL": 3}}},
  {"date": "2025-12-14", "inventory": {"パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし": {"150cm": 1, "160cm": 0, "S": 13, "M": 1, "L": 4, "XL": 3, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし": {"150cm": 0, "160cm": 2, "S": 8, "M": 0, "L": 3, "XL": 9, "XXL": 1}, "パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり": {"150cm": 0, "160cm": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}, "パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり": {"150cm": 10, "160cm": 5, "S": 0, "M": 14, "L": 12, "XL": 1, "XXL": 3}}}
]
# （※中間日程は自動補完ロジックにより、上記確定ポイントの間を埋めます）

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
        # 記録がない場合は初期化
        return cls._generate_initial_records()

    @classmethod
    def _generate_initial_records(cls):
        """確定ポイントをベースに12/14〜1/4の全日程を生成"""
        points = {r['date']: r['inventory'] for r in RAW_INITIAL_RECORDS}
        start_date = date(2025, 12, 14)
        end_date = date(2026, 1, 4)
        
        records = []
        last_inv = JAN_04_STOCK = points["2026-01-04"] # デフォルト
        
        # 12/14から順に作成
        curr = start_date
        while curr <= end_date:
            d_str = curr.strftime("%Y-%m-%d")
            # 確定ポイントがあれば更新、なければ前日の引き継ぎ
            if d_str in points:
                last_inv = points[d_str]
            
            records.append({
                'date': d_str,
                'timestamp': f"{d_str}T23:59:59",
                'inventory': json.loads(json.dumps(last_inv)),
                'note': '初期確定データ反映'
            })
            curr += timedelta(days=1)
            
        records.sort(key=lambda x: x['date'], reverse=True)
        return records

    @classmethod
    def auto_fill_missing_days(cls, records):
        """当日までの未入力日を直近の在庫で自動補完"""
        if not records: return records
        today = date.today()
        latest_date = datetime.strptime(records[0]['date'], "%Y-%m-%d").date()
        
        target_date = latest_date + timedelta(days=1)
        updated = False
        while target_date < today:
            d_str = target_date.strftime("%Y-%m-%d")
            new_record = {
                'date': d_str,
                'timestamp': datetime.now().isoformat(),
                'inventory': json.loads(json.dumps(records[0]['inventory'])),
                'note': '自動補完(前日コピー)'
            }
            records.insert(0, new_record)
            target_date += timedelta(days=1)
            updated = True
        if updated: cls.save_records(records)
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

# --- CSS設定 ---
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .big-number { font-size: 2.5rem; font-weight: bold; color: #0068c9; text-align: center; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# --- セッション初期化 ---
def init():
    InventoryManager.initialize()
    if 'records' not in st.session_state:
        recs = InventoryManager.load_records()
        st.session_state.records = InventoryManager.auto_fill_missing_days(recs)
    
    if 'inventory' not in st.session_state:
        st.session_state.inventory = json.loads(json.dumps(st.session_state.records[0]['inventory']))
    
    if 'tags' not in st.session_state:
        st.session_state.tags = InventoryManager.load_tags()
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = {}

# --- タブ表示 ---
def inventory_tab():
    st.header("📦 Tシャツ在庫入力")
    today_str = date.today().strftime("%Y-%m-%d")
    
    has_today = st.session_state.records[0]['date'] == today_str
    if has_today:
        st.success(f"✅ {today_str} の記録は保存済みです。")
    else:
        st.warning(f"🕒 {today_str} の記録は未保存です。1/4以前のデータは反映済みです。")

    if st.button("💾 本日の在庫を確定保存", type="primary"):
        save_current(today_str)
    
    st.divider()

    for ttype in TSHIRT_TYPES:
        with st.expander(f"👕 {ttype.replace('パンクラス×禅道会コラボTシャツ', '')}", expanded=True):
            cols = st.columns(len(SIZES))
            for idx, size in enumerate(SIZES):
                val = st.session_state.inventory[ttype].get(size, 0)
                new_val = cols[idx].number_input(size, min_value=0, value=val, key=f"inp_{ttype}_{size}")
                st.session_state.inventory[ttype][size] = new_val

def save_current(d_str):
    recs = st.session_state.records
    if recs[0]['date'] == d_str:
        recs[0]['inventory'] = json.loads(json.dumps(st.session_state.inventory))
        recs[0]['timestamp'] = datetime.now().isoformat()
        recs[0]['note'] = '手動更新'
    else:
        new_rec = {'date': d_str, 'timestamp': datetime.now().isoformat(), 'inventory': json.loads(json.dumps(st.session_state.inventory)), 'note': '手動保存'}
        recs.insert(0, new_rec)
    InventoryManager.save_records(recs)
    st.toast("保存完了しました")
    st.rerun()

def tags_tab():
    st.header("🏷️ タグ管理")
    curr = st.session_state.tags.get("current_stock", 0)
    st.markdown(f"<div class='big-number'>{curr:,} 枚</div>", unsafe_allow_html=True)
    
    with st.form("tag_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        mode = c1.radio("アクション", ["使用(-)", "入荷(+)", "不良(-)"])
        amt = c2.number_input("数量", min_value=1, value=1)
        note = st.text_input("備考")
        if st.form_submit_button("記録する"):
            if "入荷" in mode: curr += amt
            else: curr -= amt
            new_hist = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "action": mode, "amount": amt, "stock": curr, "note": note}
            st.session_state.tags["current_stock"] = curr
            st.session_state.tags["history"].insert(0, new_hist)
            InventoryManager.save_tags(st.session_state.tags)
            st.rerun()
    
    if st.session_state.tags["history"]:
        st.table(pd.DataFrame(st.session_state.tags["history"]).head(10))

def records_tab():
    st.header("📊 履歴・データ出力")
    df_list = []
    for r in st.session_state.records:
        for ttype, sizes in r['inventory'].items():
            row = {"日付": r['date'], "種類": ttype.split(')')[0]+')'}
            row.update(sizes)
            df_list.append(row)
    df = pd.DataFrame(df_list)
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 CSV形式で全履歴を保存", csv, "inventory_history.csv", "text/csv")

def settings_tab():
    st.header("⚙️ システム管理")
    full_data = {"records": st.session_state.records, "tags": st.session_state.tags, "export_at": datetime.now().isoformat()}
    st.download_button("📦 全データのバックアップ(JSON)", json.dumps(full_data, ensure_ascii=False, indent=2), f"backup_{date.today()}.json")

def manual_tab():
    st.header("📖 マニュアル")
    st.markdown("""
    ### 1. 在庫の反映状況
    - 2025/12/14 〜 2026/01/04 までのデータは自動反映済みです。
    - 入力のない日は、前日の在庫数値が自動補完されます。
    ### 2. 日常の操作
    - 当日の数値を確認し「確定保存」を押してください。
    """)

# --- メイン ---
def main():
    init()
    st.title(PAGE_TITLE)
    t1, t2, t3, t4, t5 = st.tabs(["📦 在庫入力", "🏷️ タグ管理", "📊 履歴・出力", "⚙️ 管理", "📖 マニュアル"])
    with t1: inventory_tab()
    with t2: tags_tab()
    with t3: records_tab()
    with t4: settings_tab()
    with t5: manual_tab()

if __name__ == "__main__":
    main()
