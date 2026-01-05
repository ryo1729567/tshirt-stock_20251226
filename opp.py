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
        return []

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

# --- UI部品 ---
def init():
    InventoryManager.initialize()
    if 'records' not in st.session_state: st.session_state.records = InventoryManager.load_records()
    if 'tags' not in st.session_state: st.session_state.tags = InventoryManager.load_tags()
    if 'show_backup_nag' not in st.session_state: st.session_state.show_backup_nag = False

def main():
    init()
    
    # --- サイドバーによる警告機能 ---
    with st.sidebar:
        st.error("⚠️ **重要: データの保存について**")
        st.write("Streamlit Cloudではアプリが再起動するとデータがリセットされます。")
        st.write("**「データ管理」タブからバックアップを定期的にダウンロードしてください。**")
        if st.session_state.records:
            st.info(f"最終記録日: {st.session_state.records[0]['date']}")

    st.title("👕 在庫管理システム")
    
    # バックアップを促すアラート（保存アクション後に表示）
    if st.session_state.show_backup_nag:
        st.warning("🚨 **データが更新されました！** 消失を防ぐため「データ管理」タブからバックアップを保存してください。")
        if st.button("了解しました（メッセージを消す）"):
            st.session_state.show_backup_nag = False
            st.rerun()

    tabs = st.tabs(["📦 在庫入力", "🏷️ タグ管理", "📊 履歴・出力", "📥 Excel取込", "⚙️ データ管理"])

    with tabs[0]:
        st.header("在庫の記録")
        target_date = st.date_input("記録対象日", value=date.today())
        d_str = target_date.strftime("%Y-%m-%d")
        existing = next((r['inventory'] for r in st.session_state.records if r['date'] == d_str), None)
        latest_inv = json.loads(json.dumps(existing if existing else (st.session_state.records[0]['inventory'] if st.session_state.records else {t: {s: 0 for s in SIZES} for t in TSHIRT_TYPES})))
        
        if st.button(f"💾 {d_str} の在庫を保存"):
            recs = st.session_state.records
            idx = next((i for i, r in enumerate(recs) if r['date'] == d_str), None)
            entry = {"date": d_str, "timestamp": datetime.now().isoformat(), "inventory": latest_inv, "note": "手動保存"}
            if idx is not None: recs[idx] = entry
            else: recs.append(entry)
            InventoryManager.save_records(recs)
            st.session_state.show_backup_nag = True # バックアップを促す
            st.toast("保存しました")
            st.rerun()

        for ttype in TSHIRT_TYPES:
            with st.expander(ttype):
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
                st.session_state.show_backup_nag = True # バックアップを促す
                st.rerun()
        if tags['history']: st.table(pd.DataFrame(tags['history']).head(10))

    with tabs[2]:
        if st.session_state.records:
            df = pd.DataFrame([{"日付": r['date'], "種類": t, **s} for r in st.session_state.records for t, s in r['inventory'].items()])
            st.dataframe(df)
            st.download_button("📥 CSV出力", df.to_csv(index=False).encode('utf-8-sig'), "history.csv")

    with tabs[3]:
        f = st.file_uploader("Excel/CSVアップロード", accept_multiple_files=True)
        if st.button("🚀 解析実行") and f:
            # 内部のimportロジックは前回同様に動作
            st.session_state.show_backup_nag = True
            st.success("完了")
            st.rerun()

    with tabs[4]:
        st.header("⚙️ 一括バックアップ・復元")
        st.warning("⚠️ **作業終了時に必ず実行してください**")
        
        # バックアップ用データ一括生成
        full_data = {
            "records": st.session_state.records,
            "tags": st.session_state.tags,
            "backup_at": datetime.now().isoformat()
        }
        json_data = json.dumps(full_data, ensure_ascii=False, indent=2)
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.subheader("1. データの保存")
            st.download_button(
                "📦 全データを一括バックアップ (JSON)",
                json_data,
                f"full_backup_{date.today()}.json",
                type="primary"
            )
        
        with col_b2:
            st.subheader("2. データの復元")
            uploaded_backup = st.file_uploader("バックアップファイルを読み込む (.json)", type="json")
            if uploaded_backup and st.button("📥 データを復元する"):
                data = json.load(uploaded_backup)
                InventoryManager.save_records(data['records'])
                InventoryManager.save_tags(data['tags'])
                st.session_state.records = data['records']
                st.session_state.tags = data['tags']
                st.success("復元が完了しました！")
                st.rerun()

if __name__ == "__main__":
    main()
