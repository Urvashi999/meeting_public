import streamlit as st
from main import transcribe_and_analyze, history, save_history, load_history, create_pdf, revise_answer
from template import questions

def authenticate(username, password):
    return username == "user" and password == "pass"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

else:
    st.sidebar.title("Navigation")
    st.sidebar.write("User: User")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    st.sidebar.title("History")
    history_data = load_history()
    if history_data:
        for idx, session in enumerate(history_data):
            with st.sidebar.expander(f"Session {idx + 1}"):
                st.write(f"Audio File: {session['audio_file']}")
                st.write(f"Transcript Text: {session['transcript_text']}")
                st.write(f"Company File: {session['company_file']}")
                st.write(f"Company Info Source: {session['company_info_source']}")
                st.write(f"Final Questions and Answers: {session['final_questions_and_answers']}")
    else:
        st.sidebar.write("No history available.")

    st.title("Meeting Analysis Tool")
    MAX_FILE_SIZE_MB = 200.0  # Max file size in MB

    st.header("Upload Files")
    audio_file = st.file_uploader("Upload Meeting Recording", type=["mp3", "wav", "mp4"])

    if audio_file is not None:
        file_size_mb = audio_file.size / (1024 * 1024)  # Convert bytes to MB
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"The audio file size is {file_size_mb:.2f} MB, which exceeds the 200 MB limit.")
        audio_file = None  # Reset the file if it exceeds the size limit
    else:
        st.success(f"Uploaded audio file: {audio_file.name}")

    company_info = st.file_uploader("Upload Company Information", type=["pdf", "docx", "ppt", "txt"], accept_multiple_files=True)

if company_info:
    for company_info in company_info:
        file_size_mb = company_info.size / (1024 * 1024)  # Convert bytes to MB
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(f"The file {company_info.name} is {file_size_mb:.2f} MB, which exceeds the 200 MB limit.")
        else:
            st.success(f"Uploaded company info file: {company_info.name}")




    company_info_link = st.text_input("Provide a website link for company information")


    st.header("Select Template")
    templates = list(questions.keys())
    selected_template = st.selectbox("Select a Template", templates)
    if st.button("Proceed"):
        if selected_template and (audio_file or company_info or company_info_link):
            st.session_state.questions = questions[selected_template]
            st.session_state.answers = transcribe_and_analyze(audio_file, company_info, company_info_link, st.session_state.questions)
            st.success("Files uploaded successfully and template selected")
        else:
            st.error("Please select a template and upload at least one file (audio or company information)")

    if 'questions' in st.session_state and 'answers' in st.session_state:
        st.header("Edit Answers")
        answers = []
        instructions = []
        for i, qa in enumerate(st.session_state.answers):
            st.write(str(f"**{qa['question']}**"))
            answer = st.text_area(f"Answer {i+1}", value=qa['answer'], key=f"answer_{i+1}")
            answers.append(answer)
            
            instruction = st.text_input(f"Instruction for Answer {i+1}", key=f"instruction_{i+1}")
            instructions.append(instruction)
            
            if st.button(f"Revise Answer {i+1}", key=f"revise_{i+1}"):
                revised_answer = revise_answer(answer, instruction)
                st.session_state.answers[i]['answer'] = revised_answer
                st.experimental_rerun()
        
        if st.button("Save"):
            st.session_state.final_answers = [{"question": st.session_state.questions[i], "answer": ans} for i, ans in enumerate(answers)]
            save_history({
                "audio_file": history["audio_file"],
                "transcript_text": history["transcript_text"],
                "company_file": history["company_file"],
                "company_info_source": history["company_info_source"],
                "final_questions_and_answers": st.session_state.final_answers
            })
            st.success("Answers saved successfully")

    if 'final_answers' in st.session_state:
        st.header("Download Final Document")
        if st.button("Generate Document"):
            pdf_doc = create_pdf(st.session_state.final_answers, "final_answers.pdf")
            st.download_button(label="Download PDF", data=pdf_doc, file_name="final_answers.pdf", mime="application/pdf")
