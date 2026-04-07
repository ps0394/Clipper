# Retrievability Scoring System

This document explains how the retrievability evaluation system scores documentation pages for readiness in retrieval systems.

## Overview

The scoring system evaluates documentation pages across multiple dimensions to determine if they are suitable for agent and retrieval system consumption. Each page receives a **Parseability Score** (0-100) and a **Failure Mode** classification.

## Scoring Components

### 1. Semantic Structure (25% weight)
- **What it measures**: Presence of semantic HTML5 elements (`<main>`, `<article>`)
- **Why it matters**: Semantic elements help extraction tools identify primary content
- **Scoring**:
  - `<main>` element: +60 points
  - `<article>` element: +40 points  
  - Maximum: 100 points

### 2. Heading Hierarchy (20% weight)
- **What it measures**: Valid H1→H2→H3 progression without level jumps
- **Why it matters**: Proper headings enable content structure understanding
- **Scoring**:
  - Valid hierarchy: 100 points
  - Invalid but has headings: 30 points
  - No headings: 0 points

### 3. Content Density (25% weight)
- **What it measures**: Ratio of primary content text to total page text
- **Why it matters**: Higher density indicates less noise for extraction
- **Scoring**: Direct ratio × 100 (0.8 ratio = 80 points)

### 4. Rich Content (10% weight)
- **What it measures**: Presence of code blocks and tables
- **Why it matters**: Indicates structured, technical content
- **Scoring**:
  - Code blocks present: +50 points
  - Tables present: +50 points
  - Maximum: 100 points

### 5. Boilerplate Resistance (20% weight)
- **What it measures**: Inverse of navigation/sidebar/footer dominance
- **Why it matters**: Less boilerplate means cleaner extraction
- **Scoring**: (1 - boilerplate_ratio) × 100

## Failure Mode Classification

### Clean (Score ≥ 80)
- High overall score with good semantic structure
- Ready for retrieval systems
- No action needed

### Structure-Missing (Low semantic/hierarchy scores)  
- Missing semantic HTML elements
- Invalid or absent heading hierarchy
- **Fix Owner**: Frontend Developer
- **Action**: Add `<main>`/`<article>` elements, fix heading hierarchy

### Extraction-Noisy (Decent structure, poor content/boilerplate)
- Has basic structure but content extraction is problematic
- High boilerplate contamination or low content density
- **Fix Owner**: Frontend Developer  
- **Action**: Improve content/chrome separation

## Deterministic Principles

All scoring is based on measurable HTML characteristics:
- Element presence (boolean)
- Text length ratios (numeric)
- Structural patterns (rule-based)

No subjective judgments or ML inference are used to ensure reproducible results.

## Usage for Agents

The JSON output provides:
- Raw signals for custom scoring
- Standardized failure modes for routing
- Evidence references for debugging
- Subscores for targeted improvements

Agents can consume this data to determine appropriate retrieval strategies or identify pages needing preprocessing.