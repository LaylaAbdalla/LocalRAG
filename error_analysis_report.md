# Error Analysis Report

RAG systems are not perfect and often make mistakes, especially with documents full of rules like university handbooks. To test our system's accuracy, we asked it tricky questions (edge cases). 

Below are three examples where the system failed, along with a simple explanation of why.

---

### Edge Case 1: Too Strict to Make Logical Guesses (LLM Failure)

**The Query:**  
> *"Under what specific conditions is a student not allowed to register for the Data Security course?"*

**The Retrieved Context:**  
The system found the right course info, which said:  
> *"co-requisite: CIS365. Computer networks"*

**The System's Output:**  
> *"I don't know."*

**Why it Failed:**  
The system prompt strictly told the AI: *"If you do not know the answer... say 'I don't know'."* Because of this strict rule, the AI refused to make an obvious logical guess. Even though a "co-requisite" clearly means you are "not allowed" to take the class without it, the AI didn't see the exact words "not allowed" in the text, so it gave up. 

---

### Edge Case 2: Broken Context & Missing the Big Picture (Pipeline Failure)

**The Query:**  
> *"If I fail 'Introduction to Programming' in my first semester, what is the exact list of courses I will be blocked from taking in my third semester?"*

**The Retrieved Context:**  
The system pulled 5 scattered paragraphs. One critical paragraph was cut off mid-sentence:  
> *"...search, and probabilistic search algorithms) b. co-requisite: CIS150. Structured Programming c. required, elective, or selected elective: Required 1. Course number and name: CIS353 Operating Systems..."*

**The System's Output:**  
> *"I don't know."*

**Why it Failed:**  
This failed for two simple reasons:
1. **Bad Text Splitting (Chunking):** The system cuts documents into chunks of 500 characters. Here, it cut a sentence right in half, separating a course from its prerequisite rule. The AI couldn't read the broken sentence properly.
2. **Can't Connect the Dots:** The question requires the AI to find a first-semester course, see what requires it, and check if those are third-semester courses. RAG systems look for single paragraphs that match the question; they struggle to connect clues across multiple different paragraphs.

---

### Edge Case 3: Distracted by Common Words (Retrieval Failure)

**The Query:**  
> *"Can a student host be responsible for policy violations committed by their on-campus guest?"*

**The Expected Answer (Hidden in the document):**  
> *"Student hosts are additionally responsible for any policy violations of their on-campus guests"*

**The Retrieved Context:**  
The search engine grabbed three paragraphs mentioning *"guests"*, *"disruption"*, and *"violations"*, but completely missed the paragraph with the actual rule.

**The System's Output:**  
> *"I don't know."*

**Why it Failed:**  
The AI did its job perfectly because it read the 3 paragraphs it was given and honestly said it didn't know. **The search engine failed.** The document uses words like "guest," "on-campus," and "violations" hundreds of times. The search engine got distracted by these common keywords and grabbed the wrong paragraphs, burying the one that actually contained the answer.
