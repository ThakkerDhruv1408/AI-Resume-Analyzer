import os
import shutil
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_ollama import OllamaLLM, OllamaEmbeddings , ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from chromadb import PersistentClient


# 1. Setup LLM and Embeddings
llm = OllamaLLM(model="mistral")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

persist_directory = "./chroma_db"


# 2. Load and process the resume
def load_resume(resume_path):
    """Loads and extracts text from a resume PDF."""
    loader = UnstructuredPDFLoader(file_path=resume_path)
    resume_text = "\n".join([doc.page_content for doc in loader.load()])
    return resume_text

#3 Create vector databases
def create_vector_db(resume_text):
    """Stores resume and job description embeddings in ChromaDB for retrieval."""
    

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100)
    
    # Split texts
    resume_chunks = text_splitter.split_text(resume_text)
    
    # Convert to document format
    resume_docs = [{"page_content": chunk} for chunk in resume_chunks]

    try:
        # Create vector stores
        resume_db = Chroma.from_texts(
            texts=[doc["page_content"] for doc in resume_docs],
            embedding=embeddings,
            collection_name="resume",
        )


    except ValueError as e:
        print("⚠️ Error initializing ChromaDB:", str(e))
        print("🔄 Trying to reset ChromaDB storage...")
        return create_vector_db(resume_text)

    return resume_db


# 4. Retrieve relevant resume sections based on job description
def retrieve_relevant_resume_sections(resume_db, job_description):
    """Retrieves the most relevant parts of the resume based on job description embeddings."""
    try:
        relevant_resume_parts = resume_db.similarity_search(query=job_description, k=5)
        return "\n".join([doc.page_content for doc in relevant_resume_parts])
    except ValueError as e:
        print("⚠️ Error retrieving from ChromaDB:", str(e))
        print("🔄 Attempting to reinitialize ChromaDB...")
        return ""



# 5. Define comparison prompt
analysis_template = """ 
Compare the candidate's resume with the job description. Provide a detailed JSON response structured as follows:
{{
    "percentage_fit": <calculated_match_percentage>,
    "analysis_points": [
        {{
            "category": "<e.g., Skills, Certifications, Experience>",
            "title": "<Specific Match>",
            "description": "<How it aligns>"
        }}
    ],
    "areas_for_improvement": [
        "<Specific improvement 1>",
        "<Specific improvement 2>"
    ]
}}

Focus on:
1. Matching skills, certifications, and experience.
2. Relevant projects or accomplishments.
3. Missing qualifications or expertise areas.

Relevant Resume Sections:
{resume}

Job Description:
{job_description}
"""


# 6. Run the comparison analysis
def analyze_resume_job_fit(resume_path, job_description):
    """Compares the most relevant sections of the resume with the job description and returns a structured response."""
    
    # Load resume text
    resume_text = load_resume(resume_path)

    # Create vector databases
    resume_db, _ = create_vector_db(resume_text)

    # Retrieve the most relevant resume sections
    relevant_resume_text = retrieve_relevant_resume_sections(resume_db, job_description)

    # Prepare the prompt
    prompt = ChatPromptTemplate.from_template(analysis_template).format(
        resume=relevant_resume_text, job_description=job_description
    )

    # Get LLM response
    result = llm.invoke(prompt)
    shutil.rmtree("./uploads")

    return result

def findResume():
    folder_path = './uploads'

    files = os.listdir(folder_path)
    if files:
        file_path = os.path.join(folder_path, files[0])
    return file_path

# Example usage
# if __name__ == "__main__":
#     resume_path = "<Resume Path>"
#     job_path = """We are seeking a Junior Blockchain Developer with a B.Tech in Computer Science (Blockchain specialization) and proven skills in Solidity, Python, and JavaScript. The ideal candidate should have experience with Web3, DeFi, Ethereum development, smart contracts, and DApps development. Key requirements include knowledge of blockchain integration with IoT, supply chain solutions, and hands-on experience with tools like Remix IDE and Foundry. The candidate should be familiar with Next.js, Tailwind CSS, and have practical experience in developing decentralized applications with MetaMask integration. A minimum CGPA of 7.5 and certifications in Blockchain Basics and Smart Contracts are required, along with understanding of cryptography, Bitcoin fundamentals, IPFS, and DAOs."""
    
#     result = analyze_resume_job_fit(resume_path, job_path)
#     print(result)
