
import os, base64, json, requests
import streamlit as st
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
import re

# OpenAI 클라이언트 생성
client = OpenAI()

# 구글 드라이브에 저장된 Gmail 계정 정보 불러오기
def load_gmail_config():

    # 기존 코드에서 사용하던 구글 드라이브 폴더 경로
    file_path = path + "api_key.txt"

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if "=" in line:
                key, value = line.split("=", 1)

                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key in ["GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"]:
                    os.environ[key] = value

# 수신자 이메일 주소가 실제 대화에서 제공되었는지 확인
def check_email_address(email, messages):

    # 이메일 주소가 비어 있으면 거부
    if not email:
        return False

    # 사용자가 직접 말한 내용만 확인
    user_text = " ".join(
        str(msg["content"])
        for msg in messages
        if msg["role"] == "user"
    )

    # 사용자가 제공한 이메일 주소 추출
    email_list = re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        user_text
    )

    # GPT가 생성한 주소가 사용자 제공 주소와 일치하는지 확인
    return email.strip().lower() in [
        a.lower() for a in email_list
    ]

# 이메일 발송 함수
def send_email(to, subject, body):
    sender = st.secrets["GMAIL_ADDRESS"]
    password = st.secrets["GMAIL_APP_PASSWORD"]

    if not sender or not password:
        return {"status": "failed", "error": "Gmail 계정 설정이 없습니다."}

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(sender, password)
            s.sendmail(sender, to, msg.as_string())

        return {"status": "success"}

    except Exception as e:
        return {"status": "failed", "error": str(e)}

# 페이지 설정
# 페이지 설정
st.set_page_config(
    page_title="에이블 | AI 개인비서",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Streamlit 화면 디자인
st.markdown("""
<style>
    /* 전체 화면 */
    .stApp {
        background-color: #F7F9FC;
        color: #1F2937;
    }

    /* 메인 콘텐츠 영역 */
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* 제목 */
    h1, h2, h3 {
        color: #172B4D;
        font-weight: 700;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5EAF1;
    }

    /* 버튼 */
    .stButton > button[kind="primary"] {
        background-color: #2563EB;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
    }

    /* 입력창 */
    [data-testid="stFileUploader"],
    [data-testid="stAudioInput"] {
        border-radius: 12px;
    }

    /* 음성 녹음 버튼 크기 및 디자인 */
[data-testid="stAudioInput"] button {
    min-width: 64px !important;
    min-height: 64px !important;
    border-radius: 16px !important;
    border: 2px solid #2563EB !important;
    background-color: #EFF6FF !important;
    color: #1D4ED8 !important;
    cursor: pointer !important;
}

/* 녹음 버튼 내부 아이콘 */
[data-testid="stAudioInput"] button svg {
    width: 30px !important;
    height: 30px !important;
}

/* 마우스를 올렸을 때 */
[data-testid="stAudioInput"] button:hover {
    background-color: #DBEAFE !important;
    border-color: #1D4ED8 !important;
}

    /* 채팅 메시지 */
    [data-testid="stChatMessage"] {
        border: 1px solid #E5EAF1;
        border-radius: 14px;
        padding: 12px;
        background-color: #FFFFFF;
    }

    /* 구분선 */
    hr {
        border-color: #E5EAF1;
    }
</style>
""", unsafe_allow_html=True)

# 상단 타이틀
st.title("🤖 에이블 | AI Personal Assistant")
st.caption("김대리 전용 스마트 업무비서")
st.markdown("업무를 더 빠르고 정확하게. 에이블이 함께합니다.")

st.divider()

# 주요 기능 소개
col1, col2, col3 = st.columns(3)

with col1:
    st.info("🎙️ 음성 인식\n\n음성 명령을 텍스트로 변환")

with col2:
    st.info("✉️ 이메일 관리\n\nAI 기반 이메일 작성 및 발송")

with col3:
    st.info("💬 대화 기억\n\n최근 10개 대화 관리")

st.divider()

st.write("음성으로 질문하시면 답변해 드립니다.")

# 역할 지정
sys_role = """
당신은 '김대리'의 전용 AI 개인비서 '에이블'입니다.

당신의 주요 역할은 다음과 같습니다.
1. 김대리의 업무 지원 및 일정 관리
2. 회의록 분석과 핵심 내용 요약
3. 업무 지시사항 및 To-Do List 추출
4. 사용자 질문에 대한 정확하고 친절한 답변
5. 이메일 작성 및 외부 도구를 활용한 발송
6. 음성 명령 이해 및 음성 응답 제공

업무 수행 원칙:
- 사용자를 '김대리님'이라고 부릅니다.
- 이전 대화 내용을 참고하여 연속적인 대화를 수행합니다.
- 답변은 간결하고 명확하게 작성합니다.
- 확인되지 않은 정보는 임의로 만들어내지 않습니다.
- 이메일은 사용자의 최종 확인을 받은 후 발송합니다.

이메일 발송 규칙:
- 사용자가 수신자 이메일 주소를 알려주지 않았다면 이메일 주소를 임의로 생성하지 않습니다.
- 수신자 이메일 주소가 없다면 반드시 "김대리님, 발송할 이메일 주소를 알려주세요."라고 질문합니다.
- 사용자가 이메일 주소를 알려주면 이전 대화 내용을 참고하여 이메일 초안을 작성합니다.
- 수신자 이메일 주소가 확인되기 전에는 send_email 도구를 호출하지 않습니다.
- 이메일은 반드시 사용자의 최종 확인을 받은 후 발송합니다.
"""

# GPT가 사용할 외부 도구 정의
tools = [{
    "type": "function",
    "name": "send_email",
    "description": "사용자의 요청에 따라 이메일을 작성하고 발송합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"}
        },
        "required": ["to", "subject", "body"],
        "additionalProperties": False
    },
    "strict": True
}]

# 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 회의록 저장 공간 초기화
if "meeting_text" not in st.session_state:
    st.session_state.meeting_text = ""

if "email_pending" not in st.session_state:
    st.session_state.email_pending = None

# 사이드바 구성
with st.sidebar:

    st.title("🤖 AIVLE")
    st.caption("Personal AI Assistant")

    st.divider()

    st.markdown("### 👤 사용자 정보")
    st.write("**사용자:** 김대리")
    st.write("**AI 비서:** 에이블")

    st.divider()

    st.markdown("### 🛠️ 주요 기능")
    st.write("🎙️ 음성 명령 인식")
    st.write("🧠 AI 업무 지원")
    st.write("✉️ 이메일 작성 및 발송")
    st.write("🔊 음성 답변")
    st.write("💬 대화 히스토리")

    st.divider()

    st.markdown("### 📊 대화 현황")

    message_count = len(st.session_state.messages)
    st.metric("저장된 대화", f"{message_count // 2} / 10")

    st.caption("최근 10개 대화까지 유지됩니다.")

    st.divider()

    st.caption("AIVLE AI Assistant · Powered by OpenAI")

    st.divider()

    if st.button(
        "🗑️ 대화 기록 초기화",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.session_state.email_pending = None
        st.session_state.meeting_text = ""
        st.rerun()
    
# 지시 영역
with st.form("task_form"):
    uploaded_file = st.file_uploader("텍스트 파일 업로드", type=["txt"])
    audio_value = st.audio_input("무엇을 도와드릴까요?")
    submit = st.form_submit_button(
    "🚀 에이블에게 요청하기",
    type="primary",
    use_container_width=True
)

# 버튼을 눌렀을 때만 실행
if submit:
    # 업로드 된 파일이 있으면 디코딩
    text = ""
    if uploaded_file is not None:
        text = uploaded_file.read().decode("utf-8")

        # 회의록 내용을 세션에 저장
        st.session_state.meeting_text = text

    # 녹음이 없으면 녹음 요청
    if audio_value is None:
        st.warning("음성을 녹음해주세요.")
        st.stop()

    # 시스템 메세지
    system_content = sys_role
    if text:
        system_content += f"\n\n다음 내용을 참고하세요:\n{text}"
    input_messages = [{"role": "system", "content": system_content}]

    # STT: 음성 → 텍스트
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=("audio.wav", audio_value, "audio/wav"))
    
    # STT 음성 인식 결과 출력
    st.subheader("🎤 음성 인식 결과")
    st.info(transcript.text)
    
    # 이전 대화 기록 불러오기
    input_messages.extend(st.session_state.messages)

    # 사용자 메시지
    input_messages.append({"role": "user", "content": transcript.text})

    # 이메일 발송 요청 처리
    if "email_pending" not in st.session_state:
        st.session_state.email_pending = None

    response_email = client.responses.create(
        model="gpt-4o-mini",
        input=input_messages,
        tools=tools,
        tool_choice="auto"
    )

    tool_calls = [
        item for item in response_email.output
        if item.type == "function_call"
        and item.name == "send_email"
    ]

    if tool_calls:
        args = json.loads(tool_calls[0].arguments)

    # 현재 음성 요청도 검사 대상에 포함
    user_messages = st.session_state.messages + [
        {"role": "user", "content": transcript.text}
    ]

    if not check_email_address(args.get("to"), user_messages):
        st.session_state.messages.append({
            "role": "user",
            "content": transcript.text
        })
        st.session_state.messages.append({
            "role": "assistant",
            "content": "김대리님, 발송할 이메일 주소를 알려주세요."
        })
        st.session_state.email_pending = None
        st.rerun()

        st.session_state.email_pending = args

        st.subheader("이메일 발송 확인")
        st.write("수신자:", args["to"])
        st.write("제목:", args["subject"])
        st.write("본문:", args["body"])

        st.session_state.messages.append({
            "role": "user",
            "content": transcript.text
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": "이메일 발송 확인이 필요합니다."
        })

        st.rerun()

    # LLM 호출 및 응답 듣기
    with st.spinner("답변을 준비하고 있습니다..."):
        # LLM 호출
        response = client.responses.create(
            model="gpt-4o-mini",
            input=input_messages
        )
        answer = response.output_text

        # 응답 출력
        st.subheader("AI 답변")
        st.write(answer)
        
        # GPT 최종 답변을 음성으로 변환
        speech = client.audio.speech.create(
           model="tts-1",
           voice="alloy",
           input=answer
        )

        # 음성 데이터를 가져오기
        audio_bytes = speech.content

        # Streamlit에서 음성 자동 재생
        st.audio(
            audio_bytes,
            format="audio/mp3",
            autoplay=True
        )

        # 사용자 질문 저장
        st.session_state.messages.append({
            "role": "user",
            "content": transcript.text
        })

        # AI 답변 저장
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        # 최근 10개 대화만 유지
        st.session_state.messages = st.session_state.messages[-20:]

# 대화 히스토리 표시
st.divider()
st.subheader("💬 최근 대화 히스토리")

for msg in st.session_state.messages[-20:]:

    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])

    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])

# 이메일 발송 최종 확인
if st.session_state.email_pending is not None:

    email = st.session_state.email_pending

    st.subheader("✉️ 이메일 최종 확인")

    st.write("**받는 사람:**", email["to"])
    st.write("**제목:**", email["subject"])
    st.write("**내용:**")
    st.info(email["body"])

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "📨 최종 발송하기",
            type="primary",
            use_container_width=True
        ):
            result = send_email(**email)

            if result["status"] == "success":
                st.session_state.email_pending = None
                st.success("이메일이 발송되었습니다.")
            else:
                st.error(result["error"])

    with col2:
        if st.button(
            "발송 취소",
            use_container_width=True
        ):
            st.session_state.email_pending = None
            st.rerun()

# AIVLE 텍스트 채팅 기능
st.divider()

# 텍스트 입력창
user_text = st.chat_input(
    "김대리님, 무엇을 도와드릴까요?"
)

# 사용자가 메시지를 입력했을 때
if user_text:

    # 사용자 질문 저장
    st.session_state.messages.append({
        "role": "user",
        "content": user_text
    })

    # 최근 대화 기록 가져오기
    history = st.session_state.messages[-20:]

    # 시스템 역할과 대화 기록 결합
    # 시스템 역할 설정
    system_content = sys_role

    # 저장된 회의록이 있다면 함께 전달
    if st.session_state.meeting_text:
        system_content += (
           "\n\n다음 회의록을 참고하여 답변하세요:\n"
           + st.session_state.meeting_text
    )

    # 시스템 역할과 대화 기록 결합
    input_messages = [
        {
            "role": "system",
            "content": system_content
        }
    ] + history

    with st.spinner("에이블이 답변을 준비하고 있습니다..."):

        # GPT 호출 (이메일 도구 포함)
        response = client.responses.create(
            model="gpt-4o-mini",
            input=input_messages,
            tools=tools,
            tool_choice="auto"
        )

        # 이메일 발송 도구 호출 확인
        tool_calls = [
            item for item in response.output
            if item.type == "function_call"
            and item.name == "send_email"
        ]

if tool_calls:

       # 이메일 내용 저장
        args = json.loads(tool_calls[0].arguments)

       if check_email_address(args.get("to"), st.session_state.messages):
           st.session_state.email_pending = args

            answer = (
               "김대리님, 이메일 발송 요청을 준비했습니다. "
               "수신자와 내용을 확인한 후 발송 버튼을 눌러주세요."
           )

        else:
            st.session_state.email_pending = None

            answer = "김대리님, 발송할 이메일 주소를 알려주세요."

            answer = (
                "김대리님, 이메일 발송 요청을 준비했습니다. "
                "수신자와 내용을 확인한 후 발송 버튼을 눌러주세요."
            )

        else:
            # 일반 질문에 대한 AI 답변
            answer = response.output_text

        # AI 답변 저장
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        # 최근 10개 대화만 유지
        st.session_state.messages = (
            st.session_state.messages[-20:]
        )

    # 새 대화 기록과 이메일 확인 화면 갱신
    st.rerun()
