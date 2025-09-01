# Application Constants

# File and path constants
MAX_SUBJECT_LENGTH_FOR_FILENAME = 15
RANDOM_ID_LENGTH = 4
PDF_EXTENSION = ".pdf"
TEX_EXTENSION = ".tex"

# LaTeX cleanup file extensions
LATEX_TEMP_EXTENSIONS = [
    ".aux",
    ".fdb_latexmk", 
    ".fls",
    ".log",
    ".out",
    ".tex",
]

# Database constants  
MAX_DOCUMENTS_PER_USER = 10
MAX_DOCUMENT_CONTENT_LENGTH = 5000

# S3 and file upload constants
S3_BUCKET_NAME = "armymarkdown"
PRESIGNED_URL_EXPIRY_SECONDS = 3600  # 1 hour

# Task polling constants
TASK_POLLING_INTERVAL_MS = 1000
TASK_MAX_POLLING_ATTEMPTS = 80
AVERAGE_TASK_COMPLETION_SECONDS = 10

# User validation constants
MIN_USERNAME_LENGTH = 6
MAX_USERNAME_LENGTH = 14
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 14

# Error messages
class ErrorMessages:
    GENERIC_ERROR = "An error occurred while processing your request. Please try again."
    PDF_GENERATION_FAILED = "PDF generation failed. Please check your memo format and try again."
    INVALID_MEMO_FORMAT = "Invalid memo format. Please check the required fields and syntax."
    FILE_UPLOAD_FAILED = "Failed to upload file to storage. Please try again."
    MEMO_PARSING_ERROR = "Error parsing memo content. Please check your formatting."
    DOCUMENT_SAVE_FAILED = "Failed to save document. Please try again."