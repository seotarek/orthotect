/**
 * ORTHOTECT v1.6.0 — Skill Studio & Interactive Demonstration Platform
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
  let playgroundTheme = currentTheme;
  let playgroundDir = "ltr";

  const validRoutes = ["home", "catalog", "playground", "builder", "gallery", "gates", "install"];

  // =========================================================================
  // 1b. MOBILE NAVIGATION DRAWER CONTROLLER & ACCESSIBLE FOCUS TRAP
  // =========================================================================
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const mobileMenuCloseBtn = document.getElementById("mobileMenuCloseBtn");
  const mobileNavDrawer = document.getElementById("mobileNavDrawer");
  const mobileNavBackdrop = document.getElementById("mobileNavBackdrop");
  let previousFocusedElement = null;

  function getFocusableElements(container) {
    if (!container) return [];
    return Array.from(container.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )).filter(el => el.offsetParent !== null || el === mobileMenuCloseBtn);
  }

  function openMobileNav() {
    if (!mobileNavDrawer) return;
    previousFocusedElement = document.activeElement;
    mobileNavDrawer.classList.add("open");
    mobileNavDrawer.setAttribute("aria-hidden", "false");
    if (mobileMenuBtn) mobileMenuBtn.setAttribute("aria-expanded", "true");
    document.body.classList.add("nav-open");
    if (mobileMenuCloseBtn) {
      setTimeout(() => mobileMenuCloseBtn.focus(), 10);
    }
  }

  function closeMobileNav() {
    if (!mobileNavDrawer) return;
    mobileNavDrawer.classList.remove("open");
    mobileNavDrawer.setAttribute("aria-hidden", "true");
    if (mobileMenuBtn) {
      mobileMenuBtn.setAttribute("aria-expanded", "false");
    }
    document.body.classList.remove("nav-open");
    if (previousFocusedElement && typeof previousFocusedElement.focus === 'function') {
      previousFocusedElement.focus();
    } else if (mobileMenuBtn) {
      mobileMenuBtn.focus();
    }
  }

  if (mobileMenuBtn) mobileMenuBtn.addEventListener("click", openMobileNav);
  if (mobileMenuCloseBtn) mobileMenuCloseBtn.addEventListener("click", closeMobileNav);
  if (mobileNavBackdrop) mobileNavBackdrop.addEventListener("click", closeMobileNav);

  // Accessible keyboard focus trap inside mobile nav drawer dialog
  if (mobileNavDrawer) {
    mobileNavDrawer.addEventListener("keydown", (e) => {
      if (!mobileNavDrawer.classList.contains("open")) return;
      if (e.key === "Tab") {
        const focusables = getFocusableElements(mobileNavDrawer);
        if (focusables.length === 0) {
          e.preventDefault();
          return;
        }
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
  }

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && mobileNavDrawer && mobileNavDrawer.classList.contains("open")) {
      closeMobileNav();
    }
  });


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

    // Update main desktop nav active indicator
    document.querySelectorAll(".nav-link").forEach(link => {
      if (link.getAttribute("data-tab") === route) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    // Update mobile nav active indicator
    document.querySelectorAll(".mobile-nav-link").forEach(link => {
      if (link.getAttribute("data-tab") === route) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    // Close mobile drawer on navigation
    closeMobileNav();

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Bind click on mobile nav links
  document.querySelectorAll(".mobile-nav-link").forEach(link => {
    link.addEventListener("click", () => {
      closeMobileNav();
    });
  });

  window.addEventListener("hashchange", handleRouting);
  handleRouting();

  // =========================================================================
  // 2. THEME ENGINE
  // =========================================================================
  function syncPlaygroundTheme(theme) {
    playgroundTheme = theme;
    const vp = document.getElementById("pgViewport");
    if (vp) vp.setAttribute("data-theme", theme);
    const pgThemeBtn = document.getElementById("pgThemeBtn");
    if (pgThemeBtn) {
      pgThemeBtn.textContent = `Theme: ${theme.charAt(0).toUpperCase() + theme.slice(1)}`;
    }
  }

  function applyTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("ortho_theme", theme);
    const themeBtnText = document.getElementById("themeBtnText");
    if (themeBtnText) {
      themeBtnText.textContent = theme === "dark" ? "Dark" : theme === "light" ? "Light" : "Contrast";
    }
    // Switch official brand logo according to theme
    document.querySelectorAll(".brand-logo-img").forEach(logo => {
      logo.src = theme === "light" ? "assets/brand/logo-light.svg" : "assets/brand/logo.svg";
    });
    syncPlaygroundTheme(theme);
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

  // Reactive theme observer for any external or automated theme mutation
  const themeObserver = new MutationObserver(mutations => {
    for (const mutation of mutations) {
      if (mutation.type === "attributes" && mutation.attributeName === "data-theme") {
        const observedTheme = document.documentElement.getAttribute("data-theme") || "dark";
        if (observedTheme !== currentTheme) {
          currentTheme = observedTheme;
          localStorage.setItem("ortho_theme", observedTheme);
          const themeBtnText = document.getElementById("themeBtnText");
          if (themeBtnText) {
            themeBtnText.textContent = observedTheme === "dark" ? "Dark" : observedTheme === "light" ? "Light" : "Contrast";
          }
        }
        document.querySelectorAll(".brand-logo-img").forEach(logo => {
          logo.src = observedTheme === "light" ? "assets/brand/logo-light.svg" : "assets/brand/logo.svg";
        });
        syncPlaygroundTheme(observedTheme);
      }
    }
  });
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  // =========================================================================
  // 3. BILINGUAL INTERNATIONALIZATION (BiDi)
  // =========================================================================
  const bidiDict = {
    en: {
      brandDesc: "v1.6.0",
      navHome: "Home",
      navCatalog: "Skill Catalog",
      navPlayground: "Playground",
      navBuilder: "Skill Builder",
      navGallery: "Examples",
      navGates: "Quality Gates",
      navInstall: "Install & Usage",
      mNavHome: "Home",
      mNavCatalog: "Skill Catalog",
      mNavPlayground: "Playground",
      mNavBuilder: "Skill Builder",
      mNavGallery: "Examples",
      mNavGates: "Quality Gates",
      mNavInstall: "Install & Usage",
      heroBadge: "v1.6.0 • Deterministic Quality Standard for Autonomous Coding Agents",
      heroTitle: "Deterministic Interface Engineering & <span class=\"hero-gradient-text\">Runtime Quality Gates</span>",
      heroSub: "Stop trusting probabilistic UI code. Orthotect enforces mathematical WCAG 2.2 token contrast, strict CSS logical properties, formal state machines, and media box bounding in parallel deterministic gates.",
      ctaPlayground: "Open Interactive Playground",
      ctaCatalog: "Browse Skill Catalog",
      ctaBuilder: "Build Custom Skill",
      proofGates: "Deterministic Gates",
      proofTests: "Automated Unit & E2E Tests",
      proofLatency: "Parallel Gate Latency",
      proofDeps: "Browser UI Dependencies",
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
      catalogSub: "Explore the 15 modular skills installed directly in skills/. Each skill provides explicit system instructions, constraints, and gate validation for autonomous coding agents.",
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
      footerCopy: "Orthotect v1.6.0 © 2026. Certified for Autonomous Coding Agents: Antigravity, Claude Code, Cursor, Codex, Grok."
    },
    ar: {
      brandDesc: "v1.6.0",
      navHome: "الرئيسية",
      navCatalog: "كتالوج المهارات",
      navPlayground: "المختبر التفاعلي",
      navBuilder: "منشئ المهارات",
      navGallery: "الأمثلة الجاهزة",
      navGates: "بوابات الجودة",
      navInstall: "التثبيت والاستخدام",
      mNavHome: "الرئيسية",
      mNavCatalog: "كتالوج المهارات",
      mNavPlayground: "المختبر التفاعلي",
      mNavBuilder: "منشئ المهارات",
      mNavGallery: "الأمثلة الجاهزة",
      mNavGates: "بوابات الجودة",
      mNavInstall: "التثبيت والاستخدام",
      heroBadge: "v1.6.0 • معيار الجودة الحتمية للوكلاء البرمجيين المستقلين",
      heroTitle: "هندسة الواجهات الحتمية و<span class=\"hero-gradient-text\">بوابات الجودة أثناء التشغيل</span>",
      heroSub: "توقف عن قبول كود الواجهات العشوائي. يفرض أورثوتكت تباين WCAG 2.2 للتوكنز، وصرامة خواص CSS المنطقية، ونزاهة آلات الحالة FSM، وتحديد أبعاد الوسائط في بوابات حتمية متوازية.",
      ctaPlayground: "فتح المختبر التفاعلي",
      ctaCatalog: "تصفح كتالوج المهارات",
      ctaBuilder: "بناء مهارة مخصصة",
      proofGates: "بوابات فحص حتمية",
      proofTests: "اختبارات نجحت بنسبة 100%",
      proofLatency: "زمن الفحص المتوازي",
      proofDeps: "اعتماديات واجهة المتصفح (صفر حشو)",
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
      catalogSub: "استكشف 15 مهارة معيارية مثبتة في skills/. تقدم كل مهارة تعليمات نظام واضحة وقيودًا حازمة وبوابات تحقق مخصصة لوكلاء البرمجة.",
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
      footerCopy: "أورثوتكت v1.6.0 © 2026. معتمد لوكلاء البرمجة الذاتية: Antigravity وClaude Code وCursor وCodex وGrok."
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
      id: "orthotect-uiux",
      name: "orthotect-uiux",
      category: "architecture",
      title: "Master UI/UX Design Intelligence & Orchestrator",
      purpose: "Orchestrates comprehensive UI/UX design intelligence, selects original style recipes, establishes 19-dimensional design reasoning, and binds intent tokens.",
      problem: "AI coding assistants generate disjointed, repetitive components that lack unified art direction and cohesive visual systems.",
      when: "Activate as central entry point for new feature workflows, landing pages, application redesigns, and design reasoning.",
      inputs: "Product brief, target user persona, domain constraints, visual preferences.",
      outputs: "Complete design reasoning model, chosen style recipe, and orchestrated implementation plan.",
      gates: "All 5 Orthotect Gates",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-uiux/SKILL.md",
      prompt: "Orchestrate interface design using Orthotect UI/UX design intelligence per skills/orthotect-uiux/SKILL.md."
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
      id: "orthotect-design-systems",
      name: "orthotect-design-systems",
      category: "tokens",
      title: "Enterprise Design System Architecture & Multi-Brand Theming",
      purpose: "Architects scalable multi-tier token hierarchies, component token bindings, and cross-framework design system pipelines.",
      problem: "Teams struggle with token drift, inconsistent naming, and painful multi-brand or white-label theming implementations.",
      when: "Use when establishing design systems, structuring token architecture, or building multi-brand theming layers.",
      inputs: "Brand color palettes, typography scales, elevation guidelines.",
      outputs: "Standardized W3C DTCG token architecture with semantic intent mappings and automated compiler targets.",
      gates: "gate_contrast_wcag.py, gate_no_slop.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-design-systems/SKILL.md",
      prompt: "Architect design system tokens with multi-theme support per skills/orthotect-design-systems/SKILL.md."
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
      id: "orthotect-forms",
      name: "orthotect-forms",
      category: "fsm",
      title: "Resilient Forms, Double-Submission Locks & Validation FSM",
      purpose: "Engineers rock-solid forms with async validation state machines, double-submission locks, inline error cues, and accessible labeling.",
      problem: "Users face lost form inputs, broken error states, double charges on repeated clicks, and unhelpful generic validation errors.",
      when: "Use when creating checkout flows, registration forms, settings panels, or multi-field operational inputs.",
      inputs: "Field validation schemas, submission endpoints, error response formats.",
      outputs: "Production-grade form components with permanent labels, ARIA error linking, and deterministic submission locks.",
      gates: "gate_fsm_integrity.py, gate_contrast_wcag.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-forms/SKILL.md",
      prompt: "Engineer resilient form with double-submit protection per skills/orthotect-forms/SKILL.md."
    },
    {
      id: "orthotect-components",
      name: "orthotect-components",
      category: "components",
      title: "Accessible UI Components & WAI-ARIA APG State Contracts",
      purpose: "Provides production-ready component contracts for Button, Input, Modal, Tabs, Dropdown, Table, and Card across 8 explicit states.",
      problem: "AI code generates visually plausible components that fail keyboard navigation, lack focus bounds, and neglect edge states.",
      when: "Use when building reusable component libraries, design system primitives, or interactive widgets.",
      inputs: "Component anatomy requirements, target framework (React, Vue, Svelte, Web Components, HTML).",
      outputs: "Accessible, fully keyboard-operable components with ARIA roles and visible focus indicators.",
      gates: "gate_fsm_integrity.py, gate_contrast_wcag.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-components/SKILL.md",
      prompt: "Author accessible component with 8 explicit states per skills/orthotect-components/SKILL.md."
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
    },
    {
      id: "orthotect-data-viz",
      name: "orthotect-data-viz",
      category: "dashboard",
      title: "Data Visualization Tokens & Accessible Telemetry Charts",
      purpose: "Builds high-density, accessible data visualizations, sparklines, and operational metrics using token-driven SVG geometry and tabular numbers.",
      problem: "Charts frequently lack color-contrast compliance, cause cumulative layout shifts, and fail screen-reader accessibility checks.",
      when: "Use when creating data charts, time-series telemetry, sparkline cards, or real-time operational graphs.",
      inputs: "Numeric datasets, chart type specifications, interval bounds.",
      outputs: "Token-bound SVG charts with tabular numerals, high-contrast metrics, and accessible alternative data tables.",
      gates: "gate_cwv_budget.mjs, gate_contrast_wcag.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-data-viz/SKILL.md",
      prompt: "Create accessible token-driven data visualization per skills/orthotect-data-viz/SKILL.md."
    },
    {
      id: "orthotect-accessibility",
      name: "orthotect-accessibility",
      category: "accessibility",
      title: "WCAG 2.2 AA/AAA Deterministic Accessibility Auditing",
      purpose: "Audits and certifies interfaces against WCAG 2.2 Level AA/AAA standards: contrast, keyboard traps, touch targets, and ARIA roles.",
      problem: "Automated linters miss cognitive traps, focus leaks, and touch target violations that degrade usability for assistive tech users.",
      when: "Mandatory review step for all public UI pages, interactive components, and production releases.",
      inputs: "HTML/CSS markup, component tree, interactive event handlers.",
      outputs: "Accessibility certification report with mathematical contrast proofs and focus-management audit.",
      gates: "gate_contrast_wcag.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-accessibility/SKILL.md",
      prompt: "Audit interface against WCAG 2.2 AA standards per skills/orthotect-accessibility/SKILL.md."
    },
    {
      id: "orthotect-visual-qa",
      name: "orthotect-visual-qa",
      category: "accessibility",
      title: "Automated Browser Visual Regression & Theme Contrast Gate",
      purpose: "Runs automated headless browser tests to verify rendered computed styles, dual-theme switching, and zero visual clash.",
      problem: "CSS-only tests miss browser-specific rendering bugs, theme desynchronization, and invisible text on computed background surfaces.",
      when: "Use when validating dual-theme changes, terminal viewports, playground components, or visual regressions.",
      inputs: "Rendered web pages, theme configurations, test viewports.",
      outputs: "Deterministic test run results proving computed contrast and zero visual clash.",
      gates: "test_docs_browser.py, gate_contrast_wcag.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-visual-qa/SKILL.md",
      prompt: "Execute automated browser visual QA test suite per skills/orthotect-visual-qa/SKILL.md."
    },
    {
      id: "orthotect-responsive",
      name: "orthotect-responsive",
      category: "responsive",
      title: "Adaptive Bento Layouts, Fluid Typography & Container Queries",
      purpose: "Engineers fluid responsive layouts using CSS Grid, container queries, and clamp() fluid typography across viewports 360px to 2560px.",
      problem: "Fixed-width breakpoints break on modern foldables and containerized dashboard widgets, causing layout clipping.",
      when: "Use when creating multi-column page layouts, responsive bento grids, or adaptive component systems.",
      inputs: "Viewport ranges, component container dimensions, content hierarchy.",
      outputs: "Zero-overflow responsive stylesheets with intrinsic container query adaptability and CLS = 0.",
      gates: "gate_no_slop.py, gate_cwv_budget.mjs",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-responsive/SKILL.md",
      prompt: "Build fluid responsive layout with container queries per skills/orthotect-responsive/SKILL.md."
    },
    {
      id: "orthotect-motion",
      name: "orthotect-motion",
      category: "motion",
      title: "Spring Physics Motion Tokens & Reduced-Motion Accessibility",
      purpose: "Implements physically grounded UI transitions using calibrated spring physics tokens and mandatory prefers-reduced-motion overrides.",
      problem: "Arbitrary CSS transitions (transition: all 0.2s) feel sluggish, trigger CPU layout recalculations, and cause vestibular discomfort.",
      when: "Use when adding transitions to dialogs, menus, tabs, hover states, and data card updates.",
      inputs: "Interactive component triggers, transition requirements.",
      outputs: "Hardware-accelerated CSS motion rules bounded by --ot-motion-snappy and --ot-motion-expressive.",
      gates: "gate_no_slop.py",
      githubUrl: "https://github.com/seotarek/orthotect/blob/main/skills/orthotect-motion/SKILL.md",
      prompt: "Implement spring physics motion with reduced-motion support per skills/orthotect-motion/SKILL.md."
    }
  ];

  function renderSkills(category = "all", query = "") {
    const container = document.getElementById("skillsContainer");
    if (!container) return;

    const filtered = skillsData.filter(s => {
      const matchCat = category === "all" || s.category === category ||
        (category === "tokens" && (s.category === "tokens" || s.id.includes("tokens") || s.id.includes("design-systems"))) ||
        (category === "components" && (s.category === "components" || s.category === "fsm")) ||
        (category === "accessibility" && (s.category === "accessibility" || s.id.includes("visual-qa"))) ||
        (category === "dashboard" && (s.category === "dashboard")) ||
        (category === "responsive" && (s.category === "responsive" || s.category === "motion"));
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
  const pgDensityBtn = document.getElementById("pgDensityBtn");
  if (pgDensityBtn) {
    pgDensityBtn.addEventListener("click", () => {
      const densities = ["default", "comfortable", "compact"];
      playgroundDensity = densities[(densities.indexOf(playgroundDensity) + 1) % densities.length];
      const vp = document.getElementById("pgViewport");
      if (vp) {
        vp.classList.remove("density-compact", "density-default", "density-comfortable");
        vp.classList.add(`density-${playgroundDensity}`);
      }
      pgDensityBtn.textContent = `Density: ${playgroundDensity.charAt(0).toUpperCase() + playgroundDensity.slice(1)}`;
    });
  }
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
      if (pgDensityBtn) {
        pgDensityBtn.textContent = `Density: ${playgroundDensity.charAt(0).toUpperCase() + playgroundDensity.slice(1)}`;
      }
    });
  });

  // Playground theme toggles
  const pgThemeBtn = document.getElementById("pgThemeBtn");
  if (pgThemeBtn) {
    pgThemeBtn.addEventListener("click", () => {
      const themes = ["dark", "light", "contrast"];
      playgroundTheme = themes[(themes.indexOf(playgroundTheme) + 1) % themes.length];
      const vp = document.getElementById("pgViewport");
      if (vp) vp.setAttribute("data-theme", playgroundTheme);
      pgThemeBtn.textContent = `Theme: ${playgroundTheme.charAt(0).toUpperCase() + playgroundTheme.slice(1)}`;
    });
  }
  document.querySelectorAll("[data-pg-theme]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-pg-theme]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      playgroundTheme = btn.getAttribute("data-pg-theme") || "dark";
      const vp = document.getElementById("pgViewport");
      if (vp) vp.setAttribute("data-theme", playgroundTheme);
      if (pgThemeBtn) {
        pgThemeBtn.textContent = `Theme: ${playgroundTheme.charAt(0).toUpperCase() + playgroundTheme.slice(1)}`;
      }
    });
  });

  // Playground direction toggles
  const pgBidiBtn = document.getElementById("pgBidiBtn");
  if (pgBidiBtn) {
    pgBidiBtn.addEventListener("click", () => {
      playgroundDir = playgroundDir === "ltr" ? "rtl" : "ltr";
      const vp = document.getElementById("pgViewport");
      if (vp) vp.setAttribute("dir", playgroundDir);
      pgBidiBtn.textContent = `BiDi: ${playgroundDir.toUpperCase()}`;
    });
  }
  document.querySelectorAll("[data-pg-dir]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-pg-dir]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      playgroundDir = btn.getAttribute("data-pg-dir") || "ltr";
      const vp = document.getElementById("pgViewport");
      if (vp) vp.setAttribute("dir", playgroundDir);
      if (pgBidiBtn) {
        pgBidiBtn.textContent = `BiDi: ${playgroundDir.toUpperCase()}`;
      }
    });
  });

  // CLI Quickstart Tabs & Copy Button
  const cliCommands = {
    init: "npx orthotect init",
    verify: "npx orthotect verify",
    compile: "npx orthotect compile core/tokens --out dist/tokens.css"
  };
  document.querySelectorAll(".cli-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".cli-tab").forEach(t => {
        t.classList.remove("active");
        t.setAttribute("aria-selected", "false");
      });
      tab.classList.add("active");
      tab.setAttribute("aria-selected", "true");
      const cmdKey = tab.getAttribute("data-cmd") || "init";
      const cmdText = document.getElementById("cliCommandText");
      if (cmdText && cliCommands[cmdKey]) {
        cmdText.textContent = cliCommands[cmdKey];
      }
    });
  });

  const cliCopyBtn = document.getElementById("cliCopyBtn");
  if (cliCopyBtn) {
    cliCopyBtn.addEventListener("click", () => {
      const cmdText = document.getElementById("cliCommandText");
      if (cmdText) {
        navigator.clipboard.writeText(cmdText.textContent.trim()).then(() => {
          const original = cliCopyBtn.textContent;
          cliCopyBtn.textContent = "✓ Copied";
          setTimeout(() => { cliCopyBtn.textContent = original; }, 2000);
        });
      }
    });
  }

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
  function formatYamlString(str) {
    if (!str) return '""';
    if (str.includes("\n")) {
      return "|\n" + str.split("\n").map(l => "    " + l).join("\n");
    }
    if (/[:#\[\]{}%@&*!`|>'"]/.test(str) || str.trim() !== str) {
      return JSON.stringify(str);
    }
    return str;
  }

  function validateSkillBuilderFields() {
    const errors = [];
    const nameEl = document.getElementById("sbName");
    const descEl = document.getElementById("sbDesc");
    const stepsEl = document.getElementById("sbSteps");

    const rawName = nameEl ? nameEl.value.trim() : "";
    const rawDesc = descEl ? descEl.value.trim() : "";
    const rawSteps = stepsEl ? stepsEl.value.trim() : "";

    if (!rawName) {
      errors.push({ field: "sbName", msg: "Skill name is required." });
    } else if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(rawName)) {
      errors.push({ field: "sbName", msg: "Name must be kebab-case (e.g. my-custom-skill, lowercase alphanumeric and hyphens)." });
    } else if (rawName.length < 3 || rawName.length > 64) {
      errors.push({ field: "sbName", msg: "Name length must be between 3 and 64 characters." });
    }

    if (!rawDesc) {
      errors.push({ field: "sbDesc", msg: "Description is required." });
    } else if (rawDesc.length < 10) {
      errors.push({ field: "sbDesc", msg: "Description must be at least 10 characters." });
    } else if (rawDesc.length > 1024) {
      errors.push({ field: "sbDesc", msg: "Description must be under 1024 characters." });
    }

    if (!rawSteps) {
      errors.push({ field: "sbSteps", msg: "At least one execution step is required." });
    }

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
description: ${formatYamlString(desc)}
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
      const errors = validateSkillBuilderFields();
      if (errors.length === 0) {
        badge.textContent = "Structure Validated (Client AST)";
        badge.style.backgroundColor = "var(--ortho-success-bg, rgba(16, 185, 129, 0.2))";
        badge.style.color = "var(--ortho-success, #10b981)";
      } else {
        badge.textContent = "Incomplete / Invalid Input";
        badge.style.backgroundColor = "var(--ortho-warning-bg, rgba(245, 158, 11, 0.15))";
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
  // 7. EXAMPLES GALLERY RENDERER (50 PRODUCTION TEMPLATES)
  // =========================================================================
  let activeGalleryCluster = "all";
  let gallerySearchQuery = "";

  function getGalleryItems() {
    if (window.ORTHOTECT_GALLERY_TEMPLATES && Array.isArray(window.ORTHOTECT_GALLERY_TEMPLATES)) {
      return window.ORTHOTECT_GALLERY_TEMPLATES;
    }
    return galleryItems;
  }

  function renderGallery() {
    const container = document.getElementById("galleryContainer");
    if (!container) return;

    const allItems = getGalleryItems();
    const filtered = allItems.filter(item => {
      // Cluster filter
      const matchesCluster = (activeGalleryCluster === "all") || (item.cluster === activeGalleryCluster);
      if (!matchesCluster) return false;

      // Search query filter
      if (!gallerySearchQuery) return true;
      const q = gallerySearchQuery.toLowerCase();
      return (
        item.title.toLowerCase().includes(q) ||
        item.desc.toLowerCase().includes(q) ||
        (item.skill && item.skill.toLowerCase().includes(q)) ||
        (item.tokens && item.tokens.toLowerCase().includes(q)) ||
        (item.cluster_name && item.cluster_name.toLowerCase().includes(q))
      );
    });

    const countBadge = document.getElementById("galleryCountBadge");
    if (countBadge) {
      countBadge.textContent = `Showing ${filtered.length} of ${allItems.length} templates`;
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 3rem 1rem; text-align: center; background: var(--ortho-surface-1); border: 1px dashed var(--ortho-border-medium); border-radius: 12px;">
          <div style="font-size: 1.5rem; margin-block-end: 0.5rem;">🔍 No templates found</div>
          <p style="color: var(--ortho-text-secondary); max-width: 480px; margin-inline: auto;">No production templates match "${gallerySearchQuery}". Try clearing search filters or selecting another cluster tab.</p>
          <button type="button" class="btn-ctrl" onclick="document.getElementById('gallerySearchInput').value=''; window.resetGallerySearch();" style="margin-block-start: 1rem;">Reset Filters</button>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(item => `
      <div class="gallery-card" data-cluster="${item.cluster || 'all'}">
        <div class="gallery-card-thumb">
          <img src="${item.thumbnail || 'assets/thumbnails/' + item.id + '.webp'}"
               alt="${item.title ? item.title.replace(/"/g, '&quot;') : 'Template preview'}"
               class="gallery-card-img"
               loading="lazy"
               width="400"
               height="200">
          <span class="gallery-cluster-badge">
            ${item.cluster_name ? item.cluster_name : 'Cluster ' + (item.cluster_num || '1')}
          </span>
        </div>
        <div class="gallery-card-body">
          <h3 class="gallery-card-title">${item.title}</h3>
          <p class="gallery-card-desc">${item.desc}</p>
          <div class="skill-meta-box">
            <div class="skill-meta-item"><strong>Target Skill:</strong> <code>${item.skill}</code></div>
            <div class="skill-meta-item"><strong>Tokens:</strong> ${item.tokens}</div>
          </div>
          <div class="gallery-card-actions">
            ${item.template_url ? `
              <a href="${item.template_url}" target="_blank" rel="noopener" class="btn-ctrl-accent gallery-open-btn">
                <span>Open Live</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              </a>
            ` : ''}
            <a href="#playground" class="btn-ctrl gallery-interactive-btn">Interactive View</a>
          </div>
        </div>
      </div>
    `).join("");
  }

  // Setup Gallery Event Listeners
  function initGalleryControls() {
    const filterButtons = document.querySelectorAll(".gallery-filter-btn");
    filterButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        filterButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activeGalleryCluster = btn.getAttribute("data-cluster") || "all";
        renderGallery();
      });
    });

    const searchInput = document.getElementById("gallerySearchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        gallerySearchQuery = e.target.value.trim();
        renderGallery();
      });
    }

    window.resetGallerySearch = function() {
      gallerySearchQuery = "";
      activeGalleryCluster = "all";
      document.querySelectorAll(".gallery-filter-btn").forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-cluster") === "all");
      });
      renderGallery();
    };
  }

  // Initialize gallery
  renderGallery();
  initGalleryControls();

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
      let passedCount = 0;
      let failedCount = 0;
      let notEvaluatedCount = 0;

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
        passedCount++;
        logLine("<span style='color: #10b981;'>✅ PASS</span> <strong>True BiDi & Logical Properties:</strong> 100% compliant.");
      } else {
        allPassed = false;
        failedCount++;
        logLine("<span style='color: #ef4444;'>❌ FAIL</span> <strong>True BiDi Properties:</strong> Banned physical coordinates: " + bidiViolations.join(", "));
      }

      // 2. WCAG Contrast Gate — requires explicit foreground color and background color pair
      const colorMatch = code.match(/(?:^|[^-])\bcolor\s*:\s*(#[0-9a-fA-F]{3,6})\b/i);
      const bgMatch = code.match(/\bbackground(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})\b/i);
      if (colorMatch && bgMatch) {
        const fg = colorMatch[1];
        const bg = bgMatch[1];
        const cr = getContrastRatio(fg, bg);
        if (cr && parseFloat(cr) >= 4.5) {
          passedCount++;
          logLine(`<span style='color: #10b981;'>✅ PASS</span> <strong>WCAG 2.2 Contrast:</strong> ${cr}:1 (Certified AA / AAA) between ${fg} and ${bg}`);
        } else if (cr) {
          allPassed = false;
          failedCount++;
          logLine(`<span style='color: #ef4444;'>❌ FAIL</span> <strong>WCAG 2.2 Contrast:</strong> ${cr}:1 (Below 4.5:1 minimum threshold) between ${fg} and ${bg}`);
        } else {
          notEvaluatedCount++;
          logLine("<span style='color: #94a3b8;'>⏭ NOT_EVALUATED</span> <strong>WCAG 2.2 Contrast:</strong> Could not parse color values.");
        }
      } else {
        notEvaluatedCount++;
        logLine("<span style='color: #94a3b8;'>⏭ NOT_EVALUATED</span> <strong>WCAG 2.2 Contrast:</strong> Provide explicit 'color: #hex' and 'background-color: #hex' declarations to evaluate.");
      }

      // 3. FSM Integrity Gate — strict JSON parse on FSM definition block
      const hasFsmKeyword = /states\b|initialState\b/i.test(code);
      if (hasFsmKeyword) {
        let fsmJson = null;
        let parseError = null;
        try {
          const jsonMatch = code.match(/\{[\s\S]*?"states"[\s\S]*?\}/) || code.match(/\{[\s\S]*?"initialState"[\s\S]*?\}/);
          if (jsonMatch) {
            fsmJson = JSON.parse(jsonMatch[0]);
          } else {
            parseError = "No enclosed JSON object found around FSM keywords.";
          }
        } catch (err) {
          parseError = err.message;
        }

        if (parseError) {
          allPassed = false;
          failedCount++;
          logLine(`<span style='color: #ef4444;'>❌ FAIL</span> <strong>Finite State Machine Integrity:</strong> Invalid FSM JSON syntax: ${parseError}`);
        } else if (fsmJson && fsmJson.states && fsmJson.initialState) {
          const stateKeys = Object.keys(fsmJson.states);
          if (stateKeys.includes(fsmJson.initialState)) {
            passedCount++;
            logLine(`<span style='color: #10b981;'>✅ PASS</span> <strong>Finite State Machine Integrity:</strong> ${stateKeys.length} states, initialState "${fsmJson.initialState}" declared.`);
          } else {
            allPassed = false;
            failedCount++;
            logLine(`<span style='color: #ef4444;'>❌ FAIL</span> <strong>FSM Integrity:</strong> initialState "${fsmJson.initialState}" not declared in states.`);
          }
        } else {
          allPassed = false;
          failedCount++;
          logLine(`<span style='color: #ef4444;'>❌ FAIL</span> <strong>FSM Integrity:</strong> Incomplete FSM schema (must declare 'states' object and 'initialState').`);
        }
      } else {
        notEvaluatedCount++;
        logLine("<span style='color: #94a3b8;'>⏭ NOT_EVALUATED</span> <strong>Finite State Machine Integrity:</strong> No FSM JSON structure detected in snippet.");
      }

      // 4. Anti-Slop Gate
      const hasAiGradient = /(linear-gradient|from-purple|via-pink)/i.test(code);
      const hasEmoji = /[\u{1F300}-\u{1F9FF}]/u.test(code);
      if (hasAiGradient || hasEmoji) {
        allPassed = false;
        failedCount++;
        logLine("<span style='color: #ef4444;'>❌ FAIL</span> <strong>Anti-Slop Pattern Inspector:</strong> Banned generative AI gradient or raw emojis detected.");
      } else {
        passedCount++;
        logLine("<span style='color: #10b981;'>✅ PASS</span> <strong>Anti-Slop Pattern Inspector:</strong> Clean semantic surfaces.");
      }

      // 5. CWV Media Aspect-Ratio Gate
      const hasImg = /<img\b[^>]*>/i.test(code);
      if (hasImg) {
        const hasWidth = /\bwidth\s*=\s*["']?[1-9]\d*["']?/i.test(code);
        const hasHeight = /\bheight\s*=\s*["']?[1-9]\d*["']?/i.test(code);
        const hasAspectRatio = /\baspect-ratio\s*:\s*([0-9.]+)\s*\/\s*([0-9.]+)/i.test(code);
        if ((hasWidth && hasHeight) || hasAspectRatio) {
          passedCount++;
          logLine("<span style='color: #10b981;'>✅ PASS</span> <strong>DOM & Media Aspect-Ratio:</strong> Media dimensions bounded (CLS = 0.00).");
        } else {
          allPassed = false;
          failedCount++;
          logLine("<span style='color: #ef4444;'>❌ FAIL</span> <strong>DOM & Media Aspect-Ratio:</strong> &lt;img&gt; lacks positive integer width and height attributes.");
        }
      } else {
        notEvaluatedCount++;
        logLine("<span style='color: #94a3b8;'>⏭ NOT_EVALUATED</span> <strong>DOM & Media Aspect-Ratio:</strong> No &lt;img&gt; elements present in snippet to evaluate dimensions.");
      }

      // DOM Depth — real nesting depth via tag scanner
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
          failedCount++;
          logLine(`<span style='color: #ef4444;'>❌ FAIL</span> <strong>DOM Depth Budget:</strong> Max nesting depth (${maxDepth}) exceeds maximum allowable 32 levels.`);
        } else if (maxDepth > 0) {
          passedCount++;
          logLine(`<span style='color: #10b981;'>✅ PASS</span> <strong>DOM Depth Budget:</strong> Max nesting depth ${maxDepth} ≤ 32.`);
        }
      })();

      const elapsed = (performance.now() - startTime).toFixed(1);
      logLine("───────────────────────────────────────────────────────────────");
      logLine(`<strong>Evaluation Summary:</strong> ${passedCount} Passed, ${failedCount} Failed, ${notEvaluatedCount} Not Evaluated`);
      if (failedCount === 0 && passedCount > 0) {
        logLine(`<strong style='color: #10b981;'>🎉 ALL EVALUATED GATES PASSED! Build certified for enterprise production (${elapsed}ms)</strong>`);
      } else if (failedCount > 0) {
        logLine(`<strong style='color: #ef4444;'>❌ BUILD REJECTED BY ORTHOTECT GATES (${failedCount} failure(s)) (${elapsed}ms)</strong>`);
      } else {
        logLine(`<strong style='color: #94a3b8;'>ℹ NO EVALUABLE CODE PATTERNS DETECTED (${elapsed}ms)</strong>`);
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

  // =========================================================================
  // HERO INTERACTIVE BENCHMARK RUNNER (PRODUCTION GATE VALIDATION ENGINE)
  // =========================================================================
  const btnRunHeroBenchmark = document.getElementById("btnRunHeroBenchmark");
  if (btnRunHeroBenchmark) {
    btnRunHeroBenchmark.addEventListener("click", () => {
      const btnText = document.getElementById("heroBenchmarkBtnText");
      const badge = document.getElementById("heroTerminalBadge");
      const cert = document.getElementById("heroTerminalCert");
      const summary = document.getElementById("heroTerminalSummary");

      const elStatus1 = document.getElementById("heroStatusGate1");
      const elTime1 = document.getElementById("heroTimeGate1");
      const elDetail1 = document.getElementById("heroDetailGate1");
      const elRow1 = elStatus1 ? elStatus1.closest(".terminal-row") : null;

      const elStatus2 = document.getElementById("heroStatusGate2");
      const elTime2 = document.getElementById("heroTimeGate2");
      const elDetail2 = document.getElementById("heroDetailGate2");
      const elRow2 = elStatus2 ? elStatus2.closest(".terminal-row") : null;

      const elStatus3 = document.getElementById("heroStatusGate3");
      const elTime3 = document.getElementById("heroTimeGate3");
      const elDetail3 = document.getElementById("heroDetailGate3");
      const elRow3 = elStatus3 ? elStatus3.closest(".terminal-row") : null;

      const elStatus4 = document.getElementById("heroStatusGate4");
      const elTime4 = document.getElementById("heroTimeGate4");
      const elDetail4 = document.getElementById("heroDetailGate4");
      const elRow4 = elStatus4 ? elStatus4.closest(".terminal-row") : null;

      const elStatus5 = document.getElementById("heroStatusGate5");
      const elTime5 = document.getElementById("heroTimeGate5");
      const elDetail5 = document.getElementById("heroDetailGate5");
      const elRow5 = elStatus5 ? elStatus5.closest(".terminal-row") : null;

      if (btnText) btnText.textContent = "Executing...";
      if (badge) {
        badge.textContent = "⚡ EXECUTING CLIENT GATES...";
        badge.className = "terminal-badge";
      }

      setTimeout(() => {
        const overallStart = performance.now();

        // ---------------------------------------------------------------------
        // 1. Gate 1: WCAG 2.2 Mathematical Contrast Matrix on Theme Tokens
        // ---------------------------------------------------------------------
        const t1Start = performance.now();
        let testedPairs = 0;
        let passedAA = 0;
        let passedAAA = 0;
        let contrastFailures = 0;

        // A. Mathematical evaluation of canonical DTCG tokens from core/tokens/
        const coreTokens = (typeof window !== "undefined" && window.ORTHOTECT_CORE && window.ORTHOTECT_CORE.tokens)
          ? window.ORTHOTECT_CORE.tokens
          : null;

        const resolveRef = (val, prims) => {
          if (typeof val === "string" && val.startsWith("{") && val.endsWith("}")) {
            const parts = val.slice(1, -1).split(".");
            let curr = prims;
            for (const p of parts) {
              if (!curr) return val;
              curr = curr[p];
            }
            return curr && curr.$value ? curr.$value : val;
          }
          return val;
        };

        if (coreTokens && coreTokens.semantics && coreTokens.semantics.theme && coreTokens.primitives) {
          const prims = coreTokens.primitives;
          const semThemes = coreTokens.semantics.theme;

          for (const [themeName, themeData] of Object.entries(semThemes)) {
            const canvasHex = resolveRef(themeData.surface.canvas.$value, prims);
            const panelHex = resolveRef(themeData.surface.panel.$value, prims);
            const actionPrimaryHex = resolveRef(themeData.action.primary.$value, prims);

            const canonicalPairs = [
              { name: `[${themeName.toUpperCase()}] Primary Text on Canvas`, fg: resolveRef(themeData.content.primary.$value, prims), bg: canvasHex, reqAA: 4.5, reqAAA: 7.0 },
              { name: `[${themeName.toUpperCase()}] Secondary Text on Canvas`, fg: resolveRef(themeData.content.secondary.$value, prims), bg: canvasHex, reqAA: 4.5, reqAAA: 7.0 },
              { name: `[${themeName.toUpperCase()}] Action Primary on Canvas`, fg: actionPrimaryHex, bg: canvasHex, reqAA: 3.0, reqAAA: 4.5 },
              { name: `[${themeName.toUpperCase()}] Action Danger on Canvas`, fg: resolveRef(themeData.action.danger.$value, prims), bg: canvasHex, reqAA: 3.0, reqAAA: 4.5 },
              { name: `[${themeName.toUpperCase()}] Border Strong on Panel`, fg: resolveRef(themeData.border.strong.$value, prims), bg: panelHex, reqAA: 3.0, reqAAA: 4.5 },
              { name: `[${themeName.toUpperCase()}] Inverse Text on Action Primary`, fg: resolveRef(themeData.content.inverse.$value, prims), bg: actionPrimaryHex, reqAA: 4.5, reqAAA: 7.0 }
            ];

            for (const p of canonicalPairs) {
              testedPairs++;
              const ratio = parseFloat(getContrastRatio(p.fg, p.bg) || "0");
              if (ratio >= p.reqAA) {
                passedAA++;
                if (ratio >= p.reqAAA) passedAAA++;
              } else {
                contrastFailures++;
              }
            }
          }
        }

        // B. Active computed styles evaluation on document.documentElement
        const activeComp = window.getComputedStyle(document.documentElement);
        const activeCanvas = activeComp.getPropertyValue("--ortho-canvas").trim() || "#090d16";
        const activePanel = activeComp.getPropertyValue("--ortho-surface-1").trim() || "#0f1626";
        const activeTextPrimary = activeComp.getPropertyValue("--ortho-text-primary").trim() || "#f8fafc";
        const activeTextSecondary = activeComp.getPropertyValue("--ortho-text-secondary").trim() || "#94a3b8";
        const activeActionPrimary = activeComp.getPropertyValue("--ortho-accent-cyan").trim() || "#00d2ff";
        const activeActionDanger = activeComp.getPropertyValue("--ortho-danger").trim() || "#ef4444";

        const liveDomPairs = [
          { name: "Live Primary Text on Canvas", fg: activeTextPrimary, bg: activeCanvas, reqAA: 4.5, reqAAA: 7.0 },
          { name: "Live Primary Text on Panel", fg: activeTextPrimary, bg: activePanel, reqAA: 4.5, reqAAA: 7.0 },
          { name: "Live Secondary Text on Canvas", fg: activeTextSecondary, bg: activeCanvas, reqAA: 4.5, reqAAA: 7.0 },
          { name: "Live Action Control on Canvas", fg: activeActionPrimary, bg: activeCanvas, reqAA: 3.0, reqAAA: 4.5 },
          { name: "Live Destructive Control on Canvas", fg: activeActionDanger, bg: activeCanvas, reqAA: 3.0, reqAAA: 4.5 }
        ];

        for (const p of liveDomPairs) {
          testedPairs++;
          const ratio = parseFloat(getContrastRatio(p.fg, p.bg) || "0");
          if (ratio >= p.reqAA) {
            passedAA++;
            if (ratio >= p.reqAAA) passedAAA++;
          } else {
            contrastFailures++;
          }
        }

        const passed1 = contrastFailures === 0 && testedPairs >= 12;
        const t1End = performance.now();
        const t1 = Math.max(0.4, t1End - t1Start);

        if (elTime1) elTime1.textContent = `${t1.toFixed(1)}ms`;
        if (elStatus1) {
          elStatus1.textContent = passed1 ? "✅ PASS" : "❌ FAIL";
          if (elRow1) elRow1.className = passed1 ? "terminal-row pass" : "terminal-row fail";
        }
        if (elDetail1) {
          elDetail1.textContent = passed1
            ? `${testedPairs}/${testedPairs} Token Pairs Pass WCAG 2.2 AA (${passedAAA} AAA)`
            : `Contrast Violation: ${contrastFailures} token pairs failed WCAG 2.2 AA`;
        }

        // ---------------------------------------------------------------------
        // 2. Gate 2: True BiDi & CSS Logical Properties (Full 16-Pattern Engine)
        // ---------------------------------------------------------------------
        const t2Start = performance.now();
        let physicalViolations = 0;
        let logicalCount = 0;

        const BANNED_BIDI = [
          /\bmargin-left\s*:/i,
          /\bmargin-right\s*:/i,
          /\bpadding-left\s*:/i,
          /\bpadding-right\s*:/i,
          /\bborder-left\b(?!-width|-color|-style)/i,
          /\bborder-right\b(?!-width|-color|-style)/i,
          /\bborder-top-left-radius\s*:/i,
          /\bborder-top-right-radius\s*:/i,
          /\bborder-bottom-left-radius\s*:/i,
          /\bborder-bottom-right-radius\s*:/i,
          /(?<![\w-])left\s*:\s*(?!auto|inherit|initial)[^;]+(?:;|\}|$)/i,
          /(?<![\w-])right\s*:\s*(?!auto|inherit|initial)[^;]+(?:;|\}|$)/i,
          /\btext-align\s*:\s*left\b/i,
          /\btext-align\s*:\s*right\b/i,
          /\bfloat\s*:\s*left\b/i,
          /\bfloat\s*:\s*right\b/i
        ];

        const LOGICAL_REGEX = /(?:margin|padding|inset|border)-(?:inline|block)|(?:inline|block)-size|text-align\s*:\s*(?:start|end)/i;

        // Scan stylesheet rules if accessible
        try {
          Array.from(document.styleSheets).forEach(sheet => {
            try {
              Array.from(sheet.cssRules || []).forEach(rule => {
                const txt = rule.cssText || "";
                for (const pat of BANNED_BIDI) {
                  if (pat.test(txt)) physicalViolations++;
                }
                if (LOGICAL_REGEX.test(txt)) logicalCount++;
              });
            } catch (_) {}
          });
        } catch (_) {}

        // Scan all DOM elements for inline style attributes
        document.querySelectorAll("*").forEach(el => {
          const styleAttr = el.getAttribute("style") || "";
          if (styleAttr) {
            for (const pat of BANNED_BIDI) {
              if (pat.test(styleAttr)) physicalViolations++;
            }
            if (LOGICAL_REGEX.test(styleAttr)) logicalCount++;
          }
        });

        const passed2 = physicalViolations === 0 && logicalCount >= 20;
        const t2End = performance.now();
        const t2 = Math.max(0.6, t2End - t2Start);

        if (elTime2) elTime2.textContent = `${t2.toFixed(1)}ms`;
        if (elStatus2) {
          elStatus2.textContent = passed2 ? "✅ PASS" : "❌ FAIL";
          if (elRow2) elRow2.className = passed2 ? "terminal-row pass" : "terminal-row fail";
        }
        if (elDetail2) {
          elDetail2.textContent = passed2
            ? `100% Directional Neutrality (${logicalCount} logical rules verified, 0 physical violations)`
            : `BiDi Violations: ${physicalViolations} physical properties detected`;
        }

        // ---------------------------------------------------------------------
        // 3. Gate 3: State Machine BFS Reachability & Lock Engine (Canonical FSMs)
        // ---------------------------------------------------------------------
        const t3Start = performance.now();
        const coreFsmObj = (typeof window !== "undefined" && window.ORTHOTECT_CORE && window.ORTHOTECT_CORE.fsm)
          ? window.ORTHOTECT_CORE.fsm
          : {};

        const productionFsms = Object.entries(coreFsmObj).map(([fname, schema]) => ({
          name: `${schema.name || fname} (core/fsm/${fname})`,
          initialState: schema.initialState,
          states: schema.states || {}
        }));

        let fsmPassed = true;
        let totalStatesCount = 0;
        const fsmErrors = [];
        const asyncKeywords = ["loading", "submitting", "pending", "processing", "fetching", "skeletonloading", "syncing"];
        const transitionKeywords = ["opening", "closing", "transitioning"];

        if (productionFsms.length === 0) {
          fsmPassed = false;
          fsmErrors.push("No FSM specifications loaded from window.ORTHOTECT_CORE.fsm");
        }

        for (const model of productionFsms) {
          if (!model.initialState || !model.states || !model.states[model.initialState]) {
            fsmPassed = false;
            fsmErrors.push(`${model.name}: invalid or missing initialState`);
            break;
          }
          const stateKeys = Object.keys(model.states);
          totalStatesCount += stateKeys.length;

          // 1. Transition targets validity
          for (const [stName, stDef] of Object.entries(model.states)) {
            const transitions = stDef.on || {};
            for (const [evt, target] of Object.entries(transitions)) {
              if (!model.states[target]) {
                fsmPassed = false;
                fsmErrors.push(`${model.name}: ${stName}.${evt} -> undefined '${target}'`);
              }
            }

            // 2. Deadlock detection: non-final state must have transitions
            if (!stDef.final && Object.keys(transitions).length === 0) {
              fsmPassed = false;
              fsmErrors.push(`${model.name}: deadlock in non-final state '${stName}'`);
            }

            // 3. Asynchronous execution & submission lock validation matching gate_fsm_integrity.py
            const nameLower = stName.toLowerCase();
            const isAsyncByName = asyncKeywords.some(kw => nameLower.includes(kw));
            const isTransitionByName = transitionKeywords.some(kw => nameLower.includes(kw));
            const isExplicitlyAsync = (
              stDef.isAsync === true ||
              stDef.async === true ||
              stDef.type === "async"
            );
            const requiresLock = (
              isAsyncByName ||
              isExplicitlyAsync ||
              isTransitionByName ||
              stDef.locksInteraction === true ||
              stDef.isLocked === true ||
              stDef.locked === true ||
              ("allowClick" in stDef && stDef.allowClick === false)
            );

            if (requiresLock) {
              const isLocked = (
                stDef.allowClick === false ||
                stDef.locksInteraction === true ||
                stDef.isLocked === true ||
                stDef.locked === true
              );

              if (stDef.allowClick === true) {
                fsmPassed = false;
                fsmErrors.push(`${model.name}: state '${stName}' must lock pointer/keyboard actions (allowClick: false)`);
              } else if (!isLocked) {
                fsmPassed = false;
                fsmErrors.push(`${model.name}: state '${stName}' must explicitly declare 'allowClick: false'`);
              }

              // Resilience check: Asynchronous operations (data/network) MUST have explicit error/failure transition
              if (isAsyncByName || isExplicitlyAsync) {
                const targets = Object.values(transitions);
                const hasRecovery = targets.some(t => /error|fail|reject/i.test(t));
                if (!hasRecovery) {
                  fsmPassed = false;
                  fsmErrors.push(`${model.name}: async state '${stName}' missing error recovery transition`);
                }
              }
            }
          }

          // 4. BFS Reachability from initialState
          const queue = [model.initialState];
          const visited = new Set();
          while (queue.length > 0) {
            const curr = queue.shift();
            if (!visited.has(curr)) {
              visited.add(curr);
              const stateObj = model.states[curr];
              if (stateObj && stateObj.on) {
                for (const target of Object.values(stateObj.on)) {
                  if (model.states[target] && !visited.has(target)) {
                    queue.push(target);
                  }
                }
              }
            }
          }

          if (visited.size !== stateKeys.length) {
            fsmPassed = false;
            const unreachable = stateKeys.filter(k => !visited.has(k));
            fsmErrors.push(`${model.name}: unreachable orphaned state(s): [${unreachable.join(", ")}]`);
          }
        }

        const passed3 = fsmPassed && fsmErrors.length === 0;
        const t3End = performance.now();
        const t3 = Math.max(0.3, t3End - t3Start);

        if (elTime3) elTime3.textContent = `${t3.toFixed(1)}ms`;
        if (elStatus3) {
          elStatus3.textContent = passed3 ? "✅ PASS" : "❌ FAIL";
          if (elRow3) elRow3.className = passed3 ? "terminal-row pass" : "terminal-row fail";
        }
        if (elDetail3) {
          elDetail3.textContent = passed3
            ? `All ${totalStatesCount} states reachable across ${productionFsms.length} production FSMs (0 deadlocks, interaction locks verified)`
            : `FSM Integrity Error: ${fsmErrors[0] || "unreachable or unlocked states"}`;
        }

        // ---------------------------------------------------------------------
        // 4. Gate 4: Anti-Slop Pattern Inspector (Full Lexical & Inline Checker)
        // ---------------------------------------------------------------------
        const t4Start = performance.now();
        let slopViolations = 0;
        const slopErrors = [];

        // A. Hardcoded AI indigo/purple gradients across stylesheets
        try {
          Array.from(document.styleSheets).forEach(sheet => {
            try {
              Array.from(sheet.cssRules || []).forEach(rule => {
                const txt = rule.cssText || "";
                if (/linear-gradient\s*\([^)]*(#6366f1|#a855f7|indigo|purple)[^)]*\)/i.test(txt)) {
                  slopViolations++;
                  slopErrors.push("Generic AI purple gradient in CSS rule");
                }
              });
            } catch (_) {}
          });
        } catch (_) {}

        // B. Inline styles: hardcoded hex/rgb colors without DTCG variables or AI gradients
        document.querySelectorAll("*").forEach(el => {
          const styleAttr = el.getAttribute("style") || "";
          if (styleAttr) {
            if (/linear-gradient\s*\([^)]*(#6366f1|#a855f7|indigo|purple)[^)]*\)/i.test(styleAttr)) {
              slopViolations++;
              slopErrors.push("Generic AI purple gradient in inline style");
            }
            if (/(?:^|;|\s)(?:color|background(?:-color)?)\s*:\s*(?:#[0-9a-fA-F]{3,6}|rgba?\([^)]+\))/i.test(styleAttr)) {
              if (!/var\(--ortho-/i.test(styleAttr)) {
                slopViolations++;
                slopErrors.push("Hardcoded color bypassing DTCG tokens in inline style");
              }
            }
          }
        });

        // C. Raw decorative AI emojis in button icons and primary headings
        const emojiRegex = /[🚀🔥✨💡🎉📈📊🧠🤖\u{1F300}-\u{1F9FF}]/u;
        document.querySelectorAll("button").forEach(btn => {
          if (emojiRegex.test(btn.textContent || "")) {
            slopViolations++;
            slopErrors.push(`Raw emoji in button: "${(btn.textContent || '').trim().slice(0, 15)}"`);
          }
        });
        document.querySelectorAll("h1, h2, h3").forEach(h => {
          if (emojiRegex.test(h.textContent || "")) {
            slopViolations++;
            slopErrors.push(`Raw emoji in heading: "${(h.textContent || '').trim().slice(0, 15)}"`);
          }
        });

        const passed4 = slopViolations === 0;
        const t4End = performance.now();
        const t4 = Math.max(0.5, t4End - t4Start);

        if (elTime4) elTime4.textContent = `${t4.toFixed(1)}ms`;
        if (elStatus4) {
          elStatus4.textContent = passed4 ? "✅ PASS" : "❌ FAIL";
          if (elRow4) elRow4.className = passed4 ? "terminal-row pass" : "terminal-row fail";
        }
        if (elDetail4) {
          elDetail4.textContent = passed4
            ? "Zero AI Slop (0 hardcoded gradients, semantic SVGs enforced, DTCG tokens pure)"
            : `Anti-Slop Violation: ${slopViolations} anti-patterns detected (${slopErrors[0] || 'violations'})`;
        }

        // ---------------------------------------------------------------------
        // 5. Gate 5: DOM Depth & Pre-Layout Media Box Budget (Iterative Traversal)
        // ---------------------------------------------------------------------
        const t5Start = performance.now();
        const allMedia = document.querySelectorAll("img, video, iframe");
        let unbudgetedMedia = 0;

        const isPositiveDimAttr = (val) => {
          if (!val || typeof val !== "string") return false;
          const clean = val.trim();
          return /^[1-9]\d*$/.test(clean);
        };

        const parseAndValidateCssCalc = (innerStr) => {
          if (!innerStr || typeof innerStr !== "string") return false;
          const str = innerStr.trim();
          if (!str) return false;

          const validUnits = new Set(["px", "rem", "em", "vw", "vh", "%", "cqi", "cqw", "pt", "cm", "mm", "in", "vmin", "vmax", "ch", "ex"]);
          const numberRegex = /^[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$/;

          const tokens = [];
          let i = 0;
          const len = str.length;
          while (i < len) {
            const ch = str[i];
            if (/\s/.test(ch)) {
              i++;
              continue;
            }
            if (ch === "(" || ch === ")" || ch === "*" || ch === "/") {
              tokens.push({ type: ch, raw: ch });
              i++;
              continue;
            }
            if (ch === "+" || ch === "-") {
              const prev = tokens.length > 0 ? tokens[tokens.length - 1].type : null;
              const isUnary = !prev || prev === "(" || prev === "+" || prev === "-" || prev === "*" || prev === "/";
              if (isUnary) {
                // In CSS Syntax Level 3, a unary sign must be followed immediately by a number (or opening parenthesis)
                // with ZERO whitespace! (e.g. "-10px", not "- 10px")
                const nextChar = str[i + 1];
                if (!nextChar || /\s/.test(nextChar)) {
                  return false; // Space after unary sign is INVALID in CSS
                }

                if (nextChar === "(") {
                  tokens.push({ type: "unary", sign: ch === "-" ? -1 : 1 });
                  i++;
                  continue;
                }

                if (/[0-9.]/.test(nextChar)) {
                  const sign = ch === "-" ? -1 : 1;
                  i++; // consume sign
                  const numStart = i;
                  while (i < len && /[0-9.]/.test(str[i])) i++;
                  // W3C CSS Syntax Module Level 3 (§ 4.3.12 Consume a number):
                  // An exponent indicator 'e' or 'E' is only part of the number if followed by an optional sign and at least one digit!
                  // This strictly avoids colliding with valid CSS units such as 'em' and 'ex' (e.g. "10em", "10ex").
                  if (i < len && (str[i] === "e" || str[i] === "E")) {
                    const rem = str.slice(i);
                    const expMatch = rem.match(/^[eE][+-]?[0-9]+/);
                    if (expMatch) {
                      i += expMatch[0].length;
                    }
                  }
                  const rawNum = str.slice(numStart, i);
                  if (!numberRegex.test(rawNum)) {
                    return false;
                  }
                  const numVal = parseFloat(rawNum);
                  if (isNaN(numVal)) return false;

                  const unitStart = i;
                  while (i < len && /[a-zA-Z%]/.test(str[i])) i++;
                  const unit = str.slice(unitStart, i).toLowerCase();
                  if (unit && !validUnits.has(unit)) return false;

                  tokens.push({
                    type: "val",
                    num: sign * numVal,
                    unit: unit || null,
                    dimType: unit ? "length" : "number"
                  });
                  continue;
                }
                return false;
              } else {
                const hasPrecedingSpace = i > 0 && /\s/.test(str[i - 1]);
                const hasFollowingSpace = (i + 1 < len) && /\s/.test(str[i + 1]);
                if (!hasPrecedingSpace || !hasFollowingSpace) {
                  return false;
                }
                tokens.push({ type: ch, raw: ch });
                i++;
                continue;
              }
            }
            if (/[0-9.]/.test(ch)) {
              const numStart = i;
              while (i < len && /[0-9.]/.test(str[i])) i++;
              // W3C CSS Syntax Module Level 3 (§ 4.3.12 Consume a number):
              // An exponent indicator 'e' or 'E' is only part of the number if followed by an optional sign and at least one digit!
              // This strictly avoids colliding with valid CSS units such as 'em' and 'ex' (e.g. "10em", "10ex").
              if (i < len && (str[i] === "e" || str[i] === "E")) {
                const rem = str.slice(i);
                const expMatch = rem.match(/^[eE][+-]?[0-9]+/);
                if (expMatch) {
                  i += expMatch[0].length;
                }
              }
              const rawNum = str.slice(numStart, i);
              if (!numberRegex.test(rawNum)) {
                return false;
              }
              const numVal = parseFloat(rawNum);
              if (isNaN(numVal)) return false;

              const unitStart = i;
              while (i < len && /[a-zA-Z%]/.test(str[i])) i++;
              const unit = str.slice(unitStart, i).toLowerCase();
              if (unit && !validUnits.has(unit)) return false;

              tokens.push({
                type: "val",
                num: numVal,
                unit: unit || null,
                dimType: unit ? "length" : "number"
              });
              continue;
            }
            return false;
          }

          if (tokens.length === 0) return false;

          let pos = 0;

          function parseFactor() {
            if (pos >= tokens.length) return null;
            let sign = 1;
            if (tokens[pos].type === "unary") {
              sign = tokens[pos].sign;
              pos++;
              if (pos >= tokens.length) return null;
            } else if (tokens[pos].type === "+" || tokens[pos].type === "-") {
              if (tokens[pos].type === "-") sign = -1;
              pos++;
              if (pos >= tokens.length) return null;
            }

            const t = tokens[pos];
            if (t.type === "(") {
              pos++;
              const expr = parseExpression();
              if (!expr) return null;
              if (pos >= tokens.length || tokens[pos].type !== ")") {
                return null;
              }
              pos++;
              return {
                dimType: expr.dimType,
                evalNode: (map) => sign * expr.evalNode(map)
              };
            }

            if (t.type === "val") {
              pos++;
              const valToken = t;
              return {
                dimType: valToken.dimType,
                evalNode: (map) => {
                  const factor = valToken.unit ? (map[valToken.unit] !== undefined ? map[valToken.unit] : 1) : 1;
                  return sign * valToken.num * factor;
                }
              };
            }

            return null;
          }

          function parseTerm() {
            let left = parseFactor();
            if (!left) return null;

            while (pos < tokens.length && (tokens[pos].type === "*" || tokens[pos].type === "/")) {
              const op = tokens[pos].type;
              pos++;
              const right = parseFactor();
              if (!right) return null;

              if (op === "*") {
                if (left.dimType === "length" && right.dimType === "length") {
                  return null;
                }
                const resDimType = (left.dimType === "length" || right.dimType === "length") ? "length" : "number";
                const prevLeft = left;
                left = {
                  dimType: resDimType,
                  evalNode: (map) => prevLeft.evalNode(map) * right.evalNode(map)
                };
              } else {
                if (right.dimType !== "number") {
                  return null;
                }
                const prevLeft = left;
                left = {
                  dimType: prevLeft.dimType,
                  evalNode: (map) => {
                    const rVal = right.evalNode(map);
                    if (rVal === 0) return NaN;
                    return prevLeft.evalNode(map) / rVal;
                  }
                };
              }
            }
            return left;
          }

          function parseExpression() {
            let left = parseTerm();
            if (!left) return null;

            while (pos < tokens.length && (tokens[pos].type === "+" || tokens[pos].type === "-")) {
              const op = tokens[pos].type;
              pos++;
              const right = parseTerm();
              if (!right) return null;

              if (left.dimType !== right.dimType) {
                return null;
              }

              const prevLeft = left;
              left = {
                dimType: prevLeft.dimType,
                evalNode: (map) => {
                  const lVal = prevLeft.evalNode(map);
                  const rVal = right.evalNode(map);
                  return op === "+" ? lVal + rVal : lVal - rVal;
                }
              };
            }
            return left;
          }

          const ast = parseExpression();
          if (!ast) return false;
          if (pos < tokens.length) return false;
          if (ast.dimType !== "length") return false;

          const mobileMap = { px: 1, rem: 16, em: 16, vw: 3.6, vh: 6.4, "%": 3.6, cqi: 3.6, cqw: 3.6, pt: 1.333, cm: 37.795, mm: 3.7795, in: 96, vmin: 3.6, vmax: 6.4, ch: 8, ex: 8 };
          const desktopMap = { px: 1, rem: 16, em: 16, vw: 14.4, vh: 9.0, "%": 14.4, cqi: 14.4, cqw: 14.4, pt: 1.333, cm: 37.795, mm: 3.7795, in: 96, vmin: 9.0, vmax: 14.4, ch: 8, ex: 8 };
          const neutralMap = { px: 1, rem: 1, em: 1, vw: 1, vh: 1, "%": 1, cqi: 1, cqw: 1, pt: 1, cm: 1, mm: 1, in: 1, vmin: 1, vmax: 1, ch: 1, ex: 1 };

          const mVal = ast.evalNode(mobileMap);
          const dVal = ast.evalNode(desktopMap);
          const nVal = ast.evalNode(neutralMap);

          if (isNaN(mVal) || isNaN(dVal) || isNaN(nVal)) return false;
          return mVal > 0 && dVal > 0 && nVal > 0;
        };

        const isValidCssDim = (val) => {
          if (!val || typeof val !== "string") return false;
          const clean = val.trim().toLowerCase().replace(/\s*!important\s*$/i, "").trim();
          if (["auto", "none", "initial", "inherit", "unset", "0", "0px", ""].includes(clean)) return false;

          // Single length/percentage dimension check: e.g. "200px", "0.5px", ".5em", "50%", "10rem", "10ex"
          // Strictly validates positive numeric value (> 0) supporting decimals below 1 and leading decimal dots per W3C CSS Values 4
          const directMatch = clean.match(/^((?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)(px|rem|em|vw|vh|%|cqi|cqw|pt|cm|mm|in|vmin|vmax|ch|ex)$/i);
          if (directMatch) {
            const num = parseFloat(directMatch[1]);
            if (!isNaN(num) && num > 0) return true;
            return false;
          }

          const calcMatch = clean.match(/^calc\((.+)\)$/i);
          if (!calcMatch) return false;

          const inner = calcMatch[1].trim();
          if (!inner) return false;

          return parseAndValidateCssCalc(inner);
        };

        const isValidAspectRatio = (val) => {
          if (!val || typeof val !== "string") return false;
          let clean = val.trim().toLowerCase().replace(/^\bauto\b\s*/i, "").replace(/\s*\bauto\b$/i, "").trim();
          clean = clean.replace(/\s*!important\s*$/i, "").trim();
          if (!clean || ["auto", "none", "initial", "inherit", "unset"].includes(clean)) return false;
          const m = clean.match(/^([0-9]*\.?[0-9]+)\s*(?:\/\s*([0-9]*\.?[0-9]+))?$/);
          if (!m) return false;
          const w = parseFloat(m[1]);
          const h = m[2] !== undefined ? parseFloat(m[2]) : 1.0;
          return !isNaN(w) && !isNaN(h) && w > 0 && h > 0;
        };

        allMedia.forEach(el => {
          // A. HTML positive integer attributes per HTML5 spec (§ 4.8.4.1.3)
          const wAttr = el.getAttribute("width") || "";
          const hAttr = el.getAttribute("height") || "";
          const hasAttrDims = isPositiveDimAttr(wAttr) && isPositiveDimAttr(hAttr);

          // B. Inline CSS style declarations
          const styleAttr = el.getAttribute("style") || "";
          let hasInlineAspect = false;
          let hasInlineDims = false;

          if (styleAttr) {
            const aspectMatch = styleAttr.match(/(?:^|;|\s)aspect-ratio\s*:\s*([^;]+)/i);
            if (aspectMatch && isValidAspectRatio(aspectMatch[1])) {
              hasInlineAspect = true;
            }
            const widthMatch = styleAttr.match(/(?:^|;|\s)width\s*:\s*([^;]+)/i);
            const heightMatch = styleAttr.match(/(?:^|;|\s)height\s*:\s*([^;]+)/i);
            if (widthMatch && heightMatch && isValidCssDim(widthMatch[1]) && isValidCssDim(heightMatch[1])) {
              try {
                const cs = window.getComputedStyle(el);
                if (parseFloat(cs.width) > 0 && parseFloat(cs.height) > 0) {
                  hasInlineDims = true;
                }
              } catch (_) {}
            }
          }

          // C. Stylesheet or computed rules
          let hasComputedAspectOrDims = false;
          try {
            const cs = window.getComputedStyle(el);
            if (cs && cs.aspectRatio && isValidAspectRatio(cs.aspectRatio)) {
              hasComputedAspectOrDims = true;
            }
            if (!hasAttrDims && !hasInlineAspect && !hasInlineDims && !hasComputedAspectOrDims) {
              for (const sheet of Array.from(document.styleSheets)) {
                try {
                  for (const rule of Array.from(sheet.cssRules || [])) {
                    if (rule.selectorText && el.matches(rule.selectorText)) {
                      if (rule.style.aspectRatio && isValidAspectRatio(rule.style.aspectRatio)) {
                        hasComputedAspectOrDims = true;
                        break;
                      }
                      if (rule.style.width && rule.style.height &&
                          isValidCssDim(rule.style.width) && isValidCssDim(rule.style.height) &&
                          parseFloat(cs.width) > 0 && parseFloat(cs.height) > 0) {
                        hasComputedAspectOrDims = true;
                        break;
                      }
                    }
                  }
                } catch (_) {}
                if (hasComputedAspectOrDims) break;
              }
            }
          } catch (_) {}

          if (!hasAttrDims && !hasInlineAspect && !hasInlineDims && !hasComputedAspectOrDims) {
            unbudgetedMedia++;
          }
        });

        // Iterative stack-based DOM depth traversal (prevents recursion call-stack exhaustion)
        function getDomDepthIterative(root) {
          let maxDepth = 0;
          const stack = [{ node: root, depth: 1 }];
          while (stack.length > 0) {
            const { node, depth } = stack.pop();
            if (depth > maxDepth) maxDepth = depth;
            for (let i = 0; i < node.children.length; i++) {
              stack.push({ node: node.children[i], depth: depth + 1 });
            }
          }
          return maxDepth;
        }

        const maxDomDepth = getDomDepthIterative(document.body);
        const passed5 = unbudgetedMedia === 0 && maxDomDepth <= 32;
        const t5End = performance.now();
        const t5 = Math.max(0.4, t5End - t5Start);

        if (elTime5) elTime5.textContent = `${t5.toFixed(1)}ms`;
        if (elStatus5) {
          elStatus5.textContent = passed5 ? "✅ PASS" : "❌ FAIL";
          if (elRow5) elRow5.className = passed5 ? "terminal-row pass" : "terminal-row fail";
        }
        if (elDetail5) {
          elDetail5.textContent = passed5
            ? `Explicit Media Bounding (${allMedia.length} elements verified, depth: ${maxDomDepth} ≤ 32)`
            : `Layout-Shift Risk: ${unbudgetedMedia} unbudgeted media elements (no explicit dimensions)`;
        }

        // ---------------------------------------------------------------------
        // Dynamic Aggregate Gate Derivation
        // ---------------------------------------------------------------------
        const overallEnd = performance.now();
        const totalDuration = (overallEnd - overallStart).toFixed(1);
        const nowTime = new Date().toLocaleTimeString();
        const allPassed = passed1 && passed2 && passed3 && passed4 && passed5;
        const failedCount = [passed1, passed2, passed3, passed4, passed5].filter(p => !p).length;

        if (summary) {
          if (allPassed) {
            summary.innerHTML = `Live Client Latency: <strong>${totalDuration}ms</strong> • Executed In-Browser at <strong>${nowTime}</strong> • <strong>100% Gates Passed</strong>`;
          } else {
            summary.innerHTML = `Live Client Latency: <strong>${totalDuration}ms</strong> • Executed In-Browser at <strong>${nowTime}</strong> • <strong>❌ GATE VIOLATIONS DETECTED (${failedCount}/5 Failed)</strong>`;
          }
        }
        if (badge) {
          if (allPassed) {
            badge.textContent = `LIVE CLIENT BENCHMARK · ${nowTime}`;
            badge.className = "terminal-badge";
          } else {
            badge.textContent = "GATE VIOLATIONS DETECTED";
            badge.className = "terminal-badge fail";
          }
        }
        if (cert) {
          if (allPassed) {
            cert.textContent = "CLIENT VERIFIED";
            cert.className = "term-certified";
          } else {
            cert.textContent = "REJECTED";
            cert.className = "term-certified fail";
          }
        }
        if (btnText) {
          btnText.textContent = "Re-run Benchmark";
        }
      }, 80);
    });
  }
});
