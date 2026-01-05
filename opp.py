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

# --- 初期データ (2025/12/14 - 2026/01/04) ---
# ご提供いただいたExcel/CSVの最新確定値（2026/01/04時点）を反映
JAN_04_STOCK = {
    'パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり': {
        '150cm': 9, '160cm': 5, 'S': 0, 'M': 12, 'L': 11, 'XL': 0, 'XXL': 3
    },
    'パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし': {
        '150cm': 5, '160cm': 3, 'S': 4, 'M': 8, 'L': 10, 'XL': 2, 'XXL': 1
    },
    'パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり': {
        '150cm': 12, '160cm': 8, 'S': 5, 'M': 15, 'L': 12, 'XL': 3, 'XXL': 2
    },
    'パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし': {
        '150cm': 7, '160cm': 4, 'S': 3, 'M': 10, 'L': 8, 'XL': 1, 'XXL': 0
    }
}

# --- データ管理クラス ---
class InventoryManager:
    DATA_DIR = Path("data")
    INVENTORY_FILE = DATA_DIR / "inventory_data.json"
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
        # 記録がない場合：2026/01/04までのダミー履歴を生成
        return cls._generate_initial_records()

    @classmethod
    def _generate_initial_records(cls):
        """1/4までの記録を生成。Excelから反映された最新数値を1/4として、それ以前を補完"""
        start_date = date(2025, 12, 14)
        end_date = date(2026, 1, 4)
        records = []
        curr = start_date
        while curr <= end_date:
            d_str = curr.strftime("%Y-%m-%d")
            records.append({
                'date': d_str,
                'timestamp': f"{d_str}T23:59:59",
                'inventory': JAN_04_STOCK,
                'note': '初期データ反映(1/4以前)'
            })
            curr += timedelta(days=1)
        # 新しい順にソート
        records.sort(key=lambda x: x['date'], reverse=True)
        return records

    @classmethod
    def auto_fill_missing_days(cls, records):
        """【新機能】当日までの未入力日を直近の在庫で自動補完"""
        if not records: return records
        
        today = date.today()
        # 最新の記録日を取得
        latest_date_str = records[0]['date']
        latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
        
        # 最後に記録された日の翌日から、昨日までの分を補完
        # (当日はまだ入力可能なので、昨日までの空白を埋める)
        target_date = latest_date + timedelta(days=1)
        updated = False
        
        while target_date < today:
            d_str = target_date.strftime("%Y-%m-%d")
            # 直近のレコードをコピー
            new_record = {
                'date': d_str,
                'timestamp': datetime.now().isoformat(),
                'inventory': json.loads(json.dumps(records[0]['inventory'])),
                'note': '自動補完(未入力のため前日コピー)'
            }
            records.insert(0, new_record)
            target_date += timedelta(days=1)
            updated = True
            
        if updated:
            cls.save_records(records)
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
    def normalize_str(s):
        return unicodedata.normalize('NFC', s)

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
        # 自動補完を実行
        st.session_state.records = InventoryManager.auto_fill_missing_days(recs)
    
    if 'inventory' not in st.session_state:
        # 1/5時点の初期表示用在庫（最新レコードから取得）
        st.session_state.inventory = json.loads(json.dumps(st.session_state.records[0]['inventory']))
    
    if 'tags' not in st.session_state:
        st.session_state.tags = InventoryManager.load_tags()
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = {}

# --- タブ表示 ---
def inventory_tab():
    st.header("📦 Tシャツ在庫入力")
    today_str = date.today().strftime("%Y-%m-%d")
    
    # 本日の記録があるか確認
    has_today = st.session_state.records[0]['date'] == today_str
    if has_today:
        st.success(f"✅ {today_str} の記録は保存済みです。修正して再保存も可能です。")
    else:
        st.warning(f"🕒 {today_str} の記録は未保存です。入力後に保存してください。")

    col1, col2 = st.columns(2)
    if col1.button("💾 本日の在庫を確定保存", type="primary"):
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
    # 既存チェック
    recs = st.session_state.records
    if recs[0]['date'] == d_str:
        recs[0]['inventory'] = json.loads(json.dumps(st.session_state.inventory))
        recs[0]['timestamp'] = datetime.now().isoformat()
        recs[0]['note'] = '手動更新'
    else:
        new_rec = {
            'date': d_str,
            'timestamp': datetime.now().isoformat(),
            'inventory': json.loads(json.dumps(st.session_state.inventory)),
            'note': '手動保存'
        }
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
            
            new_hist = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": mode,
                "amount": amt,
                "stock": curr,
                "note": note
            }
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
    st.info("サーバー再起動時に備え、定期的に以下のバックアップをPCに保存してください。")
    
    full_data = {
        "records": st.session_state.records,
        "tags": st.session_state.tags,
        "export_at": datetime.now().isoformat()
    }
    st.download_button(
        "📦 全データのバックアップ(JSON)",
        json.dumps(full_data, ensure_ascii=False, indent=2),
        f"backup_{date.today()}.json"
    )

def manual_tab():
    st.header("📖 マニュアル")
    st.markdown("""
    ### 1. 毎日の在庫更新
    - **「📦 Tシャツ在庫」**タブで現在の数値を入力し、**「確定保存」**を押してください。
    - **自動補完機能**: 入力しなかった日は、前回の在庫数値が自動的にコピーされます。
    
    ### 2. タグ管理
    - 使用や入荷があった時だけ**「🏷️ タグ管理」**から入力してください。
    
    ### 3. データの保護
    - Webアプリの特性上、稀にデータがリセットされることがあります。
    - 週に一度程度、**「⚙️ システム管理」**からバックアップを保存することを推奨します。
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
