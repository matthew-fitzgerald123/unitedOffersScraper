from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import csv

def extract_adurl(link):
    match = re.search(r'adurl=([^&]+)', link)
    return match.group(1) if match else link

def process_iframe_contents(iframe_data):
    data = []
    frame_data = {}
    inside_frame = False
    link = ''

    for line in iframe_data.split('\n'):
        if line.startswith('Switching to iframe'):
            if frame_data:
                frame_data['Link'] = link
                data.append(frame_data)
            frame_data = {}
            inside_frame = True
            link = ''
        elif inside_frame:
            if 'Content:' in line or 'Ad' in line:
                continue
            if 'Link:' in line:
                link = extract_adurl(line.split('Link: ')[1].strip())
            else:
                if 'Title' not in frame_data:
                    frame_data['Title'] = line.strip()
                elif 'Description' not in frame_data:
                    frame_data['Description'] = line.strip()
                elif 'Company' not in frame_data:
                    frame_data['Company'] = line.strip()

    if frame_data:
        frame_data['Link'] = link
        data.append(frame_data)

    return data

driver_path = 'chromedriver/mac_arm-127.0.6533.73/chromedriver-mac-arm64/chromedriver'
service = Service(executable_path=driver_path)
chrome_options = Options()
chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driver = webdriver.Chrome(service=service, options=chrome_options)
iframe_output = ""

try:
    driver.get("https://www.united.com/en/us/fly/mileageplus/mp-offers.html")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, 'iframe'))
    )
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    print(f"Total iframes found: {len(iframes)}")
    for index, iframe in enumerate(iframes):
        print(f"Iframe {index}: {iframe.get_attribute('id')} {iframe.get_attribute('src')}")

    for index in range(1, len(iframes)):
        try:
            iframe = iframes[index]
            iframe_output += f"Switching to iframe {index}: {iframe.get_attribute('id')} {iframe.get_attribute('src')}\n"
            driver.switch_to.frame(iframe)
            ad_contents = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div'))
            )

            for ad in ad_contents:
                ad_text = ad.text.strip()
                if ad_text:
                    links = ad.find_elements(By.TAG_NAME, 'a')
                    link = links[0].get_attribute('href') if links else 'No link found'
                    iframe_output += f"Iframe {index} Content:\n{ad_text}\nLink: {link}\n{'-'*50}\n"

            driver.switch_to.default_content()

        except Exception as e:
            print(f"Error processing iframe {index}: {e}")
            driver.switch_to.default_content()

finally:
    driver.quit()

data = process_iframe_contents(iframe_output)

# formatted output
output_file = 'iframe_contents_cleaned.csv'
with open(output_file, 'w', newline='') as csvfile:
    fieldnames = ['Company', 'Title', 'Description', 'Link']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for entry in data:
        writer.writerow(entry)

print(f"Data written to {output_file}")
