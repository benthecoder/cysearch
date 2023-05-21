import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from rich.progress import track


BASE_URL = "https://catalog.iastate.edu"
CATALOG_ENDPOINT = "/azcourses/"
SEMESTER_MAP = {"F.": "Fall", "S.": "Spring", "SS.": "Summer"}


def get_subject_links():
    response = requests.get(BASE_URL + CATALOG_ENDPOINT)
    soup = BeautifulSoup(response.content, "html.parser")
    div = soup.find(id="atozindex")
    links = div.find_all("a")
    subject_links = {link.text: BASE_URL + link.get("href") for link in links}
    return subject_links


def extract_credit_number(credit_block):
    credit_match = re.search(r"Cr\. (\d+-\d+|\d+)", credit_block)
    return credit_match[1] if credit_match else None


def extract_semester(credit_block):
    semesters = re.findall(r"(F\.|S\.|SS\.)+", credit_block)
    return (
        ", ".join([SEMESTER_MAP.get(sem) for sem in semesters]) if semesters else None
    )


def extract_prereq_and_info(prereq_block):
    if not prereq_block:
        return None, None
    prereq = prereq_block.find("em").get_text() if prereq_block.find("em") else None
    course_info = (
        prereq_block.get_text().replace(prereq, "")
        if prereq
        else prereq_block.get_text()
    )
    prereq = prereq.replace("Prereq:", "").strip() if prereq else None
    return prereq, course_info


def extract_course_data(block):
    course_name = block.find("div", class_="courseblocktitle").get_text(strip=True)
    # split course_name into course_code and course_title
    course_code_title = course_name.split(":")
    course_code = course_code_title[0]
    course_title = course_code_title[1].strip() if len(course_code_title) > 1 else None
    credit_block = block.find("p", class_="credits").get_text(strip=True)
    credit_number = extract_credit_number(credit_block)
    semester = extract_semester(credit_block)
    prereq, course_info = extract_prereq_and_info(block.find("p", class_="prereq"))

    return {
        "course_code": course_code,
        "course_title": course_title,
        "credit_number": credit_number,
        "semester": semester,
        "prereq": prereq,
        "course_info": course_info,
    }


def get_subject_courses(link):
    soup = BeautifulSoup(requests.get(link).content, "html.parser")
    course_blocks = soup.find_all("div", class_="courseblock")
    return [extract_course_data(block) for block in course_blocks]


def main():
    subject_links = get_subject_links()

    all_courses = []
    for subject, link in track(subject_links.items(), description="Scraping..."):
        subject_courses = get_subject_courses(link)
        for course in subject_courses:
            course["subject"] = subject
            course["link"] = link
        all_courses.extend(subject_courses)

    df = pd.DataFrame(all_courses)

    # move subject column to front
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]

    # filter empty course info
    df = df[df.course_info.notnull()]  # drops 811 courses

    df["combined"] = (
        df.subject + "; Title: " + df.course_title + "; Info: " + df.course_info
    )

    df.to_csv("data/courses.csv", index=False)


if __name__ == "__main__":
    main()
