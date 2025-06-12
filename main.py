import json  # make sure this is at the top of your script
import asyncio
import contextlib
from seleniumbase import SB
from config import CHECK_EVERY , DATA_LINK
from bs4 import BeautifulSoup

async def verify_solve():
    '''
        UNDER TEST !!!
    '''
    global sb
    '''
        Verifies if the human verification checkbox is present and clicks it.
        This function handles two different selectors for the checkbox.
    '''

    with contextlib.suppress(Exception):
        human_checkbox_selector1 = "#cf-stage > div.ctp-checkbox-container > label > input[type=checkbox]"
        human_checkbox_selector2 = "#challenge-stage > div > input"
        if human_checkbox := sb.find_element(human_checkbox_selector1):
            print("Found human checkbox 1, clicking it...")
            sb.click(human_checkbox)
        elif human_checkbox := sb.find_element(human_checkbox_selector2):
            print("Found human checkbox 2, clicking it...")
            sb.click(human_checkbox)
        sb.wait(1)
async def loginWithOutUserInf():
    '''
        Logs into the Ritaj system without user information.
        This function is a placeholder and does not perform any actions.
    '''
    global sb
    sb.open(DATA_LINK)


async def wait_for_page_load():
    '''
        Waits for the page to load by checking the title.
    '''
    global sb
    title = sb.get_title()

    while title != "Course Browser":
        print("Waiting for the page to load...")
        await verify_solve()
        title = sb.get_title()

async def extract_all_tables():
    ''''
        Extracts all course tables from the page and prints their details.
    '''
    global sb
    my_dec = {}
    sb.refresh()  # 🔄 Refresh the page before scraping
    sb.wait(3)

    tables = sb.find_elements("xpath", '//table[@cellspacing="0"]')

    # print(f"Found {len(tables)} tables with cellspacing=\"0\".\n")

    for table_index, table in enumerate(tables, start=1):
        try:
            table_html = table.get_attribute("outerHTML")
            soup = BeautifulSoup(table_html, "html.parser")

            # --- Course Info (First Row) ---
            course_row = soup.find("tr")
            if not course_row:
                continue

            cells = course_row.find_all("td")
            if len(cells) < 4:
                continue

            course_code = cells[0].text.strip()
            course_name_ar = cells[1].text.strip()
            course_name_en = cells[2].text.strip()
            study_language = cells[3].text.strip()

            # print(f"\n📘 Course: {course_code}")
            # print(f"   Arabic Name: {course_name_ar}")
            # print(f"   English Name: {course_name_en}")
            # print(f"   {study_language}")
            my_dec[course_code] = {
                "course_name_ar": course_name_ar,
                "course_name_en": course_name_en,
                "study_language": study_language,
                "sections": []
            }
            # --- Sections Info ---
            section_rows = soup.select("table")[1].find_all("tr")[1:]  # Skip header row
            for row in section_rows:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

                section_type = cols[0].text.strip()
                section_number = cols[1].text.strip()
                instructor = cols[2].text.strip()
                capacity = cols[3].text.strip()

                # Extract schedule info (days, time, location)
                schedule_table = cols[4].find("table")
                schedule_cells = schedule_table.find_all("td") if schedule_table else []
                if len(schedule_cells) >= 3:
                    days = schedule_cells[0].text.strip()
                    time = schedule_cells[1].text.strip()
                    location = schedule_cells[2].text.strip()
                else:
                    days, time, location = "N/A", "N/A", "N/A"

                # print(f"   ▶ Section {section_number} | {section_type}")
                # print(f"      Instructor: {instructor}")
                # print(f"      Students: {capacity}")
                # print(f"      Time: {days} @ {time}")
                # print(f"      Location: {location}")
                my_dec[course_code]["sections"].append({
                    "section_type": section_type,
                    "section_number": section_number,
                    "instructor": instructor,
                    "capacity": capacity,
                    "days": days,
                    "time": time,
                    "location": location
                })
            # print("\n" + "-"*50)
            # Save to data.json


        except Exception as e:
            print(f"❌ Error extracting Table {table_index}: {e}")
    return my_dec

async def main():
    global sb
    old_dec = None
    with SB(uc=True) as sb:
        await loginWithOutUserInf() # login without user information


        await wait_for_page_load()  # Wait for the page to load

        while True:
            try:
                dec = await extract_all_tables() # get the extracted data
                if old_dec is None:  # First run, no previous data to compare
                    print("First run, no previous data to compare.")
                    old_dec = dec
                    with open("data.json", "w", encoding="utf-8") as f:
                        json.dump(dec, f, ensure_ascii=False, indent=4)
                elif old_dec != dec: # if the data has changed
                    print("Data has changed, updating...")
                    with open("data.json", "w", encoding="utf-8") as f:
                        json.dump(dec, f, ensure_ascii=False, indent=4)
                else:
                    print("No changes detected.")
                await asyncio.sleep(CHECK_EVERY)
            except Exception as e:
                print(f"Error during extraction: {e}")
                break

if __name__ == '__main__':
    asyncio.run(main())

