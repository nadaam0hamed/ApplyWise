"""Prompt templates for document extraction chains."""

from langchain_core.prompts import PromptTemplate

EXTRACTION_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "document_type_label",
        "file_name",
        "document_text",
        "field_instructions",
        "format_instructions",
    ],
    template="""You are an expert document analyst for scholarship and university applications.

Extract structured information from the uploaded document below. BE PRECISE AND THOROUGH - extract all available information.

CRITICAL INSTRUCTIONS:
- Extract EVERY piece of information present in the document
- Look for exact matches first, then partial matches
- Use ALL available context clues
- For names: look for capitalized text, signature blocks, headers
- For dates: look for ANY date format (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, dates written as words)
- For numbers: look for numeric values in any format
- For addresses: look for street names, cities, countries
- For emails: look for @ symbols
- For phone numbers: look for number patterns
- DO NOT leave fields as null if the information is reasonably present
- BE AGGRESSIVE in finding information

## Document type
{document_type_label}

## File name
{file_name}

## Fields to extract
{field_instructions}

## Document text
{document_text}

{format_instructions}
""",
)


FIELD_INSTRUCTIONS: dict[str, str] = {
    "passport": (
        "- Full Name (look for any capitalized name, even if partial or in header)"
        "- Nationality (look for citizenship, country of origin, nationality field, or country name)"
        "- Passport Number (look for passport ID, document number, passport no., or similar)"
        "- Expiry Date (look for any date format: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, or date words)"
        "- Date of Birth (look for DOB, date of birth, born on, or birth date)"
        "- Place of Birth (look for place of birth, born in, or birthplace)"
    ),
    "academic_transcript": (
        "- University (look for institution name, school name, or university name)\n"
        "- Degree (look for B.Sc., M.Sc., PhD, Bachelor, Master, or degree title)\n"
        "- Major (look for field of study, specialization, or department)\n"
        "- GPA (look for GPA, grade average, CGPA, or numeric scores like 3.82/4.00)\n"
        "- Graduation Year (look for year of graduation, expected graduation, or any 4-digit year that could be graduation year)"
    ),
    "diploma": (
        "- University (look for institution name, school name, or university name)\n"
        "- Degree (look for B.Sc., M.Sc., PhD, Bachelor, Master, or degree title)\n"
        "- Major (look for field of study, specialization, or department)\n"
        "- Graduation Year (look for year of graduation, expected graduation, or any 4-digit year that could be graduation year)"
    ),
    "ielts_score": (
        "- Test type (IELTS - confirm it's IELTS)"
        "- Overall Score (look for total score, overall band, or main score)"
        "- Reading (look for reading section score)"
        "- Listening (look for listening section score)"
        "- Writing (look for writing section score)"
        "- Speaking (look for speaking section score)"
        "- Test Date (look for test date, exam date, or date taken)"
        "- Expiry Date (look for expiry date, valid until, or validity period)"
    ),
    "toefl_score": (
        "- Test type (TOEFL - confirm it's TOEFL)\n"
        "- Overall Score (look for total score, overall band, or main score)\n"
        "- Reading (look for reading section score)\n"
        "- Listening (look for listening section score)\n"
        "- Writing (look for writing section score)\n"
        "- Speaking (look for speaking section score)"
    ),
    "cv": (
        "- Full Name (look for name in header, personal info, or contact section)"
        "- Email (look for @ symbol in contact section)"
        "- Phone (look for phone number patterns in contact section)"
        "- LinkedIn (look for linkedin.com URLs or profile links)"
        "- GitHub (look for github.com URLs or profile links)"
        "- Skills (look for technical skills, soft skills, abilities, competencies - extract as list)"
        "- Experience (look for work experience, internships, jobs, roles with titles/dates - extract as list)"
        "- Projects (look for project names, academic projects, personal projects with technologies - extract as list)"
        "- Leadership (look for leadership roles, team lead, president, coordinator - extract as list)"
        "- Volunteering (look for volunteer work, community service, charity work - extract as list)"
        "- Education (look for education entries with universities, degrees, years - extract as list)"
        "- Nationality (look for citizenship, nationality, or country of origin if mentioned)"
    ),
    "statement_of_purpose": (
        "- Motivation (look for reasons for applying, why this program, personal motivation)\n"
        "- Career Goals (look for future plans, career objectives, professional goals)\n"
        "- Leadership (look for leadership examples, team activities, leadership roles mentioned)\n"
        "- Study Goals (look for academic goals, research interests, study objectives)"
    ),
    "motivation_letter": (
        "- Motivation (look for reasons for applying, why this program, personal motivation)\n"
        "- Career Goals (look for future plans, career objectives, professional goals)\n"
        "- Leadership (look for leadership examples, team activities, leadership roles mentioned)\n"
        "- Study Goals (look for academic goals, research interests, study objectives)"
    ),
    "letter_of_recommendation": (
        "- Referee (look for recommender name, author name, professor name)\n"
        "- Position (look for title, position, role, job title)\n"
        "- Organization (look for institution, company, university, organization name)\n"
        "- Strengths Mentioned (look for positive attributes, skills, qualities mentioned - extract as list)"
    ),
}


def get_extraction_prompt_template() -> PromptTemplate:
    """Return the shared extraction PromptTemplate used by DocumentExtractionChain."""
    return EXTRACTION_PROMPT_TEMPLATE


def get_field_instructions(document_type: str) -> str:
    return FIELD_INSTRUCTIONS.get(
        document_type,
        "Extract any relevant applicant information present in the document.",
    )
