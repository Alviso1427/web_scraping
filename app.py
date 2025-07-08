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

# Define script metadata
scripts = {
    "OG Metadata Extractor": "Extracts og:title, og:image, og:description, and <title> from each URL.",
    "Image to Drive Formatter": "Extracts og:image and formats it as a Google Sheets IMAGE formula.",
    "GearWrench ZIP Image Downloader": "Extracts the download link for a ZIP of product images.",
    "NZSBW Full Product Extractor": "Extracts title, image, description, and bullet list of features.",
    "Product Title Only (NZSBW)": "Extracts product title from <h2> tag with specific data-component-id.",
    "Shiels Title + Image Extractor": "Extracts product title and full-sized image from Shiels product pages.",
    "Smokemart Title + Image Extractor": "Extracts product title and image from Smokemart product pages.",
    "Mitre10 Structured Description Extractor": "Extracts structured description including bullet points from Mitre10.",
    "Total Tools Price Extractor": "Extracts price from Total Tools product pages."
}

selected_script = None

for script_name, script_desc in scripts.items():
    with st.container():
        if st.button(script_name):
            st.session_state["selected_script"] = script_name

    if st.session_state.get("selected_script") == script_name:
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

                            if script_name == "OG Metadata Extractor":
                                title = soup.find("meta", property="og:title")
                                image = soup.find("meta", property="og:image")
                                desc = soup.find("meta", property="og:description")
                                page_title = soup.title.string if soup.title else ""
                                result.update({
                                    "Title": title['content'] if title else page_title,
                                    "Image": image['content'] if image else "N/A",
                                    "Description": desc['content'] if desc else "N/A"
                                })

                            elif script_name == "Image to Drive Formatter":
                                image = soup.find("meta", property="og:image")
                                image_url = image['content'] if image else ""
                                formula = f'=IMAGE("{image_url}")' if image_url else "No image found"
                                result.update({"ImageFormula": formula})

                            elif script_name == "GearWrench ZIP Image Downloader":
                                match = re.search(r'<span class="download-images-link">[\s\S]*?<a\s+href="([^"]+)"', html)
                                base = re.match(r'https://(www\.[^/]+)', url)
                                domain = f'https://{base[1]}' if base else 'https://www.gearwrench.com.au'
                                dl_url = domain + match.group(1) if match else "Not found"
                                result.update({"ZIP Download URL": dl_url})

                            elif script_name == "NZSBW Full Product Extractor":
                                title = soup.find("meta", property="og:title")
                                image = soup.find("meta", property="og:image")
                                desc_tag = soup.find(attrs={"data-component-id": "product-description-content"})
                                feature_tags = soup.find_all("li", attrs={"data-component-id": re.compile("product-description-features-")})
                                features = "\n".join(["• " + tag.get_text(strip=True) for tag in feature_tags])
                                result.update({
                                    "Title": title['content'] if title else "N/A",
                                    "Image": image['content'] if image else "N/A",
                                    "Description": desc_tag.get_text(strip=True) if desc_tag else "N/A",
                                    "Features": features
                                })

                            elif script_name == "Product Title Only (NZSBW)":
                                match = re.search(r'<h2[^>]*data-component-id=["\']product-product-title["\'][^>]*>([^<]{1,500})</h2>', html)
                                result.update({"Title": match.group(1).strip() if match else "Title not found"})

                            elif script_name == "Shiels Title + Image Extractor":
                                title = soup.select_one(".product-title-container h1")
                                img = re.search(r'src=["\'](//www\.shiels\.com\.au/cdn/shop/[^"\']+_)[^"\']+\.jpg', html)
                                img_url = f"https:{img.group(1)}1220x1220_crop_center.jpg" if img else "Image not found"
                                result.update({
                                    "Title": title.get_text(strip=True) if title else "Title not found",
                                    "Image": img_url
                                })

                            elif script_name == "Smokemart Title + Image Extractor":
                                title = soup.find("meta", property="og:title")
                                img = re.search(r'src=\"([^\"]*/media/catalog/product/[^\"]+)\"', html)
                                result.update({
                                    "Title": title['content'] if title else "N/A",
                                    "Image": img.group(1).replace("&amp;", "&") if img else "N/A"
                                })

                            elif script_name == "Mitre10 Structured Description Extractor":
                                desc_match = re.search(r'<div[^>]*class=["\'][^"\']*product attribute description[^"\']*["\'][^>]*>\s*<div[^>]*class=["\']value["\'][^>]*>([\s\S]*?)</div>', html)
                                if desc_match:
                                    content = desc_match.group(1)
                                    ul_match = re.search(r'([\s\S]*?)<ul>([\s\S]*?)</ul>([\s\S]*)', content)
                                    parts = []
                                    if ul_match:
                                        parts.append(BeautifulSoup(ul_match.group(1), 'html.parser').get_text(strip=True))
                                        parts.extend(["• " + BeautifulSoup(li, 'html.parser').get_text(strip=True) for li in re.findall(r'<li>([\s\S]*?)</li>', ul_match.group(2))])
                                        parts.append(BeautifulSoup(ul_match.group(3), 'html.parser').get_text(strip=True))
                                    else:
                                        parts.append(BeautifulSoup(content, 'html.parser').get_text(strip=True))
                                    result["Description"] = "\n".join([p for p in parts if p])
                                else:
                                    result["Description"] = "⚠️ Description not found"

                            elif script_name == "Total Tools Price Extractor":
                                price_match = re.search(r'<span[^>]*class="currency-symbol"[^>]*>\$</span>\s*(\d+(\.\d{1,2})?)', html)
                                result["Price"] = f"${price_match.group(1)}" if price_match else "Price not found"

                        except Exception as e:
                            result["Error"] = str(e)

                        output.append(result)

                result_df = pd.DataFrame(output)
                st.success("✅ Script completed successfully!")
                st.dataframe(result_df)
                csv_buffer = BytesIO()
                result_df.to_csv(csv_buffer, index=False)
                st.download_button("⬇️ Download Results as CSV", data=csv_buffer.getvalue(), file_name="extracted_data.csv", mime="text/csv")
