import streamlit as st
import pandas as pd
import requests

appid = streamlit.secrets["appid"]
client_secret = streamlit.secrets["client_secret"]


def get_token(appid, client_secret):
    url = "https://orcid.org/oauth/token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": appid,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "/read-public"
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Failed to get token: {response.text}")
        return None

token = get_token(appid, client_secret)
print(token)

def get_author_name(orcid_id, token):
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/person"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return f"{data['name']['given-names']['value']} {data['name']['family-name']['value']}"
    else:
        print(f"Failed to get name: {response.text}")
        return None


# Function to get author works
def get_author_works(orcid_id, token):
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('group', [])
    else:
        print(f"Failed to get works: {response.text}")
        return None

    
# Function to get dataframe of journal publications
def get_journal_pub_df(orcid_ids, token):
    data = []

    for orcid_id in orcid_ids:
        name = get_author_name(orcid_id, token)
        works = get_author_works(orcid_id, token)
        for work in works:
            for item in work.get('work-summary', []):
                journal_info = item.get('journal-title', None)
                if journal_info is not None:
                    journal_title = journal_info.get('value', None)
                    if journal_title:
                        data.append({"Journal": journal_title, "ORCID": orcid_id, "Name": name})

    df = pd.DataFrame(data)
    return df

# Predefined ORCID lists
chemistry_biomolecular_sciences_orcids = [
    '0000-0003-3382-7939', '0000-0002-3930-631X', '0000-0001-6402-2311', 
    '0000-0002-1618-4620', '0000-0002-4917-9684', '0000-0002-2998-669X', 
    '0000-0003-1670-3301', '0000-0001-9942-2251', '0000-0002-8709-1667'
]

biology_orcids = [
    '0000-0002-2294-1229', '0000-0002-4539-7983', '0000-0001-7022-9482',
    '0000-0002-6716-5550', '0000-0003-4267-820X', '0000-0002-7902-4771',
    '0000-0001-6371-5466', '0000-0001-7897-6984', '0000-0003-4991-2636'
]

# Sidebar navigation
st.sidebar.title('ORCID Analyzer')
page = st.sidebar.radio("Go to", ["Home","Predefined ORCID List", "Freeform ORCID Input"])

# Clear the session state if the page changes
if 'last_page' in st.session_state and st.session_state['last_page'] != page:
    st.session_state.clear()
st.session_state['last_page'] = page

if page == "Home":
    st.title("Welcome!")
    st.write("Please select a page from the sidebar.")
elif page == "Freeform ORCID Input":
    st.title("Freeform ORCID Input")

    if 'token' not in st.session_state:
        st.session_state['token'] = token
    
    orcid_ids = st.text_area("Enter ORCID ids (one per line)", height=200)

    if st.button('Run'):
        if orcid_ids and st.session_state['token']:
            orcid_ids = orcid_ids.split('\n')
            st.session_state['df'] = get_journal_pub_df(orcid_ids, st.session_state['token'])
            st.session_state['df_display'] = st.session_state['df']['Journal'].value_counts().reset_index()
            st.session_state['df_display'].columns = ['Journal', 'Number of Publications']
            st.session_state['df_display'] = st.session_state['df_display'].sort_values('Number of Publications', ascending=False)

    if 'df_display' in st.session_state and not st.session_state['df_display'].empty:
        filter = st.text_input('Filter journals:')
        filtered_df = st.session_state['df_display'][st.session_state['df_display']['Journal'].str.contains(filter, case=False)]
        st.write(filtered_df)
        journal = st.selectbox('Select a journal to see the associated ORCID ids and Names', filtered_df['Journal'].unique())
        if journal:
            author_data = st.session_state['df'][st.session_state['df']['Journal'] == journal].groupby(['ORCID', 'Name']).size().reset_index(name='Publications in Selected Journal')
            st.write(author_data)

elif page == "Predefined ORCID List":
    st.title("Predefined ORCID List")
    
    if 'token' not in st.session_state:
        st.session_state['token'] = token

    orcid_list = st.radio("Choose a list", ["Clarkson Chemistry & Biomolecular Sciences", "Clarkson Biology"])
    orcid_ids = chemistry_biomolecular_sciences_orcids if orcid_list == "Clarkson Chemistry & Biomolecular Sciences" else biology_orcids

    if st.button('Run'):
        if st.session_state['token']:
            st.session_state['df'] = get_journal_pub_df(orcid_ids, st.session_state['token'])
            st.session_state['df_display'] = st.session_state['df']['Journal'].value_counts().reset_index()
            st.session_state['df_display'].columns = ['Journal', 'Number of Publications']
            st.session_state['df_display'] = st.session_state['df_display'].sort_values('Number of Publications', ascending=False)
        
    if 'df_display' in st.session_state and not st.session_state['df_display'].empty:
        filter = st.text_input('Filter journals:')
        filtered_df = st.session_state['df_display'][st.session_state['df_display']['Journal'].str.contains(filter, case=False)]
        st.write(filtered_df)
        journal = st.selectbox('Select a journal to see the associated ORCID ids and Names', filtered_df['Journal'].unique())
        if journal:
            author_data = st.session_state['df'][st.session_state['df']['Journal'] == journal].groupby(['ORCID', 'Name']).size().reset_index(name='Publications in Selected Journal')
            st.write(author_data)

