# Gerekli kütüphaneleri import et
import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection # <-- DOĞRU IMPORT İFADESİ BU

# -------------------- SAYFA AYARLARI --------------------
st.set_page_config(
    page_title="BES Takip Uygulaması",
    page_icon="📊",
    layout="wide"
)

# -------------------- GOOGLE SHEETS BAĞLANTISI --------------------
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Google Sheets bağlantısı kurulamadı. Lütfen Streamlit Cloud > Secrets ayarlarınızı ve Google Sheets paylaşım izinlerinizi kontrol edin.")
    st.stop() 

# -------------------- ANA BAŞLIK --------------------
st.title("📊 Bireysel Emeklilik Sözleşme Takibi")

WORKSHEET_NAME = "sozlesme_1" 

# -------------------- VERİYİ GOOGLE SHEETS'TEN OKUMA --------------------
try:
    existing_data = conn.read(worksheet=WORKSHEET_NAME, usecols=list(range(11)), ttl=5)
    existing_data = existing_data.dropna(how="all")
except Exception as e:
    st.warning(f"'{WORKSHEET_NAME}' sayfası okunamadı. Sayfa boş olabilir veya bir hata oluştu. Yeni veri ekleyerek başlayabilirsiniz.")
    existing_data = pd.DataFrame()


# -------------------- YENİ VERİ GİRİŞ FORMU --------------------
with st.form("veri_giris_formu", clear_on_submit=True):
    st.subheader("➕ Yeni Veri Girişi Yap")
    st.info("Bu forma, BES uygulamanızdaki **o anki güncel toplam** bilgilerinizi girin.")
    
    col1, col2 = st.columns(2)

    with col1:
        tarih = st.date_input("Veri Tarihi", value=date.today())
        fon_getirisi = st.number_input("O Günün Fon Getirisi (%)", value=0.0, format="%.4f", help="Örn: 0.15 veya -0.1")
        fon_turleri = st.multiselect("Fon Dağılımı", ["Değişken", "Katılım", "Esnek", "Borçlanma", "Altın", "Diğer"])
        fon_orani = st.text_input("Fon Dağılım Oranı", placeholder="Örn: %70 Değişken, %30 Altın")

    with col2:
        ana_para = st.number_input("TOPLAM Ana Para (TL)", value=0.0, format="%.2f")
        ana_para_getirisi = st.number_input("TOPLAM Ana Para Getirisi (TL)", value=0.0, format="%.2f")
        devlet_katkisi = st.number_input("TOPLAM Devlet Katkısı (TL)", value=0.0, format="%.2f")
        devlet_getirisi = st.number_input("TOPLAM Devlet Katkısı Getirisi (TL)", value=0.0, format="%.2f")

    submitted = st.form_submit_button("Kaydet")

    if submitted:
        ana_toplam = ana_para + ana_para_getirisi
        devlet_toplam = devlet_katkisi + devlet_getirisi
        toplam_birikim = ana_toplam + devlet_toplam

        new_data = pd.DataFrame([{
            "Tarih": tarih.strftime("%Y-%m-%d"),
            "Fon Getirisi (%)": fon_getirisi,
            "Fon Türü": ", ".join(fon_turleri),
            "Fon Oranı": fon_orani,
            "Ana Para": ana_para,
            "Ana Para Getirisi": ana_para_getirisi,
            "Ana Para + Getiri": ana_toplam,
            "Devlet Katkısı": devlet_katkisi,
            "Devlet Katkısı Getirisi": devlet_getirisi,
            "Devlet Katkısı + Getiri": devlet_toplam,
            "Toplam Birikim": toplam_birikim
        }])

        updated_df = pd.concat([existing_data, new_data], ignore_index=True)

        try:
            conn.update(worksheet=WORKSHEET_NAME, data=updated_df)
            st.success("Veri başarıyla kaydedildi!")
        except Exception as e:
            st.error(f"Veri kaydedilirken bir hata oluştu: {e}")
        
        st.rerun()

# -------------------- ÖZET BİLGİLER (METRİKLER) --------------------
st.subheader("📈 Anlık Bakiye (Son Girdi)")
if not existing_data.empty:
    son_veri = existing_data.sort_values(by="Tarih").iloc[-1]
    
    st.metric("💰 Toplam Birikim", f"{son_veri['Toplam Birikim']:,.2f} TL")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ana Para Toplamı", f"{son_veri['Ana Para + Getiri']:,.2f} TL", delta=f"{son_veri['Ana Para Getirisi']:,.2f} TL Getiri")
    with col2:
        st.metric("Devlet Katkısı Toplamı", f"{son_veri['Devlet Katkısı + Getiri']:,.2f} TL", delta=f"{son_veri['Devlet Katkısı Getirisi']:,.2f} TL Getiri")
else:
    st.info("Henüz görüntülenecek veri yok.")

# -------------------- DETAYLI TABLO --------------------
st.subheader("📄 Geçmiş Veriler")
st.dataframe(existing_data, use_container_width=True)
