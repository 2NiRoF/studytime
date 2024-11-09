import discord
import sqlite3
import time
import asyncio
import bottoken

INTENTS = discord.Intents.all()
client = discord.Client(intents = INTENTS)

conn = sqlite3.connect('C:\\Users\\exwpf\\Documents\\GitHub\\studytime\\studytime.db')  #데이터베이스 연결
cursor = conn.cursor()

async def check_12hour_exception():                         #10분에 한번씩 12시간 이상 공부중인 유저 확인 및 기록 취소
    while True:
        channel_id = 1281999464793505834                    #나중에 수정가능; 봇 채널 아이디 들고오면됨
        channel = client.get_channel(channel_id)
        timenow = time.time()
        cursor.execute('SELECT * FROM study_data')
        rows = cursor.fetchall()

        for i in rows:
            tempUID = i[1]
            time_start = i[2]
            if time_start is not None:
                time_passed = timenow - time_start
                if time_passed > 43200: #43200
                    cursor.execute('UPDATE study_data SET time_start = ? WHERE USERID = ?',(None, tempUID))
                    await channel.send(f'{tempUID} 유저의 공부시간이 12시간을 초과하여 측정이 종료되었습니다.')
        
        await asyncio.sleep(600)

@client.event
async def on_ready(): # 봇이 실행되면 한 번 실행됨
    print("STUDYTIME ONLINE")
    await client.change_presence(status=discord.Status.online, activity=discord.Game("StudyTime ONLINE"))
    client.loop.create_task(check_12hour_exception())


@client.event
async def on_message(message):
    if message.content == "!StudyTime": #상태확인
        await message.channel.send ("ONLINE")

    if message.content == "!help":      #도움말
        await message.channel.send ("""
    {} StudyTime 봇의 명령어 목록입니다.
                                    
        명령어는 !명령어 와 같이 사용합니다.
        help : 명령어 목록을 불러옵니다.
        StudyTime : 봇의 온라인 상태를 확인합니다.
        등록 (등록할 아이디) : 원하는 아이디로 유저를 등록합니다.
        공부시작 (등록한 아이디) : 타이머를 시작하며, 현재 시간을 기준으로 합니다.
        공부종료 (등록한 아이디) : 타이머를 종료하며, 데이터베이스에 공부시간을 기록합니다.
        정보 (등록한 아이디) : 해당 아이디를 등록한 유저의 공부 시간을 불러옵니다.
        공부초기화 (등록한 아이디) : 해당 아이디를 등록한 유저의 공부 시간을 0으로 초기화합니다.(확인 절차 없음)
        삭제 (등록한 아이디) : 해당 아이디를 삭제합니다(2번 확인 후 삭제 절차 진행)
    """.format(message.author.mention))
        
    if "!등록" in message.content:      #유저 등록 ex) 유저: "!등록 홍길동 "
        userid = message.author.id
        msg = message.content
        tempUID = msg[4:].strip()  #아이디 추출, 공백 제거 ex) '!등록 " 부분과 홍길동 뒤의 공백 삭제
        if not tempUID:
            await message.channel.send(f"{message.author.mention} 공백 문자는 등록할 수 없습니다. 올바른 이름을 등록해주세요.")
        else:
            cursor.execute('SELECT * FROM study_data WHERE USERID = ?', (tempUID,)) #추출한 아이디의 DB상 존재유무 확인(튜플)
            result = cursor.fetchone() #찾은 아이디의 행 뭉탱이로 들고오기
            if result:
                await message.channel.send(f"{message.author.mention} {tempUID}은(는) 이미 등록된 유저입니다.")
                return
            cursor.execute('INSERT INTO study_data (USERID) VALUES (?)', (tempUID,)) #유저ID 데이터베이스에 추가
            conn.commit() #말그대로 커밋
            cursor.execute('UPDATE study_data SET discord_UID = ?', (userid,))
            conn.commit()
            await message.channel.send(f"{tempUID}이(가) 등록되었습니다.")
            return


    if "!공부시작" in message.content:  #공부시작 ex) 유저: "!공부시작 홍길동"
        userid = message.author.id
        msg = message.content
        tempUID = msg[6:].strip()
        if not tempUID:
            await message.channel.send(f"{message.author.mention} <!명령어 이름> 과 같은 형식으로 호출해주세요.")
        else:
            cursor.execute('SELECT * FROM study_data WHERE USERID = ? AND discord_UID = ?', (tempUID, userid))
            result = cursor.fetchone()
            timenow = time.localtime()

            
            if result: #유저를 찾았다면?
                if result[2] is not None and result[3] is None:   #행 자체를 튜플로 가져옴 -> 자료 구조 상 USERID, start_time 순서기 때문에 [1] 인 것 같지만 데이터베이스 테이블의 자료구조는 첫 번째 열에 id(1, 2, 3...)가 생김
                    await message.channel.send(f"{message.author.mention} 공부는 이미 시작되었습니다.")
                    return
                else:
                    cursor.execute('UPDATE study_data SET time_start = ?, time_end = ?, time_studied = ? WHERE USERID = ? AND discord_UID = ?',(None, None, None, tempUID, userid))
                    conn.commit()
                    cursor.execute('UPDATE study_data SET time_start = ? WHERE USERID = ? AND discord_UID = ?', (time.time(), tempUID, userid))
                    conn.commit()
                    await message.channel.send(f"{time.strftime('%Y%m%d', timenow)} {time.strftime('%X', timenow)} {tempUID} 유저의 공부 시작 시간을 기록했습니다.")
            else:
                await message.channel.send(f"{message.author.mention} 해당 유저가 존재하지 않거나, 다른 사람의 등록 정보로 공부 시간 기록을 시도하고 있습니다.")
            return
    
    if "!공부종료" in message.content:  #공부종료
        userid = message.author.id
        msg = message.content
        tempUID = msg[6:].strip()
        if not tempUID:
            await message.channel.send(f"{message.author.mention} <!명령어 이름> 과 같은 형식으로 호출해주세요.")
        else:
            cursor.execute('SELECT * FROM study_data WHERE USERID = ? AND discord_UID = ?', (tempUID, userid))
            result = cursor.fetchone()

            if result:
                if result[2] is None:
                    await message.channel.send(f"{message.author.mention} 공부 종료는 공부 시작 이후에 가능합니다.")
                    return
                end_time = time.time()
                study_duration = end_time - result[2]
                total_time = (result[5] if result[5] else 0) + study_duration
                cursor.execute('UPDATE study_data SET time_end = ?, time_studied = ?, time_total = ? WHERE USERID = ? AND discord_UID = ?',
                            (end_time, study_duration, total_time, tempUID, userid))
                conn.commit()
                total_study_seconds = int(total_time)
                total_study_hours = total_study_seconds // 3600
                total_study_minutes = (total_study_seconds % 3600) // 60
                total_study_seconds = total_study_seconds % 60
                await message.channel.send(f"현재까지 총 {total_study_hours}시간 {total_study_minutes}분 {total_study_seconds}초 공부했습니다.")
            else:
                await message.channel.send(f"{message.author.mention} 해당 유저가 존재하지 않거나, 다른 사람의 등록 정보로 공부 시간 기록을 시도하고 있습니다.")
            return
        
    if "!랭킹" in message.content:  # 랭킹 표시
        cursor.execute('SELECT USERID, time_total FROM study_data WHERE time_total IS NOT NULL ORDER BY time_total DESC')
        ranking_data = cursor.fetchall()

        if ranking_data:
            ranking_message = "📊 **공부 시간 랭킹** 📊\n"
            for rank, (user_id, total_time) in enumerate(ranking_data, start=1):
                hours = int(total_time) // 3600
                minutes = (int(total_time) % 3600) // 60
                seconds = int(total_time) % 60
                ranking_message += f"{rank}위 - {user_id}: {hours}시간 {minutes}분 {seconds}초\n"
            
            await message.channel.send(ranking_message)
        else:
            await message.channel.send("현재 기록된 유저가 없습니다.")

    if "!공부초기화" in message.content:  # 공부 초기화
        userid = message.author.id
        msg = message.content
        tempUID = msg[6:].strip()
        if not tempUID:
            await message.channel.send(f"{message.author.mention} <!명령어 이름> 과 같은 형식으로 호출해주세요.")
        else:
            cursor.execute('SELECT * FROM study_data WHERE USERID = ? discord_UID = ?', (tempUID, userid))
            result = cursor.fetchone()

            if result:  # 해당 유저의 공부 기록 초기화
                cursor.execute('UPDATE study_data SET time_start = ?, time_end = ?, time_studied = ?, time_total = ? WHERE USERID = ? AND discord_UID = ?',
                        (None, None, None, 0, tempUID, userid))
                conn.commit()
                await message.channel.send(f"{tempUID} 유저의 공부 기록이 초기화되었습니다.")
            else:
                await message.channel.send(f"{message.author.mention} 해당 유저가 존재하지 않거나, 다른 사람의 기록에 접근을 시도하고 있습니다.")
            return
    
    if "!정보" in message.content:      #유저 정보 불러오기
        msg = message.content
        tempUID = msg[4:].strip()
        if not tempUID:
            await message.channel.send(f"{message.author.mention} <!명령어 이름> 과 같은 형식으로 호출해주세요.")
        else:
            cursor.execute('SELECT * FROM study_data WHERE USERID = ?', (tempUID,))
            result = cursor.fetchone()

            if result:
                total_time = result[5] if result[5] else 0
                total_study_seconds = int(total_time)
                total_study_hours = total_study_seconds // 3600
                total_study_minutes = (total_study_seconds % 3600) // 60
                total_study_seconds = total_study_seconds % 60
                await message.channel.send(f"현재까지 총 {total_study_hours}시간 {total_study_minutes}분 {total_study_seconds}초 공부했습니다.")
            else:
                await message.channel.send(f"{message.author.mention} 해당 유저가 존재하지 않습니다.")
            return
    
    if "!삭제" in message.content:  # 유저 삭제
        userid = message.author.id
        msg = message.content
        tempUID = msg[4:].strip()  # 사용자 ID 추출 및 공백 제거
        if not tempUID:
            await message.channel.send(f"{message.author.mention} <!명령어 이름> 과 같은 형식으로 호출해주세요.")
        else:
            # 유저가 존재하는지 확인
            cursor.execute('SELECT * FROM study_data WHERE USERID = ? AND discord_UID = ?', (tempUID, userid))
            result = cursor.fetchone()
        
            if result:
                # 삭제 확인 메시지 전송
                await message.channel.send(f"{message.author.mention} 정말로 {tempUID} 유저를 삭제하시겠습니까? Y 또는 N으로 확인하십시오. (1/2회 확인)")

                def check(msg):
                    return msg.author == message.author and msg.channel == message.channel and msg.content.upper() in ['Y', 'N']
            
                try:
                    # 첫 번째 확인 대기
                    response1 = await client.wait_for('message', timeout=60.0, check=check)
                    if response1.content.upper() == 'Y':
                        await message.channel.send(f"# {message.author.mention} 정말로 정말로 {tempUID} 유저를 삭제하시겠습니까???? Y 또는 N으로 확인하십시오!! (2/2회 확인)")

                        # 두 번째 확인 대기
                        response2 = await client.wait_for('message', timeout=60.0, check=check)
                        if response2.content.upper() == 'Y':
                            # 유저 삭제
                            cursor.execute('DELETE FROM study_data WHERE USERID = ? AND discord_UID = ?', (tempUID, userid))
                            conn.commit()
                            await message.channel.send(f"{message.author.mention} {tempUID}의 데이터가 삭제되었습니다.")
                        else:
                            await message.channel.send(f"{message.author.mention} {tempUID}의 데이터 삭제가 취소되었습니다.")
                    else:
                        await message.channel.send(f"{message.author.mention} {tempUID}의 데이터 삭제가 취소되었습니다.")
                except asyncio.TimeoutError:
                    await message.channel.send(f"{message.author.mention} 응답 시간이 초과되어 데이터 삭제가 취소되었습니다.")
            
            else:
                await message.channel.send(f"{message.author.mention} 해당 유저가 존재하지 않거나, 다른 유저의 기록에 접근을 시도하고 있습니다.")
    return



client.run(bottoken.TOKEN)