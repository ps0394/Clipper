# Phase 5 judge-calibration hand-labels

For each item, decide whether the **candidate** is a correct answer to the **question**, given that the **ground truth** is the authoritative answer. The **judge** column shows what Llama 3.3 said.

Your job: fill in the `hand` column with `correct`, `incorrect`, or `not_in_document`. 

When done, copy your labels into `hand-labels-template.json` (rename to `hand-labels.json`) and run `python main.py phase5 kappa evaluation/phase5-results/pilot-001`.


## developer-mozilla-org-en-US-docs-Web-HTTP-Status-429

### Pair 0

**Q:** What does the HTTP 429 status code indicate?

**Ground truth:** The HTTP 429 Too Many Requests client error response status code indicates the client has sent too many requests in a given amount of time.

**Candidate:** The client has sent too many requests in a given amount of time.

**Judge:** `correct` — The candidate answer conveys the same fact as the ground-truth answer, omitting only the formal status code name.

**Your label:** `TODO`

---

### Pair 1

**Q:** What is the common term for the mechanism that asks a client to slow down the rate of requests?

**Ground truth:** The common term for this mechanism is 'rate limiting'.

**Candidate:** rate limiting

**Judge:** `correct` — The candidate answer conveys the same fact as the ground-truth answer, differing only in capitalization and wording.

**Your label:** `TODO`

---

### Pair 2

**Q:** What header might be included in a 429 response to suggest how long a client should wait before retrying?

**Ground truth:** A Retry-After header may be included in a 429 response.

**Candidate:** Retry-After

**Judge:** `correct` — The candidate answer conveys the same fact as the ground-truth answer, identifying the Retry-After header as the relevant header for a 429 response.

**Your label:** `TODO`

---

### Pair 3

**Q:** What are some factors that can influence how rate-limiting restrictions are applied?

**Ground truth:** Rate-limiting restrictions may be based on a client's IP, specific to users, or authorized applications if requests are authenticated or contain a cookie.

**Candidate:** Client's IP, specific users, authorized applications, authentication, cookies, server-wide, per resource

**Judge:** `incorrect` — The candidate answer includes extra factors (server-wide, per resource) not mentioned in the ground-truth answer and also separates "authentication" and "cookies" which in the ground truth are connected to authorized applications.

**Your label:** `TODO`

---

### Pair 4

**Q:** Do rate-limiting implementations apply uniformly across an entire server or can they vary by resource?

**Ground truth:** Implementations of rate limiting vary; restrictions may be server-wide or per resource.

**Candidate:** They can vary by resource.

**Judge:** `correct` — The candidate answer conveys the same fact as the ground-truth answer, which states that rate-limiting implementations can vary by resource, in addition to possibly being server-wide.

**Your label:** `TODO`

---


## learn-microsoft-com-en-us-azure-ai-services-openai-concepts-prompt-engineering

### Pair 0

**Q:** What is the primary purpose of the 'Prompt engineering techniques' article?

**Ground truth:** The goal of the article is to help users get started with the learning process of prompt engineering by capturing general concepts and patterns that apply to all GPT models.

**Candidate:** The primary purpose of the 'Prompt engineering techniques' article is to help users get started with learning how to construct effective prompts for GPT models by capturing general concepts and patterns that apply to all GPT models, providing guidance, examples, and best practices for prompt construction.

**Judge:** `correct` — The candidate answer conveys the same factual content as the ground-truth answer, despite some differences in wording and added details.

**Your label:** `TODO`

---

### Pair 1

**Q:** What are the three distinct roles used in the Chat Completion API for prompt components?

**Ground truth:** The three distinct roles are system, user, and assistant.

**Candidate:** system, user, assistant

**Judge:** `correct` — The candidate answer conveys the same facts as the ground-truth answer, listing the three distinct roles used in the Chat Completion API for prompt components.

**Your label:** `TODO`

---

### Pair 2

**Q:** What is the term for including one or more examples of the desired behavior in a prompt?

**Ground truth:** The term is 'few-shot learning.'

**Candidate:** few-shot learning

**Judge:** `correct` — The candidate answer conveys the same fact as the ground-truth answer, differing only in capitalization and punctuation.

**Your label:** `TODO`

---

### Pair 3

**Q:** What parameter controls the randomness of the model's output, and what is its recommended range?

**Ground truth:** The parameter is 'temperature,' and its recommended range is between 0 and 2.

**Candidate:** The temperature parameter controls the randomness of the model's output, and it can be set between 0 and 2.

**Judge:** `correct` — The candidate answer conveys the same facts as the ground-truth answer, identifying the parameter as "temperature" and its recommended range as between 0 and 2.

**Your label:** `TODO`

---

### Pair 4

**Q:** Which four companies are mentioned as early customers of the Azure OpenAI GPT-4 models?

**Ground truth:** The four companies are Epic Healthcare, Coursera, Coca-Cola, and other companies of all sizes.

**Candidate:** - Epic Healthcare
- Coursera
- Coca-Cola
- Other companies of all sizes

**Judge:** `correct` — The candidate answer lists the same companies as the ground-truth answer, despite minor formatting differences.

**Your label:** `TODO`

---


## learn-microsoft-com-en-us-azure-ai-services-openai-overview

### Pair 0

**Q:** What are the two main categories of Microsoft Foundry Models in the model catalog?

**Ground truth:** Foundry Models sold directly by Azure and Foundry Models from partners and community.

**Candidate:** Foundry Models sold directly by Azure and Foundry Models from partners and community

**Judge:** `correct` — The candidate answer conveys the same facts as the ground-truth answer, with no differences in factual content.

**Your label:** `TODO`

---

### Pair 1

**Q:** Which regions are available for the gpt-5.4-mini model under the Global Standard deployment?

**Ground truth:** East US2, Sweden Central, South Central US, and Poland Central.

**Candidate:** East US2, Sweden Central, South Central US, Poland Central

**Judge:** `correct` — The candidate answer conveys the same regions as the ground-truth answer, despite minor punctuation differences.

**Your label:** `TODO`

---

### Pair 2

**Q:** What is the context window size for the gpt-5.4 model?

**Ground truth:** 1,050,000 tokens.

**Candidate:** 1,050,000

**Judge:** `correct` — The candidate answer conveys the same fact as the ground-truth answer, which is the context window size for the gpt-5.4 model.

**Your label:** `TODO`

---

### Pair 3

**Q:** What is the default value for the reasoning_effort parameter in gpt-5.1?

**Ground truth:** none

**Candidate:** none

**Judge:** `correct` — The candidate answer matches the ground-truth answer, both stating that the default value is "none".

**Your label:** `TODO`

---

### Pair 4

**Q:** Which model series includes the sora-2 model?

**Ground truth:** Video generation models.

**Candidate:** Sora

**Judge:** `incorrect` — The candidate answer does not convey the same fact as the ground-truth answer, which specifies that the sora-2 model is part of the video generation models series.

**Your label:** `TODO`

---


## stripe-com-docs-api-charges-create

### Pair 0

**Q:** What is the value of the 'object' field in the charge response from the Stripe API?

**Ground truth:** charge

**Candidate:** charge

**Judge:** `correct` — The candidate answer matches the ground-truth answer, conveying the same factual content.

**Your label:** `TODO`

---

### Pair 1

**Q:** What is the amount specified in the charge example, and in what currency?

**Ground truth:** 1099 in USD

**Candidate:** 1099, usd

**Judge:** `correct` — The candidate answer conveys the same facts as the ground-truth answer, with the amount and currency being correctly identified as 1099 and USD, respectively.

**Your label:** `TODO`

---

### Pair 2

**Q:** What is the brand of the card used in the payment method details of the charge example?

**Ground truth:** visa

**Candidate:** visa

**Judge:** `correct` — The candidate answer matches the ground-truth answer, stating the brand of the card is "visa".

**Your label:** `TODO`

---

### Pair 3

**Q:** What is the 'risk_level' assigned to the charge in the outcome section?

**Ground truth:** normal

**Candidate:** normal

**Judge:** `correct` — The candidate answer matches the ground-truth answer, conveying the same fact about the 'risk_level' assigned to the charge.

**Your label:** `TODO`

---

### Pair 4

**Q:** What is the expiration month and year of the card used in the charge example?

**Ground truth:** Expiration month is 3 and year is 2024

**Candidate:** 3, 2024

**Judge:** `correct` — The candidate answer conveys the same factual content as the ground-truth answer, providing both the expiration month and year.

**Your label:** `TODO`

---
