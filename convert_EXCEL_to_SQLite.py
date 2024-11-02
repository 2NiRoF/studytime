import pandas as pd
import sqlite3                                                      #판다스랑 요놈이 엑셀을 좀더 쌈@뽕한 데이터베이스(SQLite)로 변환해줌 

excel_file = r'C:\Users\jeong\OneDrive\바탕 화면\StudyTime_EveryWhere\DB.xlsx'
df = pd.read_excel(excel_file, sheet_name='Sheet1')                 #파일 불러오기

conn = sqlite3.connect('studytime_everywhere.db')                   #SQLite 데이터베이스 연결하고 없으면 생성
cursor = conn.cursor()                                              #객체 생성(cursor <<<없으면 아무것도못함)

cursor.execute('''
CREATE TABLE IF NOT EXISTS study_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    USERID TEXT,
    time_start REAL,
    time_end REAL,
    time_studied REAL,
    time_total REAL
)
''')                                                                #넌 이제부터 테이블이여

df.to_sql('study_data', conn, if_exists='append', index=False)      #판다스로 받아놓은 데이터프레임 그대로 SQLite에 삽입

cursor.execute('SELECT * FROM study_data')                          #SELECT: 데이터를 읽어온다 | FROM: 어디에서? | study_data에서
rows = cursor.fetchall()                                            #커서가 가지고 있는 그대로 rows에 저장
for row in rows:                                                    #싹다 출력
    print(row)

conn.commit()
conn.close()                                                        