const HEIR_PARAM_NAMES = [
    "husband",
    "wife",
    "son",
    "daughter",
    "father",
    "mother",
    "brother",
    "sister",
    "relatives",
];

const PYODIDE_VERSION = "0.26.4";
const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PYTHON_FILES = [
    {source: "heirs.py", target: "heirs.py"},
    {source: "my_utils.py", target: "my_utils.py"},
    {source: "inheritance.py", target: "inheritance.py"},
    {source: "fiqh_local.py", target: "fiqh_local.py"},
    {source: "static/python/static_bridge.py", target: "static_bridge.py"},
];

let currentLang = "ar";
let calculatorPromise = null;
let lastCase = "";

const DEFAULT_LANGUAGE = "ar";
const SYSTEM_THEME_QUERY = "(prefers-color-scheme: dark)";

const translations = {
    en: null,
    ar: null,
};

function t(key, fallback = key) {
    return translations[currentLang]?.[key] || fallback;
}

function validateHusbandWife(spouse) {
    const husband = document.getElementById("number0");
    const wife = document.getElementById("number1");
    if (Number(husband.value) === 1 && Number(wife.value) === 1) {
        alert(t("husband_wife_warning", "Both Husband and Wife cannot be 1. At least one must be 0."));
        if (spouse === "husband") {
            husband.value = 0;
        } else if (spouse === "wife") {
            wife.value = 0;
        }
    }
}

function isNumberKey(evt) {
    const charCode = evt.which ? evt.which : evt.keyCode;
    return !(charCode > 31 && (charCode < 48 || charCode > 57));
}

function limitInput(input, maxValue) {
    if (Number(input.value) > maxValue) {
        input.value = maxValue;
    }
}

function checkEnterKey(event) {
    if (event.key === "Enter" || event.keyCode === 13) {
        fillHeritageColumns();
    }
}

function clearURL() {
    const newUrl = window.location.origin + window.location.pathname;
    window.history.replaceState({path: newUrl}, "", newUrl);
}

function clearTable(clearNumbersCol = true, clearAliCalcs = true, clearFiqhCalcs = true, clearUrl = true) {
    if (clearUrl) {
        clearURL();
    }

    renderAwlMessage(false);
    lastCase = "";
    renderCase("");
    setStatus("");

    if (clearNumbersCol) {
        document.querySelectorAll('#table-body input[type="number"]').forEach((input) => {
            input.value = 0;
        });
        document.getElementById("estate-input").value = 24;
    }

    let cells = [];
    if (clearAliCalcs && clearFiqhCalcs) {
        cells = document.querySelectorAll("#table-body tr td:nth-child(3), #table-body tr td:nth-child(4)");
    } else if (clearAliCalcs) {
        cells = document.querySelectorAll("#table-body tr td:nth-child(3)");
    } else if (clearFiqhCalcs) {
        cells = document.querySelectorAll("#table-body tr td:nth-child(4)");
    }

    cells.forEach((cell) => {
        cell.textContent = "";
    });
}

function getHeirs() {
    const heirs = [];
    for (let i = 0; i < HEIR_PARAM_NAMES.length; i += 1) {
        heirs.push(Number(document.getElementById(`number${i}`).value || 0));
    }
    return heirs;
}

function getEstateValue() {
    return document.getElementById("estate-input").value || "24";
}

function updateURL(estateValue, heirs, replace = false) {
    const params = new URLSearchParams();
    params.set("estate", estateValue);
    HEIR_PARAM_NAMES.forEach((name, index) => {
        params.set(name, heirs[index]);
    });

    const newUrl = `${window.location.origin}${window.location.pathname}?${params.toString()}`;
    const method = replace ? "replaceState" : "pushState";
    window.history[method]({path: newUrl}, "", newUrl);
}

async function fillHeritageColumns(options = {}) {
    clearTable(false, true, true, false);

    const heirs = getHeirs();
    const estateValue = getEstateValue();
    updateURL(estateValue, heirs, Boolean(options.replaceUrl));

    setBusy(true, "Loading calculator...");
    try {
        const pyodide = await initializeCalculator();
        setStatus("Calculating...");
        const payloadJson = JSON.stringify({heirs, estate: estateValue});
        const resultJson = pyodide.runPython(`static_bridge.calculate(${JSON.stringify(payloadJson)})`);
        const data = JSON.parse(resultJson);

        if (data.study_error) {
            alert("An error occurred while calculating Heritage (by Ali Aloush). Please try again.");
        }
        if (data.fiqh_error) {
            alert("An error occurred while calculating Heritage (Fiqh). Please refresh the page and try again.");
        }

        lastCase = data.case;
        renderCase(data.case);

        for (let i = 0; i < HEIR_PARAM_NAMES.length; i += 1) {
            document.getElementById(`heritageStudy${i}`).innerText = data.study[i] || "";
            document.getElementById(`heritageFiqh${i}`).innerText = data.fiqh[i] || "";
        }

        renderAwlMessage(data.awl);
        setStatus("");
    } catch (error) {
        console.error("Calculation error:", error);
        alert("An error occurred while preparing the static calculator. Please refresh the page and try again.");
        setStatus("");
    } finally {
        setBusy(false);
    }
}

async function initializeCalculator() {
    if (calculatorPromise === null) {
        calculatorPromise = loadCalculator().catch((error) => {
            calculatorPromise = null;
            throw error;
        });
    }
    return calculatorPromise;
}

async function loadCalculator() {
    await waitForPyodideScript();
    const pyodide = await loadPyodide({indexURL: PYODIDE_INDEX_URL});

    for (const file of PYTHON_FILES) {
        const response = await fetch(file.source);
        if (!response.ok) {
            throw new Error(`Failed to load ${file.source}: ${response.status}`);
        }
        pyodide.FS.writeFile(file.target, await response.text());
    }

    pyodide.runPython("import static_bridge");
    return pyodide;
}

async function waitForPyodideScript() {
    for (let i = 0; i < 100; i += 1) {
        if (typeof loadPyodide === "function") {
            return;
        }
        await new Promise((resolve) => setTimeout(resolve, 50));
    }
    throw new Error("Pyodide did not load");
}

async function loadLanguage(lang) {
    currentLang = lang;

    if (translations[lang] === null) {
        const response = await fetch(`static/langs/lang-${lang}.json`);
        translations[lang] = await response.json();
    }

    applyTranslations(lang);
    localStorage.setItem("language", lang);
}

function applyTranslations(lang) {
    document.querySelectorAll("[data-lang]").forEach((el) => {
        const key = el.getAttribute("data-lang");
        if (key.startsWith("note")) {
            el.innerHTML = translations[lang][key] || "";
        } else {
            el.textContent = translations[lang][key] || "";
        }
    });

    const direction = lang === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = lang;
    document.documentElement.dir = direction;
    document.body.lang = lang;
    document.body.style.direction = direction;
    renderCase(lastCase);
}

function renderCase(caseName) {
    document.getElementById("the_case_value_id").innerText = caseName ? t(caseName, caseName) : "";
}

function renderAwlMessage(awlApplied) {
    const isAwlApplied = awlApplied === true || awlApplied === "true" || awlApplied === 1 || awlApplied === "1";
    const awlMessage = document.getElementById("awl-message");
    awlMessage.textContent = isAwlApplied ? t("awl_message", "Awl was applied") : "";
    awlMessage.classList.toggle("is-visible", isAwlApplied);
    awlMessage.dataset.active = isAwlApplied ? "true" : "false";
}

function setBusy(isBusy, message = "") {
    const calculateButton = document.getElementById("calculate-button");
    calculateButton.disabled = isBusy;
    setStatus(isBusy ? message : "");
}

function setStatus(message) {
    document.getElementById("calculator-status").textContent = message;
}

function getStoredTheme() {
    const theme = localStorage.getItem("theme");
    return theme === "dark" || theme === "light" ? theme : null;
}

function getSystemTheme() {
    return window.matchMedia?.(SYSTEM_THEME_QUERY).matches ? "dark" : "light";
}

function applyTheme(theme) {
    document.body.classList.toggle("dark-mode", theme === "dark");
}

function bindSystemThemeChanges() {
    const mediaQuery = window.matchMedia?.(SYSTEM_THEME_QUERY);
    if (!mediaQuery) {
        return;
    }

    const listener = () => {
        if (getStoredTheme() === null) {
            applyTheme(getSystemTheme());
        }
    };

    if (typeof mediaQuery.addEventListener === "function") {
        mediaQuery.addEventListener("change", listener);
    } else if (typeof mediaQuery.addListener === "function") {
        mediaQuery.addListener(listener);
    }
}

function populateFromQuery() {
    const params = new URLSearchParams(window.location.search);
    let foundShareableParams = false;

    const estateParam = params.get("estate");
    if (estateParam !== null) {
        document.getElementById("estate-input").value = estateParam;
        foundShareableParams = true;
    }

    HEIR_PARAM_NAMES.forEach((name, index) => {
        const value = params.get(name);
        if (value !== null) {
            document.getElementById(`number${index}`).value = value;
            foundShareableParams = true;
        }
    });

    return foundShareableParams;
}

function bindEvents() {
    document.getElementById("switch-en").addEventListener("click", () => loadLanguage("en"));
    document.getElementById("switch-ar").addEventListener("click", () => loadLanguage("ar"));
    document.getElementById("dark-mode-toggle").addEventListener("click", () => {
        const nextTheme = document.body.classList.contains("dark-mode") ? "light" : "dark";
        applyTheme(nextTheme);
        localStorage.setItem("theme", nextTheme);
    });
    document.getElementById("estate-input").addEventListener("keydown", checkEnterKey);
}

async function boot() {
    bindEvents();
    bindSystemThemeChanges();

    applyTheme(getStoredTheme() || getSystemTheme());

    await loadLanguage(localStorage.getItem("language") === "en" ? "en" : DEFAULT_LANGUAGE);

    const hasShareableParams = populateFromQuery();
    if (hasShareableParams) {
        fillHeritageColumns({replaceUrl: true});
    }
}

window.validateHusbandWife = validateHusbandWife;
window.isNumberKey = isNumberKey;
window.limitInput = limitInput;
window.checkEnterKey = checkEnterKey;
window.clearTable = clearTable;
window.fillHeritageColumns = fillHeritageColumns;

window.addEventListener("DOMContentLoaded", boot);
