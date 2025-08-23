import streamlit as st
import pandas as pd
from utils.email_discovery import EmailDiscovery
from utils.email_validator import EmailValidator
import time


def show_email_discovery():
    st.header("🔍 Email Discovery")
    st.markdown("Temukan alamat email dari domain website seperti hunter.io")
    
    # Initialize session state for discovery results
    if 'discovery_results' not in st.session_state:
        st.session_state.discovery_results = None
    if 'pattern_verification' not in st.session_state:
        st.session_state.pattern_verification = None
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Domain input form
        with st.form("domain_discovery_form"):
            domain_input = st.text_input(
                "Masukkan domain website:",
                placeholder="contoh: github.com atau https://github.com"
            )
            
            col_settings1, col_settings2 = st.columns(2)
            with col_settings1:
                max_pages = st.slider("Maksimal halaman untuk di-scan:", 1, 10, 5)
            
            with col_settings2:
                verify_patterns = st.checkbox("Verifikasi pola email umum", value=True)
            
            submitted = st.form_submit_button("🔍 Mulai Pencarian", type="primary")
            
            if submitted and domain_input:
                discovery = EmailDiscovery()
                validator = EmailValidator() if verify_patterns else None
                
                with st.spinner(f"Sedang mencari email di {domain_input}..."):
                    # Discover emails
                    result = discovery.discover_emails_from_domain(domain_input, max_pages)
                
                if result['status'] == 'domain_unreachable':
                    st.error(f"❌ Domain {domain_input} tidak dapat diakses")
                    if 'error' in result:
                        st.error(f"Error: {result['error']}")
                    st.session_state.discovery_results = None
                    st.session_state.pattern_verification = None
                else:
                    # Store results in session state
                    st.session_state.discovery_results = result
                    
                    # Handle pattern verification
                    if result['common_patterns'] and verify_patterns:
                        with st.spinner("Memverifikasi pola email umum..."):
                            pattern_results = discovery.verify_email_patterns(
                                result['common_patterns'], 
                                validator
                            )
                        st.session_state.pattern_verification = pattern_results
                    else:
                        st.session_state.pattern_verification = None
                    
                    st.success(f"✅ Pencarian selesai untuk {result['domain']}")
            
            elif submitted and not domain_input:
                st.warning("⚠️ Silakan masukkan domain website")
        
        # Display results outside the form
        if st.session_state.discovery_results:
            result = st.session_state.discovery_results
            
            # Summary metrics
            col_m1, col_m2, col_m3 = st.columns(3)
            
            with col_m1:
                st.metric("Email Ditemukan", len(result['emails_found']))
            
            with col_m2:
                st.metric("Halaman Di-scan", len(result['pages_scanned']))
            
            with col_m3:
                st.metric("Pola Email", len(result['common_patterns']))
            
            # Discovered emails
            if result['emails_found']:
                st.subheader("📧 Email yang Ditemukan")
                
                emails_df = pd.DataFrame({
                    'Email': result['emails_found'],
                    'Status': ['Ditemukan'] * len(result['emails_found'])
                })
                
                st.dataframe(emails_df, use_container_width=True)
                
                # Export discovered emails (outside form)
                emails_csv = '\n'.join(result['emails_found'])
                domain_clean = result['domain'].replace('https://', '').replace('http://', '').replace('/', '_')
                st.download_button(
                    label="📥 Download Email yang Ditemukan",
                    data=emails_csv,
                    file_name=f"discovered_emails_{domain_clean}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_discovered"
                )
            else:
                st.info("🔍 Tidak ada email yang ditemukan di halaman website")
            
            # Pattern verification results
            if st.session_state.pattern_verification:
                pattern_results = st.session_state.pattern_verification
                st.subheader("🎯 Verifikasi Pola Email Umum")
                
                if pattern_results['valid_emails']:
                    st.success(f"✅ {len(pattern_results['valid_emails'])} pola email valid ditemukan!")
                    
                    valid_patterns_df = pd.DataFrame([
                        {
                            'Email': r['email'],
                            'Status': 'Valid' if r['is_valid'] else 'Invalid',
                            'Confidence': f"{r['confidence']}%"
                        }
                        for r in pattern_results['valid_emails']
                    ])
                    
                    st.dataframe(valid_patterns_df, use_container_width=True)
                    
                    # Export valid patterns (outside form)
                    valid_emails_text = '\n'.join([r['email'] for r in pattern_results['valid_emails']])
                    domain_clean = result['domain'].replace('https://', '').replace('http://', '').replace('/', '_')
                    st.download_button(
                        label="📥 Download Email Valid",
                        data=valid_emails_text,
                        file_name=f"valid_emails_{domain_clean}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key="download_valid_patterns"
                    )
                else:
                    st.info("ℹ️ Tidak ada pola email umum yang valid ditemukan")
            
            elif result['common_patterns'] and st.session_state.pattern_verification is None:
                st.subheader("💡 Pola Email Umum (Belum Diverifikasi)")
                
                patterns_df = pd.DataFrame({
                    'Email Pattern': result['common_patterns'],
                    'Status': ['Belum Diverifikasi'] * len(result['common_patterns'])
                })
                
                st.dataframe(patterns_df, use_container_width=True)
                st.info("💡 Centang 'Verifikasi pola email umum' untuk memvalidasi email ini")
            
            # Scanned pages
            if result['pages_scanned']:
                with st.expander("📄 Halaman yang Di-scan"):
                    for page in result['pages_scanned']:
                        st.write(f"• {page}")
    
    with col2:
        st.markdown("### Cara Kerja")
        st.info("""
        **Fitur Email Discovery:**
        
        🌐 **Scan Website**
        - Menjelajahi halaman utama
        - Halaman contact, about, team
        - Mengekstrak email otomatis
        
        🎯 **Pola Email Umum**
        - info@domain.com
        - contact@domain.com
        - sales@domain.com
        - support@domain.com
        
        ✅ **Verifikasi Real-time**
        - Validasi syntax email
        - Cek keberadaan domain
        - Verifikasi SMTP server
        """)
        
        st.markdown("### Tips Penggunaan")
        st.success("""
        💡 **Tips:**
        
        • Gunakan domain lengkap (tanpa 'www')
        • Scan maksimal 5-10 halaman
        • Aktifkan verifikasi untuk hasil akurat
        • Unduh hasil untuk penggunaan lanjutan
        """)


if __name__ == "__main__":
    show_email_discovery()