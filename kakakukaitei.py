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

def xls_df_db():
    # ***ファイルアップロード ***
    uploaded_file = st.sidebar.file_uploader('価格改定リスト', type='xlsx', key='kakaku')
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

    

def calc():
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
        new_price = a + (a * (rate *0.01))
        new_price = int((new_price//100)*100) #100円以下切り捨て　//整数部分のみ返す
        new_ab.append(new_price)

    # C
    for a, c in zip(df2['A-S/A/B'], df2['C']):
        new_price = a + (a * (rate *0.01))
        new_price = int((new_price//100)*100) + (c - a) #100円以下切り捨て　//整数部分のみ返す
        new_c.append(new_price)

    # E
    for a, e in zip(df2['A-S/A/B'], df2['E']):
        new_price = a + (a * (rate *0.01))
        new_price = int((new_price//100)*100) + (e - a) #100円以下切り捨て　//整数部分のみ返す
        new_e.append(new_price)

    # 本革A
    for a, ha in zip(df2['A-S/A/B'], df2['本革A']):
        new_price = a + (a * (rate *0.01))
        new_price = int((new_price//100)*100) + (ha - a) #100円以下切り捨て　//整数部分のみ返す
        new_ha.append(new_price)

    for a, hb in zip(df2['A-S/A/B'], df2['本革B']):
        new_price = a + (a * (rate *0.01))
        new_price = int((new_price//100)*100) + (hb - a) #100円以下切り捨て　//整数部分のみ返す
        new_hb.append(new_price)

    series = df2['シリーズ']
    hinban = df2['品番']
    buhin1 = df2['部品1']
    buhin2 = df2['部品2']
    column_list = df2.columns

    df_new = pd.DataFrame(list(zip(series, hinban, buhin1, buhin2, new_ab, new_c, new_e, new_ha, new_hb)), columns=column_list)
    df_new[['A-S/A/B', 'C', 'E', '本革A', '本革B']] = df_new[['A-S/A/B', 'C', 'E', '本革A', '本革B']].astype('int')

    st.table(df_new)

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
    st.sidebar.download_button(label='Download Excel file',
                                    data=df_xlsx ,
                                    file_name= 'kakakukaitei.xlsx')

def select_series():
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
    st.table(df_result)

def select_hinban():
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

    st.table(df_result)


def main():
    # アプリケーション名と対応する関数のマッピング
    apps = {
        '-': None,
        'シリーズから検索': select_series,
        '品番から検索': select_hinban,
        'Excel読み込み': xls_df_db,
        '価格改定計算': calc,
        
        
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

