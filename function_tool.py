"""
Function Tools for Job Search
=============================
This module provides utility functions for job search operations using the FindSGJobs API.

Functions:
- search_jobs_api: Search for jobs with detailed information
- calculate_job_statistics: Get aggregated statistics about job market

Author: ADK Demo
Date: November 11, 2025
"""

import requests
from typing import Dict, Any
from bs4 import BeautifulSoup
import re


def search_jobs_api(keywords: str, page: int = 1, per_page_count: int = 10) -> Dict[str, Any]:
    """
    Search for jobs using the FindSGJobs API.

    Args:
        keywords: Search keywords (e.g., "cook", "engineer", "manager")
        page: Page number (default: 1)
        per_page_count: Number of results per page (default: 10, max: 20)

    Returns:
        dict: Structured job search results with success status
    """
    base_url = "https://www.findsgjobs.com/apis/job/search"

    params = {
        "page": page,
        "per_page_count": min(per_page_count, 20),
        "keywords": keywords
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        json_response = response.json()

        # Extract and structure job data
        jobs = []
        total_count = 0
        current_page = page
        total_pages = 0

        if "data" in json_response:
            data = json_response["data"]

            # Get pagination info
            if "pager" in data:
                pager = data["pager"]
                total_count = pager.get("record_count", 0)
                current_page = pager.get("page", page)
                total_pages = pager.get("page_count", 0)

            # Extract job details
            if "result" in data:
                for item in data["result"]:
                    job = item.get('job', {})
                    company = item.get('company', {})

                    # Extract salary information
                    salary_info = None
                    if not job.get('id_Job_Donotdisplaysalary', 0):
                        salary_range = job.get('Salaryrange', {}).get('caption')
                        if salary_range:
                            currency = job.get('id_Job_Currency', {}).get('caption', 'SGD')
                            interval = job.get('id_Job_Interval', {}).get('caption', 'Month')
                            salary_info = f"{currency} {salary_range} per {interval}"

                    # Extract description (clean HTML)
                    description = job.get('JobDescription', '')
                    if description:
                        soup = BeautifulSoup(description, 'html.parser')
                        plain_text = soup.get_text()
                        plain_text = re.sub(r'\n+', '\n', plain_text).strip()
                        description = plain_text[:500] + '...' if len(plain_text) > 500 else plain_text

                    job_info = {
                        "job_id": job.get('id', ''),
                        "title": job.get('Title', 'N/A'),
                        "company": company.get('CompanyName', 'N/A'),
                        "url": f"https://www.findsgjobs.com/job/{job.get('id', '')}" if job.get('id') else '',
                        "categories": [cat.get('caption', '') for cat in job.get('JobCategory', [])],
                        "employment_type": [et.get('caption', '') for et in job.get('EmploymentType', [])],
                        "location": [mrt.get('caption', '') for mrt in job.get('id_Job_NearestMRTStation', [])],
                        "salary": salary_info,
                        "experience": job.get('MinimumYearsofExperience', {}).get('caption', 'N/A'),
                        "education": job.get('MinimumEducationLevel', {}).get('caption', 'N/A'),
                        "position_level": job.get('id_Job_PositionLevel', {}).get('caption', 'N/A'),
                        "work_arrangement": job.get('id_Job_WorkArrangement', {}).get('caption', 'N/A'),
                        "skills": job.get('id_Job_Skills', []),
                        "posted_date": job.get('activation_date', 'N/A'),
                        "expires_date": job.get('expiration_date', 'N/A'),
                        "description": description
                    }

                    jobs.append(job_info)

        return {
            "success": True,
            "total_jobs": total_count,
            "current_page": current_page,
            "total_pages": total_pages,
            "results_on_page": len(jobs),
            "jobs": jobs
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def calculate_job_statistics(keywords: str, sample_size: int = 20) -> Dict[str, Any]:
    """
    Get statistical summary of job search results.

    Args:
        keywords: Search keywords
        sample_size: Number of jobs to analyze (max 20)

    Returns:
        dict: Job market statistics with success status
    """
    # Get job listings
    result = search_jobs_api(keywords, page=1, per_page_count=min(sample_size, 20))

    if not result.get("success"):
        return result

    jobs = result.get("jobs", [])
    total_jobs = result.get("total_jobs", 0)

    # Compute statistics
    category_counts = {}
    employment_type_counts = {}
    location_counts = {}
    education_counts = {}
    experience_counts = {}

    for job in jobs:
        # Count categories
        for category in job.get("categories", []):
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1

        # Count employment types
        for emp_type in job.get("employment_type", []):
            if emp_type:
                employment_type_counts[emp_type] = employment_type_counts.get(emp_type, 0) + 1

        # Count locations
        for location in job.get("location", []):
            if location:
                location_counts[location] = location_counts.get(location, 0) + 1

        # Count education levels
        education = job.get("education")
        if education and education != "N/A":
            education_counts[education] = education_counts.get(education, 0) + 1

        # Count experience levels
        experience = job.get("experience")
        if experience and experience != "N/A":
            experience_counts[experience] = experience_counts.get(experience, 0) + 1

    return {
        "success": True,
        "keyword": keywords,
        "total_jobs_in_market": total_jobs,
        "jobs_analyzed": len(jobs),
        "statistics": {
            "top_categories": dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "employment_types": employment_type_counts,
            "top_locations": dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "education_requirements": education_counts,
            "experience_requirements": experience_counts
        }
    }