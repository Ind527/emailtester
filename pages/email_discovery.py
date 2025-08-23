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
        # Domain input method selection
        input_method = st.radio(
            "Pilih metode input domain:",
            ["📝 Single Domain", "📄 Multiple Domains (Text)", "📁 Upload CSV File"],
            horizontal=True
        )
        
        # Domain input form
        with st.form("domain_discovery_form"):
            domains_to_scan = []
            
            if input_method == "📝 Single Domain":
                domain_input = st.text_input(
                    "Masukkan domain website:",
                    placeholder="contoh: github.com atau https://github.com"
                )
                if domain_input:
                    domains_to_scan = [domain_input.strip()]
            
            elif input_method == "📄 Multiple Domains (Text)":
                domains_text = st.text_area(
                    "Masukkan domain (satu per baris):",
                    height=150,
                    placeholder="github.com\nfacebook.com\ngoogle.com\n..."
                )
                if domains_text:
                    domains_to_scan = [domain.strip() for domain in domains_text.split('\n') if domain.strip()]
            
            elif input_method == "📁 Upload CSV File":
                csv_file = st.file_uploader("Upload CSV dengan domain", type=['csv'], key="domain_csv")
                if csv_file:
                    try:
                        df = pd.read_csv(csv_file)
                        domain_col = st.selectbox("Pilih kolom domain:", df.columns)
                        if domain_col:
                            domains_to_scan = df[domain_col].dropna().tolist()
                            st.info(f"Loaded {len(domains_to_scan)} domain untuk di-scan")
                    except Exception as e:
                        st.error(f"Error membaca CSV: {str(e)}")
            
            # Show preview of domains
            if domains_to_scan:
                with st.expander("Preview domain yang akan di-scan", expanded=False):
                    st.write(domains_to_scan[:10])  # Show first 10
                    if len(domains_to_scan) > 10:
                        st.write(f"... dan {len(domains_to_scan) - 10} domain lainnya")
            
            col_settings1, col_settings2 = st.columns(2)
            with col_settings1:
                max_pages = st.slider("Maksimal halaman untuk di-scan:", 1, 10, 5)
            
            with col_settings2:
                verify_patterns = st.checkbox("Verifikasi pola email umum", value=True)
            
            submitted = st.form_submit_button("🔍 Mulai Pencarian", type="primary")
            
            if submitted and domains_to_scan:
                discovery = EmailDiscovery()
                validator = EmailValidator() if verify_patterns else None
                
                # Process multiple domains
                all_results = []
                all_emails_found = set()
                all_pattern_results = []
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, domain in enumerate(domains_to_scan):
                    status_text.text(f"Memproses domain {i+1}/{len(domains_to_scan)}: {domain}")
                    
                    with st.spinner(f"Sedang mencari email di {domain}..."):
                        result = discovery.discover_emails_from_domain(domain, max_pages)
                    
                    if result['status'] == 'domain_unreachable':
                        st.warning(f"⚠️ Domain {domain} tidak dapat diakses: {result.get('error', 'Unknown error')}")
                        result['processed'] = False
                    else:
                        result['processed'] = True
                        all_emails_found.update(result['emails_found'])
                        
                        # Handle pattern verification for this domain
                        if result['common_patterns'] and verify_patterns:
                            pattern_results = discovery.verify_email_patterns(
                                result['common_patterns'], 
                                validator
                            )
                            result['pattern_verification'] = pattern_results
                            if pattern_results['valid_emails']:
                                all_pattern_results.extend(pattern_results['valid_emails'])
                    
                    all_results.append(result)
                    
                    # Update progress
                    progress = (i + 1) / len(domains_to_scan)
                    progress_bar.progress(progress)
                    
                    # Small delay between domains to be respectful
                    if i < len(domains_to_scan) - 1:
                        time.sleep(2)
                
                # Store results in session state
                st.session_state.discovery_results = {
                    'all_results': all_results,
                    'all_emails_found': list(all_emails_found),
                    'all_pattern_results': all_pattern_results,
                    'total_domains': len(domains_to_scan),
                    'successful_domains': sum(1 for r in all_results if r.get('processed', False))
                }
                
                status_text.success(f"✅ Selesai memproses {len(domains_to_scan)} domain!")
                progress_bar.progress(1.0)
            
            elif submitted and not domains_to_scan:
                st.warning("⚠️ Silakan masukkan domain website")
        
        # Display results outside the form
        if st.session_state.discovery_results:
            results_data = st.session_state.discovery_results
            
            # Check if this is single domain (old format) or multiple domains (new format)
            if 'all_results' in results_data:
                # Multiple domains format
                st.subheader("📊 Ringkasan Hasil")
                
                # Summary metrics
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.metric("Total Domain", results_data['total_domains'])
                
                with col_m2:
                    st.metric("Domain Berhasil", results_data['successful_domains'])
                
                with col_m3:
                    st.metric("Total Email Ditemukan", len(results_data['all_emails_found']))
                
                with col_m4:
                    st.metric("Email Valid Pattern", len(results_data['all_pattern_results']))
                
                # All discovered emails
                if results_data['all_emails_found']:
                    st.subheader("📧 Semua Email yang Ditemukan")
                    
                    # Create detailed DataFrame with source domain
                    detailed_emails = []
                    for result in results_data['all_results']:
                        if result.get('processed') and result['emails_found']:
                            for email in result['emails_found']:
                                detailed_emails.append({
                                    'Email': email,
                                    'Domain Source': result['domain'],
                                    'Status': 'Ditemukan'
                                })
                    
                    if detailed_emails:
                        emails_df = pd.DataFrame(detailed_emails)
                        st.dataframe(emails_df, use_container_width=True)
                        
                        # Export all discovered emails
                        all_emails_text = '\n'.join(results_data['all_emails_found'])
                        st.download_button(
                            label="📥 Download Semua Email yang Ditemukan",
                            data=all_emails_text,
                            file_name=f"all_discovered_emails_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            key="download_all_discovered"
                        )
                
                # All valid pattern emails
                if results_data['all_pattern_results']:
                    st.subheader("🎯 Semua Email Valid Pattern")
                    
                    valid_patterns_df = pd.DataFrame([
                        {
                            'Email': r['email'],
                            'Status': 'Valid' if r['is_valid'] else 'Invalid',
                            'Confidence': f"{r['confidence']}%"
                        }
                        for r in results_data['all_pattern_results']
                    ])
                    
                    st.dataframe(valid_patterns_df, use_container_width=True)
                    
                    # Export all valid patterns
                    valid_emails_text = '\n'.join([r['email'] for r in results_data['all_pattern_results']])
                    st.download_button(
                        label="📥 Download Semua Email Valid Pattern",
                        data=valid_emails_text,
                        file_name=f"all_valid_pattern_emails_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key="download_all_valid_patterns"
                    )
                
                # Per-domain breakdown
                st.subheader("🌐 Detail per Domain")
                
                for i, result in enumerate(results_data['all_results']):
                    with st.expander(f"Domain: {result['domain']} ({'✅ Berhasil' if result.get('processed') else '❌ Gagal'})", expanded=False):
                        if result.get('processed'):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Email Ditemukan", len(result['emails_found']))
                            
                            with col2:
                                st.metric("Halaman Di-scan", len(result['pages_scanned']))
                            
                            with col3:
                                st.metric("Pola Email", len(result['common_patterns']))
                            
                            if result['emails_found']:
                                st.markdown("**Email yang Ditemukan:**")
                                for email in result['emails_found']:
                                    st.write(f"• {email}")
                            
                            if result.get('pattern_verification') and result['pattern_verification']['valid_emails']:
                                st.markdown("**Email Valid Pattern:**")
                                for pattern in result['pattern_verification']['valid_emails']:
                                    st.write(f"• {pattern['email']} ({pattern['confidence']}% confidence)")
                            
                            if result['pages_scanned']:
                                st.markdown("**Halaman yang Di-scan:**")
                                for page in result['pages_scanned']:
                                    st.write(f"• {page}")
                        else:
                            st.error(f"Domain tidak dapat diakses: {result.get('error', 'Unknown error')}")
            
            else:
                # Single domain format (backward compatibility)
                result = results_data
                
                # Summary metrics
                col_m1, col_m2, col_m3 = st.columns(3)
                
                with col_m1:
                    st.metric("Email Ditemukan", len(result['emails_found']))
                
                with col_m2:
                    st.metric("Halaman Di-scan", len(result['pages_scanned']))
                
                with col_m3:
                    st.metric("Pola Email", len(result['common_patterns']))
                
                # [Rest of single domain display logic remains the same...]
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