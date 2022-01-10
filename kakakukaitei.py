import pandas as pd
import numpy as np
from pandas.core.frame import DataFrame
import openpyxl
import sqlite3
import streamlit as st
from streamlit.state.session_state import Value
from io import BytesIO
from xlsxwriter import Workbook


st.set_page_config(page_title='価格改定test')
st.markdown('#### 価格改定test')

db_name = 'kakakukaitei.db'

# *************** main *******************

def xls_df_db_main():
    # ***ファイルアップロード ***
    uploaded_file = st.sidebar.file_uploader('部品価格表　プロパー', type='xlsx', key='kakaku')
    df = DataFrame()
    if uploaded_file:
        df = pd.read_excel(uploaded_file, sheet_name='Sheet1', index_col=0)
        st.info('ファイルのアップロードとデータベースへの格納が完了しました。')
    
    global conn
    conn = sqlite3.connect(db_name) 
    # dbファイルと接続
    # cbファイルがあれば読み込む。無い場合は自動的に作る。

    df.to_sql('kakaku_table', conn, if_exists='replace') #テーブル名、DB
    conn.close()

    

def calc_main():
    conn = sqlite3.connect(db_name)
    #c = conn.cursor()
    query_select = '''
    select * from kakaku_table
    '''
    # c.execute(query_select)
    # output = c.fetchall() #リストで取得
    df2 = pd.read_sql_query(query_select, conn) #DBから全情報取り出し　df化
    conn.close()

    rate =st.number_input('UP率を入力してください。　半角数字　％')
    
    new_ab =[]
    new_c = []
    new_e = []
    new_ha = []
    new_hb = []

    # A-S/A/B
    for a in df2['A-S/A/B']:
        if a == 0:
            new_price =0
        else:    
            new_price = a + (a * (rate *0.01))
            new_price = (new_price//100)*100 #100円以下切り捨て　//整数部分のみ返す 
        new_ab.append(new_price)

    # C
    for a, c in zip(df2['A-S/A/B'], df2['C']):
        if c == 0:
            new_price =0
        else:    
            new_price = a + (a * (rate *0.01))
            new_price = (new_price//100)*100 + (c - a) #100円以下切り捨て　//整数部分のみ返す
        new_c.append(new_price)

    # E
    for a, e in zip(df2['A-S/A/B'], df2['E']):
        if e == 0:
            new_price =0
        else:    
            new_price = a + (a * (rate *0.01))
            new_price = (new_price//100)*100 + (e - a) #100円以下切り捨て　//整数部分のみ返す
        new_e.append(new_price)

    # 本革A
    for a, ha in zip(df2['A-S/A/B'], df2['本革A']):
        if ha == 0:
            new_price =0
        else:    
            new_price = a + (a * (rate *0.01))
            new_price = (new_price//100)*100 + (ha - a) #100円以下切り捨て　//整数部分のみ返す
        new_ha.append(new_price)

    for a, hb in zip(df2['A-S/A/B'], df2['本革B']):
        if hb == 0:
            new_price =0
        else:
            new_price = a + (a * (rate *0.01))
            new_price = (new_price//100)*100 + (hb - a) #100円以下切り捨て　//整数部分のみ返す
        new_hb.append(new_price)

    series = df2['シリーズ']
    hinban = df2['品番']
    buhin1 = df2['部品1']
    buhin2 = df2['部品2']
    column_list = df2.columns

    df_new = pd.DataFrame(list(zip(series, hinban, buhin1, buhin2, new_ab, new_c, new_e, new_ha, new_hb)), columns=column_list)
    df_new[['A-S/A/B', 'C', 'E', '本革A', '本革B']] = df_new[['A-S/A/B', 'C', 'E', '本革A', '本革B']].fillna(0).astype(int) #int型に変換
    st.caption('上位30件のみ表示')
    st.table(df_new.head(30))

    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index = False, sheet_name='Sheet1')
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']
        format1 = workbook.add_format({'num_format': '0.00'}) # Tried with '0%' and '#,##0.00' also.
        worksheet.set_column('A:A', None, format1) # Say Data are in column A
        writer.save()
        processed_data = output.getvalue()
        return processed_data
    
    df_xlsx = to_excel(df_new)
    st.sidebar.download_button(label='ダウンロード　プロパー',
                                    data=df_xlsx ,
                                    file_name= 'proper.xlsx')

def select_series_main():
    conn = sqlite3.connect(db_name)
    #c = conn.cursor()
    query_select = '''
    select * from kakaku_table
    '''
    # c.execute(query_select)
    # output = c.fetchall() #リストで取得
    df_all = pd.read_sql_query(query_select, conn) #DBから全情報取り出し　df化

    conn.close()

    # *** selectbox シリーズ***
    series_list = df_all['シリーズ'].unique()
    option_series = st.selectbox(
        'series:',
        series_list,   
    ) 

    df_result = df_all[df_all['シリーズ']== option_series]
    df_result[['A-S/A/B', 'C', 'E', '本革A', '本革B']] = df_result[['A-S/A/B', 'C', 'E', '本革A', '本革B']].astype(int)
    st.table(df_result)

def select_hinban_main():
    conn = sqlite3.connect(db_name)
    #c = conn.cursor()
    query_select = '''
    select * from kakaku_table
    '''
    # c.execute(query_select)
    # output = c.fetchall() #リストで取得
    df_all = pd.read_sql_query(query_select, conn) #DBから全情報取り出し　df化

    conn.close()

    df_all['頭品番'] = df_all['品番'].str[0:2] #先頭2行の文字列を抽出

    # *** input 品番***
    hinban = st.text_input('品番を入力　半角英数 大文字', 'SN')
    st.caption('品番の先頭2文字を入力')

    df_result = df_all[df_all['頭品番']==hinban]
    df_result[['A-S/A/B', 'C', 'E', '本革A', '本革B']] = df_result[['A-S/A/B', 'C', 'E', '本革A', '本革B']].astype(int)

    st.table(df_result)

# *************** 穂高 *******************

def xls_df_db_hk():
    # ***ファイルアップロード ***
    uploaded_file = st.sidebar.file_uploader('部品価格表　穂高', type='xlsx', key='kakaku')
    df = DataFrame()
    if uploaded_file:
        df = pd.read_excel(uploaded_file, sheet_name='Sheet1', index_col=0) #最初のカラムが0行目
        st.info('ファイルのアップロードとデータベースへの格納が完了しました。')
    
    global conn
    conn = sqlite3.connect(db_name) 
    # dbファイルと接続
    # cbファイルがあれば読み込む。無い場合は自動的に作る。

    df.to_sql('hk_table', conn, if_exists='replace') #テーブル名、DB
    conn.close()

    

def calc_hk():
    conn = sqlite3.connect(db_name)
    #c = conn.cursor()
    query_select = '''
    select * from hk_table
    '''
    # c.execute(query_select)
    # output = c.fetchall() #リストで取得
    df_hk = pd.read_sql_query(query_select, conn) #DBから全情報取り出し　df化
    conn.close()

    rate =st.number_input('UP率を入力してください。　半角数字　％')
    
    new_as =[]
    new_a = []
    new_b = []
    new_c = []
    new_d = []
    new_e = []
    new_ha = []
    new_hb = []

    # A-S
    for ass in df_hk['A-S']:
        if ass == 0:
            new_price =0
        else:    
            new_price = ass + (ass * (rate *0.01))
            new_price = (new_price//100)*100 #100円以下切り捨て　//整数部分のみ返す 
        new_as.append(new_price)

    # A
    for ass, a in zip(df_hk['A-S'], df_hk['A']):
        if a == 0:
            new_price =0
        else:    
            new_price = ass + (ass * (rate *0.01))
            new_price = (new_price//100)*100 + (a - ass) #100円以下切り捨て　//整数部分のみ返す
        new_a.append(new_price)

    # B
    for ass, b in zip(df_hk['A-S'], df_hk['B']):
        if b == 0:
            new_price =0
        else:    
            new_price = ass + (ass * (rate *0.01))
            new_price = (new_price//100)*100 + (b - ass) #100円以下切り捨て　//整数部分のみ返す
        new_b.append(new_price)        

    # C
    for ass, c in zip(df_hk['A-S'], df_hk['C']):
        if c == 0:
            new_price =0
        else:    
            new_price = ass + (ass * (rate *0.01))
            new_price = (new_price//100)*100 + (c - ass) #100円以下切り捨て　//整数部分のみ返す
        new_c.append(new_price)

    # D
    for ass, d in zip(df_hk['A-S'], df_hk['D']):
        if d == 0:
            new_price =0
        else:    
            new_price = ass + (ass * (rate *0.01))
            new_price = (new_price//100)*100 + (d - ass) #100円以下切り捨て　//整数部分のみ返す
        new_d.append(new_price)    

    # E
    for ass, e in zip(df_hk['A-S'], df_hk['E']):
        if e == 0:
            new_price =0
        else:    
            new_price = ass + (ass * (rate *0.01))
            new_price = (new_price//100)*100 + (e - ass) #100円以下切り捨て　//整数部分のみ返す
        new_e.append(new_price)

    # 本革A
    for ass, ha in zip(df_hk['A-S'], df_hk['本革A']):
        if ha == 0:
            new_price =0
        else:    
            new_price = ass + (ass * (rate *0.01))
            new_price = (new_price//100)*100 + (ha - ass) #100円以下切り捨て　//整数部分のみ返す
        new_ha.append(new_price)
    
    # 本革B
    for ass, hb in zip(df_hk['A-S'], df_hk['本革B']):
        if hb == 0:
            new_price =0
        else:
            new_price = ass + (ass * (rate *0.01))
            new_price = (new_price//100)*100 + (hb - ass) #100円以下切り捨て　//整数部分のみ返す
        new_hb.append(new_price)

    series = df_hk['シリーズ']
    hinban = df_hk['品番']
    buhin1 = df_hk['部品1']
    buhin2 = df_hk['部品2']
    bikou = df_hk['備考']
    column_list = df_hk.columns

    df_new = pd.DataFrame(list(zip(series, hinban, buhin1, buhin2, new_as, new_a, new_b, new_c, new_d, new_e, new_ha, new_hb, bikou)), columns=column_list)
    df_new[['A-S','A', 'B', 'C', 'D', 'E', '本革A', '本革B']] = df_new[['A-S','A', 'B', 'C', 'D', 'E', '本革A', '本革B']].fillna(0).astype(int) #naを0で埋めてint型に変換
    st.caption('上位30件のみ表示')
    st.table(df_new.head(30))

    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index = False, sheet_name='Sheet1')
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']
        format1 = workbook.add_format({'num_format': '0.00'}) # Tried with '0%' and '#,##0.00' also.
        worksheet.set_column('A:A', None, format1) # Say Data are in column A
        writer.save()
        processed_data = output.getvalue()
        return processed_data
    
    df_xlsx = to_excel(df_new)
    st.sidebar.download_button(label='ダウンロード　穂高',
                                    data=df_xlsx ,
                                    file_name= 'hodaka.xlsx')

def select_hk():
    conn = sqlite3.connect(db_name)
    #c = conn.cursor()
    query_select = '''
    select * from hk_table
    '''
    # c.execute(query_select)
    # output = c.fetchall() #リストで取得
    df_all = pd.read_sql_query(query_select, conn) #DBから全情報取り出し　df化

    conn.close()

    st.table(df_all)

def main():
    # アプリケーション名と対応する関数のマッピング
    apps = {
        '--プロパー--': None,
        'シリーズから検索pro': select_series_main,
        '品番から検索pro': select_hinban_main,
        'Excel読み込みpro': xls_df_db_main,
        '価格改定計算pro': calc_main,
        '--穂高--': None,
        '価格表表示hk': select_hk,
        'Excel読み込みhk': xls_df_db_hk,
        '価格改定計算hk': calc_hk,
        
        
    }
    selected_app_name = st.sidebar.selectbox(label='作業の選択',
                                             options=list(apps.keys()))
    link = '[home](http://linkpagetest.s3-website-ap-northeast-1.amazonaws.com/)'
    st.sidebar.markdown(link, unsafe_allow_html=True)
    st.sidebar.caption('homeに戻る')                                       

    # 選択されたアプリケーションを処理する関数を呼び出す
    render_func = apps[selected_app_name]
    render_func()

if __name__ == '__main__':
    main()

