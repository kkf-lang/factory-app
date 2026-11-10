import streamlit as st
import requests

# Page Config
st.set_page_config(page_title="n8n AI Agent Chat", page_icon="🤖", layout="centered")

st.title("🤖 n8n AI Agent with Streamlit")
st.markdown("ဤနေရာတွင် n8n AI Agent နှင့် တိုက်ရိုက် Chat ၍ မေးမြန်းနိုင်ပါသည်။")

# n8n Webhook URL (အပေါ်အဆင့် ၁ တွင် ရလာသော URL ကို ဤနေရာတွင် ထည့်ပါ)
N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/your-webhook-id"

# Chat History သိမ်းဆည်းရန် Session State သုံးခြင်း
if "messages" not in st.session_state:
    st.session_state.messages = []

# Message ဟောင်းများကို ပြန်ပြရန်
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User ဆီက Input တောင်းခံခြင်း
if user_input := st.chat_input("AI Agent ကို မေးလိုသည်များကို ရိုက်ထည့်ပါ..."):
    # User ရဲ့ မေးခွန်းကို UI ပေါ်တွင် ပြသရန်နှင့် History ထဲ သိမ်းရန်
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # n8n Webhook ဆီသို့ Request ပို့ခြင်း
    with st.chat_message("assistant"):
        with st.spinner("AI Agent စဉ်းစားနေသည်..."):
            try:
                payload = {"message": user_input}
                response = requests.post(N8N_WEBHOOK_URL, json=payload)
                
                if response.status_code == 200:
                    # n8n မှ ပြန်လာသော JSON ထဲမှ AI ဖြေသည့် စာသားကို ယူခြင်း 
                    # (n8n ဘက်တွင် Response JSON ဖွဲ့စည်းပုံပေါ်မူတည်၍ .get("output") သို့မဟုတ် .get("response") ကို ပြင်သုံးနိုင်ပါသည်)
                    ai_response = response.json().get("output", "အဖြေ မရရှိပါ။")
                else:
                    ai_response = f"⚠️ Server Error: {response.status_code}"
            except Exception as e:
                ai_response = f"❌ ချိတ်ဆက်မှု အမှားအယွင်းရှိပါသည်: {e}"
            
            st.markdown(ai_response)
    
    # Assistant ရဲ့ အဖြေကို History ထဲ သိမ်းရန်
    st.session_state.messages.append({"role": "assistant", "content": ai_response})