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
st.set_page_config(page_title="Tシャツ在庫管理システム Pro", page_icon="👕", layout="wide")

# --- 定数 ---
TSHIRT_TYPES = [
    'パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークなし',
    'パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークなし',
    'パンクラス×禅道会コラボTシャツ(ホワイト)ゼンプロマークあり',
    'パンクラス×禅道会コラボTシャツ(ブラック)ゼンプロマークあり'
]
SIZES = ['150cm', '160cm', 'S', 'M', 'L', 'XL', 'XXL']

# --- スタイル ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    .big-number { font-size: 2.2rem; font-weight: bold; color: #0068c9; text-align: center; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; }
    .status-box { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

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
        # 日付順（新しい順）に並べ替えて保存
        records.sort(key=lambda x: x['date'], reverse=True)
        with open(cls.RECORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    @staticmethod
    def normalize_size(val):
        """Excelの商品名からサイズを特定"""
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
        """ファイル名やシート名からTシャツの種類を特定"""
        text = filename + sheet_name
        color = "ブラック" if ("黒" in text or "ブラック" in text) else "ホワイト"
        mark = "あり" if "あり" in text else "なし"
        return f"パンクラス×禅道会コラボTシャツ({color})ゼンプロマーク{mark}"

    @classmethod
    def fast_import_matrix(cls, uploaded_files):
        """最速マトリクス解析ロジック"""
        all_records = {r['date']: r['inventory'] for r in cls.load_records()}
        processed_count = 0

        for up_file in uploaded_files:
            try:
                # Excel/CSV読み込み
                if up_file.name.endswith('.csv'):
                    sheets = {up_file.name: pd.read_csv(up_file, header=None)}
                else:
                    sheets = pd.read_excel(up_file, sheet_name=None, header=None, engine='openpyxl')

                for s_name, df in sheets.items():
                    target_type = cls.determine_type(up_file.name, s_name)
                    
                    # ヘッダー行（日付が並んでいる行）を特定
                    header_idx = None
                    for idx, row in df.iterrows():
                        if any("商品名" in str(v) for v in row.values):
                            header_idx = idx
                            break
                    
                    if header_idx is None: continue
                    
                    header_row = df.iloc[header_idx]
                    data_df = df.iloc[header_idx+1:]
                    
                    # 日付列の特定
                    date_cols = {}
                    for col_idx, val in header_row.items():
                        d_str = None
                        if isinstance(val, datetime): d_str = val.strftime("%Y-%m-%d")
                        elif re.match(r'^\d{4}-\d{2}-\d{2}', str(val)): d_str = str(val)[:10]
                        
                        if d_str: date_cols[col_idx] = d_str
                    
                    # データの抽出
                    for _, row in data_df.iterrows():
                        size = cls.normalize_size(row.iloc[1]) # B列(index 1)を想定
                        if not size: continue
                        
                        for col_idx, d_str in date_cols.items():
                            try:
                                count = int(float(row.iloc[col_idx])) if pd.notnull(row.iloc[col_idx]) else 0
                            except: count = 0
                            
                            if d_str not in all_records:
                                all_records[d_str] = {t: {s: 0 for s in SIZES} for t in TSHIRT_TYPES}
                            
                            all_records[d_str][target_type][size] = count
                            processed_count += 1
            except Exception as e:
                st.error(f"ファイル解析エラー ({up_file.name}): {e}")

        # JSON形式へ変換
        new_records = []
        for d, inv in all_records.items():
            new_records.append({"date": d, "timestamp": f"{d}T23:59:59", "inventory": inv, "note": "Excel一括反映"})
        
        cls.save_records(new_records)
        return processed_count

# --- セッション初期化 ---
def init():
    InventoryManager.initialize()
    if 'records' not in st.session_state:
        st.session_state.records = InventoryManager.load_records()
    if 'tags' not in st.session_state:
        if InventoryManager.TAG_FILE.exists():
            st.session_state.tags = json.load(open(InventoryManager.TAG_FILE, 'r', encoding='utf-8'))
        else:
            st.session_state.tags = {"current_stock": 0, "history": []}

# --- メインUI ---
def main():
    init()
    st.title("👕 Tシャツ在庫管理 Pro")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📦 在庫入力", "🏷️ タグ管理", "📊 履歴・出力", "📥 Excel取込", "📖 ヘルプ"])

    with tab1:
        st.header("在庫の記録")
        # 任意の日付設定機能
        col_d1, col_d2 = st.columns([2, 3])
        target_date = col_d1.date_input("記録対象日を選択", value=date.today())
        d_str = target_date.strftime("%Y-%m-%d")
        
        # 既存データの読み込み
        existing_data = next((r['inventory'] for r in st.session_state.records if r['date'] == d_str), None)
        if not existing_data:
            # 記録がない場合は直近のデータをコピー
            latest = st.session_state.records[0]['inventory'] if st.session_state.records else {t: {s: 0 for s in SIZES} for t in TSHIRT_TYPES}
            current_inv = json.loads(json.dumps(latest))
            st.info(f"💡 {d_str} の記録はまだありません。直近のデータを表示しています。")
        else:
            current_inv = json.loads(json.dumps(existing_data))
            st.success(f"✅ {d_str} の保存済みデータを表示中。")

        if st.button(f"💾 {d_str} の在庫を保存する", type="primary"):
            # 既存レコードの更新または新規追加
            recs = st.session_state.records
            idx = next((i for i, r in enumerate(recs) if r['date'] == d_str), None)
            new_entry = {"date": d_str, "timestamp": datetime.now().isoformat(), "inventory": current_inv, "note": "手動保存"}
            if idx is not None: recs[idx] = new_entry
            else: recs.append(new_entry)
            InventoryManager.save_records(recs)
            st.session_state.records = recs
            st.toast("保存が完了しました！")

        st.divider()
        for ttype in TSHIRT_TYPES:
            with st.expander(f"👕 {ttype.replace('パンクラス×禅道会コラボTシャツ', '')}", expanded=True):
                cols = st.columns(len(SIZES))
                for idx, size in enumerate(SIZES):
                    current_val = current_inv[ttype].get(size, 0)
                    new_val = cols[idx].number_input(size, min_value=0, value=int(current_val), key=f"inp_{d_str}_{ttype}_{size}")
                    current_inv[ttype][size] = new_val

    with tab2:
        st.header("タグ（衣服）管理")
        tags = st.session_state.tags
        st.markdown(f"<div class='big-number'>{tags['current_stock']:,} 枚</div>", unsafe_allow_html=True)
        with st.form("tag_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 2])
            mode = c1.radio("区分", ["使用(-)", "入荷(+)", "不良(-)"], horizontal=True)
            amt = c2.number_input("枚数", min_value=1, value=1)
            note = c3.text_input("備考")
            if st.form_submit_button("更新を記録"):
                change = amt if "入荷" in mode else -amt
                tags['current_stock'] += change
                tags['history'].insert(0, {"date": date.today().isoformat(), "action": mode, "amount": amt, "note": note})
                with open(InventoryManager.TAG_FILE, 'w', encoding='utf-8') as f: json.dump(tags, f, ensure_ascii=False)
                st.rerun()
        if tags['history']: st.table(pd.DataFrame(tags['history']).head(10))

    with tab3:
        st.header("履歴一覧とエクスポート")
        if not st.session_state.records:
            st.info("データがありません。")
        else:
            rows = []
            for r in st.session_state.records:
                for ttype, sizes in r['inventory'].items():
                    row = {"日付": r['date'], "種類": ttype.replace('パンクラス×禅道会コラボTシャツ', '')}
                    row.update(sizes)
                    rows.append(row)
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 全履歴をCSVで保存", df.to_csv(index=False).encode('utf-8-sig'), "inventory_history.csv", "text/csv")

    with tab4:
        st.header("Excel/CSV 一括取込")
        st.markdown("提供いただいた管理表（横軸が日付、縦軸がサイズ）を最速で解析し、過去の記録をすべて復元します。")
        files = st.file_uploader("Excelファイル（.xlsx / .csv）を選択", accept_multiple_files=True)
        if st.button("🚀 取込を開始する", type="primary") and files:
            with st.spinner("解析中..."):
                count = InventoryManager.fast_import_matrix(files)
                st.session_state.records = InventoryManager.load_records()
                st.success(f"解析完了！ {count} 個のデータポイントを反映しました。")
                st.rerun()

    with tab5:
        st.markdown("""
        ### 基本操作
        1. **在庫入力**: 日付を選んで各サイズを入力し、「保存」を押します。
        2. **Excel取込**: 過去の管理表ファイルをここにアップロードすれば、一瞬で履歴が作られます。
        3. **データ消去の注意**: Streamlit Cloudは再起動でデータが消えるため、定期的に「履歴・出力」タブからCSVを保存するか、GitHubにJSONをコミットしてください。
        """)

if __name__ == "__main__":
    main()
