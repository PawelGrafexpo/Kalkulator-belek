import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from collections import defaultdict
from fpdf import FPDF
import tempfile
import os

# Konfiguracja strony aplikacji
st.set_page_config(page_title="Kalkulator Rusztu Podłogowego GRAFEXPO", layout="wide")

st.title("🏗️ Kalkulator rusztu podłogowego GRAFEXPO")
st.write("Wprowadź parametry podłogi oraz kantówek w panelu poniżej, aby wygenerować plan rozkroju oraz precyzyjne zestawienie materiałowe.")

# Panel wprowadzania danych w układzie kolumnowym
with st.form("kalkulator_form"):
    st.subheader("Parametry konstrukcji")
    col1, col2 = st.columns(2)
    
    with col1:
        szer_podlogi = st.number_input("Szerokość podłogi w mm", min_value=500.0, value=12500.0, step=100.0)
        dl_podlogi = st.number_input("Długość podłogi w mm", min_value=500.0, value=9500.0, step=100.0)
    with col2:
        kantowka_dl = st.number_input("Standardowa długość kantówki w mm", min_value=500.0, value=4800.0, step=100.0)
        kantowka_szer = st.number_input("Szerokość / grubość kantówki w mm", min_value=10.0, value=38.0, step=1.0)
        
    submitted = st.form_submit_button("Oblicz i wygeneruj plan")

if submitted:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Rysowanie konturu podłogi
    podloga_rect = patches.Rectangle((0, 0), szer_podlogi, dl_podlogi, 
                                      linewidth=2, edgecolor='black', facecolor='#f9f9f9')
    ax.add_patch(podloga_rect)
    
    zapotrzebowanie_dlugosci = defaultdict(int)
    
    # --- 1. RAMA POZIOMA (DÓŁ I GÓRA) ---
    pelne_poz = math.floor(szer_podlogi / kantowka_dl)
    reszta_poz = szer_podlogi % kantowka_dl
    
    if pelne_poz > 0:
        zapotrzebowanie_dlugosci[kantowka_dl] += pelne_poz * 2
    if reszta_poz > 0:
        zapotrzebowanie_dlugosci[reszta_poz] += 2
        
    def rysuj_rame_poziomą(y_start):
        x_akt = 0
        for _ in range(pelne_poz):
            ax.add_patch(patches.Rectangle((x_akt, y_start), kantowka_dl, kantowka_szer, linewidth=1.2, edgecolor='darkred', facecolor='sandybrown', alpha=0.7))
            x_akt += kantowka_dl
        if reszta_poz > 0:
            ax.add_patch(patches.Rectangle((x_akt, y_start), reszta_poz, kantowka_szer, linewidth=1.2, edgecolor='darkred', facecolor='sandybrown', alpha=0.7))

    rysuj_rame_poziomą(0)
    rysuj_rame_poziomą(dl_podlogi - kantowka_szer)

    # --- 2. RAMA PIONOWA BOCZNA (LEWA I PRAWA) ---
    wys_boczna = dl_podlogi - (2 * kantowka_szer)
    pelne_pion = math.floor(wys_boczna / kantowka_dl)
    reszta_pion = wys_boczna % kantowka_dl

    if pelne_pion > 0:
        zapotrzebowanie_dlugosci[kantowka_dl] += pelne_pion * 2
    if reszta_pion > 0:
        zapotrzebowanie_dlugosci[reszta_pion] += 2

    def rysuj_rame_pionowa(x_start):
        y_akt = kantowka_szer
        for _ in range(pelne_pion):
            ax.add_patch(patches.Rectangle((x_start, y_akt), kantowka_szer, kantowka_dl, linewidth=1.2, edgecolor='darkred', facecolor='sandybrown', alpha=0.7))
            y_akt += kantowka_dl
        if reszta_pion > 0:
            ax.add_patch(patches.Rectangle((x_start, y_akt), kantowka_szer, reszta_pion, linewidth=1.2, edgecolor='darkred', facecolor='sandybrown', alpha=0.7))

    rysuj_rame_pionowa(0)
    rysuj_rame_pionowa(szer_podlogi - kantowka_szer)

    # --- 3. WEWNĘTRZNE KANTÓWKI PIONOWE (NA ZAKŁADKĘ) ---
    przeswit = 300
    x_pos = kantowka_szer + przeswit 
    wew_wys = wys_boczna
    
    n_wew = math.ceil(wew_wys / kantowka_dl)
    zaklad_wew = (n_wew * kantowka_dl - wew_wys) / (n_wew - 1) if n_wew > 1 else 0

    liczba_wew_pionowych_linii = 0
    while x_pos < szer_podlogi - kantowka_szer:
        liczba_wew_pionowych_linii += 1
        y_akt = kantowka_szer
        for i in range(n_wew):
            if i > 0:
                y_akt -= zaklad_wew
            x_offset = kantowka_szer if (i % 2 == 1) else 0
            ax.add_patch(patches.Rectangle((x_pos + x_offset, y_akt), kantowka_szer, kantowka_dl, 
                                            linewidth=1, edgecolor='navy', facecolor='peru', alpha=0.6))
            y_akt += kantowka_dl
        x_pos += przeswit + kantowka_szer

    if liczba_wew_pionowych_linii > 0:
        zapotrzebowanie_dlugosci[kantowka_dl] += liczba_wew_pionowych_linii * n_wew

    calkowita_dlugosc_metrow = sum(dł * ilosc for dł, ilosc in zapotrzebowanie_dlugosci.items()) / 1000

    # Ustawienia wykresu
    margines = max(szer_podlogi, dl_podlogi) * 0.05
    ax.set_xlim(-margines, szer_podlogi + margines)
    ax.set_ylim(-margines, dl_podlogi + margines)
    ax.set_aspect('equal')
    plt.title(f"Ruszt podlogowy | Szer: {szer_podlogi:.0f} mm | Dlug: {dl_podlogi:.0f} mm | Kantowka: {kantowka_dl} mm", fontsize=10, pad=15)
    plt.xlabel("Szerokosc podlogi (mm)", fontsize=10)
    plt.ylabel("Dlugosc podlogi (mm)", fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.5)

    # Wyświetlanie wykresu w Streamlit
    st.pyplot(fig)

    # Wyniki i podsumowania w formie wizualnych kart
    st.markdown("---")
    st.subheader("📊 Szczegółowy Bilans Elementów")
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.markdown(f"**Rama pozioma (góra i dół):**")
        st.write(f"- Pełne kantówki: **{pelne_poz * 2} szt.** (po {pelne_poz} szt. na rząd)")
        st.write(f"- Docinka końcowa: **{2 if reszta_poz > 0 else 0} szt.** o długości {reszta_poz:.0f} mm")
        
        st.markdown(f"**Rama pionowa boczna (lewa i prawa):**")
        st.write(f"- Pełne kantówki: **{pelne_pion * 2} szt.** (po {pelne_pion} szt. na stronę)")
        st.write(f"- Docinka końcowa: **{2 if reszta_pion > 0 else 0} szt.** o długości {reszta_pion:.0f} mm")
        
    with col_res2:
        st.markdown(f"**Kantówka wewnętrzna pionowa (liczba linii: {liczba_wew_pionowych_linii}):**")
        st.write(f"- Segmentów na 1 linię: **{n_wew} szt.**")
        st.write(f"- Wyliczony zakład: **{zaklad_wew:.0f} mm**")
        st.write(f"- Razem elementów: **{liczba_wew_pionowych_linii * n_wew} szt.**")

    st.markdown("---")
    st.subheader("📋 Podsumowanie Materiałowe (Lista elementów do zakupu)")
    
    for dł, ilosc in sorted(zapotrzebowanie_dlugosci.items(), key=lambda x: x[0], reverse=True):
        st.info(f"👉 **Kantówka o długości {dł:.0f} mm** -> **{ilosc} szt.**")
        
    st.success(f"📏 **Łączna długość elementów konstrukcji: {calkowita_dlugosc_metrow:.2f} m**")

    # --- GENEROWANIE PLIKU PDF Z WYKRESEM ---
    def bezpieczny(tekst):
        return tekst.encode('latin-1', 'replace').decode('latin-1')

    # Zapisujemy wykres do pliku tymczasowego PNG, aby wkleić go do PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
        fig.savefig(tmp_img.name, bbox_inches='tight', dpi=150)
        img_path = tmp_img.name

    class PDF(FPDF):
        def header(self):
            self.set_font("helvetica", "B", 13)
            self.cell(0, 8, bezpieczny("Kalkulator rusztu podlogowego GRAFEXPO - Raport"), 0, 1, "C")
            self.ln(3)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", "", 10)
    
    pdf.cell(0, 6, bezpieczny(f"Szerokosc podlogi: {szer_podlogi:.0f} mm | Dlugosc podlogi: {dl_podlogi:.0f} mm"), 0, 1)
    pdf.cell(0, 6, bezpieczny(f"Kantowka handlowa: {kantowka_dl:.0f} mm | Szerokosc kantowki: {kantowka_szer:.0f} mm"), 0, 1)
    pdf.ln(3)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, bezpieczny("Podsumowanie materialowe (do zakupu / ciecia):"), 0, 1)
    pdf.set_font("helvetica", "", 10)
    
    for dł, ilosc in sorted(zapotrzebowanie_dlugosci.items(), key=lambda x: x[0], reverse=True):
        pdf.cell(0, 6, bezpieczny(f"-> Kantowka o dlugosci {dł:.0f} mm: {ilosc} szt."), 0, 1)
        
    pdf.ln(3)
    pdf.cell(0, 6, bezpieczny(f"Laczna dlugosc elementów: {calkowita_dlugosc_metrow:.2f} m"), 0, 1)
    pdf.ln(5)

    # Wklejenie wykresu do PDF (szerokość 190 mm ładnie mieści się na stronie A4)
    pdf.image(img_path, x=10, y=pdf.get_y(), w=190)
    
    # Zapis do pliku tymczasowego PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf.output(tmp_file.name)
        tmp_path = tmp_file.name

    with open(tmp_path, "rb") as pdf_file:
        PDFbyte = pdf_file.read()

    # Usuwamy plik tymczasowy obrazka z dysku
    try:
        os.unlink(img_path)
    except:
        pass

    st.download_button(
        label="📥 Pobierz podsumowanie w formacie PDF z wykresem",
        data=PDFbyte,
        file_name="zapotrzebowanie_kantowek_grafexpo.pdf",
        mime="application/octet-stream"
    )
