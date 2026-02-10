import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

st.set_page_config(page_title="Analisis Kontrak", layout="wide")
st.title("📊 Analisis Data Kontrak")

# ==================== FILE UPLOAD ====================
st.header("1️⃣ Upload Data")
uploaded_file = st.file_uploader("Upload CSV atau Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Load data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Display data info
    st.success(f"✅ Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # ==================== DATA CLEANING ====================
    # Convert dateCreated to datetime
    if 'dateCreated' in df.columns:
        df['dateCreated'] = pd.to_datetime(df['dateCreated'], errors='coerce')
    
    # ==================== SECTION 1: KONTRAK IN MULTIPLE MENUS ====================
    st.header("2️⃣ Kontrak Yang Masuk ke >1 Menu")
    
    # Expand rows jika ada multiple menu per kontrak
    if 'MENU' in df.columns and 'NO KONTRAK' in df.columns:
        # Split menu jika ada multiple
        df_expanded = df.copy()
        df_expanded['MENU'] = df_expanded['MENU'].fillna('')
        
        # Filter kontrak yang masuk ke multiple menu
        kontrak_counts = df.groupby('NO KONTRAK')['MENU'].nunique()
        multiple_menu_kontrak = kontrak_counts[kontrak_counts > 1].index.tolist()
        
        if len(multiple_menu_kontrak) > 0:
            df_multiple = df[df['NO KONTRAK'].isin(multiple_menu_kontrak)].copy()
            df_multiple = df_multiple[['NO KONTRAK', 'MENU', 'dateCreated', 'Produk']].sort_values(['NO KONTRAK', 'dateCreated'])
            
            st.subheader(f"Total: {len(multiple_menu_kontrak)} kontrak")
            st.dataframe(df_multiple, use_container_width=True)
            
            # Download button
            csv_multiple = df_multiple.to_csv(index=False)
            st.download_button(
                label="📥 Download Kontrak Multiple Menu (CSV)",
                data=csv_multiple,
                file_name="kontrak_multiple_menu.csv",
                mime="text/csv"
            )
        else:
            st.info("❌ Tidak ada kontrak yang masuk ke multiple menu")
    
    # ==================== SECTION 2: PIVOT 1 - BY LATEST DATE & STATUS ====================
    st.header("3️⃣ Pivot 1: Berdasarkan Status Terakhir (Latest Date Created)")
    
    if 'MENU' in df.columns and 'Produk' in df.columns and 'NO KONTRAK' in df.columns:
        # Get latest record per NO KONTRAK
        df_latest_date = df.sort_values('dateCreated', ascending=False).drop_duplicates(
            subset=['NO KONTRAK'], keep='first'
        )
        
        # Create pivot
        pivot1 = pd.crosstab(
            df_latest_date['MENU'],
            df_latest_date['Produk'],
            values='NO KONTRAK',
            aggfunc='count',
            margins=False
        ).fillna(0).astype(int)
        
        # Add total row and column
        pivot1['TOTAL'] = pivot1.sum(axis=1)
        pivot1.loc['TOTAL'] = pivot1.sum()
        
        st.subheader("Pivot Table: MENU (rows) vs PRODUK (columns) - Count Distinct NO KONTRAK")
        st.dataframe(pivot1, use_container_width=True)
        
        # Download
        csv_pivot1 = pivot1.to_csv()
        st.download_button(
            label="📥 Download Pivot 1 (CSV)",
            data=csv_pivot1,
            file_name="pivot1_by_latest_date.csv",
            mime="text/csv"
        )
    
    # ==================== SECTION 3: PIVOT 2 - BY LATEST STATUS ONLY ====================
    st.header("4️⃣ Pivot 2: Berdasarkan Status Terakhir (Latest Status, Ignore Date)")
    
    if 'STATUS' in df.columns and 'MENU' in df.columns and 'Produk' in df.columns:
        # Get latest status per NO KONTRAK (regardless of date)
        # Sort by STATUS to get consistent "latest" status
        df_latest_status = df.sort_values(['NO KONTRAK', 'STATUS'], ascending=[True, False]).drop_duplicates(
            subset=['NO KONTRAK'], keep='first'
        )
        
        # Create pivot
        pivot2 = pd.crosstab(
            df_latest_status['MENU'],
            df_latest_status['Produk'],
            values='NO KONTRAK',
            aggfunc='count',
            margins=False
        ).fillna(0).astype(int)
        
        # Add total row and column
        pivot2['TOTAL'] = pivot2.sum(axis=1)
        pivot2.loc['TOTAL'] = pivot2.sum()
        
        st.subheader("Pivot Table: MENU (rows) vs PRODUK (columns) - Count Distinct NO KONTRAK")
        st.dataframe(pivot2, use_container_width=True)
        
        # Download
        csv_pivot2 = pivot2.to_csv()
        st.download_button(
            label="📥 Download Pivot 2 (CSV)",
            data=csv_pivot2,
            file_name="pivot2_by_latest_status.csv",
            mime="text/csv"
        )
    
    # ==================== SECTION 4: TOP CABANG BY MENU ====================
    st.header("5️⃣ Top CABANG Untuk Menu Tertentu")
    
    if 'CABANG' in df.columns and 'NO KONTRAK' in df.columns:
        # Define target menus
        target_menus = ['Approval DD', 'Approval Direksi', 'Approval RM', 'Upload hasil Survey']
        
        col1, col2 = st.columns(2)
        
        for idx, menu in enumerate(target_menus):
            df_menu = df[df['MENU'] == menu].copy()
            
            if len(df_menu) > 0:
                # Count distinct NO KONTRAK per CABANG
                top_cabang = df_menu.groupby('CABANG')['NO KONTRAK'].nunique().sort_values(ascending=False).head(10)
                
                if idx % 2 == 0:
                    with col1:
                        st.subheader(f"📍 {menu}")
                        
                        if len(top_cabang) > 0:
                            fig_data = {
                                'CABANG': top_cabang.index,
                                'Jumlah NO KONTRAK': top_cabang.values
                            }
                            st.bar_chart(pd.DataFrame(fig_data).set_index('CABANG'))
                            
                            # Table
                            st.write(f"**Top 10 Cabang - {menu}**")
                            st.dataframe(top_cabang, use_container_width=True)
                        else:
                            st.warning(f"Tidak ada data untuk {menu}")
                else:
                    with col2:
                        st.subheader(f"📍 {menu}")
                        
                        if len(top_cabang) > 0:
                            fig_data = {
                                'CABANG': top_cabang.index,
                                'Jumlah NO KONTRAK': top_cabang.values
                            }
                            st.bar_chart(pd.DataFrame(fig_data).set_index('CABANG'))
                            
                            # Table
                            st.write(f"**Top 10 Cabang - {menu}**")
                            st.dataframe(top_cabang, use_container_width=True)
                        else:
                            st.warning(f"Tidak ada data untuk {menu}")
            else:
                if idx % 2 == 0:
                    with col1:
                        st.warning(f"Tidak ada data untuk menu: {menu}")
                else:
                    with col2:
                        st.warning(f"Tidak ada data untuk menu: {menu}")
    
    # ==================== SECTION 5: RAW DATA PREVIEW ====================
    st.header("6️⃣ Preview Data")
    
    st.subheader("Beberapa kolom penting:")
    important_cols = ['NO KONTRAK', 'dateCreated', 'Produk', 'CABANG', 'MENU', 'STATUS']
    available_cols = [col for col in important_cols if col in df.columns]
    
    st.dataframe(df[available_cols].head(20), use_container_width=True)

else:
    st.info("👆 Silakan upload file CSV atau Excel untuk memulai analisis")
