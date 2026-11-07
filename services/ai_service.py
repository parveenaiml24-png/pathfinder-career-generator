import json
import re
from urllib.parse import quote_plus

import requests


def _demo_content(profile):
    name = profile.get("name") or "the student"
    degree = " ".join(
        part for part in (profile.get("degree"), profile.get("branch")) if part
    ) or "an undergraduate degree"
    domain = profile.get("domain") or "technology"
    goal = profile.get("career_goals") or f"build a career in {domain}"
    skills = _split(profile.get("technical_skills", "") + "," + profile.get("languages", ""))
    current_skills = skills[:6] or ["Problem solving", "Communication"]
    required = _required_skills(domain)
    missing = [skill for skill in required if skill.lower() not in {s.lower() for s in skills}]
    if not missing:
        missing = ["Build project depth", "Technical communication"]
    roles = _roles(domain)
    youtube_search = lambda topic: (
        "https://www.youtube.com/results?search_query="
        + quote_plus(f"{topic} tutorial for beginners")
    )

    return {
        "mode": "demo",
        "professional_summary": (
            f"{name} is a motivated {degree} student with a foundation in "
            f"{', '.join(current_skills[:3])}. Focused on {goal}, {name} is "
            f"building practical expertise for opportunities in {domain}."
        ),
        "career_objective": (
            f"To apply academic knowledge and growing skills in {domain} to "
            f"contribute to meaningful projects while progressing toward {goal}."
        ),
        "linkedin_about": (
            f"I'm {name}, a {degree} student interested in {domain}. My current "
            f"strengths include {', '.join(current_skills[:4])}. I am working "
            f"toward {goal} and enjoy learning through hands-on projects, "
            "collaboration, and thoughtful problem solving."
        ),
        "portfolio_intro": (
            f"Welcome to {name}'s portfolio — a collection of learning projects "
            f"and work exploring {domain}, grounded in {', '.join(current_skills[:3])}."
        ),
        "interview_intro": (
            f"Hello, I'm {name}. I'm studying {degree} and developing my skills "
            f"in {domain}. I have experience with {', '.join(current_skills[:3])}, "
            f"and my career goal is to {goal}. I'm excited to bring curiosity, "
            "a learning mindset, and practical problem solving to this role."
        ),
        "roles": roles,
        "career_paths": [
            f"{roles[0]} → Mid-level specialist → Senior {domain} professional",
            f"{roles[1]} → Project lead → Technical leader",
        ],
        "strengths": current_skills[:4],
        "improvements": missing[:4],
        "skill_analysis": {
            "current": current_skills,
            "required": required,
            "missing": missing,
            "proficiency": [
                {"skill": skill, "level": _level(profile.get("skill_level", "Beginner"))}
                for skill in current_skills[:5]
            ],
            "gap_percent": min(90, round(100 * len(missing) / max(len(required), 1))),
        },
        "roadmap": [
            {
                "week": "Weeks 1–2",
                "level": "Foundation",
                "focus": missing[0],
                "topics": ["Core concepts", "Guided practice", "Knowledge check"],
                "resource": "freeCodeCamp — free, self-paced tutorials",
                "url": "https://www.freecodecamp.org/learn/",
                "youtube_url": youtube_search(missing[0]),
                "schedule": ["Mon–Tue: learn the core concepts", "Wed–Thu: follow a guided tutorial", "Fri: practice and reflect"],
            },
            {
                "week": "Weeks 3–4",
                "level": "Build",
                "focus": missing[1] if len(missing) > 1 else "Project depth",
                "topics": ["Build a small project", "Use version control", "Write a project README"],
                "resource": "Google Career Certificates — course catalog",
                "url": "https://grow.google/certificates/",
                "youtube_url": youtube_search(missing[1] if len(missing) > 1 else domain),
                "schedule": ["Mon–Tue: plan a small project", "Wed–Thu: build and test", "Fri: document what you learned"],
            },
            {
                "week": "Weeks 5–6",
                "level": "Advance",
                "focus": "Interview and portfolio readiness",
                "topics": ["Practice role-specific questions", "Polish portfolio", "Request feedback"],
                "resource": "Microsoft Learn — free learning paths",
                "url": "https://learn.microsoft.com/training/",
                "youtube_url": youtube_search(f"{domain} interview preparation"),
                "schedule": ["Mon–Tue: practice role questions", "Wed–Thu: refine your portfolio", "Fri: ask for feedback and plan next steps"],
            },
        ],
        "interview": {
            "technical": [
                {
                    "question": f"What fundamentals are most important for a {domain} role?",
                    "answer": f"Start with core concepts such as {', '.join(required[:3])}. Explain how you have practiced them and connect your answer to a project or coursework example.",
                },
                {
                    "question": "Describe a challenging problem you solved.",
                    "answer": "Use the STAR structure: explain the situation, your task, the actions you took, and the measurable result. Be specific about what you learned.",
                },
                {
                    "question": "How do you approach learning an unfamiliar tool?",
                    "answer": "Clarify the goal, consult trusted documentation, build a small experiment, and validate the result. Mention how you would ask for feedback when blocked.",
                },
            ],
            "hr": [
                {
                    "question": "Tell me about yourself.",
                    "answer": f"Use the introduction above, then add one relevant project and why this opportunity aligns with your goal to {goal}.",
                },
                {
                    "question": "What is one area you are working to improve?",
                    "answer": f"Choose a genuine area such as {missing[0]}, describe your current learning plan, and share how you will measure progress.",
                },
            ],
            "coding": [
                "Write a function to count the frequency of each item in a list.",
                "Given a string, determine whether it is a palindrome while ignoring spaces and letter case.",
            ],
            "resume_questions": [
                {
                    "question": "Choose a project, coursework, or experience from your resume that best relates to this role. What was your contribution?",
                    "answer": "Describe the context, your specific responsibility, the steps you took, and the outcome. Be clear about what you did yourself and what you learned.",
                },
                {
                    "question": "What would you improve if you revisited one item on your resume?",
                    "answer": "Pick a real project or experience, explain one thoughtful improvement, and describe how you would measure whether that change worked.",
                },
            ],
        },
        "readiness_score": max(20, 100 - min(75, round(100 * len(missing) / max(len(required), 1)))),
    }


def _split(value):
    return [item.strip() for item in re.split(r"[,;\n]+", value or "") if item.strip()]


def _required_skills(domain):
    normalized = domain.lower()
    if "data" in normalized or "analytics" in normalized:
        return ["Python", "SQL", "Statistics", "Data visualization", "Machine learning"]
    if "web" in normalized or "software" in normalized:
        return ["Programming", "Data structures", "Git", "APIs", "Testing"]
    if "cyber" in normalized or "security" in normalized:
        return ["Networking", "Linux", "Python", "Security fundamentals", "Incident response"]
    if "design" in normalized or "ui" in normalized:
        return ["User research", "Wireframing", "Figma", "Accessibility", "Prototyping"]
    return ["Communication", "Problem solving", "Domain fundamentals", "Digital tools", "Teamwork"]


def _roles(domain):
    normalized = domain.lower()
    if "data" in normalized or "analytics" in normalized:
        return ["Data Analyst", "Junior Data Scientist", "Business Intelligence Analyst"]
    if "cyber" in normalized or "security" in normalized:
        return ["Security Analyst", "SOC Analyst", "Junior Penetration Tester"]
    if "design" in normalized or "ui" in normalized:
        return ["UI/UX Designer", "Product Designer", "UX Research Assistant"]
    return ["Junior Software Developer", "Web Developer", "QA Automation Engineer"]


def _level(value):
    return {"Beginner": 1, "Intermediate": 2, "Advanced": 3}.get(value, 1)


def generate_career_content(profile, api_key="", model="gemini-2.0-flash"):
    """Generate one consistent profile payload, falling back explicitly to demo mode."""
    if not api_key:
        return _demo_content(profile)

    prompt = f"""
Create a truthful, internally consistent career coaching profile using this student data:
{json.dumps(profile, ensure_ascii=False)}
Return ONLY valid JSON with exactly these keys:
professional_summary (string), career_objective (string), linkedin_about (string),
portfolio_intro (string), interview_intro (string), roles (array of 3 strings),
career_paths (array of 2 strings), strengths (array of strings), improvements (array of strings),
skill_analysis (object with current, required, missing arrays; proficiency array of objects
with skill and level integer 1-3; gap_percent integer 0-100),
roadmap (array of objects with week, level, focus, topics array, resource, url, youtube_url,
schedule array),
interview (object with technical, hr, and resume_questions arrays of question/answer objects
and coding array of strings),
readiness_score (integer 0-100).
Avoid invented experience or credentials. Keep recommendations practical and beginner-friendly.
"""
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    response = requests.post(
        endpoint,
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"responseMimeType": "application/json"}},
        timeout=45,
    )
    response.raise_for_status()
    body = response.json()
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("The AI provider returned an invalid career profile.") from error
    required = {
        "professional_summary", "career_objective", "linkedin_about", "portfolio_intro",
        "interview_intro", "roles", "career_paths", "strengths", "improvements",
        "skill_analysis", "roadmap", "interview", "readiness_score",
    }
    if not required.issubset(result):
        raise ValueError("The AI provider response is missing required career profile fields.")
    result["mode"] = "gemini"
    return result
