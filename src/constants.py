"""
Curated vocabularies used by the ranker.

These lists were derived two ways:
  1. Close reading of job_description.md (the "absolutely need" / "nice to
     have" / "explicitly do NOT want" sections, and the "how to read between
     the lines" section).
  2. Profiling the actual candidates.jsonl skill/company/title vocabulary
     (see notebooks/ for the exploration) so the matching is grounded in
     what the dataset actually contains, not just guessed keywords.

Everything here is deliberately transparent and editable -- this is a
rule-based / feature-scored ranker, not a black box, which is also why it
runs in seconds on a laptop CPU with zero network calls.
"""

import datetime

TODAY = datetime.date(2026, 7, 2)  # module close date; used for recency calcs

# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

# Directly named in the JD "absolutely need" section, or a clear synonym of
# it, and confirmed present in the dataset's skill vocabulary.
CORE_SKILLS = {
    # embeddings / retrieval / LLM systems
    "embeddings", "sentence transformers", "hugging face transformers",
    "semantic search", "vector search", "information retrieval",
    "information retrieval systems", "rag", "llms", "fine-tuning llms",
    "prompt engineering", "langchain", "nlp", "natural language processing",
    "machine learning", "deep learning", "text encoders",
    "vector representations", "content matching", "search & discovery",
    "search backend", "search infrastructure", "indexing algorithms",
    "document processing",
    # vector db / hybrid search infra
    "pinecone", "faiss", "weaviate", "milvus", "qdrant", "elasticsearch",
    "opensearch", "pgvector", "haystack", "llamaindex", "bm25",
    # python / core ml stack
    "python", "pytorch", "tensorflow", "scikit-learn",
    # ranking / evaluation
    "learning to rank", "recommendation systems", "ranking systems",
    # fine-tuning
    "lora", "qlora", "peft", "model adaptation",
}

NICE_TO_HAVE_SKILLS = {
    "mlops", "kubeflow", "mlflow", "bentoml", "weights & biases",
    "data science", "statistical modeling", "time series", "forecasting",
    "feature engineering", "reinforcement learning",
    "open-source ml libraries", "workflow orchestration",
}

# CV / speech / robotics -- JD explicitly says people whose *primary*
# expertise is here, without NLP/IR exposure, are not a fit.
OFFTOPIC_SKILLS = {
    "computer vision", "opencv", "image classification", "object detection",
    "cnn", "yolo", "gans", "diffusion models", "asr", "speech recognition",
    "tts",
}

# Recent-only, wrapper-style AI skills. Not bad on their own, but per the
# JD: "AI experience consisting primarily of recent (<12mo) LangChain->
# OpenAI projects, without pre-LLM production ML" is a soft disqualifier.
SHALLOW_WRAPPER_SKILLS = {"langchain", "prompt engineering", "rag", "llms"}

PROFICIENCY_MULT = {
    "beginner": 0.5,
    "intermediate": 0.75,
    "advanced": 1.0,
    "expert": 1.15,
}

# ---------------------------------------------------------------------------
# Titles
# ---------------------------------------------------------------------------

CORE_TITLES = {
    "ml engineer", "junior ml engineer", "senior software engineer (ml)",
    "ai research engineer", "ai specialist", "ai engineer",
    "senior ai engineer", "lead ai engineer", "applied ml engineer",
    "senior applied scientist", "data scientist", "senior data scientist",
    "nlp engineer", "senior nlp engineer", "recommendation systems engineer",
    "search engineer", "machine learning engineer",
}

# Computer-vision-labelled titles are AI-adjacent but the JD explicitly
# flags CV-only backgrounds without NLP/IR as not a fit, so these get a
# lower base than CORE_TITLES.
CV_ONLY_TITLES = {"computer vision engineer"}

ADJACENT_TITLES = {
    "software engineer", "senior software engineer", "backend engineer",
    "data engineer", "senior data engineer", "analytics engineer",
    "data analyst", "full stack developer", "devops engineer",
    "cloud engineer", "mobile developer", "frontend engineer",
    "java developer", ".net developer", "qa engineer",
}

IRRELEVANT_TITLES = {
    "hr manager", "content writer", "business analyst", "sales executive",
    "customer support", "accountant", "civil engineer",
    "mechanical engineer", "graphic designer", "operations manager",
    "project manager", "marketing manager",
}

# ---------------------------------------------------------------------------
# Companies (63 unique employers observed in the dataset)
# ---------------------------------------------------------------------------

# IT-services / staffing-model firms -- JD explicitly flags "people who have
# only worked at consulting firms ... in their entire career" as not a fit.
CONSULTING_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "mindtree", "mphasis",
}

# Small, real-looking AI-native / AI-heavy product companies in the dataset.
AI_PRODUCT_COMPANIES = {
    "sarvam ai", "aganitha", "rephrase.ai", "niramai", "glance", "haptik",
    "wysa", "krutrim", "saarthi.ai", "verloop.io", "mad street den",
    "yellow.ai", "locobuzz", "observe.ai", "genpact ai",
}

# Elite / large-scale product companies -- rare in the pool, strong signal
# of having operated retrieval/ranking/search systems at real scale.
ELITE_PRODUCT_COMPANIES = {
    "meta", "google", "netflix", "amazon", "microsoft", "salesforce",
    "linkedin", "apple", "adobe", "uber",
}

# Other genuine (non-AI-specific) Indian/global product companies -- still
# "product company" experience rather than IT-services/consulting.
OTHER_PRODUCT_COMPANIES = {
    "swiggy", "cred", "razorpay", "zomato", "flipkart", "meesho", "paytm",
    "phonepe", "ola", "dream11", "policybazaar", "pharmeasy", "nykaa",
    "inmobi", "zoho", "freshworks", "byju's", "upgrad", "unacademy",
    "vedantu",
}

# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

PRIMARY_LOCATIONS = {"pune", "noida"}
TIER1_INDIA_LOCATIONS = {
    "hyderabad", "mumbai", "delhi", "gurgaon", "bangalore", "chennai",
}

# ---------------------------------------------------------------------------
# Free-text evidence phrases (searched over headline+summary+career
# descriptions) that indicate real production / at-scale engineering, as
# opposed to toy-project or purely-academic language.
# ---------------------------------------------------------------------------

PRODUCTION_EVIDENCE_PHRASES = [
    "production", "deployed", "at scale", "scaled to", "real-time",
    "real time", "latency", "shipped", "launched", "a/b test", "ab test",
    "online experiment", "recommendation system", "search system",
    "ranking system", "retrieval system", "embedding", "vector index",
    "hybrid search", "index refresh", "recruiter-facing", "millions of",
    "throughput", "p99", "sla",
]

PURE_RESEARCH_PHRASES = [
    "postdoc", "post-doctoral", "phd thesis", "research scientist",
    "academic lab", "published a paper", "peer-reviewed",
]

PRODUCTION_DEPLOYMENT_PHRASES = [
    "production", "deployed", "shipped", "launched", "at scale",
    "real users", "real-time", "throughput", "latency",
]

# Rough cut-off: dataset dates before this are treated as "pre-LLM-era".
PRE_LLM_ERA_CUTOFF = datetime.date(2023, 1, 1)
