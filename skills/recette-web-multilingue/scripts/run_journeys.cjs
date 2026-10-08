#!/usr/bin/env node
/*
 * Deterministic journey runner for recette-web-multilingue.
 *
 * Executes the declarative journeys of a QA config with Playwright and writes
 * <out>/results.json plus <out>/evidence/. Tickets are NOT written here: the
 * agent reviews the results, then drafts tickets (see draft_tickets.py).
 *
 *   node run_journeys.cjs --config qa-config.json --out qa-output
 *        [--journeys J01,J02] [--languages en,fr] [--executable-path /path/to/chromium]
 *        (--out defaults to output.dir of the config, resolved from the current directory)
 *        [--campaign-id ID] [--label "retest after fix"]
 *
 * Requires the `playwright` npm package (local or global) and a Chromium build.
 * If either is missing, every case is recorded as BLOCKED with the reason:
 * a tooling failure never becomes a site defect.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const RUNNER_VERSION = "1.0.0";
const SENSITIVE_PARAM = /^(token|access_token|password|pass|pwd|secret|session|sid|auth|key|api_key|code)$/i;

function parseArgs(argv) {
  const a = {};
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    if (!k.startsWith("--")) continue;
    const v = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
    a[k.slice(2)] = v;
  }
  return a;
}

function loadPlaywright() {
  try { return require("playwright"); } catch (_) { /* try global */ }
  try {
    const root = execSync("npm root -g", { stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
    return require(path.join(root, "playwright"));
  } catch (e) {
    return null;
  }
}

function nowIso() { return new Date().toISOString(); }

function maskUrl(u) {
  try {
    const url = new URL(u);
    for (const k of [...url.searchParams.keys()]) if (SENSITIVE_PARAM.test(k)) url.searchParams.set(k, "***");
    url.username = url.username ? "***" : "";
    url.password = url.password ? "***" : "";
    return url.toString();
  } catch (_) { return u; }
}

function resolveTemplate(value, ctx) {
  if (typeof value !== "string") return value;
  return value.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (m, key) => {
    const [ns, ...rest] = key.split(".");
    const name = rest.join(".");
    if (ns === "lang") return ctx.lang.code;
    const table = { url: ctx.lang.urls, s: ctx.lang.strings, data: ctx.data }[ns];
    if (!table || !(name in table)) throw new Error(`unresolved placeholder ${m} for language ${ctx.lang.code}`);
    return table[name];
  });
}

function resolveStep(step, ctx) {
  const out = {};
  for (const [k, v] of Object.entries(step)) out[k] = Array.isArray(v) ? v.map((x) => resolveTemplate(x, ctx)) : resolveTemplate(v, ctx);
  return out;
}

function absolute(base, u) { return new URL(u, base).toString(); }

function pathOf(u) { try { const x = new URL(u); return x.pathname + x.search; } catch (_) { return u; } }

function describe(step) {
  if (step.description) return step.description;
  const bits = Object.entries(step).filter(([k]) => !["action", "sensitive", "description"].includes(k))
    .map(([k, v]) => `${k}=${step.sensitive && k === "value" ? "***" : JSON.stringify(v)}`);
  return `${step.action}(${bits.join(", ")})`;
}

class Expectation extends Error {}

function locatorFor(page, step) {
  if (step.selector) return page.locator(step.selector).first();
  if (step.role) return page.getByRole(step.role, step.name ? { name: step.name, exact: !!step.exact } : {}).first();
  if (step.text) return page.getByText(step.text, { exact: !!step.exact }).first();
  throw new Error("step needs selector, role or text");
}

async function runStep(page, step, st, cfg) {
  const timeout = cfg.limits.timeout_ms;
  const wait = cfg.limits.assert_timeout_ms; // how long an expectation may wait for the page to settle
  switch (step.action) {
    case "goto": {
      const url = absolute(cfg.target.start_url, step.url);
      const resp = await page.goto(url, { waitUntil: "load", timeout });
      st.lastStatus = resp ? resp.status() : null;
      if (st.lastStatus === 401 || st.lastStatus === 403) {
        const e = new Error(`HTTP ${st.lastStatus} on ${pathOf(url)}: authentication or authorization required`);
        e.blocked = "auth";
        throw e;
      }
      return `HTTP ${st.lastStatus} at ${pathOf(page.url())}`;
    }
    case "click": {
      const loc = locatorFor(page, step);
      await loc.click({ timeout });
      await page.waitForLoadState("load", { timeout }).catch(() => {});
      return `clicked; now at ${pathOf(page.url())}`;
    }
    case "fill": {
      await locatorFor(page, step).fill(step.value ?? "", { timeout });
      return step.sensitive ? "filled (value masked)" : `filled ${JSON.stringify(step.value ?? "")}`;
    }
    case "press": {
      const times = step.times || 1;
      for (let i = 0; i < times; i++) await page.keyboard.press(step.key);
      await page.waitForLoadState("load", { timeout }).catch(() => {});
      return `pressed ${step.key} x${times}; now at ${pathOf(page.url())}`;
    }
    case "type": {
      await page.keyboard.type(step.value ?? "");
      return step.sensitive ? "typed (value masked)" : `typed ${JSON.stringify(step.value ?? "")}`;
    }
    case "wait": { await page.waitForTimeout(step.ms || 250); return `waited ${step.ms || 250} ms`; }
    case "tab_until_focus": {
      const max = step.max || 25;
      for (let i = 1; i <= max; i++) {
        await page.keyboard.press("Tab");
        const hit = await page.evaluate((sel) => { const el = document.querySelector(sel); return !!el && document.activeElement === el; }, step.selector);
        if (hit) return `focus reached ${step.selector} after ${i} Tab press(es)`;
      }
      const active = await page.evaluate(() => { const a = document.activeElement; return a ? a.tagName.toLowerCase() + (a.id ? "#" + a.id : "") : "none"; });
      throw new Expectation(`${step.selector} never received keyboard focus within ${max} Tab presses (last focused: ${active})`);
    }
    case "expect_status": {
      const allowed = step.in || [200];
      if (!allowed.includes(st.lastStatus)) throw new Expectation(`expected HTTP ${allowed.join("/")}, got ${st.lastStatus} at ${pathOf(page.url())}`);
      return `HTTP ${st.lastStatus}`;
    }
    case "expect_url": {
      const match = (u) => (step.path ? u.pathname === step.path : new RegExp(step.path_regex).test(u.pathname + u.search));
      await page.waitForURL(match, { timeout: wait, waitUntil: "load" }).catch(() => {});
      const actual = pathOf(page.url());
      if (!match(new URL(page.url()))) throw new Expectation(`expected path ${step.path || step.path_regex}, observed ${actual}`);
      return `at ${actual}`;
    }
    case "expect_lang": {
      const lang = await page.evaluate(() => document.documentElement.getAttribute("lang"));
      if ((lang || "").toLowerCase().split("-")[0] !== step.value.toLowerCase().split("-")[0]) throw new Expectation(`expected <html lang> ${step.value}, observed ${JSON.stringify(lang)}`);
      return `<html lang="${lang}">`;
    }
    case "expect_text": {
      const scope = step.selector ? page.locator(step.selector).first() : page.locator("body");
      const ok = (t) => (step.exact ? t.trim() === step.text : t.includes(step.text));
      let txt = null;
      const deadline = Date.now() + wait;
      do {
        txt = await scope.innerText({ timeout: 250 }).catch(() => null);
        if (txt !== null && ok(txt)) return `found ${JSON.stringify(step.text)}`;
        await page.waitForTimeout(100);
      } while (Date.now() < deadline);
      if (txt === null) throw new Expectation(`element ${step.selector} not found`);
      throw new Expectation(`expected text ${JSON.stringify(step.text)} in ${step.selector || "page"}, observed ${JSON.stringify(txt.trim().slice(0, 200))}`);
    }
    case "expect_no_text": {
      const scope = step.selector ? page.locator(step.selector).first() : page.locator("body");
      const txt = (await scope.innerText({ timeout }).catch(() => "")) || "";
      if (txt.includes(step.text)) throw new Expectation(`unexpected text ${JSON.stringify(step.text)} present in ${step.selector || "page"}`);
      return `absent ${JSON.stringify(step.text)}`;
    }
    case "expect_visible": {
      const loc = locatorFor(page, step);
      const vis = await loc.waitFor({ state: "visible", timeout: wait }).then(() => true, () => false);
      if (!vis) throw new Expectation(`${step.selector || step.role || step.text} is not visible`);
      return "visible";
    }
    case "expect_hidden": {
      const hidden = await locatorFor(page, step).waitFor({ state: "hidden", timeout: wait }).then(() => true, () => false);
      if (!hidden) throw new Expectation(`${step.selector || step.role || step.text} is still visible`);
      return "hidden";
    }
    case "expect_attr": {
      const v = await page.locator(step.selector).first().getAttribute(step.attr, { timeout }).catch(() => null);
      if (v !== step.value) throw new Expectation(`expected ${step.selector}[${step.attr}]=${JSON.stringify(step.value)}, observed ${JSON.stringify(v)}`);
      return `${step.attr}=${JSON.stringify(v)}`;
    }
    case "expect_no_horizontal_overflow": {
      const m = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
      if (m.sw > m.cw + 1) throw new Expectation(`horizontal overflow: scrollWidth ${m.sw}px > viewport ${m.cw}px`);
      return `scrollWidth ${m.sw}px <= viewport ${m.cw}px`;
    }
    case "screenshot": {
      const rel = path.posix.join("evidence", st.caseId, `${String(st.stepIndex).padStart(2, "0")}-${step.name || "shot"}-attempt${st.attempt}.png`);
      await page.screenshot({ path: path.join(st.outDir, rel), fullPage: !!step.full_page });
      st.evidence.push({ type: "screenshot", path: rel, step: st.stepIndex });
      return `saved ${rel}`;
    }
    default:
      throw new Error(`unknown action ${step.action}`);
  }
}

function allowedRequest(cfg, req) {
  const url = new URL(req.url());
  const origins = cfg.target.allowed_origins || [new URL(cfg.target.start_url).origin];
  if (url.protocol === "data:" || url.protocol === "blob:") return { ok: true };
  if (!origins.includes(url.origin)) return { ok: false, why: `origin ${url.origin} not in allowed_origins` };
  for (const p of cfg.target.excluded_paths || []) if (url.pathname.startsWith(p) && req.method() === "GET" && req.isNavigationRequest()) return { ok: false, why: `path ${url.pathname} excluded` };
  if (req.method() !== "GET" && req.method() !== "HEAD") {
    const allow = (cfg.allowed_actions && cfg.allowed_actions.submit_paths) || [];
    if (!allow.some((p) => url.pathname.startsWith(p))) return { ok: false, why: `${req.method()} ${url.pathname} not in allowed_actions.submit_paths` };
  }
  return { ok: true };
}

async function runCase(browser, cfg, journey, lang, device, outDir, attempt) {
  const caseId = `${journey.id}-${lang.code}-${device.id}`;
  const st = { caseId, outDir, attempt, evidence: [], stepIndex: 0, lastStatus: null };
  fs.mkdirSync(path.join(outDir, "evidence", caseId), { recursive: true });
  const ctx = await browser.newContext({
    viewport: device.viewport, isMobile: !!device.is_mobile, hasTouch: !!device.has_touch,
    userAgent: device.user_agent, locale: lang.locale || lang.code,
    timezoneId: device.timezone || cfg.target.timezone || undefined,
  });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const failedRequests = [];
  const blockedRequests = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text().slice(0, 500)); });
  page.on("pageerror", (e) => consoleErrors.push(String(e).slice(0, 500)));
  page.on("requestfailed", (r) => failedRequests.push({ url: maskUrl(r.url()), method: r.method(), error: (r.failure() || {}).errorText }));
  page.on("response", (r) => { if (r.status() >= 400) failedRequests.push({ url: maskUrl(r.url()), method: r.request().method(), status: r.status() }); });
  await page.route("**/*", (route) => {
    const verdict = allowedRequest(cfg, route.request());
    if (verdict.ok) return route.continue();
    blockedRequests.push({ url: maskUrl(route.request().url()), method: route.request().method(), reason: verdict.why });
    return route.abort("blockedbyclient");
  });

  const data = Object.assign({}, journey.test_data || {});
  const steps = [];
  let status = "PASS";
  let reason = null;
  let halted = false;
  const started = nowIso();
  const resolved = journey.steps.map((s) => { try { return { step: resolveStep(s, { lang, data }) }; } catch (e) { return { error: e.message, step: s }; } });
  for (let i = 0; i < resolved.length; i++) {
    st.stepIndex = i + 1;
    const r = resolved[i];
    const rec = { index: i + 1, action: r.step.action, description: describe(r.step), status: "NOT_RUN", detail: null };
    steps.push(rec);
    if (halted) { rec.detail = "not executed: an earlier step ended the journey"; continue; }
    if (r.error) { rec.status = "BLOCKED"; rec.detail = r.error; status = "BLOCKED"; reason = `config error: ${r.error}`; halted = true; continue; }
    try {
      rec.detail = await runStep(page, r.step, st, cfg);
      rec.status = "PASS";
    } catch (e) {
      const msg = String(e.message || e).split("\n")[0].slice(0, 400);
      rec.detail = msg;
      if (e instanceof Expectation) {
        rec.status = "FAIL"; status = "FAIL";
        reason = reason ? `${reason}; ${msg}` : msg;
        // A "soft" expectation records the failure and lets independent checks continue.
        if (!r.step.soft) halted = true;
      } else {
        rec.status = "BLOCKED"; halted = true;
        if (status !== "FAIL") { status = "BLOCKED"; reason = e.blocked === "auth" ? msg : `tool could not perform step ${i + 1}: ${msg}`; }
      }
    }
  }
  // Final-state evidence for every case, plus logs.
  const shot = path.posix.join("evidence", caseId, `final-attempt${attempt}.png`);
  try { await page.screenshot({ path: path.join(outDir, shot), fullPage: false }); st.evidence.push({ type: "screenshot", path: shot, step: "final" }); } catch (_) { /* page may be gone */ }
  const log = path.posix.join("evidence", caseId, `log-attempt${attempt}.json`);
  fs.writeFileSync(path.join(outDir, log), JSON.stringify({ console_errors: consoleErrors, failed_requests: failedRequests, blocked_requests: blockedRequests }, null, 2));
  st.evidence.push({ type: "log", path: log, step: "final" });
  const finalUrl = maskUrl(page.url());
  await ctx.close();
  return {
    case_id: caseId, status, reason, started_at: started, finished_at: nowIso(), url_final: finalUrl, steps,
    evidence: st.evidence, console_errors: consoleErrors, failed_requests: failedRequests, blocked_requests: blockedRequests,
  };
}

function blockedCase(journey, lang, device, why) {
  return {
    case_id: `${journey.id}-${lang.code}-${device.id}`, status: "BLOCKED", reason: why, started_at: nowIso(), finished_at: nowIso(),
    url_final: null, evidence: [], console_errors: [], failed_requests: [], blocked_requests: [],
    steps: journey.steps.map((s, i) => ({ index: i + 1, action: s.action, description: describe(s), status: "NOT_RUN", detail: "not executed: " + why })),
  };
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.config) { console.error("usage: run_journeys.cjs --config qa-config.json [--out DIR] [--journeys J01,..] [--languages en,..] [--executable-path P]"); process.exit(2); }
  const cfg = JSON.parse(fs.readFileSync(args.config, "utf8"));
  args.out = args.out || (cfg.output && cfg.output.dir) || "qa-output"; // relative paths resolve from the current directory
  cfg.limits = Object.assign({ timeout_ms: 10000, assert_timeout_ms: 3000, retries: 1, max_cases: 200 }, cfg.limits || {});
  const outDir = path.resolve(args.out);
  fs.mkdirSync(path.join(outDir, "evidence"), { recursive: true });
  const onlyJ = args.journeys ? String(args.journeys).split(",") : null;
  const onlyL = args.languages ? String(args.languages).split(",") : null;
  const langs = Object.fromEntries(cfg.languages.map((l) => [l.code, l]));
  const devices = Object.fromEntries(cfg.devices.map((d) => [d.id, d]));

  const plan = [];
  for (const j of cfg.journeys) {
    if (onlyJ && !onlyJ.includes(j.id)) continue;
    for (const code of j.languages || Object.keys(langs)) {
      if (onlyL && !onlyL.includes(code)) continue;
      for (const dev of j.devices || [j.device]) plan.push({ journey: j, lang: langs[code], device: devices[dev] });
    }
  }
  const skipped = plan.splice(cfg.limits.max_cases);

  const pw = loadPlaywright();
  const browserName = "chromium";
  let browser = null;
  let launchError = null;
  if (!pw) launchError = "Playwright npm package not found (npm i playwright, or install it globally)";
  else {
    try {
      browser = await pw[browserName].launch({ executablePath: args["executable-path"] || process.env.QA_BROWSER_PATH || undefined });
    } catch (e) { launchError = `browser unavailable: ${String(e.message).split("\n")[0]}`; }
  }

  const cases = [];
  for (const { journey, lang, device } of plan) {
    const meta = {
      journey_id: journey.id, title: journey.title, language: lang.code, device: device.id,
      viewport: device.viewport, emulated_mobile: !!device.is_mobile, country: null,
      priority: journey.priority || "P2", release_critical: !!journey.release_critical,
      preconditions: journey.preconditions || [], expected: journey.expected || null,
      url_start: journey.steps[0] && journey.steps[0].action === "goto" ? (() => { try { return absolute(cfg.target.start_url, resolveStep(journey.steps[0], { lang, data: journey.test_data || {} }).url); } catch (_) { return null; } })() : null,
      checks: journey.checks || [],
    };
    // A PASS on the first attempt is final. A FAIL or BLOCKED attempt is retried
    // (bounded by limits.retries) to measure reproduction or ride out a transient
    // tool error. Any FAIL makes the case FAIL, reported as "k/n" with a flaky flag.
    let result;
    const runs = [];
    if (!browser) {
      result = blockedCase(journey, lang, device, launchError);
    } else {
      const maxAttempts = 1 + Number(cfg.limits.retries || 0);
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        let r;
        try { r = await runCase(browser, cfg, journey, lang, device, outDir, attempt); }
        catch (e) { r = blockedCase(journey, lang, device, `runner error: ${String(e.message).split("\n")[0]}`); }
        runs.push(r);
        if (r.status === "PASS" && attempt === 1) break;
        if (r.status === "BLOCKED" && /^HTTP 40[13]/.test(r.reason || "")) break; // auth wall: retrying will not help
      }
      const firstFail = runs.find((r) => r.status === "FAIL");
      result = firstFail || runs.find((r) => r.status === "PASS") || runs[runs.length - 1];
      result.evidence = runs.flatMap((r) => r.evidence);
      if (firstFail && runs.some((r) => r.status === "PASS")) result.flaky = true;
    }
    const attempts = runs.length;
    const fails = runs.filter((r) => r.status === "FAIL").length;
    const reproduction = result.status === "FAIL" ? `${fails}/${attempts}` : null;
    cases.push(Object.assign(meta, result, { attempts, reproduction, limitations: [] }));
    process.stdout.write(`${result.case_id.padEnd(22)} ${result.status}${reproduction ? " (" + reproduction + ")" : ""}${result.reason ? "  - " + result.reason : ""}\n`);
  }
  for (const { journey, lang, device } of skipped) {
    const c = blockedCase(journey, lang, device, "budget limit max_cases reached");
    c.status = "NOT_RUN";
    cases.push(Object.assign({ journey_id: journey.id, title: journey.title, language: lang.code, device: device.id, priority: journey.priority || "P2", release_critical: !!journey.release_critical, expected: journey.expected || null, preconditions: journey.preconditions || [], attempts: 0, reproduction: null, limitations: [] }, c));
  }
  const version = browser ? browser.version() : null;
  if (browser) await browser.close();

  const geo = (cfg.countries || []).map((c) => ({
    country_requested: c, country_verified: null, status: "NOT_RUN",
    reason: "this runner does not control or prove the network egress country; locale, timezone and Accept-Language are not geographic proof",
  }));

  const results = {
    schema_version: "1.0",
    campaign: {
      id: args["campaign-id"] || (cfg.campaign && cfg.campaign.id) || "QA-" + new Date().toISOString().slice(0, 10),
      name: (cfg.campaign && cfg.campaign.name) || "Release QA", label: args.label || null,
      environment: (cfg.campaign && cfg.campaign.environment) || "unspecified",
      started_at: cases.length ? cases[0].started_at : nowIso(), finished_at: nowIso(),
      output_language: (cfg.output && cfg.output.output_language) || "en",
    },
    scope: {
      start_url: cfg.target.start_url, allowed_origins: cfg.target.allowed_origins || [],
      languages: cfg.languages.map((l) => l.code), devices: cfg.devices.map((d) => d.id),
      journeys: cfg.journeys.map((j) => ({ id: j.id, title: j.title, release_critical: !!j.release_critical, priority: j.priority || "P2" })),
      filters: { journeys: onlyJ, languages: onlyL },
    },
    environment: {
      runner: `run_journeys.cjs ${RUNNER_VERSION}`, browser: browserName, browser_version: version,
      node: process.version, platform: process.platform, browser_error: launchError,
    },
    capabilities: {
      page_extraction: !!browser, click: !!browser, typing: !!browser, screenshots: !!browser,
      network_observation: !!browser, console_capture: !!browser, traces: false,
      geo_verification: false, real_device: false,
      notes: browser ? ["mobile profiles are Chromium device emulation, not real phones"] : [launchError],
    },
    assumptions: cfg.assumptions || [],
    cases, geo_checks: geo, observations: [], tickets: [],
  };
  fs.writeFileSync(path.join(outDir, "results.json"), JSON.stringify(results, null, 2));
  console.log(`\nwrote ${path.join(outDir, "results.json")} (${cases.length} cases)`);
}

main().catch((e) => { console.error(e); process.exit(1); });
