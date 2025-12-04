## Part 2 – Realistic Tasks and Agent Trajectories

This section demonstrates **three realistic tasks** that I would normally perform manually, and how they can instead be automated using my implemented `SearchAgent`.  
For each task, I:

- **Describe the real-world manual workflow**
- **Show a complete agent trajectory** with at least 5 steps and at least 3 different tools
- **Discuss whether the agent completed the task correctly**, and analyze what went wrong if not

All trajectories are based on the actual capabilities exposed in `tools.py`:  
`google_search`, `browse_website`, `google_shopping`, `google_maps_search`, `recommend_places`, and `google_scholar`.

---

## Task 1 – Finding a Quiet Café in Central for Studying with Friends

### 1.1 Real-World Manual Workflow

In reality, if I want to find a quiet café in Central (Hong Kong) that is suitable for studying with friends, I would:

- Open Google Maps and search for coffee shops near *Central, Hong Kong*.
- Filter by rating and number of reviews to identify promising candidates.
- Click into each place, open the website or social pages (if available) to check photos, menu, whether there is Wi‑Fi, power outlets, and whether there is a time limit.
- Sometimes, I also Google blog reviews like “`<café name> quiet study`” to confirm the environment and see if people mention it is suitable for studying.
- Finally, I choose one place and share the location link with my friends.

### 1.2 Agent Configuration and Tools Used

To automate this with my agent, I configure:

- `SearchAgent(use_tools=True, use_browsing=True, enable_maps=True)`

The main tools used in this trajectory:

- `google_maps_search` – to find candidate cafés and get ratings/review counts.
- `browse_website` – to open café websites or map pages for details (Wi‑Fi, time limits, etc.).
- `google_search` – to search for external reviews or blog posts mentioning the study environment.

### 1.3 Agent Trajectory (≥ 5 Steps, ≥ 3 Tools)

- **Step 1 – Initial Reasoning (no tool)**  
  The user asks: *“Find a quiet café in Central, Hong Kong for studying with friends, preferably with Wi‑Fi and a calm environment.”*  
  The agent’s internal reasoning (recorded in `reasoning_steps`) identifies:
  - Location constraint: *Central, Hong Kong*
  - Place type: *coffee shop / café*
  - Preferences: *quiet, Wi‑Fi, comfortable for longer stays*  
  The agent decides to start with **Google Maps** to get a list of candidate places.

- **Step 2 – Maps Search (`google_maps_search`)**  
  The agent issues a tool call:
  - Function: `google_maps_search`
  - Arguments (conceptual):  
    - `query = "coffee shop with wifi"`  
    - `location = "Central, Hong Kong"`  
    - `num = 10`  
  The tool returns a standardized `places` list containing information such as:
  - `title`, `address`, `rating`, `reviews`, `price_level`, `category`, `google_maps_link`, etc.  
  In the next assistant message, the agent summarizes that it has several candidates, e.g., cafés with rating > 4.3 and > 200 reviews.

- **Step 3 – Website Browsing (`browse_website`)**  
  For one of the promising cafés (let’s call it *Cafe A*), the agent:
  - Extracts the café’s `website` URL or the `google_maps_link` from the previous step.
  - Calls `browse_website` with that URL.  
  From the returned text, the agent scans for cues such as:
  - “free Wi‑Fi”, “no time limit”, “study”, “work friendly”, “power outlets”
  - Any notes about noise level or typical customers  
  These findings are recorded in the next reasoning step.

- **Step 4 – External Review Search (`google_search`)**  
  To verify the environment, the agent issues:
  - Function: `google_search`
  - Arguments:  
    - `query = "<Cafe A name> quiet study review"`  
    - `page = 1`  
    - `tbs = "anytime"`  
  It inspects the `organic` results, especially snippets mentioning *“quiet”, “noise”, “good for studying”, “laptop friendly”*, and records representative snippets in `tool_calls`.

- **Step 5 – Comparing with Another Candidate (`browse_website` + Maps info)**  
  The agent repeats a similar `browse_website` call for another high-rated café (*Cafe B*), and uses the Maps ratings/reviews plus website text to compare:
  - Is there Wi‑Fi?
  - Are there power outlets?
  - Are there mentions of crowding or time limits?

- **Step 6 – Final Recommendation (no further tools)**  
  Based on the gathered information, the agent:
  - Chooses the café that offers Wi‑Fi, good ratings (e.g., > 4.3), sufficient reviews, and textual indications that it is suitable for studying.
  - Produces a final answer summarizing:
    - The recommended café name and address.
    - Rough walking directions / station (“near Central MTR Station”).
    - Why it thinks it is study-friendly (Wi‑Fi, reviews mentioning quiet environment, etc.).
  This appears as `final_answer` in the trajectory output.

### 1.4 Correctness and Failure Analysis

- **Overall outcome**  
  The agent is generally able to complete this task correctly:
  - It uses `google_maps_search` to identify good candidates.
  - `browse_website` extracts website text mentioning Wi‑Fi and other conditions.
  - `google_search` provides external opinions about quietness and study friendliness.

- **Potential failure modes**  
  - Some cafés may not have an accessible website or the HTML structure may be complex, causing `browse_website` to miss important information such as Wi‑Fi or time limits.
  - `price_level` or `category` fields can be missing in Maps data, making it harder to judge “study-friendly” purely from structured fields.
  - The agent’s interpretation of “quiet” is based on sparse text; if reviews are mixed, it might still pick a place that feels noisy in real life.

Even with these limitations, the agent significantly reduces the manual effort compared to browsing Maps and multiple web pages by hand.

---

## Task 2 – Choosing a Value-for-Money Noise-Cancelling Headphone for Classes and Commuting

### 2.1 Real-World Manual Workflow

In real life, when I want to buy noise-cancelling headphones for classes and commuting (with a budget, say 1500–2500 HKD), I would:

- Use Google to search “best noise cancelling headphones for students / commuting”.
- Read articles and blog posts listing top models, pros/cons, and usage scenarios.
- Visit shopping sites (local e-commerce, official stores, etc.) to check prices and availability.
- Compare a few candidates in terms of price, noise-cancelling performance, comfort, and battery life.
- Finally, pick one model and a store with a reasonable price and acceptable seller reputation.

### 2.2 Agent Configuration and Tools Used

To automate this with my agent, I configure:

- `SearchAgent(use_tools=True, use_browsing=True, use_shopping=True)`

The main tools used:

- `google_search` – to discover popular models and read summaries/comparisons.
- `google_shopping` – to check prices and sellers for specific models.
- `browse_website` – to open specific product pages and read details like warranty, shipping, and authenticity.

### 2.3 Agent Trajectory (≥ 5 Steps, ≥ 3 Tools)

- **Step 1 – Initial Reasoning (no tool)**  
  The user asks:  
  *“With a budget of 1500–2500 HKD, recommend a pair of noise-cancelling headphones suitable for attending classes and commuting, and give me the best value purchase link.”*  
  The agent reasons that it first needs to:
  - Identify good candidate models that fit “noise cancelling + commuting + students”.
  - Then compare actual prices and sellers using shopping results.

- **Step 2 – Discover Candidate Models (`google_search`)**  
  The agent calls:
  - `google_search` with arguments like:  
    - `query = "best noise cancelling headphones for students and commuting 2024"`  
    - `page = 1`  
    - `tbs = "past_year"`  
  From the `organic` results, it extracts:
  - Frequently mentioned models (e.g., Sony WH‑1000XM series, Bose QuietComfort series, AirPods Pro, etc.).
  - Any quick comments like *“best for commuters”*, *“comfortable while studying”*.

- **Step 3 – Price and Availability Check (`google_shopping`)**  
  For two or three promising models, the agent issues separate shopping tool calls, for example:
  - `{"query": "Sony WH-1000XM5 Hong Kong price", "num": 10, "page": 1}`  
  - `{"query": "Bose QuietComfort noise cancelling headphones Hong Kong", "num": 10, "page": 1}`  
  From each `shopping` result, it extracts:
  - `title`, `price`, `source` (seller), `rating`, and `link`.  
  It then compares which options fall into the 1500–2500 HKD budget and have good seller reputation (if available).

- **Step 4 – Detailed Product Information (`browse_website`)**  
  For the most promising few shopping results, the agent:
  - Calls `browse_website` on the product page URLs.  
  Using the returned content, it checks:
  - Whether the item is likely a Hong Kong official product (warranty information, authorized dealer notes, etc.).
  - Shipping details and return policy.
  - Any mentions of student discounts or bundles.  
  These details are summarized into `reasoning_steps` to justify the final recommendation.

- **Step 5 – Additional Review Comparison (`google_search`)**  
  If two models seem close in price and availability, the agent runs another:
  - `google_search` with a comparative query, such as:  
    - `query = "Sony WH-1000XM5 vs Bose QuietComfort noise cancelling commuting review"`  
  It reads the snippets to compare:
  - Noise-cancelling performance.
  - Comfort during long wear (classes, commuting).
  - Battery life and portability.

- **Step 6 – Final Recommendation and Link (no further tools)**  
  Based on all information collected, the agent:
  - Selects a single model that best balances price, noise cancellation, comfort, and availability.
  - Chooses one or two shopping links within the budget that appear trustworthy.
  - Produces a final answer explaining:
    - Why this model is recommended (e.g., strong noise cancellation for commuting, comfortable for long lectures, good battery life).
    - Why the suggested store offers good value (price within range, adequate seller rating, warranty).

### 2.4 Correctness and Failure Analysis

- **Overall outcome**  
  The agent can typically recommend a **reasonable** and **justified** headphone choice:
  - It grounds its decision on mainstream recommendations from `google_search`.
  - It uses `google_shopping` to ensure the choice is budget-appropriate and available in Hong Kong.
  - It uses `browse_website` to double-check key details that matter in real decisions (warranty, seller, etc.).

- **Limitations and possible errors**  
  - Prices are time-sensitive and can fluctuate; `google_shopping` gives a snapshot but not a guarantee of “absolute cheapest price”.
  - Some e-commerce sites rely heavily on JavaScript; `browse_website` may not capture all structured data, causing the agent to miss, for example, warranty or region information.
  - The agent might slightly mis-rank models if it over-weights price or a single review snippet; human preferences (comfort, brand preference) play a big role.

Even with these caveats, the agent substantially automates comparison and information gathering compared to manually browsing multiple review blogs and shopping platforms.

---

## Task 3 – Initial Literature Screening for a Few-Shot Multimodal Learning Project

### 3.1 Real-World Manual Workflow

When planning a course project on **few-shot multimodal learning**, my typical manual workflow is:

- Go to Google Scholar and search for “few-shot multimodal learning”.
- Filter results by publication year (e.g., 2020 and later).
- Look at titles, venues, and citation counts to find influential or representative papers.
- Open the PDF or HTML versions to read abstracts and introductions.
- Choose a small set of papers (e.g., 5) to read in a reasonable order, from foundational to more specialized or recent work.

### 3.2 Agent Configuration and Tools Used

To automate this with my agent, I configure:

- `SearchAgent(use_tools=True, use_browsing=True, enable_scholar=True)`

The main tools used:

- `google_scholar` – to search for academic papers and filter by year.
- `google_search` – to find summaries, blog posts, or secondary explanations of key papers.
- `browse_website` – to open PDF/HTML versions from arXiv or other repositories and extract abstracts and introductions.

### 3.3 Agent Trajectory (≥ 5 Steps, ≥ 3 Tools)

- **Step 1 – Initial Reasoning (no tool)**  
  The user asks:  
  *“I want to do a project about few-shot multimodal learning. Please find 5 important papers published after 2020, give a 2–3 sentence summary for each, and suggest a reading order.”*  
  The agent reasons that it needs to:
  - Use Google Scholar to obtain relevant papers with year filters.
  - Use PDFs/HTML pages to read abstracts and skim introductions.
  - Optionally use general search to get secondary summaries.

- **Step 2 – Scholar Search (`google_scholar`)**  
  The agent calls:
  - `google_scholar` with arguments like:  
    - `query = "few-shot multimodal learning"`  
    - `num = 20`  
    - `year_low = 2020`  
  From the returned `papers` list, it collects:
  - `title`, `authors`, `year`, `cited_by`, and `pdf_link` / `htmlUrl`.  
  The agent then selects candidate papers that are both recent (≥ 2020) and sufficiently cited.

- **Step 3 – Supplementary Background (`google_search`)**  
  For one or two high-impact papers, the agent calls:
  - `google_search` with queries like:  
    - `"<paper title> summary"` or `"<paper title> blog"`.  
  It reads snippets or blog summaries that explain the contribution and context in more accessible language than the original paper.

- **Step 4 – Reading Abstracts and Introductions (`browse_website`)**  
  For each of the top candidate papers (say, 5–8 papers before narrowing down to 5), the agent:
  - Calls `browse_website` with the `pdf_link` or HTML link (often arXiv or publisher pages).  
  From the resulting content, it attempts to:
  - Extract the title and abstract.
  - Skim the first part of the introduction to understand:
    - What problem is being addressed.
    - What methods are used (e.g., meta-learning, contrastive pretraining).
    - What modalities are involved (e.g., image-text, audio-visual).

- **Step 5 – Possible Second Scholar Query (`google_scholar`)**  
  If the initial query mostly returns, for example, image-text papers, but the agent wants broader coverage (e.g., other modalities or related foundational works), it may:
  - Issue a second Scholar query:  
    - `query = "few-shot vision-language model"` or  
    - `query = "few-shot multimodal representation learning"`  
    with the same `year_low = 2020`.  
  It then merges these results with the previous set and selects a diverse subset of 5 papers.

- **Step 6 – Final Selection, Summaries, and Reading Order (no further tools)**  
  Finally, the agent:
  - Picks **5 papers** that together cover:
    - foundational ideas,
    - representative methods, and
    - recent improvements or extensions.
  - For each paper, it writes a **2–3 sentence summary** in the final answer, based primarily on the abstract and introduction it read via `browse_website`, and optionally on blog summaries from `google_search`.
  - It also proposes a **reading order**, e.g.:
    1. A more general or survey-style paper for high-level context.
    2. A foundational few-shot multimodal method.
    3–5. More specialized or recent improvements building on that foundation.

### 3.4 Correctness and Failure Analysis

- **Overall outcome**  
  - The agent is able to automatically produce a **reasonable initial reading list** and reading order:
    - `google_scholar` ensures the papers are relevant and satisfy the year constraint.
    - Citation counts and titles help it prioritize more impactful or central works.
    - `browse_website` enables extraction of abstracts and introductions to form concise summaries.

- **Limitations and possible errors**  
  - Some PDFs or HTML pages (especially publisher sites) have complex structures; `browse_website` might include navigation text or cut off parts of the abstract, which can slightly distort summaries.
  - Citation counts are not a perfect indicator of importance, especially for very recent papers; a promising but new paper may be underweighted.
  - The year filtering via Serper’s Scholar endpoint depends on how well `year_low` and `year_high` are enforced; in rare cases, papers just outside the desired range might appear.

Nevertheless, the agent greatly speeds up the **literature screening** phase by automating search, filtering, and basic summarization, leaving only deeper critical reading to the human.

---

## Summary of the Three Tasks

- **Task 1 (Café search)** primarily demonstrates **location-based decision making** using `google_maps_search`, `browse_website`, and `google_search`.
- **Task 2 (Headphone purchase)** demonstrates **shopping and product comparison**, centered on `google_shopping`, with `google_search` and `browse_website` for context and validation.
- **Task 3 (Literature screening)** demonstrates **academic search and reading order planning**, using `google_scholar`, `browse_website`, and `google_search`.  

Each trajectory uses at least **three different tools** and consists of at least **five steps**, closely mirroring how I would perform these tasks manually while showing how the agent automates the process end-to-end.


