import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO
import re

st.set_page_config(page_title="Product Info Extractor", layout="centered")

st.markdown("""
    <h2 style='background-color: #666666; color: white; padding: 12px; border-radius: 10px;'>🛍️ Product Info Extractor</h2>
""", unsafe_allow_html=True)

scripts = {
    "Info Extractor": "Extracts og:title, og:image, og:description and page <title>.",
    "Image Extractor": "Fetches og:image and formats as Google Sheets IMAGE formula.",
    "GearWrench ZIP Link": "Extracts downloadable ZIP image link from GearWrench.",
    "NZSBW Full Extractor": "Extracts title, image, description, and bullet point features.",
    "NZSBW Title Only": "Extracts only product title from a specific <h2> tag.",
    "Shiels Meta Details": "Extracts Shiels title and og:image:secure_url.",
    "Smokemart Extractor": "Extracts title and catalog product image from Smokemart.",
    "Mitre10 Description Extractor": "Extracts structured product description from Mitre10.",
    "Total Tools Price": "Extracts price using currency symbol from Total Tools.",
    "Super Cheap Auto (YouTube IDs)": "Extracts all embedded YouTube video IDs.",
    "Ramsau Pharma Image": "Extracts image from globalassets/commerce path.",
    "Shaver Shop Image": "Extracts one or more image URLs depending on page type.",
    "Toyworlds AU/NZ": "Extracts title, description, and images from toyworlds.com.au/.nz.",
    "Cleverpatch + YouTube": "Extracts OG data and embedded YouTube video ID.",
    "MikkoShoes Price": "Extracts current price from MikkoShoes men's product pages."
}

if "selected_script" not in st.session_state:
    st.session_state.selected_script = None

for script_name, script_desc in scripts.items():
    with st.container():
        if st.button(script_name):
            st.session_state.selected_script = script_name

    if st.session_state.selected_script == script_name:
        st.markdown(f"**Description:** {script_desc}")
        uploaded_file = st.file_uploader("📥 Upload Excel file with 'URL' and 'ProductID' columns", type=["xlsx"], key=script_name)
        run_button = st.button("▶️ Run the Script", key=f"run_{script_name}")

        if uploaded_file and run_button:
            df = pd.read_excel(uploaded_file)
            if not {'URL', 'ProductID'}.issubset(df.columns):
                st.error("Excel must contain 'URL' and 'ProductID' columns")
            else:
                output = []
                with st.spinner("🔍 Processing..."):
                    for idx, row in df.iterrows():
                        url = row['URL']
                        pid = row['ProductID']
                        result = {"ProductID": pid, "URL": url}

                        try:
                            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
                            html = r.text
                            soup = BeautifulSoup(html, 'html.parser')

                            if script_name == "Info Extractor":
                                result["Title"] = soup.find("meta", property="og:title")['content'] if soup.find("meta", property="og:title") else (soup.title.string if soup.title else "N/A")
                                result["Image"] = soup.find("meta", property="og:image")['content'] if soup.find("meta", property="og:image") else "N/A"
                                result["Description"] = soup.find("meta", property="og:description")['content'] if soup.find("meta", property="og:description") else "N/A"

                            elif script_name == "Image Extractor":
                                image = soup.find("meta", property="og:image")
                                result["ImageFormula"] = f'=IMAGE("{image["content"]}")' if image else "No image"

                            elif script_name == "GearWrench ZIP Link":
                                match = re.search(r'<span class="download-images-link">[\s\S]*?<a\s+href="([^"]+)"', html)
                                base = re.match(r'https://(www\.[^/]+)', url)
                                domain = f'https://{base[1]}' if base else ''
                                result["ZIP URL"] = domain + match.group(1) if match else "Not found"

                            elif script_name == "NZSBW Full Extractor":
                                title = soup.find("meta", property="og:title")
                                image = soup.find("meta", property="og:image")
                                desc = soup.find(attrs={"data-component-id": "product-description-content"})
                                features = soup.find_all("li", attrs={"data-component-id": re.compile("product-description-features-")})
                                result.update({
                                    "Title": title['content'] if title else "N/A",
                                    "Image": image['content'] if image else "N/A",
                                    "Description": desc.get_text(strip=True) if desc else "N/A",
                                    "Features": '\n'.join("• " + f.get_text(strip=True) for f in features)
                                })

                            elif script_name == "NZSBW Title Only":
                                match = re.search(r'<h2[^>]*data-component-id=["\']product-product-title["\'][^>]*>([^<]+)</h2>', html)
                                result["Title"] = match.group(1).strip() if match else "Not found"

                            elif script_name == "Shiels Meta Details":
                                title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html)
                                image = re.search(r'<meta[^>]+property=["\']og:image:secure_url["\'][^>]+content=["\']([^"\']+)', html)
                                result["Title"] = title.group(1) if title else "N/A"
                                result["Image"] = image.group(1) if image else "N/A"

                            elif script_name == "Smokemart Extractor":
                                title = soup.find("meta", property="og:title")
                                img = re.search(r'src=\"([^\"]*/media/catalog/product/[^\"]+)', html)
                                result["Title"] = title['content'] if title else "N/A"
                                result["Image"] = img.group(1).replace("&amp;", "&") if img else "N/A"

                            elif script_name == "Mitre10 Description Extractor":
                                match = re.search(r'<div[^>]*class=["\']value["\'][^>]*>([\s\S]*?)</div>', html)
                                if match:
                                    raw = match.group(1)
                                    bullets = ["• " + BeautifulSoup(li, 'html.parser').get_text(strip=True)
                                               for li in re.findall(r'<li>([\s\S]*?)</li>', raw)]
                                    clean = BeautifulSoup(raw, 'html.parser').get_text(" ", strip=True)
                                    result["Description"] = clean + ("\n" + "\n".join(bullets) if bullets else "")
                                else:
                                    result["Description"] = "Not found"

                            elif script_name == "Total Tools Price":
                                match = re.search(r'<span[^>]*class="currency-symbol"[^>]*>\$</span>\s*(\d+(\.\d{1,2})?)', html)
                                result["Price"] = f"${match.group(1)}" if match else "Not found"

                            elif script_name == "Super Cheap Auto (YouTube IDs)":
                                ids = set(re.findall(r'id="video-([a-zA-Z0-9_-]{11})"', html))
                                for i, vid in enumerate(ids):
                                    result[f"Video {i+1}"] = f"https://www.youtube.com/watch?v={vid}"
                                if not ids:
                                    result["Video"] = "No video found"

                            elif script_name == "Ramsau Pharma Image":
                                match = re.search(r'<img[^>]+src="(/globalassets/commerce/product/images/[^"?]+\.jpg)', html)
                                if match:
                                    base = re.match(r'^(https?://[^/]+)', url)
                                    result["Image"] = base.group(1) + match.group(1) if base else match.group(1)
                                else:
                                    result["Image"] = "Not found"

                            elif script_name == "Shaver Shop Image":
                                images = re.findall(r'class="primary-image[^"]*"[^>]+(?:data-src|src)="([^"]+)"', html)
                                for i, img in enumerate(images):
                                    result[f"Image {i+1}"] = img
                                if not images:
                                    result["Image"] = "No images found"

                            elif script_name == "Toyworlds AU/NZ":
                                title = re.search(r'<h1[^>]*class="product-title-details"[^>]*>(.*?)</h1>', html)
                                desc = re.search(r'<div[^>]+id="product-description"[\s\S]*?<div[^>]+class="tab-content attributedescription"[^>]*>([\s\S]*?)</div>', html)
                                anchors = re.findall(r'<a[^>]+data-variants[^>]+href="([^"]+)"', html)
                                imgs = ["https://www.toyworld.com.au" + p if not p.startswith("http") else p for p in anchors]
                                result["Title"] = BeautifulSoup(title.group(1), 'html.parser').get_text(strip=True) if title else "Not found"
                                result["Description"] = BeautifulSoup(desc.group(1), 'html.parser').get_text(strip=True) if desc else "Not found"
                                result["Images"] = ", ".join(imgs) if imgs else "No images"

                            elif script_name == "Cleverpatch + YouTube":
                                title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html)
                                ogurl = re.search(r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)', html)
                                image = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html)
                                yt = re.search(r'<iframe[^>]+src=["\'](?:https?:)?//www\.youtube\.com/embed/([^"?&]+)', html)
                                result["OG Title"] = title.group(1) if title else "❌"
                                result["OG URL"] = ogurl.group(1) if ogurl else "❌"
                                result["OG Image"] = image.group(1) if image else "❌"
                                result["YouTube"] = f"https://www.youtube.com/watch?v={yt.group(1)}" if yt else "❌"

                            elif script_name == "MikkoShoes Price":
                                match = re.search(r'id="ctl00_MainCentre_container_container_Content_31_StyleDetail1_lblCurrentPrice"[^>]*>\s*\$([\d,.]+)', html)
                                result["Price"] = f"${match.group(1)}" if match else "Not found"

                        except Exception as e:
                            result["Error"] = str(e)

                        output.append(result)

                df_out = pd.DataFrame(output)
                st.success("✅ Extraction complete")
                st.dataframe(df_out)
                csv = BytesIO()
                df_out.to_csv(csv, index=False)
                st.download_button("⬇️ Download CSV", data=csv.getvalue(), file_name="results.csv", mime="text/csv")
