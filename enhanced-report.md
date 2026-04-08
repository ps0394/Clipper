# YARA Evaluation Report

Generated: 2026-04-08 13:42:22
Total Pages Evaluated: 9

## Executive Summary

- **Average Parseability Score**: 68.2/100
- **Clean Pages**: 3 (33.3%)
- **Structure Issues**: 3 (33.3%)
- **Extraction Issues**: 3 (33.3%)

## Failure Mode Analysis

### Distribution

| Failure Mode | Count | Percentage | Description |
|--------------|-------|------------|-------------|
| clean | 3 | 33.3% | Ready for retrieval systems |
| structure-missing | 3 | 33.3% | Lacks semantic HTML structure |
| extraction-noisy | 3 | 33.3% | Has structure but content extraction issues |

## Individual Page Results

### ⚠️ Page 1

**Overall Score**: 41.8/100
**Failure Mode**: `extraction-noisy`

**What Failed:**

- Low content density - too much non-primary content
- High boilerplate contamination from navigation/sidebar elements

**Why It Failed:**

- Primary content not clearly distinguished from secondary content
- Navigation, sidebar, or footer content overwhelms primary content

**Fix Owner:**

- **Frontend Developer** - Improve content/chrome separation and reduce boilerplate dominance

**Priority Fixes:**

| Fix | Impact | Effort | Score Gain | Priority |
|-----|--------|--------|------------|----------|
| Improve content density | High | Medium | +18 pts | 🔥 Critical |
| Reduce boilerplate | High | High | +15 pts | 📋 Planned |

**How to Fix:**

**Improve Content Density:**
```html
<!-- Before (content scattered) -->
<div class="page">
  <nav>...</nav>        <!-- Noise -->
  <aside>...</aside>    <!-- Noise -->
  <div class="content">
    <p>Main content</p>
  </div>
  <footer>...</footer>  <!-- Noise -->
</div>

<!-- After (content prioritized) -->
<div class="page">
  <main>
    <article>
      <p>Main content</p>
    </article>
  </main>
  <nav>...</nav>
  <aside>...</aside>
  <footer>...</footer>
</div>
```

**Reduce Boilerplate Contamination:**
```html
<!-- Use semantic elements to separate content -->
<body>
  <header>Site navigation</header>
  
  <main>  <!-- ✅ Primary content area -->
    <article>
      <h1>Article Title</h1>
      <p>Article content...</p>
    </article>
  </main>
  
  <aside>Sidebar content</aside>  <!-- ✅ Secondary -->
  <footer>Footer links</footer>   <!-- ✅ Auxiliary -->
</body>
```

**Component Scores:**

- Semantic Structure: 60.0/100
- Heading Hierarchy: 100.0/100
- Content Density: 27.4/100
- Rich Content: 0.0/100
- Boilerplate Resistance: 0.0/100

---

### ❌ Page 2

**Overall Score**: 42.1/100
**Failure Mode**: `structure-missing`

**What Failed:**

- Missing semantic HTML elements (<main>, <article>)
- Invalid or missing heading hierarchy

**Why It Failed:**

- HTML lacks semantic content containers
- Heading levels jump incorrectly (e.g., H1 directly to H3)

**Fix Owner:**

- **Frontend Developer** - HTML structure needs semantic markup and heading organization

**Priority Fixes:**

| Fix | Impact | Effort | Score Gain | Priority |
|-----|--------|--------|------------|----------|
| Add `<main>` element | High | Low | +15 pts | 🔥 Critical |
| Fix heading hierarchy | High | Medium | +12 pts | 🔥 Critical |
| Add `<article>` wrapper | Medium | Low | +10 pts | ⚠️ Important |

**How to Fix:**

**Add Semantic HTML Structure:**
```html
<!-- Before (problematic) -->
<div class="content">
  <h1>Page Title</h1>
  <p>Content here...</p>
</div>

<!-- After (semantic) -->
<main>
  <article>
    <h1>Page Title</h1>
    <p>Content here...</p>
  </article>
</main>
```

**Fix Heading Hierarchy:**
```html
<!-- Before (hierarchy jumps) -->
<h1>Main Title</h1>
<h3>Subsection</h3>  <!-- ❌ Skip H2 -->
<h2>Section</h2>     <!-- ❌ Wrong order -->

<!-- After (proper hierarchy) -->
<h1>Main Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>  <!-- ✅ Logical flow -->
```

**Component Scores:**

- Semantic Structure: 0.0/100
- Heading Hierarchy: 30.0/100
- Content Density: 81.9/100
- Rich Content: 0.0/100
- Boilerplate Resistance: 78.4/100

---

### ❌ Page 3

**Overall Score**: 50.8/100
**Failure Mode**: `structure-missing`

**What Failed:**

- Invalid or missing heading hierarchy

**Why It Failed:**

- Heading levels jump incorrectly (e.g., H1 directly to H3)

**Fix Owner:**

- **Content Author/Developer** - Fix heading hierarchy (H1→H2→H3 progression)

**Priority Fixes:**

| Fix | Impact | Effort | Score Gain | Priority |
|-----|--------|--------|------------|----------|
| Fix heading hierarchy | High | Medium | +12 pts | 🔥 Critical |

**How to Fix:**

**Fix Heading Hierarchy:**
```html
<!-- Before (hierarchy jumps) -->
<h1>Main Title</h1>
<h3>Subsection</h3>  <!-- ❌ Skip H2 -->
<h2>Section</h2>     <!-- ❌ Wrong order -->

<!-- After (proper hierarchy) -->
<h1>Main Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>  <!-- ✅ Logical flow -->
```

**Component Scores:**

- Semantic Structure: 100.0/100
- Heading Hierarchy: 30.0/100
- Content Density: 29.6/100
- Rich Content: 50.0/100
- Boilerplate Resistance: 37.1/100

---

### ❌ Page 4

**Overall Score**: 63.3/100
**Failure Mode**: `structure-missing`

**What Failed:**

- Missing semantic HTML elements (<main>, <article>)

**Why It Failed:**

- HTML lacks semantic content containers

**Fix Owner:**

- **Frontend Developer** - Add semantic HTML containers (<main>, <article>)

**Priority Fixes:**

| Fix | Impact | Effort | Score Gain | Priority |
|-----|--------|--------|------------|----------|
| Add `<main>` element | High | Low | +15 pts | 🔥 Critical |
| Add `<article>` wrapper | Medium | Low | +10 pts | ⚠️ Important |

**How to Fix:**

**Add Semantic HTML Structure:**
```html
<!-- Before (problematic) -->
<div class="content">
  <h1>Page Title</h1>
  <p>Content here...</p>
</div>

<!-- After (semantic) -->
<main>
  <article>
    <h1>Page Title</h1>
    <p>Content here...</p>
  </article>
</main>
```

**Component Scores:**

- Semantic Structure: 0.0/100
- Heading Hierarchy: 100.0/100
- Content Density: 93.3/100
- Rich Content: 0.0/100
- Boilerplate Resistance: 100.0/100

---

### ⚠️ Page 5

**Overall Score**: 77.1/100
**Failure Mode**: `extraction-noisy`

**Fix Owner:**

- **Frontend Developer** - Improve content/chrome separation and reduce boilerplate dominance

**Component Scores:**

- Semantic Structure: 100.0/100
- Heading Hierarchy: 100.0/100
- Content Density: 70.0/100
- Rich Content: 0.0/100
- Boilerplate Resistance: 73.1/100

---

### ⚠️ Page 6

**Overall Score**: 78.1/100
**Failure Mode**: `extraction-noisy`

**Fix Owner:**

- **Frontend Developer** - Improve content/chrome separation and reduce boilerplate dominance

**Component Scores:**

- Semantic Structure: 60.0/100
- Heading Hierarchy: 100.0/100
- Content Density: 84.6/100
- Rich Content: 50.0/100
- Boilerplate Resistance: 84.9/100

---

### ✅ Page 7

**Overall Score**: 83.7/100
**Failure Mode**: `clean`

**Fix Owner:**

- **Development Team** - Review page structure and content organization

**Component Scores:**

- Semantic Structure: 60.0/100
- Heading Hierarchy: 100.0/100
- Content Density: 97.1/100
- Rich Content: 50.0/100
- Boilerplate Resistance: 97.3/100

---

### ✅ Page 8

**Overall Score**: 88.0/100
**Failure Mode**: `clean`

**Fix Owner:**

- **Development Team** - Review page structure and content organization

**Component Scores:**

- Semantic Structure: 60.0/100
- Heading Hierarchy: 100.0/100
- Content Density: 96.9/100
- Rich Content: 100.0/100
- Boilerplate Resistance: 93.8/100

---

### ✅ Page 9

**Overall Score**: 88.4/100
**Failure Mode**: `clean`

**Fix Owner:**

- **Development Team** - Review page structure and content organization

**Component Scores:**

- Semantic Structure: 60.0/100
- Heading Hierarchy: 100.0/100
- Content Density: 97.3/100
- Rich Content: 100.0/100
- Boilerplate Resistance: 95.3/100

---

## Recommendations

**For structure-missing pages**: Implement semantic HTML5 elements (<main>, <article>) and ensure proper heading hierarchy (H1→H2→H3 without skipping levels).

**For extraction-noisy pages**: Reduce navigation/sidebar dominance by moving primary content higher in DOM order and using clearer content boundaries.
