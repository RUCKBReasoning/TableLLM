# Install `pip3 install streamlit`
# Run `streamlit run streamlit.py --server.port 8501`
# For more, check the docs for streamlit

import warnings
warnings.filterwarnings('ignore')
import time
import pandas as pd
import streamlit as st

from code_exec import save_file, run_code
from tablellm import get_tablellm_response
from mongodb import update_vote_by_session_id
from default_table import get_single, get_double

st.set_page_config(page_title="TableLLM", layout = "wide")

if 'chat' not in st.session_state:
    st.session_state['chat'] = {
        "user_input_single": None,
        "user_input_double": None,
        "bot_response_single_1": None, # single table operation, show text or code
        "bot_response_single_2": None, # single table operation, show code execution result
        "bot_response_double_1": None, # multiple table operation, show text or code
        "bot_response_double_2": None, # multiple table operation, show code execution result
    }

# chat mode: QA or Code
if 'chat_mode' not in st.session_state:
    st.session_state['chat_mode'] = None

# question list
if 'questions' not in st.session_state:
    st.session_state['questions'] = None
if 'questions_double' not in st.session_state:
    st.session_state['questions_double'] = None

if 'table0' not in st.session_state:
    table, df, file_detail, questions, chat_mode = get_single()
    st.session_state['table0'] = {
        "uploadFile": None,
        "table": table,
        "dataframe": df,
        "file_detail": file_detail,
    }
    st.session_state['questions'] = questions
    st.session_state['chat_mode'] = chat_mode

if 'table1' not in st.session_state and 'table2' not in st.session_state:
    tables, dfs, file_details, questions = get_double()
    st.session_state['table1'] = {
        "uploadFile": None,
        "table": tables[0],
        "dataframe": dfs[0],
        "file_detail": file_details[0]
    }
    st.session_state['table2'] = {
        "uploadFile": None,
        "table": tables[1],
        "dataframe": dfs[1],
        "file_detail": file_details[1]
    }
    questions = ["Merge two tables and keep only the rows that are successfully merged.",
                "Merge the two tables and fill in the blanks with NAN."]
    st.session_state['questions_double'] = questions

# session id
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = None
if 'session_id_double' not in st.session_state:
    st.session_state['session_id_double'] = None

text_style = """
    <style>
        .mytext {
            border:1px solid black;
            border-radius:10px;
            border-color: #D6D6D8;
            padding:10px;
            height:auto;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            margin-bottom: 15px;
        }
    </style>
"""

def delete_question():
    if st.session_state['table0']["uploadFile"] is not None:
        st.session_state['questions'] = None
        st.session_state['table0'] = {
            "uploadFile": None,
            "table": None,
            "dataframe": None,
            "file_detail": None,
        }

def delete_question_double():
    if st.session_state['table1']["uploadFile"] is not None or st.session_state['table2']["uploadFile"] is not None:
        st.session_state['questions_double'] = None

st.markdown(text_style, unsafe_allow_html=True)

st.markdown('## TableLLM: Enabling Tabular Data Manipulation by LLMs in Real Office Usage Scenarios')

tab1, tab2 = st.tabs(["Single Table Operation", "Double Table Operation"])
with tab1:
    left_column, right_column = st.columns(2, gap = "large")
    
    with right_column.container():
        with st.chat_message(name="user", avatar="user"):
            user_input_single_placeholder = st.empty()
        with st.chat_message(name="assistant", avatar="assistant"):
            bot_response_single_1_placeholder = st.empty()
            bot_response_single_2_placeholder = st.empty()

        user_input = st.text_area("Enter your query:", key = "single tab1 user input")

        # buttons (send, upvote, downvote)
        button_column = st.columns(3)
        button_info = st.empty()
        with button_column[2]:
            send_button = st.button("✉️ Send", key = "single tab1 button", use_container_width=True)
            if send_button and len(user_input) != 0:
                if st.session_state['table0']['table'] is not None:
                    user_input_single_placeholder.markdown(user_input)
                    with st.spinner('loading...'):
                        bot_response, session_id = get_tablellm_response(user_input, 
                            st.session_state['table0']['table'],
                            st.session_state['table0']['file_detail'],
                            st.session_state['chat_mode'])

                    st.session_state['chat']['user_input_single'] = user_input
                    st.session_state['chat']['bot_response_single_1'] = bot_response
                    st.session_state['session_id'] = session_id

                    if st.session_state['chat_mode'] == 'QA':
                        bot_response_single_1_placeholder.markdown(bot_response)
                        st.session_state['chat']['bot_response_single_2'] = None
                    else:
                        bot_response_single_1_placeholder.code(bot_response, language='python')
                        
                        # run code and display result
                        code_res = run_code(bot_response, st.session_state['table0']['file_detail']['local_path'])
                        st.session_state['chat']['bot_response_single_2'] = code_res
                        
                        # change the type of code_res
                        if isinstance(code_res, pd.Series):
                            code_res = pd.DataFrame(code_res)

                        if isinstance(code_res, pd.DataFrame):
                            bot_response_single_2_placeholder.dataframe(code_res, height=min(250, len(st.session_state['table0']['dataframe'])*50), use_container_width=True)
                        elif bot_response.find('plt') != -1 and not isinstance(code_res, str):
                            bot_response_single_2_placeholder.pyplot(code_res)
                        else:
                            bot_response_single_2_placeholder.markdown(code_res)
                else:
                    st.text("Please upload a file to start")

        with button_column[1]:
            upvote_button = st.button("👍 Upvote", key = "single upvote button", use_container_width=True)
            if upvote_button and st.session_state['table0']['table'] is not None and st.session_state['session_id'] is not None:
                if st.session_state['chat']['user_input_single'] is not None:
                    user_input_single_placeholder.markdown(st.session_state['chat']['user_input_single'])
                if st.session_state['chat']['bot_response_single_1'] is not None:
                    if st.session_state['chat_mode'] == 'QA':
                        bot_response_single_1_placeholder.markdown(st.session_state['chat']['bot_response_single_1'])
                    else:
                        bot_response_single_1_placeholder.code(st.session_state['chat']['bot_response_single_1'], language='python')
                if st.session_state['chat']['bot_response_single_2'] is not None:
                    if st.session_state['chat_mode'] == 'Code':
                        code_res = st.session_state['chat']['bot_response_single_2']
                        if isinstance(code_res, pd.DataFrame):
                            bot_response_single_2_placeholder.dataframe(code_res, height=min(250, len(st.session_state['table0']['dataframe'])*50), use_container_width=True)
                        elif st.session_state['chat']['bot_response_single_1'].find('plt') != -1:
                            code_res = run_code(st.session_state['chat']['bot_response_single_1'], st.session_state['table0']['file_detail']['local_path'])
                            bot_response_single_2_placeholder.pyplot(code_res)
                        else:
                            bot_response_single_2_placeholder.markdown(code_res)
                # update vote
                update_vote_by_session_id(1, st.session_state['session_id'])
                button_info.success("Your upvote has been uploaded")
            elif upvote_button:
                button_info.info("Please start a conversation before voting.")

        with button_column[0]:
            downvote_button = st.button("👎 Downvote", key = "single downvote button", use_container_width=True)
            if downvote_button and st.session_state['table0']['table'] is not None and st.session_state['session_id'] is not None:
                if st.session_state['chat']['user_input_single'] is not None:
                    user_input_single_placeholder.markdown(st.session_state['chat']['user_input_single'])
                if st.session_state['chat']['bot_response_single_1'] is not None:
                    if st.session_state['chat_mode'] == 'QA':
                        bot_response_single_1_placeholder.markdown(st.session_state['chat']['bot_response_single_1'])
                    else:
                        bot_response_single_1_placeholder.code(st.session_state['chat']['bot_response_single_1'], language='python')
                if st.session_state['chat']['bot_response_single_2'] is not None:
                    if st.session_state['chat_mode'] == 'Code':
                        code_res = st.session_state['chat']['bot_response_single_2']
                        if isinstance(code_res, pd.DataFrame):
                            bot_response_single_2_placeholder.dataframe(code_res, height=min(250, len(st.session_state['table0']['dataframe'])*50), use_container_width=True)
                        elif st.session_state['chat']['bot_response_single_1'].find('plt') != -1:
                            code_res = run_code(st.session_state['chat']['bot_response_single_1'], st.session_state['table0']['file_detail']['local_path'])
                            bot_response_single_2_placeholder.pyplot(code_res)
                        else:
                            bot_response_single_2_placeholder.markdown(code_res)
                # update vote
                update_vote_by_session_id(-1, st.session_state['session_id'])
                button_info.success("Your downvote has been uploaded")
            elif downvote_button:
                button_info.info("Please start a conversation before voting.")

        # if st.session_state['table0']['uploadFile'] is None:
        if st.session_state['questions'] is not None:
            st.markdown("##### Possible questions to ask:")

            questions = st.session_state['questions']
            # random.shuffle(questions)
            button_num = min(5, len(questions))
            
            for i in range(button_num):
                question_columns1 = st.columns([7,1])
                with question_columns1[0]:
                    st.markdown("<div class='mytext'>{question}</div>".format(question=questions[i]), unsafe_allow_html=True)
            
                with question_columns1[1]:
                    if st.button("Send", use_container_width=True, key=f'single_question{i}'):
                        if st.session_state['table0']['table'] is not None:
                            user_input_single_placeholder.markdown(questions[i])
                            with st.spinner('loading...'):
                                bot_response, session_id = get_tablellm_response(questions[i], 
                                    st.session_state['table0']['table'],
                                    st.session_state['table0']['file_detail'],
                                    st.session_state['chat_mode'])
                                
                            st.session_state['chat']['user_input_single'] = questions[i]
                            st.session_state['chat']['bot_response_single_1'] = bot_response
                            st.session_state['session_id'] = session_id

                            if st.session_state['chat_mode'] == 'QA':
                                bot_response_single_1_placeholder.markdown(bot_response)
                                st.session_state['chat']['bot_response_single_2'] = None
                            else:
                                bot_response_single_1_placeholder.code(bot_response, language='python')
                                
                                # run code and display result
                                code_res = run_code(bot_response, st.session_state['table0']['file_detail']['local_path'])
                                st.session_state['chat']['bot_response_single_2'] = code_res
                                
                                if isinstance(code_res, pd.DataFrame):
                                    bot_response_single_2_placeholder.dataframe(code_res, height=min(250, len(st.session_state['table0']['dataframe'])*50), use_container_width=True)
                                elif bot_response.find('plt') != -1 and not isinstance(code_res, str):
                                    bot_response_single_2_placeholder.pyplot(code_res)
                                else:
                                    bot_response_single_2_placeholder.markdown(code_res)

                        elif st.session_state['table0']['table'] is None:
                            button_info.info("Please upload a file to start.")


    with left_column:
        illustration0 = st.markdown('- We will provide you a table and a list of possible questions to ask.\n\n- You can choose one of the provided questions or create your own question to have a conversation with the table.\n\n- You can also upload your own file containing table to start a conversation.')
        uploadFile = st.file_uploader("Upload your own file if you like", type=["csv", "xlsx", "xls", "docx"], on_change=delete_question)
        # uploadFile = st.file_uploader("Upload your own file if you like", type=["csv", "xlsx", "xls", "docx"])

        title_column = st.columns(3, gap = "large")
        text_prompt = st.empty()
        with title_column[0]:
            table_title = st.markdown('##### Provided table:')
        with title_column[2]:
            refresh_button = st.button("🔄 Refresh Table", key = "refresh table button", use_container_width=True)
            if refresh_button:
                if st.session_state['table0']["uploadFile"] is None:
                    # uploadFile = None
                    table, df, file_detail, questions, chat_mode = get_single(last_table=st.session_state['table0']['table'])
                    st.session_state['table0'] = {
                        "uploadFile": None,
                        "table": table,
                        "dataframe": df,
                        "file_detail": file_detail,
                    }
                    st.session_state['questions'] = questions
                    st.session_state['chat_mode'] = chat_mode
                    st.rerun()
                else:
                    text_prompt.info("Please delete the uploaded file before getting a new default table.")
                    time.sleep(1)
                    text_prompt.text("")

        if uploadFile is not None:
            if uploadFile == st.session_state['table0']['uploadFile']:
                st.dataframe(st.session_state['table0']['dataframe'], height=min(500, len(st.session_state['table0']['dataframe'])*50), use_container_width=True)
            else:
                try:
                    # if upload csv or xlsx, use Code mode
                    if uploadFile.name.endswith(('.csv', '.xlsx')):
                        st.session_state['chat_mode'] = 'Code'
                    elif uploadFile.name.endswith(('.docx')):
                        st.session_state['chat_mode'] = 'QA'

                    # save file
                    with st.spinner('loading...'):
                        df, tabular, file_detail = save_file(uploadFile)
                        st.session_state['table0'] = {
                            "uploadFile": uploadFile,
                            "table": tabular,
                            "dataframe": df,
                            "file_detail": file_detail
                        }
                        # generate questions
                        questions = []
                        
                    st.session_state['questions'] = questions
                    st.dataframe(df, height=min(500, len(df)*50), use_container_width=True)
                    st.session_state['chat']['user_input_single'] = None
                    st.session_state['chat']['bot_response_single_1'] = None
                    st.session_state['chat']['bot_response_single_2'] = None

                    # st.session_state['questions'] = []
                except Exception as e:
                    # print(str(e))
                    st.text("Error Saving File")
                st.rerun()
        elif st.session_state['questions'] is not None:
            df = st.session_state['table0']['dataframe']
            st.dataframe(df, height=min(500, len(df)*50), use_container_width=True)
        else:
            st.session_state['table0'] = {"uploadFile": None, "table": None, "dataframe": None, "file_detail": None}

with tab2:
    left_column2, right_column2= st.columns(2, gap = "large")
    with left_column2:
        illustration1 = st.markdown('- We will provide you two tables and a merge instruction.\n\n- You can use the given instruction to merge this two tables or create your own instruction.\n\n- You can also upload your own file containing table to create a merge.')

        uploadFile1 = st.file_uploader("Upload your first table", type=["csv", "xlsx", "xls"], on_change=delete_question_double)
        uploadFile2 = st.file_uploader("Upload your second table", type=["csv", "xlsx", "xls"], on_change=delete_question_double)

        title_column2 = st.columns(3, gap = "large")
        text_prompt2 = st.empty()
        with title_column2[0]:
            table_title2 = st.markdown('##### Provided table:')
        with title_column2[2]:
            refresh_button2 = st.button("🔄 Refresh Table", key = "refresh table button 2", use_container_width=True)
            if refresh_button2:
                if st.session_state['table1']["uploadFile"] is None and st.session_state['table2']["uploadFile"] is None:
                    tables, dfs, file_details, questions = get_double()
                    st.session_state['table1'] = {
                        "uploadFile": None,
                        "table": tables[0],
                        "dataframe": dfs[0],
                        "file_detail": file_details[0]
                    }
                    st.session_state['table2'] = {
                        "uploadFile": None,
                        "table": tables[1],
                        "dataframe": dfs[1],
                        "file_detail": file_details[1]
                    }
                    # questions = get_merge_q(st.session_state['table1']['dataframe'], st.session_state['table2']['dataframe'])
                    questions = ["Merge two tables and keep only the rows that are successfully merged.",
                                "Merge the two tables and fill in the blanks with NAN."]
                    st.session_state['questions_double'] = questions
                else:
                    text_prompt2.info("Please delete the uploaded file before getting a new default table.")
                    time.sleep(1)
                    text_prompt2.text("")

        if uploadFile1 is not None:
            if uploadFile1 != st.session_state['table1']['uploadFile']:
                try:
                    with st.spinner('loading table1...'):
                        df, tabular, file_detail = save_file(uploadFile1)
                        st.session_state['table1'] = {
                            "uploadFile": uploadFile1,
                            "table": tabular,
                            "dataframe": df,
                            "file_detail": file_detail
                        }
                        st.session_state['chat']['user_input_double'] = None
                        st.session_state['chat']['bot_response_double_1'] = None
                        st.session_state['chat']['bot_response_double_2'] = None
                except:
                    st.write("Error Saving File")
        elif st.session_state['questions_double'] is None:
            st.session_state['table1'] = {"uploadFile": None, "table": None, "dataframe": None, "file_detail": None}
            
        if uploadFile2 is not None:
            if uploadFile2 != st.session_state['table2']['uploadFile']:
                try:
                    with st.spinner('loading table2...'):
                        df, tabular, file_detail = save_file(uploadFile2)
                        st.session_state['table2'] = {
                            "uploadFile": uploadFile2,
                            "table": tabular,
                            "dataframe": df,
                            "file_detail": file_detail
                        }
                        st.session_state['chat']['user_input_double'] = None
                        st.session_state['chat']['bot_response_double_1'] = None
                        st.session_state['chat']['bot_response_double_2'] = None
                except:
                    st.write("Error Saving File")
        elif st.session_state['questions_double'] is None:
            st.session_state['table2'] = {"uploadFile": None, "table": None, "dataframe": None, "file_detail": None}
            
        if (st.session_state['table1']['dataframe'] is not None) and (st.session_state['table2']['dataframe'] is not None):
            questions = ["Merge two tables and keep only the rows that are successfully merged.",
                        "Merge the two tables and fill in the blanks with NAN."]
            st.session_state['questions_double'] = questions
            # st.session_state['questions_double'] = get_merge_q(st.session_state['table1']['dataframe'], st.session_state['table2']['dataframe'])
            st.dataframe(st.session_state['table1']['dataframe'], height=min(250, len(st.session_state['table1']['dataframe'])*50), use_container_width=True)
            st.dataframe(st.session_state['table2']['dataframe'], height=min(250, len(st.session_state['table2']['dataframe'])*50), use_container_width=True)


    with right_column2:
        with st.chat_message(name="user", avatar="user"):
            user_input_double_placeholder = st.empty()
        with st.chat_message(name="assistant", avatar="assistant"):
            bot_response_double_1_placeholder = st.empty()
            bot_response_double_2_placeholder = st.empty()

        user_input = st.text_area("Enter your query:", key = "double tab2 user input")

        button_column = st.columns(3)
        button_info2 = st.empty()
        with button_column[2]:
            send_button = st.button("✉️ Send", key = "double tab1 button", use_container_width=True)
            if send_button and len(user_input) != 0:
                if (st.session_state['table1']['dataframe'] is not None) and (st.session_state['table2']['dataframe'] is not None):
                    user_input_double_placeholder.markdown(user_input)
                    with st.spinner('loading...'):
                        bot_response, session_id = get_tablellm_response(question=user_input,
                            table=(st.session_state['table1']['table'], st.session_state['table2']['table']),
                            file_detail=[st.session_state['table1']['file_detail'], st.session_state['table2']['file_detail']],
                            mode='Code_Merge')

                    st.session_state['chat']['user_input_double'] = user_input
                    st.session_state['chat']['bot_response_double_1'] = bot_response
                    st.session_state['session_id_double'] = session_id

                    bot_response_double_1_placeholder.code(bot_response, language='python')
                    
                    # run code and display result
                    code_res = run_code(bot_response,
                        (st.session_state['table1']['file_detail']['local_path'], st.session_state['table2']['file_detail']['local_path']),
                        is_merge=True)
                    st.session_state['chat']['bot_response_double_2'] = code_res
                    bot_response_double_2_placeholder.dataframe(code_res, height=min(250, len(st.session_state['table1']['dataframe'])*50), use_container_width=True)
                else:
                    button_info2.text("Please upload a file to start")

        with button_column[1]:
            upvote_button = st.button("👍 Upvote", key = "double upvote button", use_container_width=True)
            if upvote_button and (st.session_state['table1']['dataframe'] is not None) and (st.session_state['table2']['dataframe'] is not None) and st.session_state['session_id_double'] is not None:
                if st.session_state['chat']['user_input_double'] is not None:
                    user_input_double_placeholder.markdown(st.session_state['chat']['user_input_double'])
                if st.session_state['chat']['bot_response_double_1'] is not None:
                    bot_response_double_1_placeholder.code(st.session_state['chat']['bot_response_double_1'], language='python')
                if st.session_state['chat']['bot_response_double_2'] is not None:
                    bot_response_double_2_placeholder.dataframe(st.session_state['chat']['bot_response_double_2'], height=min(250, len(st.session_state['table2']['dataframe'])*50), use_container_width=True)
                # update vote
                update_vote_by_session_id(1, st.session_state['session_id_double'])
                button_info2.success("Your upvote has been uploaded")
            elif upvote_button:
                button_info2.info("Please start a conversation before voting.")

        with button_column[0]:
            downvote_button = st.button("👎 Downvote", key = "double downvote button", use_container_width=True)
            if downvote_button and (st.session_state['table1']['dataframe'] is not None) and (st.session_state['table2']['dataframe'] is not None) and st.session_state['session_id_double'] is not None:
                if st.session_state['chat']['user_input_double'] is not None:
                    user_input_double_placeholder.markdown(st.session_state['chat']['user_input_double'])
                if st.session_state['chat']['bot_response_double_1'] is not None:
                    bot_response_double_1_placeholder.code(st.session_state['chat']['bot_response_double_1'], language='python')
                if st.session_state['chat']['bot_response_double_2'] is not None:
                    bot_response_double_2_placeholder.dataframe(st.session_state['chat']['bot_response_double_2'], height=min(250, len(st.session_state['table2']['dataframe'])*50), use_container_width=True)
                # update vote
                update_vote_by_session_id(-1, st.session_state['session_id_double'])
                button_info2.success("Your upvote has been uploaded")
            elif downvote_button:
                button_info2.info("Please start a conversation before voting.")

        if st.session_state['questions_double'] is not None:
            st.markdown("##### Possible questions to ask:")
            
            questions = st.session_state['questions_double']
            button_num = min(5, len(questions))

            for i in range(button_num):
                question_columns2 = st.columns([7,1])
                with question_columns2[0]:
                    st.markdown("<div class='mytext'>{question}</div>".format(question=questions[i]), unsafe_allow_html=True)
                with question_columns2[1]:
                    if st.button("Send", use_container_width=True, key=f'double_question{i}'):
                        if (st.session_state['table1']['dataframe'] is not None) and (st.session_state['table2']['dataframe'] is not None):
                            user_input_double_placeholder.markdown(questions[i])
                            with st.spinner('loading...'):
                                bot_response, session_id = get_tablellm_response(questions[i], 
                                    [st.session_state['table1']['table'], st.session_state['table2']['table']],
                                    [st.session_state['table1']['file_detail'], st.session_state['table1']['file_detail']],
                                    'Code_Merge')

                            st.session_state['chat']['user_input_double'] = questions[i]
                            st.session_state['chat']['bot_response_double_1'] = bot_response
                            st.session_state['session_id_double'] = session_id

                            bot_response_double_1_placeholder.code(bot_response, language='python')
                                
                            # run code and display result
                            code_res = run_code(bot_response,
                                                [st.session_state['table1']['file_detail']['local_path'], st.session_state['table2']['file_detail']['local_path']],
                                                is_merge=True)
                            st.session_state['chat']['bot_response_double_2'] = code_res
                            bot_response_double_2_placeholder.dataframe(code_res, height=min(250, len(st.session_state['table1']['dataframe'])*50), use_container_width=True)
                        else:
                            st.text("Please upload a file to start")
