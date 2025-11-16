#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lojistik Maliyet Hesaplama Sistemi - Streamlit Uygulaması
Öğrenciler cevaplarını gönder → Otomatik puan al
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# ═══════════════════════════════════════════════════════════════════════════════
# SAYFA AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Lojistik Maliyet Hesaplama",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { padding-top: 2rem; }
    .stButton>button { width: 100%; }
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VERİTABANI BAĞLANTISI
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_db_connection():
    """Veritabanı bağlantısı oluştur (cache'lendi)"""
    try:
        # Lokalde test ederken
        db_path = "data/database/logistics.db"
        if not os.path.exists(db_path):
            # Streamlit Cloud'da
            db_path = "./data/database/logistics.db"
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        st.error(f"❌ Veritabanı bağlantı hatası: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# PUANLAMA FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════════════════════

def get_student_info(student_id):
    """Öğrenci bilgilerini al"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()
        conn.close()
        return dict(student) if student else None
    except Exception as e:
        st.error(f"Öğrenci sorgusu hatası: {e}")
        return None

def get_student_invoices(student_id):
    """Öğrencinin faturalarını al"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT invoice_number, product_name, origin_country, destination_country, 
                   route_name, quantity, unit_price, total_value
            FROM invoices 
            WHERE student_id = ? 
            ORDER BY invoice_number
        """, (student_id,))
        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return invoices
    except Exception as e:
        st.error(f"Fatura sorgusu hatası: {e}")
        return []

def get_correct_answers(student_id, invoice_number):
    """Doğru cevapları al"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT customs_duty, excise_tax, vat, logistics_cost, shipping_cost, total_cost
            FROM invoice_calculations
            WHERE student_id = ? AND invoice_number = ?
        """, (student_id, invoice_number))
        answers = cursor.fetchone()
        conn.close()
        return dict(answers) if answers else None
    except Exception as e:
        st.error(f"Doğru cevap sorgusu hatası: {e}")
        return None

def grade_answers(student_id, invoice_number, submitted_answers):
    """
    Cevapları puanla
    
    Parameters:
    - submitted_answers: {
        'customs_duty': float,
        'excise_tax': float,
        'vat': float,
        'logistics_cost': float,
        'shipping_cost': float,
        'total_cost': float
    }
    
    Returns:
    - (score, details)
    """
    
    correct = get_correct_answers(student_id, invoice_number)
    if not correct:
        return 0, "Doğru cevaplar bulunamadı"
    
    # Her alan için tolerans: 0.5 TL
    TOLERANCE = 0.5
    fields = [
        ('Lojistik Maliyeti', 'logistics_cost'),
        ('Nakliye Maliyeti', 'shipping_cost'),
        ('Gümrük Vergisi', 'customs_duty'),
        ('Özel Tüketim Vergisi', 'excise_tax'),
        ('KDV', 'vat'),
        ('Toplam Tutar', 'total_cost')
    ]
    
    correct_count = 0
    details = []
    
    for label, key in fields:
        if key not in submitted_answers or submitted_answers[key] is None:
            details.append(f"❌ {label}: Boş")
            continue
        
        submitted = submitted_answers[key]
        correct_val = correct[key]
        diff = abs(submitted - correct_val)
        
        if diff <= TOLERANCE:
            correct_count += 1
            details.append(f"✅ {label}: {submitted:.2f} TL")
        else:
            details.append(f"❌ {label}: {submitted:.2f} TL (Doğru: {correct_val:.2f} TL)")
    
    # Puanlama: Her doğru cevap ~16.67% (6 alan = 100%)
    score = (correct_count / 6) * 100
    
    return score, "\n".join(details)

def save_submission(student_id, invoice_number, submitted_answers, score):
    """Cevapları veritabanına kaydet"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO submissions 
            (student_id, invoice_number, customs_duty, excise_tax, vat, 
             logistics_cost, shipping_cost, total_cost, score, submission_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            invoice_number,
            submitted_answers.get('customs_duty', 0),
            submitted_answers.get('excise_tax', 0),
            submitted_answers.get('vat', 0),
            submitted_answers.get('logistics_cost', 0),
            submitted_answers.get('shipping_cost', 0),
            submitted_answers.get('total_cost', 0),
            score,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Kayıt hatası: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# STREAMLIT ARAYÜZü
# ═══════════════════════════════════════════════════════════════════════════════

# Başlık
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📦 Lojistik Maliyet Hesaplama Sistemi")
    st.write("Fatura hesaplamalarını girin ve otomatik olarak puanlanın")

with col2:
    st.write("")
    st.write("")
    st.info("v1.0 - Production Ready")

st.divider()

# Sidebar - Öğrenci Seçimi
with st.sidebar:
    st.header("👤 Öğrenci Giriş")
    
    student_id = st.text_input(
        "Öğrenci Numarası (10 haneli)",
        placeholder="1212603034",
        max_chars=10
    )
    
    if student_id:
        student = get_student_info(student_id)
        if student:
            st.success("✅ Öğrenci bulundu!")
            st.write(f"**Ad:** {student['name']}")
            st.write(f"**Kayıt Tarihi:** {student['registration_date']}")
        else:
            st.error("❌ Öğrenci bulunamadı")
            student = None
    else:
        student = None

# Ana İçerik
if not student_id:
    st.warning("👈 Lütfen soldan öğrenci numarasını girin")
    
elif not student:
    st.error("Öğrenci bulunamadı. Lütfen numarayı kontrol edin.")
    
else:
    # Sekmeler
    tab1, tab2, tab3 = st.tabs(["📋 Öğrenci Bilgileri", "📄 Faturalar", "📝 Cevap Gönder"])
    
    # ─────────────────────────────────────────────────────────────────────
    # TAB 1: Öğrenci Bilgileri
    # ─────────────────────────────────────────────────────────────────────
    with tab1:
        st.subheader(f"👤 {student['name']}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Öğrenci No", student_id)
        with col2:
            st.metric("Kayıt Tarihi", student['registration_date'][:10])
        with col3:
            invoices = get_student_invoices(student_id)
            st.metric("Fatura Sayısı", len(invoices))
        with col4:
            st.metric("Fatura Başına", "6 Soru")
        
        st.divider()
        st.info("📌 Sağdan 'Cevap Gönder' sekmesine geçerek cevaplarınızı girin")
    
    # ─────────────────────────────────────────────────────────────────────
    # TAB 2: Faturalar (Bilgi Amaçlı)
    # ─────────────────────────────────────────────────────────────────────
    with tab2:
        invoices = get_student_invoices(student_id)
        
        if not invoices:
            st.error("Fatura bulunamadı")
        else:
            st.subheader("📋 Faturalarınız")
            
            # Fatura seç
            invoice_numbers = [inv['invoice_number'] for inv in invoices]
            selected_invoice_num = st.selectbox(
                "Fatura Seçin",
                invoice_numbers,
                format_func=lambda x: f"Fatura #{x}"
            )
            
            # Seçili faturayı göster
            selected = next((inv for inv in invoices if inv['invoice_number'] == selected_invoice_num), None)
            
            if selected:
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Ürün:** {selected['product_name']}")
                    st.write(f"**Miktar:** {selected['quantity']} birim")
                with col2:
                    st.write(f"**Gönderen:** {selected['origin_country']}")
                    st.write(f"**Alan:** {selected['destination_country']}")
                with col3:
                    st.write(f"**Rota:** {selected['route_name']}")
                    st.write(f"**Tutar:** {selected['total_value']:.2f} USD")
                
                st.divider()
                
                # Doğru cevapları göster
                correct = get_correct_answers(student_id, selected_invoice_num)
                if correct:
                    st.subheader("✅ Doğru Cevaplar (Referans)")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Lojistik Maliyeti", f"{correct['logistics_cost']:.2f} TL")
                        st.metric("Gümrük Vergisi", f"{correct['customs_duty']:.2f} TL")
                    with col2:
                        st.metric("Nakliye Maliyeti", f"{correct['shipping_cost']:.2f} TL")
                        st.metric("ÖTV", f"{correct['excise_tax']:.2f} TL")
                    with col3:
                        st.metric("KDV", f"{correct['vat']:.2f} TL")
                        st.metric("TOPLAM", f"{correct['total_cost']:.2f} TL", delta=None)
    
    # ─────────────────────────────────────────────────────────────────────
    # TAB 3: Cevap Gönder
    # ─────────────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("📝 Cevaplarınızı Girin")
        
        invoices = get_student_invoices(student_id)
        if not invoices:
            st.error("Fatura bulunamadı")
        else:
            # Fatura seç
            invoice_numbers = [inv['invoice_number'] for inv in invoices]
            selected_invoice_num = st.selectbox(
                "Hangi Fatura İçin Cevap Veriyorsunuz?",
                invoice_numbers,
                format_func=lambda x: f"Fatura #{x}",
                key="submit_invoice"
            )
            
            st.divider()
            
            # Cevap giriş alanları
            st.write("**6 Alanı TL cinsinden girin:**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                logistics_cost = st.number_input(
                    "Lojistik Maliyeti (TL)",
                    min_value=0.0,
                    step=10.0,
                    value=0.0
                )
                nakliye_cost = st.number_input(
                    "Nakliye Maliyeti (TL)",
                    min_value=0.0,
                    step=10.0,
                    value=0.0
                )
            
            with col2:
                customs_duty = st.number_input(
                    "Gümrük Vergisi (TL)",
                    min_value=0.0,
                    step=10.0,
                    value=0.0
                )
                excise_tax = st.number_input(
                    "ÖTV (TL)",
                    min_value=0.0,
                    step=10.0,
                    value=0.0
                )
            
            with col3:
                vat = st.number_input(
                    "KDV (TL)",
                    min_value=0.0,
                    step=10.0,
                    value=0.0
                )
                total_cost = st.number_input(
                    "Toplam Tutar (TL)",
                    min_value=0.0,
                    step=10.0,
                    value=0.0
                )
            
            st.divider()
            
            # Gönder butonu
            if st.button("✅ Cevapları Gönder ve Puanını Öğren", use_container_width=True):
                
                # Doğrulama
                if all([logistics_cost, nakliye_cost, customs_duty, excise_tax, vat, total_cost]):
                    
                    # Puanlama yap
                    submitted_answers = {
                        'logistics_cost': logistics_cost,
                        'shipping_cost': nakliye_cost,
                        'customs_duty': customs_duty,
                        'excise_tax': excise_tax,
                        'vat': vat,
                        'total_cost': total_cost
                    }
                    
                    score, details = grade_answers(student_id, selected_invoice_num, submitted_answers)
                    
                    # Sonucu kaydet
                    if save_submission(student_id, selected_invoice_num, submitted_answers, score):
                        
                        # Sonuç göster
                        st.divider()
                        
                        if score == 100:
                            st.balloons()
                            st.success(f"🎉 MÜKEMMEL! Puanınız: **{score:.0f}%**")
                        elif score >= 80:
                            st.success(f"✅ Başarılı! Puanınız: **{score:.0f}%**")
                        elif score >= 60:
                            st.warning(f"⚠️ Kabul edilebilir. Puanınız: **{score:.0f}%**")
                        else:
                            st.error(f"❌ Tekrar deneyin. Puanınız: **{score:.0f}%**")
                        
                        st.divider()
                        st.subheader("📊 Detaylar:")
                        st.code(details)
                        
                        st.info("💾 Cevaplarınız kaydedildi. Admin panelinde görüntülenebilir.")
                    else:
                        st.error("❌ Cevaplar kaydedilemedi")
                
                else:
                    st.error("⚠️ Lütfen tüm alanları doldurun")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    <p>Lojistik Maliyet Hesaplama Sistemi | v1.0</p>
    <p>Gümrük İşletme Bölümü</p>
</div>
""", unsafe_allow_html=True)
