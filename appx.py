import openai
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import requests

# Set up your API keys here
openai.api_key = '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'
youtube_api_key = 'AIzaSyDtEGRf_JaEps61FBUkRntQhh62JwwP-9Q'

st.title("ChatGPT-like clone with YouTube Video Analyzer")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo-16k"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "video_url" not in st.session_state:
    st.session_state["video_url"] = ""

if "video_details" not in st.session_state:
    st.session_state["video_details"] = {}

if "full_transcript" not in st.session_state:
    st.session_state["full_transcript"] = ""

if "url_entered" not in st.session_state:
    st.session_state["url_entered"] = False

if "summary_generated" not in st.session_state:
    st.session_state["summary_generated"] = False

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Define a variable to hold the API response
api_response = None

if not st.session_state["url_entered"]:
    prompt = st.chat_input("Enter YouTube Video URL:")
    if prompt:
        st.session_state["video_url"] = prompt
        video_id = prompt.split('v=')[-1].split('&')[0]

        try:
            video_details_url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={youtube_api_key}'
            response = requests.get(video_details_url)
            video_details = response.json()
            
            # Check if video details are available
            if not video_details.get('items'):
                raise Exception("No video details found. Please check the URL and try again.")
            
            video_title = video_details['items'][0]['snippet']['title']
            
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            full_transcript = " ".join([x['text'] for x in transcript])

            st.session_state['video_details'] = video_details
            st.session_state['full_transcript'] = full_transcript
            st.session_state["url_entered"] = True
            st.success('Transcript fetched successfully!')
            # Store the API response in the variable
            api_response = response.json()
        except YouTubeTranscriptApi.TranscriptsDisabled:
            st.error('Could not retrieve transcript. The video might not have transcripts enabled.')
        except YouTubeTranscriptApi.NoTranscriptFound:
            st.error('Could not retrieve transcript. No transcript found.')
        except Exception as e:
            st.error(f'Error fetching transcript: {str(e)}')

        # Automatically initiate a chat request for summary
        if not st.session_state.get('summary_generated', False):
            video_details = st.session_state['video_details']
            video_title = video_details['items'][0]['snippet']['title']
            full_transcript = st.session_state['full_transcript']
            
            st.session_state['current_chat'] = [
                {"role": "system", "content": 'You are a helpful assistant.'},
                {"role": "user", "content": f"I have watched a video titled '{video_title}' from the channel '{video_details['items'][0]['snippet']['channelTitle']}' with the following transcript: {full_transcript}"},
                {"role": "user", "content": "Can you give me a summary or gist of what the video is about? if needed, you can use points and elaborate quickly upon each point."}
            ]

            with st.spinner('Generating summary...'):
                try:
                        # Create a placeholder for the summary message
                        with st.chat_message("assistant"):
                            summary_message_placeholder = st.empty()
                            full_response = ""
                            for response in openai.ChatCompletion.create(
                                model=st.session_state["openai_model"], 
                                messages=st.session_state['current_chat'],
                                stream=True,  # Set stream=True to get streaming responses
                            ):
                                full_response += response.choices[0].delta.get("content", "")
                                summary_message_placeholder.markdown(full_response + "▌")
                            summary_message_placeholder.markdown(full_response)
                        
                        st.session_state.messages.append({"role": "user", "content": st.session_state['current_chat'][2]["content"]})
                        st.session_state.messages.append({"role": "assistant", "content": full_response.strip()})
                        st.session_state['summary_generated'] = True

                        # Force Streamlit to rerun the script to update the chat input prompt
                        st.experimental_rerun()
                except openai.error.OpenAIError as e:
                    st.error(f'Error generating summary: {str(e)}')


        # Display the new messages
        for message in st.session_state.messages[-2:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

else:
    # Show "behind the scenes" - Transcript
    if st.checkbox('Show Behind the Scenes - Transcript', key='transcript_behind_the_scenes'):
        st.write(f"Transcript: {st.session_state.get('full_transcript', '...')}")  # Corrected the default value parameter

    # Chat input field
    prompt = st.chat_input("Enter your question about the video:" if st.session_state["url_entered"] else "Enter YouTube Video URL:")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})








# allow me to edit every entry name in the chat history only if I click an edit button next to the entry name. the edit button should be a pencil icon.






# add text to speech
#sharing youtube link doesn't work
# embed the video below the page title, below it have the Transciprt
#add time stamps and allow me to jump to a specific time stamp in the video. Can we also make the summary to address the time stamps?
# for a new video the script doesn't automatically ask for a summary, it should.
# in the user settings allow me to choose between the models gpt-3.5-turbo-16k, gpt-3.5-turbo, gpt-4, gpt-4-32k
# Count the number of words in the transcript and if it's more than 12000 words cut it to several parts and ask for summary for each part. for each part allow to ask questions by declaring in the prompt the part number.
# for every entry in the chat history, if there is no video title fetched, than assign the current day and time as the title.
# in prompt add the video title and the video channel related to give a context to the AI.
# chat history is a direct link to the video instead of loading the video again in the main area and showing the conversation history and allowing me to ask more questions or read the previous questions and answers.
# user setting button at the buttom, and should be closed when clicked again
# search bar in chat history to search video titles or responses in the chat.
# ask about the prompt structure of the user question. 
# handle API key errors by asking the user to edit the key in the pop up window.
#get the chat side bar


# the api response should be saved and not fetched again from the server. same for the show the transcipt.
#add youtube API to fetch video titles
# when clicking new chat button, the 'Enter YouTube Video URL:' should remove the existing url when clicked if there is a url, and clean the reset the page make it ready for a new chat.


## the enter your quetion must be the buttom of the page
## only one status bar that is replacing the status should be
## when I clicked the API response and transcript button I saw new entry in the chat history, for the same video, there must be one entry for each video session.
## In the text field of entering a question, allow me to have shift enter to expand the field and get down to the next line to enter additional text.




### still getting 2 new enter video URL fields when I click new chat button.
### new chat doesn't work as it should in the first time the script is running, also it doens't include the prompt and the transcipt in it. and the web ui doesn't 
### The status bar, is not there.
### I fetched a video and clicked show API response and it showed 'No API response available.' which is not true.
### Visit the URL https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps#build-a-simple-chatbot-gui-with-streaming and take the web ui from the streamlit 'Build conversational apps' tutorial, but with my script functionality.just the prompt strucure so the 'full_transcript will be given at the end of it, to make sure the chatgpt is paying attention to the question.
###
###
###
###
###
###
###
###
###
