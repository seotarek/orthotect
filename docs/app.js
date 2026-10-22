/**
 * ORTHOTECT v1.5.0 — Skill Studio & Interactive Demonstration Platform
 * 100% Client-Side | Zero Bloat | True Bidirectional Runtime
 */

document.addEventListener("DOMContentLoaded", () => {
  // =========================================================================
  // 1. STATE & ROUTING ENGINE
  // =========================================================================
  let currentTheme = localStorage.getItem("ortho_theme") || "dark";
  let currentDir = localStorage.getItem("ortho_dir") || "ltr";
  let currentLang = localStorage.getItem("ortho_lang") || "en";
  let activePlaygroundComponent = "analytics";
  let playgroundDensity = "default";
  let playgroundTheme = "dark";
  let playgroundDir = "ltr";

  const validRoutes = ["home", "catalog", "playground", "builder", "gallery", "gates", "install"];

  function handleRouting() {
    const rawHash = window.location.hash.replace(/^#\/?/, "").toLowerCase();
    const route = validRoutes.includes(rawHash) ? rawHash : "home";

    // Switch view sections
    document.querySelectorAll(".page-view").forEach(el => {
      el.classList.remove("active");
    });
    const targetView = document.getElementById(`view-${route}`);
    if (targetView) {
      targetView.classList.add("active");
    }

    // Update main nav active indicator
    document.querySelectorAll(".nav-link").forEach(link => {
      if (link.getAttribute("data-tab") === route) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  window.addEventListener("hashchange", handleRouting);
  handleRouting();

  // =========================================================================
  // 2. THEME ENGINE
  // =========================================================================
  function applyTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("ortho_theme", theme);
    const themeBtnText = document.getElementById("themeBtnText");
    if (themeBtnText) {
      themeBtnText.textContent = theme === "dark" ? "Dark" : theme === "light" ? "Light" : "Contrast";
    }
  }

  const themeToggleBtn = document.getElementById("themeToggleBtn");
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const themes = ["dark", "light", "contrast"];
      const nextTheme = themes[(themes.indexOf(currentTheme) + 1) % themes.length];
      applyTheme(nextTheme);
    });
  }
  applyTheme(currentTheme);

  // =========================================================================
  // 3. BILINGUAL INTERNATIONALIZATION (BiDi)
  // =========================================================================
  const bidiDict = {
    en: {
      brandDesc: "Skill Studio v1.5.0",
      navHome: "Home",
      navCatalog: "Skill Catalog",
      navPlayground: "Playground",
      navBuilder: "Skill Builder",
      navGallery: "Examples",
      navGates: "Quality Gates",
      navInstall: "Install & Usage",
      heroBadge: "v1.5.0 • Deterministic Quality Standard for Autonomous Coding Agents",
      heroTitle: "Deterministic Interface Engineering & <span class=\"hero-gradient-text\">Runtime Quality Gates</span>",
      heroSub: "Stop trusting probabilistic UI code. Orthotect enforces mathematical WCAG AAA contrast, 100% CSS logical properties, formal state machines, and zero layout shift in sub-400ms parallel gates.",
      ctaPlayground: "Open Interactive Playground",
      ctaCatalog: "Browse Skill Catalog",
      ctaBuilder: "Build Custom Skill",
      proofGates: "Deterministic Gates",
      proofTests: "Automated Unit & E2E Tests",
      proofLatency: "Parallel Gate Latency",
      proofDeps: "Runtime Dependencies",
      proofBidi: "CSS Logical Properties",
      pipelinePill: "Autonomous Engineering Lifecycle",
      pipelineTitle: "The Orthotect Runtime Pipeline",
      pipelineSub: "How agent instructions transform into verifiable, certified enterprise code through deterministic gates.",
      step1Title: "Skill Specification",
      step1Desc: "Agent loads domain doctrine, DTCG token contracts, and FSM transition schemas.",
      step2Title: "Agent Generation",
      step2Desc: "AI model synthesizes UI code strictly referencing semantic tokens and FSM handlers.",
      step3Title: "5 Deterministic Gates",
      step3Desc: "Parallel mathematical AST verification: WCAG contrast, BiDi coordinates, FSM graphs, CWV budgets, and anti-slop.",
      step4Title: "Certified Production Release",
      step4Desc: "Validated zero-CLS code committed directly to main, deployable without human rework.",
      catalogPill: "Repository Synchronized Skills",
      catalogTitle: "Orthotect Skill Catalog",
      catalogSub: "Explore the 6 modular skills installed directly in skills/. Each skill provides explicit system instructions, constraints, and gate validation for autonomous coding agents.",
      playgroundPill: "Live Interface Sandbox",
      playgroundTitle: "Interactive Skill Playground",
      playgroundSub: "Interact with 7 pre-validated enterprise components built using Orthotect skills. Toggle theme, text direction, and spacing density in real time to observe deterministic behavior.",
      builderPill: "Interactive Skill Authoring",
      builderTitle: "Orthotect Skill Builder",
      builderSub: "Author production-ready SKILL.md definitions tailored for Google Antigravity, Claude Code, Cursor, and Codex. Form inputs generate validated markdown with instant live preview.",
      galleryPill: "Verified Production Templates",
      galleryTitle: "Examples Gallery",
      gallerySub: "Explore downloadable, pre-certified production components built to Orthotect standards. Each example includes design tokens, FSM models, test coverage, and one-click source downloads.",
      gatesPill: "Deterministic Quality Assurance",
      gatesTitle: "The 5 Quality Gates Specification",
      gatesSub: "Transparent, evidence-based engineering breakdown of what each gate validates, its limitations, file targets, and corresponding test suites.",
      installPill: "Developer Tooling & CLI",
      installTitle: "Installation & CLI Usage",
      installSub: "Orthotect provides zero-config command line tools to scaffold, compile, and verify projects deterministically in local environments and GitHub Actions CI.",
      footerCopy: "Orthotect v1.5.0 © 2026. Certified for Autonomous Coding Agents: Antigravity, Claude Code, Cursor, Codex, Grok."
    },
    ar: {
      brandDesc: "استوديو المهارات v1.5.0",
      navHome: "الرئيسية",
      navCatalog: "كتالوج المهارات",
      navPlayground: "المختبر التفاعلي",
      navBuilder: "منشئ المهارات",
      navGallery: "الأمثلة الجاهزة",
      navGates: "بوابات الجودة",
      navInstall: "التثبيت والاستخدام",
      heroBadge: "v1.5.0 • معيار الجودة الحتمية للوكلاء البرمجيين المستقلين",
      heroTitle: "هندسة الواجهات الحتمية و<span class=\"hero-gradient-text\">بوابات الجودة أثناء التشغيل</span>",
      heroSub: "توقف عن قبول كود الواجهات العشوائي. يفرض أورثوتكت تباين WCAG AAA الرياضي، وخواص CSS المنطقية 100%، وآلات الحالة المنتهية FSM، وانعدام الـ Layout Shift في بوابات متوازية تحت 400ms.",
      ctaPlayground: "فتح المختبر التفاعلي",
      ctaCatalog: "تصفح كتالوج المهارات",
      ctaBuilder: "بناء مهارة مخصصة",
      proofGates: "بوابات فحص حتمية",
      proofTests: "اختبارات نجحت بنسبة 100%",
      proofLatency: "زمن الفحص المتوازي",
      proofDeps: "اعتماديات التشغيل (صفر حشو)",
      proofBidi: "خواص CSS المنطقية",
      pipelinePill: "دورة حياة الهندسة الذاتية",
      pipelineTitle: "مسار عمل أورثوتكت أثناء التشغيل",
      pipelineSub: "كيف تتحول تعليمات الوكيل إلى كود إنتاجي معتمد ومثبت رياضيًا عبر البوابات الحتمية.",
      step1Title: "مواصفة المهارة",
      step1Desc: "يحمّل الوكيل مبادئ النطاق الهندسي، وعقود توكنز DTCG، ومخططات انتقالات FSM.",
      step2Title: "توليد الكود",
      step2Desc: "ينشئ نموذج الذكاء الاصطناعي واجهة ترتبط حصريًا بتوكنز الألوان الدلالية ومعالجات آلة الحالة.",
      step3Title: "5 بوابات حتمية",
      step3Desc: "فحص رياضي متوازٍ لشجرة AST: تباين الألوان، الإحداثيات المنطقية، سلامة FSM، وموازنة DOM.",
      step4Title: "إصدار إنتاجي معتمد",
      step4Desc: "كود موثق بانعدام CLS يُدمج في main مباشرة ويدخل الإنتاج دون حاجة لإعادة صياغة بشرية.",
      catalogPill: "مهارات متزامنة مع المستودع",
      catalogTitle: "كتالوج مهارات أورثوتكت",
      catalogSub: "استكشف المهارات الست المثبتة في skills/. تقدم كل مهارة تعليمات نظام واضحة وقيودًا حازمة وبوابات تحقق مخصصة لوكلاء البرمجة.",
      playgroundPill: "المختبر الحي للمكونات",
      playgroundTitle: "مختبر المهارات التفاعلي",
      playgroundSub: "تفاعل مع 7 مكونات مؤسسية مبنية وفق مهارات أورثوتكت. بدّل الثيم والاتجاه وكثافة المسافات لملاحظة السلوك الحتمي الموثوق.",
      builderPill: "تأليف المهارات التفاعلي",
      builderTitle: "منشئ مهارات أورثوتكت",
      builderSub: "أنشئ مواصفات SKILL.md جاهزة للإنتاج ومخصصة لـ Antigravity وClaude Code وCursor وCodex مع معاينة حية وتحميل مباشر.",
      galleryPill: "قوالب إنتاجية معتمدة",
      galleryTitle: "معرض الأمثلة المعتمدة",
      gallerySub: "استكشف مكونات إنتاجية قابلة للتنزيل مبنية وفق معايير أورثوتكت، تشمل توكنز التصميم ونماذج FSM والاختبارات.",
      gatesPill: "ضمان الجودة الحتمي",
      gatesTitle: "مواصفة بوابات الجودة الخمس",
      gatesSub: "تشريح هندسي شفاف ومبني على الأدلة لما تفحصه كل بوابة وحدودها والملفات المستهدفة والاختبارات المرتبطة بها.",
      installPill: "أدوات المطور وسطر الأوامر",
      installTitle: "التثبيت وأوامر الاستخدام",
      installSub: "يوفر أورثوتكت أدوات سطر أوامر خفيفة لتهيئة المشاريع وترجمة التوكنز وفحص الكود حتميًا في البيئة المحلية وسير العمل CI.",
      footerCopy: "أورثوتكت v1.5.0 © 2026. معتمد لوكلاء البرمجة الذاتية: Antigravity وClaude Code وCursor وCodex وGrok."
    }
  };

  function applyLanguage(lang) {
    currentLang = lang;
    currentDir = lang === "ar" ? "rtl" : "ltr";
    document.documentElement.setAttribute("dir", currentDir);
    document.documentElement.setAttribute("lang", lang);
    localStorage.setItem("ortho_lang", lang);
    localStorage.setItem("ortho_dir", currentDir);

    const langBtnText = document.getElementById("langBtnText");
    if (langBtnText) {
      langBtnText.textContent = lang === "ar" ? "English" : "العربية";
    }

    const dict = bidiDict[lang] || bidiDict.en;
    Object.keys(dict).forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.innerHTML = dict[id];
      }
    });
  }

  const bidiToggleBtn = document.getElementById("bidiToggleBtn");
  if (bidiToggleBtn) {
    bidiToggleBtn.addEventListener("click", () => {
      applyLanguage(currentLang === "en" ? "ar" : "en");
    });
  }
  applyLanguage(currentLang);

  // =========================================================================
  // 4. SKILL CATALOG DATA & RENDERER
  // =========================================================================
  const skillsData = [
    {
      id: "orthotect-doctrine",
      name: "orthotect-doctrine",
      category: "architecture",
      title: "The 7 Non-Negotiable Laws of Interface Engineering",
      purpose: "Enforces the foundational 7 Laws of Interface Engineering for autonomous AI agents, eliminating probabilistic slop, uncalibrated visual noise, and physical coordinate anti-patterns.",
      problem: "AI models default to generic gradients, arbitrary hex colors, and physical coordinates (margin-left), breaking internationalization and accessibility.",
      when: "Activate first on every frontend task, landing page, component architecture, or UI refactoring session.",
      inputs: "UI component requirements, user prompt, target platform constraints.",
      outputs: "Certified production markup conforming to all 7 Laws (DTCG tokens, logical properties, FSM).",
      gates: "gate_contrast_wcag, gate_bidi_logical, gate_fsm_integrity, gate_no_slop, gate_cwv_budget",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-doctrine/SKILL.md",
      prompt: "Execute task adhering strictly to the 7 Non-Negotiable Laws of Interface Engineering in skills/orthotect-doctrine/SKILL.md."
    },
    {
      id: "orthotect-gates",
      name: "orthotect-gates",
      category: "architecture",
      title: "Deterministic Quality Gates Execution",
      purpose: "Runs the 5 parallel mathematical and AST quality gates in sub-400ms to verify contrast, logical properties, state machines, and layout-shift budgets.",
      problem: "Traditional CI linting passes broken accessibility and layout shifts because it lacks AST-aware DOM depth and CSS box-sizing mathematical models.",
      when: "Trigger before creating commits, opening PRs, or completing autonomous implementation loops.",
      inputs: "Target source directory containing HTML, CSS, or DTCG token files.",
      outputs: "Verification report (CLI console, JSON, or Markdown) certifying zero defects or halting build with exact violation lines.",
      gates: "All 5 Orthotect Gates",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-gates/SKILL.md",
      prompt: "Verify target codebase using Orthotect quality gates: npx orthotect verify ./src."
    },
    {
      id: "orthotect-bidi",
      name: "orthotect-bidi",
      category: "internationalization",
      title: "True Bidirectional (BiDi) & Logical Properties Engineering",
      purpose: "Guarantees 100% directional neutrality across Arabic (RTL) and English (LTR) by enforcing modern CSS Logical Properties.",
      problem: "95% of AI-generated components use margin-left, padding-right, and left:0, which completely invert and break in right-to-left languages.",
      when: "Use whenever authoring, reviewing, or styling any component, navigation bar, or layout container.",
      inputs: "Component CSS rules, layout specifications.",
      outputs: "Pure logical property stylesheets using margin-inline, padding-inline, inset-inline, and text-align: start.",
      gates: "gate_bidi_logical.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-bidi/SKILL.md",
      prompt: "Engineer interface with 100% bidirectional symmetry using CSS logical properties per skills/orthotect-bidi/SKILL.md."
    },
    {
      id: "orthotect-tokens",
      name: "orthotect-tokens",
      category: "tokens",
      title: "W3C DTCG 3-Tier Design Tokens & Multi-Theme Compiler",
      purpose: "Transforms 3-tier DTCG token JSON (primitives, semantics, ergonomics, motion) into production CSS variables with compile-time WCAG contrast certification.",
      problem: "Hardcoded colors lead to theme fragmentation, uncalibrated visual hierarchy, and contrast failures.",
      when: "Use when creating color palettes, type scales, spacing scales, or setting up multi-brand design systems.",
      inputs: "core/tokens/*.json schema files.",
      outputs: "Compiled tokens.css with :root and [data-theme='dark'] scopes, certifying WCAG AAA contrast in the header comment.",
      gates: "gate_contrast_wcag.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-tokens/SKILL.md",
      prompt: "Compile W3C DTCG tokens with mathematical contrast verification: npx orthotect compile core/tokens --out tokens.css."
    },
    {
      id: "orthotect-fsm",
      name: "orthotect-fsm",
      category: "fsm",
      title: "Finite State Machine (FSM) Interface Engineering",
      purpose: "Architects interactive UI components as resilient Finite State Machines with BFS graph reachability, double-submission locks, and error recovery.",
      problem: "AI code commonly creates deadlocks, leaves buttons enabled during async fetch calls, and fails to restore focus on modal close.",
      when: "Mandatory for modals, dialogs, form submission buttons, data grids, multi-step wizards, and async loaders.",
      inputs: "core/fsm/*.json state machine definition schemas.",
      outputs: "Mathematically deadlock-free interactive components with active in-engine submission locks.",
      gates: "gate_fsm_integrity.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-fsm/SKILL.md",
      prompt: "Implement interactive component governed strictly by FSM schema in skills/orthotect-fsm/SKILL.md."
    },
    {
      id: "orthotect-dashboard",
      name: "orthotect-dashboard",
      category: "dashboard",
      title: "High-Density Zero-CLS Telemetry & SVG Consoles",
      purpose: "Engineers cognitive-ergonomic enterprise dashboards and analytics consoles with inline SVG sparklines, zero layout shift (CLS = 0.00), and full RTL symmetry.",
      problem: "Dashboards built with heavy client chart libraries suffer from flash-of-unstyled-content, layout shifts, and RTL layout inversion.",
      when: "Use when designing monitoring consoles, SaaS analytics, trading terminals, or high-density metrics grids.",
      inputs: "Telemetry data streams, metric thresholds, time-series data.",
      outputs: "Zero-dependency inline SVG charts with bounded aspect-ratios and accessible numeric telemetry.",
      gates: "gate_cwv_budget.mjs, gate_contrast_wcag.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-dashboard/SKILL.md",
      prompt: "Build high-density enterprise dashboard with inline SVG telemetry and zero layout shift per skills/orthotect-dashboard/SKILL.md."
    }
  ];

  function renderSkills(category = "all", query = "") {
    const container = document.getElementById("skillsContainer");
    if (!container) return;

    const filtered = skillsData.filter(s => {
      const matchCat = category === "all" || s.category === category;
      const q = query.toLowerCase();
      const matchQuery = !q || s.name.includes(q) || s.title.toLowerCase().includes(q) || s.purpose.toLowerCase().includes(q);
      return matchCat && matchQuery;
    });

    if (filtered.length === 0) {
      container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--ortho-text-muted);">No skills match your search criteria.</div>`;
      return;
    }

    container.innerHTML = filtered.map(s => `
      <div class="skill-card">
        <div class="skill-card-hdr">
          <span class="skill-badge">${s.category.toUpperCase()}</span>
          <span style="font-size: 0.75rem; color: var(--ortho-text-muted); font-family: var(--font-mono);">skills/${s.name}</span>
        </div>
        <h3 class="skill-title">${s.title}</h3>
        <p class="skill-desc">${s.purpose}</p>
        <div class="skill-meta-box">
          <div class="skill-meta-item"><strong>When to Use:</strong> ${s.when}</div>
          <div class="skill-meta-item"><strong>Enforced Gates:</strong> <code>${s.gates}</code></div>
        </div>
        <div class="skill-actions-row">
          <button class="btn-ctrl-accent btn-copy-skill-prompt" data-prompt="${encodeURIComponent(s.prompt)}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
            <span>Copy Prompt</span>
          </button>
          <a href="${s.githubUrl}" target="_blank" rel="noopener" class="btn-ctrl" style="text-decoration: none;">
            <span>GitHub Source</span>
          </a>
        </div>
      </div>
    `).join("");

    // Attach copy prompt listeners
    container.querySelectorAll(".btn-copy-skill-prompt").forEach(btn => {
      btn.addEventListener("click", () => {
        const promptText = decodeURIComponent(btn.getAttribute("data-prompt") || "");
        navigator.clipboard.writeText(promptText).then(() => {
          const original = btn.innerHTML;
          btn.innerHTML = `<span>✓ Copied!</span>`;
          setTimeout(() => { btn.innerHTML = original; }, 2000);
        });
      });
    });
  }

  // Filter pills
  document.querySelectorAll(".filter-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      const cat = pill.getAttribute("data-cat") || "all";
      const q = document.getElementById("skillSearchInput") ? document.getElementById("skillSearchInput").value : "";
      renderSkills(cat, q);
    });
  });

  const skillSearchInput = document.getElementById("skillSearchInput");
  if (skillSearchInput) {
    skillSearchInput.addEventListener("input", (e) => {
      const activePill = document.querySelector(".filter-pill.active");
      const cat = activePill ? activePill.getAttribute("data-cat") : "all";
      renderSkills(cat, e.target.value);
    });
  }
  renderSkills();

  // =========================================================================
  // 5. INTERACTIVE SKILL PLAYGROUND ENGINE
  // =========================================================================
  const playgroundComponents = {
    analytics: {
      skill: "orthotect-dashboard",
      desc: "Builds zero-layout-shift high-density consoles with inline SVG telemetry and cognitive ergonomic hierarchy.",
      tokens: ["--ot-surface-canvas", "--ot-content-primary", "--ot-action-primary", "--ot-space-md", "--ot-radius-md"],
      prompt: "Build an enterprise SaaS telemetry dashboard with 4 inline SVG sparkline charts, median latency metrics, and zero layout shift using skills/orthotect-dashboard/SKILL.md.",
      render: () => `
        <div style="display: flex; flex-direction: column; gap: var(--pt-gap, 1rem);">
          <div style="display: flex; align-items: center; justify-content: space-between; border-block-end: 1px solid var(--ortho-border-subtle); padding-block-end: 0.75rem;">
            <div>
              <h2 style="font-size: 1.15rem; font-weight: 700;">Global Cluster Telemetry</h2>
              <p style="font-size: 0.8rem; color: var(--ortho-text-secondary);">Real-time stream across 12 distributed regions.</p>
            </div>
            <span class="badge-status badge-success">● Shards Operational</span>
          </div>

          <div class="analytics-metrics-grid">
            <div class="metric-card">
              <div class="metric-header">
                <span>Active Throughput</span>
                <span style="color: var(--ortho-success);">+14.2%</span>
              </div>
              <div class="metric-val">128,450 <span style="font-size: 0.8rem; font-weight: 500; color: var(--ortho-text-muted);">req/s</span></div>
              <div class="metric-chart">
                <svg width="100%" height="32" viewBox="0 0 160 32" fill="none" style="display: block;">
                  <polyline points="0,24 20,20 40,22 60,14 80,18 100,8 120,12 140,4 160,8" stroke="var(--ortho-accent-cyan)" stroke-width="2" stroke-linecap="round" />
                </svg>
              </div>
            </div>

            <div class="metric-card">
              <div class="metric-header">
                <span>Median P99 Latency</span>
                <span style="color: var(--ortho-success);">-8.1ms</span>
              </div>
              <div class="metric-val">24.6 <span style="font-size: 0.8rem; font-weight: 500; color: var(--ortho-text-muted);">ms</span></div>
              <div class="metric-chart">
                <svg width="100%" height="32" viewBox="0 0 160 32" fill="none" style="display: block;">
                  <polyline points="0,16 20,18 40,14 60,15 80,12 100,10 120,8 140,10 160,6" stroke="var(--ortho-success)" stroke-width="2" stroke-linecap="round" />
                </svg>
              </div>
            </div>

            <div class="metric-card">
              <div class="metric-header">
                <span>Error Budget</span>
                <span style="color: var(--ortho-warning);">99.98%</span>
              </div>
              <div class="metric-val">0.002%</div>
              <div class="metric-chart">
                <svg width="100%" height="32" viewBox="0 0 160 32" fill="none" style="display: block;">
                  <polyline points="0,28 30,26 60,28 90,24 120,28 150,26 160,28" stroke="var(--ortho-warning)" stroke-width="2" stroke-linecap="round" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      `
    },

    crm: {
      skill: "orthotect-doctrine",
      desc: "Architects pipeline stages, customer profiles, and interactive cards with 100% bidirectional symmetry.",
      tokens: ["--ot-surface-1", "--ot-surface-2", "--ot-border-medium", "--ot-text-primary", "--ot-accent-cyan"],
      prompt: "Create a modern CRM pipeline board with stage columns, deal values, and customer cards conforming to skills/orthotect-doctrine/SKILL.md.",
      render: () => `
        <div style="display: flex; flex-direction: column; gap: var(--pt-gap, 1rem);">
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
              <h2 style="font-size: 1.15rem; font-weight: 700;">Enterprise Deal Pipeline</h2>
              <p style="font-size: 0.8rem; color: var(--ortho-text-secondary);">4 active deals in evaluation stage.</p>
            </div>
            <button class="btn-ctrl-accent" style="padding-inline: 0.8rem; padding-block: 0.4rem;">+ New Deal</button>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--pt-gap, 1rem);">
            <div style="background-color: var(--ortho-surface-1); border: 1px solid var(--ortho-border-subtle); border-radius: var(--radius-md); padding: 0.75rem;">
              <div style="font-size: 0.75rem; font-weight: 700; color: var(--ortho-text-muted); text-transform: uppercase; margin-block-end: 0.5rem;">Qualification (2)</div>
              <div style="background-color: var(--ortho-surface-2); border: 1px solid var(--ortho-border-subtle); border-radius: var(--radius-sm); padding: 0.75rem; margin-block-end: 0.5rem;">
                <div style="font-weight: 700; font-size: 0.85rem;">Nexus Financial Bank</div>
                <div style="font-size: 0.75rem; color: var(--ortho-accent-cyan); font-family: var(--font-mono); margin-block: 0.2rem;">$180,000 / yr</div>
                <span class="badge-status badge-success">High Probability</span>
              </div>
              <div style="background-color: var(--ortho-surface-2); border: 1px solid var(--ortho-border-subtle); border-radius: var(--radius-sm); padding: 0.75rem;">
                <div style="font-weight: 700; font-size: 0.85rem;">Starlight Telecom</div>
                <div style="font-size: 0.75rem; color: var(--ortho-accent-cyan); font-family: var(--font-mono); margin-block: 0.2rem;">$95,000 / yr</div>
                <span class="badge-status badge-warning">Reviewing Security</span>
              </div>
            </div>

            <div style="background-color: var(--ortho-surface-1); border: 1px solid var(--ortho-border-subtle); border-radius: var(--radius-md); padding: 0.75rem;">
              <div style="font-size: 0.75rem; font-weight: 700; color: var(--ortho-text-muted); text-transform: uppercase; margin-block-end: 0.5rem;">Contract Review (1)</div>
              <div style="background-color: var(--ortho-surface-2); border: 1px solid var(--ortho-border-subtle); border-radius: var(--radius-sm); padding: 0.75rem;">
                <div style="font-weight: 700; font-size: 0.85rem;">AeroSpace Dynamics</div>
                <div style="font-size: 0.75rem; color: var(--ortho-accent-cyan); font-family: var(--font-mono); margin-block: 0.2rem;">$340,000 / yr</div>
                <span class="badge-status badge-success">Legal Approved</span>
              </div>
            </div>
          </div>
        </div>
      `
    },

    ecommerce: {
      skill: "orthotect-tokens",
      desc: "Guarantees tokenized color contrast and responsive tables for product inventories.",
      tokens: ["--ot-surface-canvas", "--ot-surface-1", "--ot-border-medium", "--ot-content-primary", "--ot-radius-sm"],
      prompt: "Design a retail e-commerce inventory management view with stock steppers, status tags, and pricing using skills/orthotect-tokens/SKILL.md.",
      render: () => `
        <div class="data-table-wrap">
          <div class="table-toolbar">
            <h2 style="font-size: 1rem; font-weight: 700;">Stock Inventory</h2>
            <input type="text" class="form-input" style="max-inline-size: 200px; padding: 0.35rem 0.6rem; font-size: 0.8rem;" placeholder="Filter inventory..." />
          </div>
          <table class="dt-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Stock Level</th>
                <th>Unit Price</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="font-family: var(--font-mono);">OT-NVME-01</td>
                <td><strong>4TB Enterprise NVMe Drive</strong></td>
                <td>48 units</td>
                <td>$320.00</td>
                <td><span class="badge-status badge-success">In Stock</span></td>
              </tr>
              <tr>
                <td style="font-family: var(--font-mono);">OT-GPU-A100</td>
                <td><strong>Tensor Acceleration Card 80GB</strong></td>
                <td>3 units</td>
                <td>$8,990.00</td>
                <td><span class="badge-status badge-danger">Critical Low</span></td>
              </tr>
              <tr>
                <td style="font-family: var(--font-mono);">OT-NIC-100G</td>
                <td><strong>Dual-Port 100GbE NIC Interface</strong></td>
                <td>14 units</td>
                <td>$540.00</td>
                <td><span class="badge-status badge-warning">Reordering</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      `
    },

    datatable: {
      skill: "orthotect-fsm",
      desc: "Demonstrates finite state machine transitions across Loading, Empty, Error, and Populated data states.",
      tokens: ["--ot-surface-1", "--ot-surface-2", "--ot-border-subtle", "--ot-accent-cyan", "--ot-radius-md"],
      prompt: "Implement an enterprise data table with explicit FSM edge states (loading, empty, error, ready) per skills/orthotect-fsm/SKILL.md.",
      render: () => `
        <div style="display: flex; flex-direction: column; gap: var(--pt-gap, 1rem);">
          <!-- State Switcher Bar for Playground Inspection -->
          <div style="display: flex; align-items: center; gap: 0.5rem; background-color: var(--ortho-surface-2); padding: 0.5rem 0.75rem; border-radius: var(--radius-sm); font-size: 0.8rem;">
            <span style="font-weight: 600;">Simulate FSM State:</span>
            <button class="btn-ctrl active-dt-state" data-state="ready" id="dtBtnActive" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">Ready (Normal)</button>
            <button class="btn-ctrl" data-state="loading" id="dtBtnSkeleton" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">Loading</button>
            <button class="btn-ctrl" data-state="empty" id="dtBtnEmpty" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">Empty</button>
            <button class="btn-ctrl" data-state="error" id="dtBtnError" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">Error</button>
          </div>

          <div id="dtDynamicArea" class="data-table-wrap">
            <!-- Populated state by default -->
            <table class="dt-table">
              <thead>
                <tr>
                  <th>User ID</th>
                  <th>Engineer</th>
                  <th>Department</th>
                  <th>Cluster Role</th>
                  <th>Security Posture</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style="font-family: var(--font-mono);">USR-904</td>
                  <td>Sarah Jenkins</td>
                  <td>Core Systems</td>
                  <td>Staff SRE</td>
                  <td><span class="badge-status badge-success">2FA Active</span></td>
                </tr>
                <tr>
                  <td style="font-family: var(--font-mono);">USR-812</td>
                  <td>Tarek Mansour</td>
                  <td>Architecture</td>
                  <td>Principal Architect</td>
                  <td><span class="badge-status badge-success">2FA Active</span></td>
                </tr>
                <tr>
                  <td style="font-family: var(--font-mono);">USR-743</td>
                  <td>Elena Rostova</td>
                  <td>Security Research</td>
                  <td>AppSec Auditor</td>
                  <td><span class="badge-status badge-success">2FA Active</span></td>
                </tr>
              </tbody>
            </table>
            <div class="dt-pagination">
              <span>Showing 1 to 3 of 48 records</span>
              <div style="display: flex; gap: 0.25rem;">
                <button class="btn-ctrl" style="padding: 0.2rem 0.5rem;">Prev</button>
                <button class="btn-ctrl" style="padding: 0.2rem 0.5rem;">1</button>
                <button class="btn-ctrl" style="padding: 0.2rem 0.5rem;">2</button>
                <button class="btn-ctrl" style="padding: 0.2rem 0.5rem;">Next</button>
              </div>
            </div>
          </div>
        </div>
      `
    },

    settings: {
      skill: "orthotect-bidi",
      desc: "Guarantees full RTL/LTR mirror symmetry across labels, inputs, and security toggles.",
      tokens: ["--ot-surface-1", "--ot-border-medium", "--ot-text-primary", "--ot-accent-cyan", "--ot-radius-sm"],
      prompt: "Build an account settings and security preferences view with password strength meter using skills/orthotect-bidi/SKILL.md.",
      render: () => `
        <div style="background-color: var(--ortho-surface-1); border: 1px solid var(--ortho-border-subtle); border-radius: var(--radius-md); padding: 1.5rem; max-inline-size: 560px;">
          <h2 style="font-size: 1.15rem; font-weight: 700; margin-block-end: 0.25rem;">Security Credentials</h2>
          <p style="font-size: 0.8rem; color: var(--ortho-text-secondary); margin-block-end: 1.25rem;">Update identity access and two-factor cryptographic keys.</p>

          <div class="form-group">
            <label class="form-label">Principal Email Address</label>
            <input type="email" class="form-input" value="engineer@enterprise.cloud" />
          </div>

          <div class="form-group">
            <label class="form-label">Update Session Key / Password</label>
            <input type="password" class="form-input" value="SuperSecure123!" />
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-block-start: 0.4rem;">
              <div style="flex: 1; block-size: 4px; background-color: var(--ortho-success); border-radius: 2px;"></div>
              <div style="flex: 1; block-size: 4px; background-color: var(--ortho-success); border-radius: 2px;"></div>
              <div style="flex: 1; block-size: 4px; background-color: var(--ortho-success); border-radius: 2px;"></div>
              <span style="font-size: 0.72rem; color: var(--ortho-success); font-weight: 600;">Strong</span>
            </div>
          </div>

          <div style="display: flex; align-items: center; justify-content: space-between; padding-block: 0.75rem; border-block-start: 1px solid var(--ortho-border-subtle); margin-block-start: 1rem;">
            <div>
              <div style="font-weight: 600; font-size: 0.85rem;">Hardware Two-Factor Auth (FIDO2)</div>
              <div style="font-size: 0.75rem; color: var(--ortho-text-secondary);">Enforce physical YubiKey authentication.</div>
            </div>
            <input type="checkbox" checked style="inline-size: 18px; block-size: 18px;" />
          </div>

          <div style="margin-block-start: 1.25rem;">
            <button class="btn-primary-action" style="inline-size: 100%; justify-content: center;">Save Credentials</button>
          </div>
        </div>
      `
    },

    modal: {
      skill: "orthotect-fsm",
      desc: "Full W3C APG accessible dialog with focus trapping, Escape handling, and double-click submission locks.",
      tokens: ["--ot-surface-1", "--ot-border-medium", "--ot-action-primary", "--ot-radius-md"],
      prompt: "Implement an accessible modal dialog conforming to core/fsm/modal-dialog.json with inert background shell.",
      render: () => `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem; background-color: var(--ortho-surface-1); border: 1px solid var(--ortho-border-subtle); border-radius: var(--radius-md); text-align: center;">
          <h2 style="font-size: 1.25rem; font-weight: 700; margin-block-end: 0.5rem;">FSM Governed Modal Dialog</h2>
          <p style="font-size: 0.85rem; color: var(--ortho-text-secondary); max-inline-size: 420px; margin-block-end: 1.5rem;">
            Click below to open the production modal dialog. Focus will be trapped inside the dialog with Tab/Shift+Tab, background will be inert, and Escape will restore focus.
          </p>
          <button id="pgTriggerModalBtn" class="btn-primary-action">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
            <span>Launch Modal Dialog</span>
          </button>
        </div>
      `
    },

    landing: {
      skill: "orthotect-doctrine",
      desc: "Responsive landing page hero with zero layout shift, semantic tokens, and directional symmetry.",
      tokens: ["--ot-canvas", "--ot-surface-1", "--ot-accent-cyan", "--ot-text-primary", "--ot-radius-pill"],
      prompt: "Build an enterprise responsive landing page hero with call to action and proof matrix using skills/orthotect-doctrine/SKILL.md.",
      render: () => `
        <div style="padding: 2rem; background-color: var(--ortho-surface-1); border: 1px solid var(--ortho-border-subtle); border-radius: var(--radius-md); text-align: center;">
          <div style="display: inline-block; font-size: 0.75rem; font-weight: 600; color: var(--ortho-accent-cyan); background-color: var(--ortho-surface-2); padding: 0.2rem 0.6rem; border-radius: var(--radius-pill); margin-block-end: 1rem;">
            Enterprise Autonomous Coding Standard
          </div>
          <h2 style="font-size: 1.8rem; font-weight: 800; line-height: 1.2; margin-block-end: 0.75rem;">
            Deterministic Interfaces for Critical Systems
          </h2>
          <p style="font-size: 0.95rem; color: var(--ortho-text-secondary); max-inline-size: 580px; margin-inline: auto; margin-block-end: 1.5rem;">
            Empower AI coding agents to produce accessible, high-performance interfaces certified by parallel mathematical AST gates.
          </p>
          <div style="display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap;">
            <button class="btn-primary-action">Explore Architecture</button>
            <button class="btn-secondary-action">View Telemetry</button>
          </div>
        </div>
      `
    }
  };

  function updatePlayground() {
    const comp = playgroundComponents[activePlaygroundComponent];
    if (!comp) return;

    // Render viewport
    const contentArea = document.getElementById("pgContentArea");
    if (contentArea) {
      contentArea.innerHTML = comp.render();
    }

    // Update meta inspector
    const skillBadge = document.getElementById("pgSkillBadge");
    if (skillBadge) skillBadge.textContent = comp.skill;

    const skillDesc = document.getElementById("pgSkillDesc");
    if (skillDesc) skillDesc.textContent = comp.desc;

    const tokensList = document.getElementById("pgTokensList");
    if (tokensList) {
      tokensList.innerHTML = comp.tokens.map(t => `<span class="token-chip">${t}</span>`).join("");
    }

    const promptCode = document.getElementById("pgPromptCode");
    if (promptCode) promptCode.textContent = comp.prompt;

    // Attach interactive listeners for the rendered component
    if (activePlaygroundComponent === "datatable") {
      document.querySelectorAll("[data-state]").forEach(b => {
        b.addEventListener("click", () => {
          // Switch state simulation
          const st = b.getAttribute("data-state");
          const area = document.getElementById("dtDynamicArea");
          if (!area) return;
          if (st === "loading") {
            area.innerHTML = `
              <div class="skeleton-loading-rows" style="display: flex; flex-direction: column; gap: 0.75rem; padding: 1.5rem; background-color: var(--ortho-surface-1);">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-block-end: 0.5rem;">
                  <div class="btn-spinner" style="inline-size: 16px; block-size: 16px;"></div>
                  <span style="font-size: 0.8rem; color: var(--ortho-text-muted);">Fetching cluster records (Skeleton loading state)...</span>
                </div>
                <div class="skeleton-bar" style="inline-size: 100%; block-size: 24px; background-color: var(--ortho-surface-2); border-radius: var(--radius-sm);"></div>
                <div class="skeleton-bar" style="inline-size: 85%; block-size: 24px; background-color: var(--ortho-surface-2); border-radius: var(--radius-sm);"></div>
                <div class="skeleton-bar" style="inline-size: 92%; block-size: 24px; background-color: var(--ortho-surface-2); border-radius: var(--radius-sm);"></div>
              </div>
            `;
          } else if (st === "empty") {
            area.innerHTML = `<div style="padding: 3rem; text-align: center; color: var(--ortho-text-muted);"><p>No matching records found in active cluster partition.</p></div>`;
          } else if (st === "error") {
            area.innerHTML = `<div style="padding: 2rem; background-color: var(--ortho-danger-bg); color: var(--ortho-danger); text-align: center; border-radius: var(--radius-sm);"><p>Gateway 504: Data Pipeline Failure. Failed to stream records.</p><button class="btn-ctrl" style="margin-block-start: 0.5rem;" onclick="location.hash='#playground'">Retry</button></div>`;
          } else {
            updatePlayground();
          }
        });
      });
    } else if (activePlaygroundComponent === "modal") {
      const trigger = document.getElementById("pgTriggerModalBtn");
      if (trigger) {
        trigger.addEventListener("click", openModal);
      }
    }
  }

  // Playground tab switching
  document.querySelectorAll(".pg-tab, .pg-btn").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".pg-tab, .pg-btn").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      activePlaygroundComponent = tab.getAttribute("data-pg") || tab.getAttribute("data-comp") || "analytics";
      updatePlayground();
    });
  });

  // Playground density toggles
  document.querySelectorAll("[data-pg-density]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-pg-density]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      playgroundDensity = btn.getAttribute("data-pg-density") || "default";
      const vp = document.getElementById("pgViewport");
      if (vp) {
        vp.classList.remove("density-compact", "density-default", "density-comfortable");
        vp.classList.add(`density-${playgroundDensity}`);
      }
    });
  });

  // Playground theme toggles
  document.querySelectorAll("[data-pg-theme]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-pg-theme]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      playgroundTheme = btn.getAttribute("data-pg-theme") || "dark";
      const vp = document.getElementById("pgViewport");
      if (vp) vp.setAttribute("data-theme", playgroundTheme);
    });
  });

  // Playground direction toggles
  document.querySelectorAll("[data-pg-dir]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-pg-dir]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      playgroundDir = btn.getAttribute("data-pg-dir") || "ltr";
      const vp = document.getElementById("pgViewport");
      if (vp) vp.setAttribute("dir", playgroundDir);
    });
  });

  // Copy agent prompt button
  const pgCopyPromptBtn = document.getElementById("pgCopyPromptBtn");
  if (pgCopyPromptBtn) {
    pgCopyPromptBtn.addEventListener("click", () => {
      const comp = playgroundComponents[activePlaygroundComponent];
      if (comp && comp.prompt) {
        navigator.clipboard.writeText(comp.prompt).then(() => {
          const original = pgCopyPromptBtn.innerHTML;
          pgCopyPromptBtn.innerHTML = `<span>✓ Prompt Copied!</span>`;
          setTimeout(() => { pgCopyPromptBtn.innerHTML = original; }, 2000);
        });
      }
    });
  }

  // Download template button
  const pgDownloadBtn = document.getElementById("pgDownloadBtn");
  if (pgDownloadBtn) {
    pgDownloadBtn.addEventListener("click", () => {
      const comp = playgroundComponents[activePlaygroundComponent];
      const templateHtml = `<!DOCTYPE html>
<html lang="en" dir="${playgroundDir}" data-theme="${playgroundTheme}">
<head>
  <meta charset="UTF-8" />
  <title>Orthotect — ${activePlaygroundComponent.toUpperCase()} Component</title>
  <link rel="stylesheet" href="https://seotarek.github.io/orthotect/styles.css" />
</head>
<body style="padding: 2rem; background-color: var(--ortho-canvas); color: var(--ortho-text-primary);">
  ${comp ? comp.render() : "<div>Component</div>"}
</body>
</html>`;
      const blob = new Blob([templateHtml], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `orthotect-${activePlaygroundComponent}-template.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  updatePlayground();

  // =========================================================================
  // 6. SKILL BUILDER ENGINE
  // =========================================================================
  function validateSkillBuilderFields() {
    const errors = [];
    const nameEl = document.getElementById("sbName");
    const descEl = document.getElementById("sbDesc");
    const stepsEl = document.getElementById("sbSteps");

    const rawName = nameEl ? nameEl.value.trim() : "";
    const rawDesc = descEl ? descEl.value.trim() : "";
    const rawSteps = stepsEl ? stepsEl.value.trim() : "";

    if (!rawName) errors.push({ field: "sbName", msg: "Skill name is required." });
    else if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(rawName)) errors.push({ field: "sbName", msg: "Name must be kebab-case (e.g. my-skill)." });

    if (!rawDesc) errors.push({ field: "sbDesc", msg: "Description is required." });
    else if (rawDesc.length > 1024) errors.push({ field: "sbDesc", msg: "Description must be under 1024 characters." });

    if (!rawSteps) errors.push({ field: "sbSteps", msg: "At least one execution step is required." });

    return errors;
  }

  function showSkillBuilderFieldErrors(errors) {
    // Clear all previous errors
    ["sbName", "sbDesc", "sbInputs", "sbSteps", "sbDod"].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.style.borderColor = "";
        el.removeAttribute("aria-invalid");
      }
      const errEl = document.getElementById(id + "Error");
      if (errEl) errEl.remove();
    });

    errors.forEach(({ field, msg }) => {
      const el = document.getElementById(field);
      if (!el) return;
      el.style.borderColor = "var(--ortho-error, #ef4444)";
      el.setAttribute("aria-invalid", "true");
      // Insert error message after the field
      const errEl = document.createElement("span");
      errEl.id = field + "Error";
      errEl.role = "alert";
      errEl.style.cssText = "color: var(--ortho-error, #ef4444); font-size: 0.78rem; display: block; margin-top: 2px;";
      errEl.textContent = msg;
      el.insertAdjacentElement("afterend", errEl);
    });
  }

  function updateSkillBuilderPreview() {
    const nameRaw = document.getElementById("sbName") ? document.getElementById("sbName").value.trim() : "";
    const descRaw = document.getElementById("sbDesc") ? document.getElementById("sbDesc").value.trim() : "";
    const stepsRaw = document.getElementById("sbSteps") ? document.getElementById("sbSteps").value.trim() : "";

    const name = nameRaw || "my-custom-skill";
    const desc = descRaw || "Skill description";
    const inputs = (document.getElementById("sbInputs") ? document.getElementById("sbInputs").value.trim() : "") || "Component requirements";
    const steps = stepsRaw || "1. Step one\n2. Step two";
    const dod = (document.getElementById("sbDod") ? document.getElementById("sbDod").value.trim() : "") || "All quality gates pass.";

    const agents = [];
    if (document.getElementById("agentAgy") && document.getElementById("agentAgy").checked) agents.push("Antigravity (AGY)");
    if (document.getElementById("agentClaude") && document.getElementById("agentClaude").checked) agents.push("Claude Code");
    if (document.getElementById("agentCursor") && document.getElementById("agentCursor").checked) agents.push("Cursor Agent");
    if (document.getElementById("agentCodex") && document.getElementById("agentCodex").checked) agents.push("OpenAI Codex");

    const gates = [];
    if (document.getElementById("gateContrast") && document.getElementById("gateContrast").checked) gates.push("WCAG 2.2 Mathematical Contrast (4.5:1)");
    if (document.getElementById("gateBidi") && document.getElementById("gateBidi").checked) gates.push("True BiDi & CSS Logical Properties (100%)");
    if (document.getElementById("gateFsm") && document.getElementById("gateFsm").checked) gates.push("Finite State Machine Integrity & Deadlock Prevention");
    if (document.getElementById("gateCwv") && document.getElementById("gateCwv").checked) gates.push("DOM Budget (<=32 levels) & Media Dimensions (CLS=0.00)");
    if (document.getElementById("gateSlop") && document.getElementById("gateSlop").checked) gates.push("Anti-Slop Pattern Inspector (No generic AI gradients)");

    const markdown = `---
name: ${name}
description: ${desc}
compatibility: [${agents.join(", ")}]
metadata:
  version: "1.0.0"
  standard: "Orthotect Interface Engineering Architecture"
---

# ${name}

${desc}

## Supported Autonomous Coding Agents
${agents.map(a => `- ${a}`).join("\n")}

## Prerequisites & Required Inputs
${inputs}

## Step-by-Step Execution Workflow
${steps}

## Enforced Orthotect Quality Gates
${gates.map(g => `- ${g}`).join("\n")}

## Definition of Done (Acceptance Criteria)
${dod}
`;

    const previewArea = document.getElementById("sbMarkdownPreview");
    if (previewArea) {
      previewArea.textContent = markdown;
    }

    const badge = document.getElementById("previewStatusBadge");
    if (badge) {
      // Use raw values to determine real validity
      if (nameRaw && descRaw && stepsRaw) {
        badge.textContent = "Valid Structure";
        badge.style.backgroundColor = "var(--ortho-success-bg)";
        badge.style.color = "var(--ortho-success)";
      } else {
        badge.textContent = "Incomplete Fields";
        badge.style.backgroundColor = "var(--ortho-warning-bg, #f59e0b22)";
        badge.style.color = "var(--ortho-warning, #f59e0b)";
      }
    }

    return markdown;
  }

  // Attach input listeners — clear field errors on typing
  ["sbName", "sbDesc", "sbInputs", "sbSteps", "sbDod"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("input", () => {
        // Clear error for this specific field on input
        const errEl = document.getElementById(id + "Error");
        if (errEl) errEl.remove();
        if (el.style.borderColor) el.style.borderColor = "";
        el.removeAttribute("aria-invalid");
        updateSkillBuilderPreview();
      });
    }
  });
  ["agentAgy", "agentClaude", "agentCursor", "agentCodex", "gateContrast", "gateBidi", "gateFsm", "gateCwv", "gateSlop"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("change", updateSkillBuilderPreview);
  });

  const btnCopySkill = document.getElementById("btnCopySkill");
  if (btnCopySkill) {
    btnCopySkill.addEventListener("click", () => {
      const errors = validateSkillBuilderFields();
      showSkillBuilderFieldErrors(errors);
      if (errors.length > 0) return; // Block copy if invalid
      const md = updateSkillBuilderPreview();
      navigator.clipboard.writeText(md).then(() => {
        const original = btnCopySkill.innerHTML;
        btnCopySkill.innerHTML = `<span>✓ SKILL.md Copied!</span>`;
        setTimeout(() => { btnCopySkill.innerHTML = original; }, 2000);
      });
    });
  }

  const btnDownloadSkill = document.getElementById("btnDownloadSkill");
  if (btnDownloadSkill) {
    btnDownloadSkill.addEventListener("click", () => {
      const errors = validateSkillBuilderFields();
      showSkillBuilderFieldErrors(errors);
      if (errors.length > 0) {
        // Scroll the first invalid field into view
        const firstField = document.getElementById(errors[0].field);
        if (firstField) firstField.scrollIntoView({ behavior: "smooth", block: "center" });
        return; // Block download if invalid
      }
      const md = updateSkillBuilderPreview();
      const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "SKILL.md";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  const btnResetSkill = document.getElementById("btnResetSkill");
  if (btnResetSkill) {
    btnResetSkill.addEventListener("click", () => {
      if (document.getElementById("sbName")) document.getElementById("sbName").value = "custom-data-grid";
      if (document.getElementById("sbDesc")) document.getElementById("sbDesc").value = "Engineer enterprise data grids with virtual scrolling and FSM loading states.";
      updateSkillBuilderPreview();
    });
  }
  updateSkillBuilderPreview();

  // =========================================================================
  // 7. EXAMPLES GALLERY RENDERER
  // =========================================================================
  const galleryItems = [
    {
      title: "Global Telemetry Console",
      desc: "High-density SVG latency monitors with zero cumulative layout shifts (CLS = 0.00).",
      skill: "orthotect-dashboard",
      tokens: "primitives.json, ergonomics.json",
      fsm: "core/fsm/data-table-loader.json"
    },
    {
      title: "CRM Deal Pipeline Board",
      desc: "Multi-stage deal flow with true bidirectional symmetry across LTR and RTL.",
      skill: "orthotect-bidi",
      tokens: "semantics.json, motion.json",
      fsm: "core/fsm/button-states.json"
    },
    {
      title: "Enterprise Data Grid",
      desc: "Sortable, searchable tabular grid with formal FSM states for loading, empty, and errors.",
      skill: "orthotect-fsm",
      tokens: "semantics.json, primitives.json",
      fsm: "core/fsm/data-table-loader.json"
    },
    {
      title: "Store Inventory Matrix",
      desc: "Product stock levels, interactive quantity steppers, and WCAG certified status pills.",
      skill: "orthotect-tokens",
      tokens: "semantics.json (light & dark)",
      fsm: "core/fsm/button-states.json"
    },
    {
      title: "FSM Modal Dialog System",
      desc: "Full W3C APG dialog compliance: focus trap, Escape key handling, and submission locking.",
      skill: "orthotect-fsm",
      tokens: "semantics.json, motion.json",
      fsm: "core/fsm/modal-dialog.json"
    },
    {
      title: "Identity & Credentials Portal",
      desc: "Account settings with live password strength calculation and two-factor auth.",
      skill: "orthotect-doctrine",
      tokens: "semantics.json, ergonomics.json",
      fsm: "core/fsm/button-states.json"
    }
  ];

  function renderGallery() {
    const container = document.getElementById("galleryContainer");
    if (!container) return;

    container.innerHTML = galleryItems.map(item => `
      <div class="gallery-card">
        <div class="gallery-card-thumb">
          <svg width="100%" height="80" viewBox="0 0 200 80" fill="none">
            <rect width="200" height="80" rx="8" fill="var(--ortho-surface-1)" />
            <line x1="20" y1="20" x2="180" y2="20" stroke="var(--ortho-border-medium)" stroke-width="2" />
            <rect x="20" y="32" width="40" height="10" rx="4" fill="var(--ortho-accent-cyan)" />
            <rect x="70" y="32" width="60" height="10" rx="4" fill="var(--ortho-border-subtle)" />
            <rect x="20" y="52" width="160" height="14" rx="4" fill="var(--ortho-surface-2)" />
          </svg>
        </div>
        <div class="gallery-card-body">
          <h3 class="gallery-card-title">${item.title}</h3>
          <p class="gallery-card-desc">${item.desc}</p>
          <div class="skill-meta-box">
            <div class="skill-meta-item"><strong>Skill:</strong> <code>${item.skill}</code></div>
            <div class="skill-meta-item"><strong>Tokens:</strong> ${item.tokens}</div>
          </div>
          <div class="gallery-card-actions">
            <a href="#playground" class="btn-ctrl-accent" style="text-decoration: none;">Interactive View</a>
            <a href="https://github.com/seotarek/orthotect" target="_blank" rel="noopener" class="btn-ctrl" style="text-decoration: none;">GitHub Source</a>
          </div>
        </div>
      </div>
    `).join("");
  }
  renderGallery();

  // =========================================================================
  // 8. QUALITY GATES SIMULATOR (EDUCATIONAL IN-BROWSER INSPECTOR)
  // =========================================================================
  const samplePresets = {
    golden: {
      name: "Gold Standard (All Gates Pass)",
      code: `/* Orthotect Certified Component */
.ortho-badge {
  display: inline-flex;
  align-items: center;
  padding-inline: 0.75rem;
  padding-block: 0.35rem;
  margin-inline-end: 0.5rem;
  background-color: #0f141c;
  color: #38bdf8; /* Contrast: 9.2:1 (WCAG AAA) */
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 6px;
  text-align: start;
}

<div class="ortho-badge">
  <img src="avatar.webp" width="16" height="16" alt="Avatar" />
  <span>Certified Enterprise UI</span>
</div>`
    },
    bidi_fail: {
      name: "BiDi Failure: Physical Coordinates",
      code: `/* Broken Non-Logical Component */
.user-card {
  margin-left: 24px;   /* VIOLATION: Must use margin-inline-start */
  padding-right: 16px; /* VIOLATION: Must use padding-inline-end */
  left: 0;             /* VIOLATION: Must use inset-inline-start */
  text-align: left;    /* VIOLATION: Must use text-align: start */
}`
    },
    contrast_fail: {
      name: "WCAG Failure: Low Contrast Text",
      code: `/* Low-Contrast AI Slop */
.muted-caption {
  background-color: #0d1117;
  color: #4b5563; /* VIOLATION: Contrast ratio is 2.3:1 (Fails AA & AAA) */
  font-size: 0.75rem;
}`
    },
    cwv_fail: {
      name: "CWV Failure: Missing Image Dimensions",
      code: `<!-- Layout Shift Hazard (CLS) -->
<div class="hero-banner">
  <img src="/banner.webp" alt="Preview Banner" class="responsive-img" />
  <!-- VIOLATION: Missing explicit integer width/height or style aspect-ratio -->
</div>`
    },
    slop_fail: {
      name: "Anti-Slop Failure: Generic Gradient & Emojis",
      code: `/* Banned Generative AI Slop */
.submit-btn {
  background: linear-gradient(to right, #8b5cf6, #ec4899); /* VIOLATION: Banned AI gradient */
  border: none;
}
<button class="submit-btn">
  Launch Platform ✨ <!-- VIOLATION: Uncalibrated emoji substitutes -->
</button>`
    },
    dom_fail: {
      name: "DOM Nesting Failure: Depth > 32",
      code: `<!-- DOM Depth Violation (> 32 Nested Levels) -->
<div><div><div><div><div><div><div><div><div><div>
<div><div><div><div><div><div><div><div><div><div>
<div><div><div><div><div><div><div><div><div><div>
<div><div><div><span>Exceeds max allowable tree depth (33 > 32)</span></div></div></div>
</div></div></div></div></div></div></div></div></div></div>
</div></div></div></div></div></div></div></div></div></div>
</div></div></div></div></div></div></div></div></div></div>`
    }
  };

  const sampleSelector = document.getElementById("sampleSelector");
  const codeEditor = document.getElementById("codeEditor");
  const gateTerminal = document.getElementById("gateTerminal");
  const runGateBtn = document.getElementById("runGateBtn");

  if (sampleSelector && codeEditor) {
    sampleSelector.addEventListener("change", () => {
      const preset = samplePresets[sampleSelector.value];
      if (preset) {
        codeEditor.value = preset.code;
      }
    });
    codeEditor.value = samplePresets.golden.code;
  }

  function parseHex(h) {
    if (!h) return null;
    let clean = h.replace("#", "").trim();
    if (clean.length === 3) clean = clean.split("").map(c => c + c).join("");
    if (clean.length !== 6) return null;
    const r = parseInt(clean.substring(0, 2), 16);
    const g = parseInt(clean.substring(2, 4), 16);
    const b = parseInt(clean.substring(4, 6), 16);
    return isNaN(r) || isNaN(g) || isNaN(b) ? null : [r, g, b];
  }

  function getLuminance(rgb) {
    const a = rgb.map(v => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
  }

  function getContrastRatio(hex1, hex2) {
    const rgb1 = parseHex(hex1);
    const rgb2 = parseHex(hex2);
    if (!rgb1 || !rgb2) return null;
    const l1 = getLuminance(rgb1);
    const l2 = getLuminance(rgb2);
    return ((Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)).toFixed(2);
  }

  if (runGateBtn && codeEditor && gateTerminal) {
    runGateBtn.addEventListener("click", () => {
      const code = codeEditor.value;
      const startTime = performance.now();
      gateTerminal.innerHTML = "";

      function logLine(msg) {
        gateTerminal.innerHTML += msg + "<br/>";
      }

      logLine("<strong style='color: #38bdf8;'>[ORTHOTECT DETERMINISTIC QUALITY GATES]</strong>");
      logLine("<em style='color: #94a3b8;'>⚠ Educational Client-Side Simulation — not actual gate execution. Run <code>orthotect verify</code> in CI for authoritative results.</em>");
      logLine("───────────────────────────────────────────────────────────────");

      let allPassed = true;

      // 1. BiDi Gate
      const bannedBidi = [
        { regex: /margin-left\s*:/i, name: "margin-left", alt: "margin-inline-start" },
        { regex: /margin-right\s*:/i, name: "margin-right", alt: "margin-inline-end" },
        { regex: /padding-left\s*:/i, name: "padding-left", alt: "padding-inline-start" },
        { regex: /padding-right\s*:/i, name: "padding-right", alt: "padding-inline-end" },
        { regex: /\bleft\s*:\s*0/i, name: "left: 0", alt: "inset-inline-start: 0" },
        { regex: /\bright\s*:\s*0/i, name: "right: 0", alt: "inset-inline-end: 0" },
        { regex: /text-align\s*:\s*left/i, name: "text-align: left", alt: "text-align: start" }
      ];
      let bidiViolations = [];
      bannedBidi.forEach(rule => {
        if (rule.regex.test(code)) bidiViolations.push(rule.name);
      });
      if (bidiViolations.length === 0) {
        logLine("<span style='color: #10b981;'>✅ PASS</span> <strong>True BiDi & Logical Properties:</strong> 100% compliant.");
      } else {
        allPassed = false;
        logLine("<span style='color: #ef4444;'>❌ FAIL</span> <strong>True BiDi Properties:</strong> Banned physical coordinates: " + bidiViolations.join(", "));
      }

      // 2. WCAG Contrast Gate
      const colors = code.match(/#[0-9a-fA-F]{3,6}/g);
      if (colors && colors.length >= 2) {
        const cr = getContrastRatio(colors[0], colors[1]);
        if (cr && parseFloat(cr) >= 4.5) {
          logLine(`<span style='color: #10b981;'>✅ PASS</span> <strong>WCAG 2.2 Contrast:</strong> ${cr}:1 (Certified AA / AAA)`);
        } else if (cr) {
          allPassed = false;
          logLine(`<span style='color: #ef4444;'>❌ FAIL</span> <strong>WCAG 2.2 Contrast:</strong> ${cr}:1 (Below 4.5:1 minimum threshold)`);
        }
      } else {
        logLine("<span style='color: #94a3b8;'>⏭ NOT_EVALUATED</span> <strong>WCAG 2.2 Contrast:</strong> Provide at least two hex color values to evaluate.");
      }

      // 3. FSM Integrity Gate — only evaluates when FSM JSON with 'states'+'initialState' is present
      (function() {
        let fsmJson = null;
        try {
          // eslint-disable-next-line no-useless-escape
          const jsonMatch = code.match(/\{[\s\S]*?"states"[\s\S]*?"initialState"[\s\S]*?\}/);
          if (jsonMatch) fsmJson = JSON.parse(jsonMatch[0]);
        } catch (_) { /* not valid JSON — skip */ }
        if (fsmJson && fsmJson.states && fsmJson.initialState) {
          const stateKeys = Object.keys(fsmJson.states);
          if (stateKeys.includes(fsmJson.initialState)) {
            logLine(`<span style='color: #10b981;'>✅ PASS</span> <strong>Finite State Machine Integrity:</strong> ${stateKeys.length} states, initialState "${fsmJson.initialState}" declared.`);
          } else {
            allPassed = false;
            logLine(`<span style='color: #ef4444;'>❌ FAIL</span> <strong>FSM Integrity:</strong> initialState "${fsmJson.initialState}" not declared in states object.`);
          }
        } else {
          logLine("<span style='color: #94a3b8;'>⏭ NOT_EVALUATED</span> <strong>Finite State Machine Integrity:</strong> No FSM JSON with 'states' + 'initialState' detected.");
        }
      })();

      // 4. Anti-Slop Gate
      const hasAiGradient = /(linear-gradient|from-purple|via-pink)/i.test(code);
      const hasEmoji = /[\u{1F300}-\u{1F9FF}]/u.test(code);
      if (hasAiGradient || hasEmoji) {
        allPassed = false;
        logLine("<span style='color: #ef4444;'>❌ FAIL</span> <strong>Anti-Slop Pattern Inspector:</strong> Banned generative AI gradient or raw emojis detected.");
      } else {
        logLine("<span style='color: #10b981;'>✅ PASS</span> <strong>Anti-Slop Pattern Inspector:</strong> Clean semantic surfaces.");
      }

      // 5. CWV Media & DOM Budget Gate
      const hasImg = /<img\b[^>]*>/i.test(code);
      if (hasImg) {
        const hasWidth = /\bwidth\s*=\s*["']?[1-9]\d*["']?/i.test(code);
        const hasHeight = /\bheight\s*=\s*["']?[1-9]\d*["']?/i.test(code);
        const hasAspectRatio = /\baspect-ratio\s*:\s*([0-9.]+)\s*\/\s*([0-9.]+)/i.test(code);
        if ((hasWidth && hasHeight) || hasAspectRatio) {
          logLine("<span style='color: #10b981;'>✅ PASS</span> <strong>DOM & Media Aspect-Ratio:</strong> Media dimensions bounded (CLS = 0.00).");
        } else {
          allPassed = false;
          logLine("<span style='color: #ef4444;'>❌ FAIL</span> <strong>DOM & Media Aspect-Ratio:</strong> <img> lacks positive integer width and height attributes.");
        }
      } else {
        logLine("<span style='color: #10b981;'>✅ PASS</span> <strong>DOM & Media Aspect-Ratio:</strong> Zero unbudgeted layout shift detected.");
      }

      // DOM Depth — real nesting depth via tag scanner (not a div count heuristic)
      (function() {
        let maxDepth = 0, currentDepth = 0;
        const tagRe = /<(\/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*\/?>/g;
        const voidTags = new Set(["area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"]);
        let m;
        while ((m = tagRe.exec(code)) !== null) {
          const isClose = m[1] === "/";
          const tagName = m[2].toLowerCase();
          if (voidTags.has(tagName)) continue;
          if (isClose) { currentDepth = Math.max(0, currentDepth - 1); }
          else { currentDepth++; maxDepth = Math.max(maxDepth, currentDepth); }
        }
        if (maxDepth > 32) {
          allPassed = false;
          logLine(`<span style='color: #ef4444;'>❌ FAIL</span> <strong>DOM Depth Budget:</strong> Max nesting depth (${maxDepth}) exceeds maximum allowable 32 levels.`);
        } else if (maxDepth > 0) {
          logLine(`<span style='color: #10b981;'>✅ PASS</span> <strong>DOM Depth Budget:</strong> Max nesting depth ${maxDepth} ≤ 32.`);
        }
      })();

      const elapsed = (performance.now() - startTime).toFixed(1);
      logLine("───────────────────────────────────────────────────────────────");
      if (allPassed) {
        logLine(`<strong style='color: #10b981;'>🎉 ALL GATES PASSED! Build certified for enterprise production (${elapsed}ms)</strong>`);
      } else {
        logLine(`<strong style='color: #ef4444;'>❌ BUILD REJECTED BY ORTHOTECT GATES (${elapsed}ms)</strong>`);
      }
    });
  }

  // =========================================================================
  // 9. GLOBAL ACCESSIBLE MODAL CONTROLLER
  // =========================================================================
  const modalBackdrop = document.getElementById("docsModalBackdrop");
  const modalCloseBtn = document.getElementById("docsModalCloseBtn");
  const modalCancelBtn = document.getElementById("docsModalCancelBtn");
  const modalSaveBtn = document.getElementById("docsModalSaveBtn");
  const modalRetryBtn = document.getElementById("docsModalRetryBtn");
  const shardInput = document.getElementById("docsShardInput");
  const errorBanner = document.getElementById("docsModalErrorBanner");
  const statusText = document.getElementById("docsModalStatusText");
  const spinner = document.getElementById("docsModalSpinner");
  const appShell = document.getElementById("appShell");

  let lastActiveElement = null;

  function openModal() {
    lastActiveElement = document.activeElement;
    if (modalBackdrop) modalBackdrop.style.display = "flex";
    if (modalBackdrop) modalBackdrop.setAttribute("aria-hidden", "false");
    if (appShell) {
      appShell.setAttribute("inert", "");
      appShell.setAttribute("aria-hidden", "true");
    }
    if (shardInput) shardInput.focus();
    if (errorBanner) errorBanner.style.display = "none";
    if (statusText) statusText.textContent = "";
  }

  function closeModal() {
    if (modalBackdrop) modalBackdrop.style.display = "none";
    if (modalBackdrop) modalBackdrop.setAttribute("aria-hidden", "true");
    if (appShell) {
      appShell.removeAttribute("inert");
      appShell.setAttribute("aria-hidden", "false");
    }
    if (lastActiveElement && typeof lastActiveElement.focus === "function") {
      lastActiveElement.focus();
    }
  }

  if (modalCloseBtn) modalCloseBtn.addEventListener("click", closeModal);
  if (modalCancelBtn) modalCancelBtn.addEventListener("click", closeModal);

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modalBackdrop && modalBackdrop.style.display === "flex") {
      closeModal();
    }
    // Focus Trap
    if (e.key === "Tab" && modalBackdrop && modalBackdrop.style.display === "flex") {
      const focusables = modalBackdrop.querySelectorAll("button, input, [tabindex]:not([tabindex='-1'])");
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
  });

  if (modalSaveBtn) {
    modalSaveBtn.addEventListener("click", () => {
      const val = shardInput ? shardInput.value.trim() : "";
      if (modalSaveBtn.disabled) return;

      modalSaveBtn.disabled = true;
      if (spinner) spinner.style.display = "inline-block";
      if (statusText) statusText.textContent = "Committing shard configuration...";

      setTimeout(() => {
        if (spinner) spinner.style.display = "none";
        modalSaveBtn.disabled = false;

        if (val.toLowerCase().includes("error")) {
          if (errorBanner) errorBanner.style.display = "block";
          if (modalRetryBtn) modalRetryBtn.style.display = "inline-block";
          if (statusText) statusText.textContent = "Operation failed (504 Timeout).";
        } else {
          if (statusText) statusText.textContent = "✓ Configuration saved!";
          setTimeout(closeModal, 800);
        }
      }, 700);
    });
  }

  if (modalRetryBtn) {
    modalRetryBtn.addEventListener("click", () => {
      modalRetryBtn.style.display = "none";
      if (errorBanner) errorBanner.style.display = "none";
      if (shardInput) shardInput.value = "shard-prod-01";
      if (modalSaveBtn) modalSaveBtn.click();
    });
  }

  // Copy buttons throughout site
  document.querySelectorAll("[data-copy]").forEach(btn => {
    btn.addEventListener("click", () => {
      const text = btn.getAttribute("data-copy") || "";
      navigator.clipboard.writeText(text).then(() => {
        const orig = btn.textContent;
        btn.textContent = "Copied!";
        setTimeout(() => { btn.textContent = orig; }, 1800);
      });
    });
  });
});
