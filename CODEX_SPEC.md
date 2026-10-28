# CODEX_SPEC.md
# Personal Academic Website — Initial Implementation

Version: 1.0
Date: 2026-10-26
Project: Academic_Website
Status: Initial local development

## 1. Mission

Build a functional bilingual personal academic website
from the current Academic_Website directory.

The website belongs to:

林李泽强 / Ze-Qiang Linli
Guangdong University of Foreign Studies

The project must integrate:

1. Personal academic homepage
2. Research overview
3. Publication database and PDF library
4. Teaching courses and resource library
5. Academic team and opportunities
6. Research and teaching notes
7. Contact and academic links

Read AGENTS.md and README.md before implementation.

AGENTS.md provides persistent rules.
README.md describes intended use.
This specification defines the first implementation task.

Do not simply provide another planning document.
Create a real, locally buildable, testable project.

## 2. Working Scope and Permissions

Authorized:
- Inspect the Academic_Website directory
- Inspect installed development tools
- Create project directories
- Write and modify local project code
- Create local test data
- Run local scripts and build commands
- Use publicly available academic information
- Generate local reports

Not authorized without further user approval:
- Publish the website publicly
- Push code to GitHub
- Create public remote repositories
- Upload user documents
- Purchase services
- Modify unrelated directories
- Delete original files

All work should stay inside Academic_Website unless
a separate location is explicitly authorized.

Preserve existing files.

## 3. Phase 0 — Environment and Source Survey

### 3.1 Inspect environment

Check availability and versions of:

- Quarto
- Git
- Python
- pip or uv
- PowerShell
- Browser preview tools

Identify missing dependencies.

Install only free, relevant development dependencies
when safe and supported in the local environment.

Do not install unnecessary frameworks.

Record versions and installation requirements.

### 3.2 Inspect existing project

Check current directory contents.

Do not overwrite existing project files.

If the project is empty except for AGENTS.md,
README.md and CODEX_SPEC.md, initialize it.

If a Git repository already exists, preserve its history.

### 3.3 Collect academic information

Use the official profile:

https://stxy.gdufs.edu.cn/info/1683/4359.htm

Collect verified public information including:

- Name
- Affiliation
- Academic position
- Research directions
- Public contact email
- Selected publications
- Publicly documented teaching activities

Check other official publication records when necessary.

Do not invent DOI information or publication metadata.

The university profile may be outdated. Track source dates.

Create an internal list of unverified or missing details.

Do not use personal memory as the sole publication source.

Deliver:
workspace/reports/phase0_environment.md
workspace/reports/phase0_information_review.md

## 4. Phase 1 — Website Foundation

### 4.1 Technology

Use:
- Quarto
- QMD / Markdown
- YAML
- Python
- CSS
- GitHub Pages-compatible static output

Do not introduce a database or backend server.

### 4.2 Bilingual architecture

Create independent Chinese and English Quarto projects.

Chinese website output:
dist/

English website output:
dist/en/

Both languages must use shared structured metadata.

Do not duplicate manually maintained publication records.

A build script should:

1. Validate public metadata
2. Generate required pages or listings
3. Build the Chinese website
4. Build the English website
5. Merge outputs into dist/
6. Copy only approved public assets
7. Run output validation

Do not rely on Windows symlinks.

Support both:
- GitHub user site at /
- GitHub project site at /<repo>/

Use a configurable base path and test generated URLs.

### 4.3 Site navigation

Create seven sections:

Chinese:
- 首页
- 研究方向
- 学术成果
- 教学资源
- 团队与招生
- 学术笔记
- 关于与联系

English:
- Home
- Research
- Publications
- Teaching
- Team & Opportunities
- Notes
- About & Contact

Every main page must have a working language switch.

### 4.4 Homepage content

Include:

- Personal name in Chinese and English
- Academic role and affiliation
- Profile image area
- Research summary
- Three major research directions
- Selected publications
- Teaching resources entrance
- Team and collaboration entrance
- Academic contact information

If no authorized profile photo is present, use a clean
neutral placeholder without implying it is a real portrait.

Do not use fake publication cards in the final public pages.

### 4.5 Visual identity

Use a modern academic design:

Primary: #16324F
Accent: #168A91
Background: #FFFFFF
Secondary background: #F5F7FA

Requirements:

- Responsive desktop and mobile layouts
- Clear typography
- Comfortable spacing
- Accessible navigation
- Chinese and English typography support
- Minimal decorative animation
- Consistent paper and resource cards
- Minimal external service dependencies

Use Quarto native capabilities wherever possible.

## 5. Phase 2 — Structured Academic Data

### 5.1 Public data

Create:

data/profile.yml
data/research.yml
data/publications.yml
data/courses.yml
data/resources.yml
data/links.yml

Validate required fields and types.

Use stable IDs.

Track sources and verification dates.

### 5.2 Publication schema

Each publication should support:

- id
- title
- authors
- journal
- year
- doi
- publisher_url
- abstract or summary
- research_category
- selected
- pdf_version
- pdf_permission_status
- pdf_public_path
- verified_source
- verified_date

A publication can appear on the website without a PDF.

The PDF must be separately approved.

### 5.3 Course schema

Each course should support:

- course_id
- title_zh
- title_en
- description_zh
- description_en
- language
- chapters
- resources
- publication_status

Do not invent courses that the owner does not teach.

### 5.4 Resource schema

Each teaching or publication asset should support:

- resource_id
- resource_type
- related_publication_or_course
- source_file
- sha256
- format
- size
- language
- version
- license
- permission_status
- approval_reference
- public_path
- last_updated

Keep local source paths and private review evidence
outside public metadata whenever possible.

## 6. Phase 3 — Resource Import Pipeline

### 6.1 Resource inbox

Create:

workspace/inbox/papers/
workspace/inbox/teaching/

The owner can drop files into these directories.

Initial supported formats:

- PDF
- PPTX
- Markdown
- QMD

### 6.2 Scanner

Implement:

scripts/scan_resources.py

Required behavior:

- Read files without modifying them
- Calculate SHA-256
- Identify file type and size
- Extract PDF or PPTX metadata
- Extract usable titles when reliable
- Detect exact duplicates
- Detect possible metadata duplicates
- Generate review reports

Do not perform bulk OCR by default.

Do not automatically rename source files.

Do not automatically upload any file.

### 6.3 Paper matching

For publication PDFs:

- Attempt DOI extraction
- Match with existing publication records
- Identify possible publisher versions
- Flag uncertain information
- Generate proposed record changes

Network-based metadata lookup should fail gracefully.

Do not assume an unidentified PDF is published or
redistributable.

### 6.4 Teaching resource matching

For teaching materials:

- Identify possible course
- Identify chapter or lecture
- Read PPTX titles where possible
- Detect duplicated resources
- Record version and language
- Suggest a standardized public filename

Do not create false course or chapter information.

### 6.5 Approval workflow

Implement a review mechanism.

Required statuses:

- pending_review
- approved
- private_only
- external_link_only
- rejected

Only approved files may be copied to public/.

Require explicit approval tied to the exact file hash.

Approval of metadata does not approve redistribution.

If a file changes, invalidate previous asset approval.

Do not treat missing license information as approval.

### 6.6 PDF conversion

If a reliable local converter is available:

- Convert PPTX to a separate PDF
- Preserve the original PPTX
- Record conversion results
- Check slide count and layout where possible
- Mark uncertain conversions for review

Do not rely on unverified conversion quality.

Do not publicly publish a derivative before approval.

## 7. Phase 4 — Publications and Teaching Pages

### 7.1 Publications

Build:

- Publications overview
- Selected Publications
- Full Publications list
- Individual publication detail pages

Support filtering or grouping by:
- Year
- Research area
- Publication type

Each paper may include:
- Publisher / DOI
- Research summary
- Read PDF
- Download PDF

PDF links are conditional on authorization.

### 7.2 Teaching

Build:

- Teaching overview
- Course detail pages
- Chapter or lecture lists
- Resource tables
- PDF preview or download links

Show file format and language.

An empty or partially completed course must not be
misrepresented as having resources.

### 7.3 Notes

Create an extensible Notes area.

Initial categories:
- Statistics
- Neuroimaging
- Research Practice

Do not automatically republish WeChat articles.

Provide a place for approved future content.

### 7.4 Team and contact

Use verified academic information.

Display collaboration interests and public contact details.

Do not invent students, team members, or open positions.

Where appropriate, distinguish general interest in
collaboration from active recruitment.

## 8. Phase 5 — Public Asset Management

Treat public/ as an explicitly reviewed publication area.

Example:
- public/images/
- public/papers/
- public/teaching/

Only allowlisted approved files may enter the build.

Never copy workspace/ into dist/.

Only user-approved files can be staged for Git commit.

Record:
- Asset ID
- Hash
- Permission status
- License or permission evidence
- Approval scope

If the permission is uncertain, offer DOI or another
legitimate external link rather than a hosted copy.

Build must fail if an unapproved binary asset is referenced
or included.

Add size limits and a website capacity report.

Use a configurable internal warning threshold of 700 MB
for the overall generated website.

Avoid using Git LFS as a substitute for ordinary
GitHub Pages PDF delivery.

## 9. Phase 6 — SEO and Accessibility

Implement:

- Bilingual page titles
- Page descriptions
- Semantic headings
- Descriptive links
- Image alt text
- Language switch
- Canonical URL configuration
- hreflang links where applicable
- Sitemap
- Robots.txt
- Open Graph metadata

Use verified names and content.

Avoid unverifiable academic claims.

Keep design usable without external JavaScript services
where possible.

## 10. Phase 7 — Build and Validation

Implement working commands:

    python scripts/build_site.py
    
    python scripts/validate_content.py
    
    python scripts/validate_site.py

Include meaningful automated tests.

Required checks:

1. Chinese pages render successfully
2. English pages render successfully
3. Language switches work
4. Internal links resolve
5. Base paths work for user and project GitHub Pages
6. No private files are in dist/
7. No unauthorized PDF is in dist/
8. Download links point to existing authorized assets
9. Publication data has no unintended duplicates
10. Course and resource references are valid
11. HTML output has required metadata
12. The site remains within configured capacity limits

If a dependency is missing and cannot safely be installed,
report the limitation and complete all feasible tasks.

Never fabricate a successful test result.

## 11. Phase 8 — GitHub Pages Preparation

Create:

.github/workflows/pages.yml

Recommended workflow:

- Pull Request: build and validate only
- Push to main: build, validate, and deploy
- Use GitHub Pages official artifact deployment actions
- Use minimal GitHub Actions permissions

Create the GitHub workflow locally only.

Do not push or publish without explicit user authorization.

Document the steps for repository creation, configuring
Settings -> Pages -> GitHub Actions, and deploying.

Use the actual repository name when configured.

Do not assume the GitHub username.

Support later custom-domain configuration.

## 12. Mainland China Access

V1 hosting strategy:
GitHub Pages as the initial international site.

Provide an independent report on:
- No-VPN access testing requirements
- China mainland fallback options
- Hong Kong hosting feasibility
- Domain and SSL requirements
- ICP filing considerations
- Synchronizing a single static build to another host

Do not purchase or activate any service.

Do not claim mainland accessibility without actual tests.

## 13. Security and Repository Hygiene

Create an appropriate .gitignore.

Exclude:
- workspace/
- dist/
- temporary builds
- local environments
- private metadata
- credentials and secrets
- unapproved source assets

Include pre-commit or pre-publish validation.

Do not depend solely on .gitignore to prevent leaks.

Check the staged file list before any future public commit.

Do not place private path inventories or sensitive data
in public build artifacts.

No unauthorized remote operations.

## 14. Documentation

Update README.md so it matches implemented behavior.

Create or document:
- Installation
- Local build
- Local preview
- Publication import
- Teaching import
- Approval workflow
- Public asset preparation
- Testing
- GitHub Pages deployment
- Common errors and troubleshooting

The owner should be able to maintain the site with short
Codex prompts instead of manually editing HTML.

## 15. Acceptance Criteria

At the end of local development:

[ ] All seven sections exist in both languages
[ ] Website design is responsive
[ ] Research and contact content is verified
[ ] Publications come from structured data
[ ] Teaching resources have structured metadata
[ ] Scan pipeline works on test files
[ ] Duplicate detection works
[ ] Resource approval rules work
[ ] Unapproved files cannot enter public output
[ ] Authorized PDF links can be generated
[ ] Both languages build locally
[ ] Internal links and base paths are tested
[ ] GitHub Actions workflow exists
[ ] README reflects actual commands
[ ] Original user documents remain untouched
[ ] No website has been publicly deployed
[ ] Final report clearly describes completed work

If real PDFs or PPTX files have not yet been provided,
use synthetic test fixtures stored in the test area.

Never publish fake academic results or fixtures as real
website content.

## 16. Deliverables

Generate:

1. A functioning local website
2. Chinese and English pages
3. Structured academic metadata
4. Publications and Teaching modules
5. Resource scanning and validation scripts
6. Explicit approval and public asset process
7. GitHub Pages workflow
8. Updated README
9. Test results
10. Remaining TODO and user approval checklist

Create internal reports under workspace/reports/.

At the end, explain:

- What was actually built
- Which files were created or modified
- What was successfully tested
- What remains incomplete
- Which details require user confirmation
- How the owner can add the first real paper
- How the owner can add the first real lecture slide
- How to preview the website locally
- How future public deployment should be performed

## 17. Execution Strategy

Proceed through all phases that can safely be completed
without further user input.

Do not stop merely because some publication metadata,
profile photos, or PDF documents are unavailable.

Implement functioning architecture with verified content
and test fixtures.

Do not fabricate missing real content.

Make reasonable, documented engineering decisions.

Prefer a working minimum viable website over elaborate
but untested scaffolding.

Maintain consistency with AGENTS.md.

Do not request approval for ordinary local code changes,
tests, or non-destructive development.

Stop before remote publication or disclosure of private
documents.

The final result must be an operational local project,
not merely a proposal or directory outline.
